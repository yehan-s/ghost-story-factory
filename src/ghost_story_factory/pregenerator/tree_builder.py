"""
对话树构建器

核心组件，负责完整对话树的生成
使用 BFS 遍历所有可能的选择路径
"""

import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
from copy import deepcopy

from .dialogue_node import DialogueNode, create_root_node
from .state_manager import StateManager
from .progress_tracker import ProgressTracker
from .time_validator import TimeValidator
from .skeleton_model import PlotSkeleton


class DialogueTreeBuilder:
    """对话树构建器"""

    def __init__(
        self,
        city: str,
        synopsis: str,
        gdd_content: str,
        lore_content: str,
        main_story: str,
        test_mode: bool = False,
        plot_skeleton: Optional[PlotSkeleton] = None,
    ):
        """
        初始化构建器

        Args:
            city: 城市名称
            synopsis: 故事简介
            gdd_content: GDD 内容
            lore_content: Lore 内容
            main_story: 主线故事内容
            test_mode: 测试模式
        """
        self.city = city
        self.synopsis = synopsis
        self.gdd = gdd_content
        self.lore = lore_content
        self.main_story = main_story
        self.test_mode = test_mode

        # 可选：故事骨架（v4 guided 模式）
        self.plot_skeleton: Optional[PlotSkeleton] = plot_skeleton
        self.guided_mode: bool = plot_skeleton is not None

        # 核心组件
        self.state_manager = StateManager()
        self.progress_tracker = ProgressTracker()
        self.time_validator = TimeValidator()

        # guided 模式下：优先用骨架配置对 TimeValidator 做一次对齐，
        # 让“主线深度 / 结局数量”的判定来源收敛到 PlotSkeleton，而不是环境变量。
        if self.plot_skeleton is not None:
            try:
                cfg_min_depth = int(self.plot_skeleton.config.min_main_depth)
                if cfg_min_depth > 0:
                    self.time_validator.min_main_path_depth = cfg_min_depth
            except Exception:
                # 骨架里没给出合理的深度约束时，保持原来的环境配置
                pass
            try:
                cfg_target_endings = int(self.plot_skeleton.config.target_endings)
                if cfg_target_endings > 0:
                    self.time_validator.min_endings = cfg_target_endings
            except Exception:
                # 同理，target_endings 异常时不强行覆盖
                pass

        # LLM 生成器（延迟初始化，复用现有的）
        self.choice_generator = None
        self.response_generator = None

        # 配置
        self.max_depth = 20
        self.min_main_path_depth = 15
        self.max_branches_per_node = 3  # 每个节点最多 3 个选择
        # 更密集的检查点：小树也能被恢复，避免重跑
        self.checkpoint_interval = 25

        # 并发与增量检查点
        import os
        self.concurrent_workers = int(os.getenv("TREE_BUILDER_CONCURRENCY", "6"))
        self.incremental_log_path = os.getenv("INCREMENTAL_LOG_PATH", "checkpoints/tree_incremental.jsonl")
        self._inc_log_file = None

        # 安全阈值：防止极端情况下长时间不收敛
        # 说明：这是 v3/v4 共用的“硬闸”，不是 heuristics，只做上限保护。
        self.max_total_nodes = int(os.getenv("MAX_TOTAL_NODES", "300"))
        self.progress_plateau_limit = int(os.getenv("PROGRESS_PLATEAU_LIMIT", "2"))

        # Skeleton 模式与分支控制（用于快速拉深主线）
        try:
            self.max_branches_per_node = int(os.getenv("MAX_BRANCHES_PER_NODE", str(self.max_branches_per_node)))
        except Exception:
            pass
        self.skeleton_mode = os.getenv("SKELETON_MODE", "0") == "1"
        # v4 guided 模式：强制启用 skeleton 行为，并优先采用骨架中的分支上限配置
        if self.guided_mode:
            self.skeleton_mode = True
            try:
                if self.plot_skeleton:
                    self.max_branches_per_node = int(self.plot_skeleton.config.max_branches_per_node)
            except Exception:
                pass

        # Beam 搜索（主线优先），默认关闭以保持向后兼容
        self.beam_mode = os.getenv("BEAM_MODE", "0") == "1"
        self.beam_width = int(os.getenv("BEAM_WIDTH", "50"))

        # 导演上下文（DirectorContext）：记录最近若干步的选择 / 响应 / 节拍信息，
        # 供 Choice / Response Prompt 避免重复并保持节奏一致。
        self.director_context = {
            "recent_choices": [],   # 最近若干次选择文本
            "recent_responses": [], # 最近若干段响应叙事
            "recent_beats": [],     # 最近若干个节拍元数据
        }
        try:
            self.director_context_window = int(os.getenv("DIRECTOR_CONTEXT_WINDOW", "5"))
        except Exception:
            self.director_context_window = 5

    def _init_generators(self):
        """初始化 LLM 生成器（复用现有引擎）"""
        from ..engine.choices import ChoicePointsGenerator
        from ..engine.response import RuntimeResponseGenerator

        self.choice_generator = ChoicePointsGenerator(
            self.gdd,
            self.lore,
            self.main_story
        )

        self.response_generator = RuntimeResponseGenerator(
            self.gdd,
            self.lore,
            self.main_story
        )

        print("✅ LLM 生成器初始化完成")

    # ==================== 骨架辅助方法（guided 模式） ====================

    def _get_flat_beats(self):
        """展开骨架的所有节拍为一维列表（guided 模式使用）"""
        if not self.plot_skeleton:
            return []
        try:
            return list(self.plot_skeleton.beats)
        except Exception:
            return []

    def _beat_for_depth(self, depth: int):
        """
        根据节点深度获取对应节拍。

        约定：
        - root 深度为 0；
        - depth=1 对应第一个节拍；
        - 超出范围时使用最后一个节拍。
        """
        beats = self._get_flat_beats()
        if not beats:
            return None
        # 映射到索引（最小 0，最大 len-1）
        idx = max(0, depth - 1)
        if idx >= len(beats):
            idx = len(beats) - 1
        return beats[idx]

    def _max_children_for_next_depth(self, next_depth: int) -> Optional[int]:
        """获取某一深度下建议的最大子节点数量（若骨架未指定则返回 None）"""
        beat = self._beat_for_depth(next_depth)
        if not beat:
            return None
        try:
            branches = getattr(beat, "branches", None) or []
            if not branches:
                return None
            return max(int(getattr(b, "max_children", 0) or 0) for b in branches) or None
        except Exception:
            return None

    def _allow_ending_for_depth(self, depth: int) -> bool:
        """在 guided 模式下，判断给定深度是否允许出现结局节点。"""
        beat = self._beat_for_depth(depth)
        if not beat:
            return True
        try:
            return bool(getattr(beat, "leads_to_ending", False))
        except Exception:
            return True

    def generate_tree(
        self,
        max_depth: int = 20,
        min_main_path_depth: int = 15,
        checkpoint_path: str = "checkpoints/tree_checkpoint.json"
    ) -> Dict[str, Any]:
        """
        生成完整对话树（BFS遍历）
        支持断点续传！

        Args:
            max_depth: 最大深度
            min_main_path_depth: 主线最小深度
            checkpoint_path: 检查点文件路径

        Returns:
            完整对话树
        """
        self.max_depth = max_depth
        self.min_main_path_depth = min_main_path_depth
        # TimeValidator 的主线深度阈值也跟调用参数保持一致，避免与环境变量产生分裂
        try:
            self.time_validator.min_main_path_depth = int(min_main_path_depth)
        except Exception:
            pass

        # 初始化生成器
        if not self.choice_generator:
            self._init_generators()

        # 🔄 尝试加载检查点（优先完整结构）
        checkpoint = None
        try:
            checkpoint = self.progress_tracker.load_full_checkpoint(checkpoint_path)
        except Exception:
            checkpoint = self.progress_tracker.load_checkpoint(checkpoint_path)

        if checkpoint:
            print("\n✅ 发现未完成的检查点！正在恢复...")
            dialogue_tree = checkpoint.get("tree", {})
            queue_data = checkpoint.get("queue", [])
            node_counter = checkpoint.get("node_counter", 1)
            state_cache = checkpoint.get("state_cache", {})
            scene_index = checkpoint.get("scene_index", {})
            # 兼容旧版本字段
            if not state_cache and checkpoint.get("state_registry"):
                state_cache = checkpoint.get("state_registry", {})

            # 恢复队列
            queue = deque([(node_data, depth) for node_data, depth in queue_data])

            # 恢复状态管理器
            self.state_manager.state_cache = state_cache or {}
            self.state_manager.scene_index = scene_index or {}

            print(f"   已恢复 {len(dialogue_tree)} 个节点")
            print(f"   队列中还有 {len(queue)} 个待处理节点")
            print(f"   从节点 #{node_counter} 继续生成...\n")

            # 开始进度追踪（恢复模式）
            self.progress_tracker.start(max_depth, test_mode=self.test_mode)

        else:
            print("\n🆕 开始新的对话树生成...\n")

            # 开始进度追踪
            self.progress_tracker.start(max_depth, test_mode=self.test_mode)

            # 创建根节点
            root_node = create_root_node()

            # 生成开场叙事
            print("📝 生成开场叙事...")
            root_node.narrative = self._generate_opening()

            # 生成首批选择
            print("🔀 生成首批选择...")
            root_node.choices = self._generate_choices(root_node)

            # 注册根节点状态
            state_hash = self.state_manager.get_state_hash(root_node.game_state)
            root_node.state_hash = state_hash
            self.state_manager.register_state(state_hash, "root")

            # 初始化对话树和队列（确保选择已生成）
            root_dict = root_node.to_dict()
            dialogue_tree = {
                "root": root_dict
            }
            queue = deque([(root_dict, 0)])  # (节点字典, 深度)

            node_counter = 1

        # 打开增量日志
        self._open_incremental_log()

        # BFS/Beam 遍历（批量并发扩展子节点）
        import concurrent.futures, threading
        id_lock = threading.Lock()
        while queue:
            current_node_dict, depth = queue.popleft()
            current_node = DialogueNode.from_dict(current_node_dict)

            # 检查终止条件
            if self.state_manager.should_prune(current_node.game_state, depth, max_depth):
                continue

            # 为每个选择生成子节点（并发限制）
            # Skeleton / guided 模式：对选择进行排序，使推进/critical 优先
            choices_all = list(current_node.choices or [])
            if self.skeleton_mode and choices_all:
                def _score_choice(ch: dict) -> int:
                    score = 0
                    if ch.get("choice_type") == "critical" or ch.get("critical") is True:
                        score += 100
                    cons = ch.get("consequences") or {}
                    if isinstance(cons, dict):
                        if cons.get("critical") is True:
                            score += 80
                        for k in ("next_scene", "CT", "next_event"):
                            if k in cons:
                                score += 50
                        for k in ("time", "timestamp", "time_skip"):
                            if k in cons:
                                score += 20
                    # 轻量关键词启发（仅在文本存在时）
                    txt = (ch.get("choice_text") or "")
                    if any(kw in txt for kw in ("前往", "推进", "直接", "关键")):
                        score += 10
                    return -score  # 小顶堆：负分排序即高分在前
                try:
                    choices_all.sort(key=_score_choice)
                except Exception:
                    pass

            # guided 模式：根据骨架对下一层深度的分支数做约束；否则使用全局配置
            if self.guided_mode and choices_all:
                max_children = self._max_children_for_next_depth(depth + 1)
                if max_children is not None and max_children > 0:
                    choices_batch = choices_all[:max_children]
                else:
                    choices_batch = choices_all[:self.max_branches_per_node]
            else:
                choices_batch = choices_all[:self.max_branches_per_node]

            def _expand_choice(choice):
                # 创建新状态
                new_state = self.state_manager.update_state(
                    current_node.game_state,
                    choice.get("consequences", {})
                )

                # 记录最近一次选择文本及本轮所有选项文本，供后续节点在 Prompt 中做“去重复”约束
                try:
                    new_state["last_choice_text"] = choice.get("choice_text", "")
                    all_texts = [
                        c.get("choice_text", "")
                        for c in choices_all
                        if isinstance(c, dict)
                    ]
                    new_state["last_choices_texts"] = [t for t in all_texts if t]
                except Exception:
                    pass

                # 计算状态哈希
                state_hash = self.state_manager.get_state_hash(new_state)

                # 检查状态是否已存在（去重）
                existing_node_id = self.state_manager.get_node_by_state(state_hash)
                if existing_node_id:
                    return {
                        "type": "reuse",
                        "parent_id": current_node.node_id,
                        "choice_id": choice.get("choice_id"),
                        "existing_node_id": existing_node_id
                    }

                # 近似状态匹配（同场景合并）
                approx_node_id = self.state_manager.find_approximate(new_state)
                if approx_node_id:
                    return {
                        "type": "reuse",
                        "parent_id": current_node.node_id,
                        "choice_id": choice.get("choice_id"),
                        "existing_node_id": approx_node_id
                    }

                # 创建新节点
                child_node = DialogueNode(
                    node_id="",  # 暂不分配，主线程统一编号
                    scene=new_state.get("current_scene", current_node.scene),
                    depth=depth + 1,
                    game_state=new_state,
                    state_hash=state_hash,
                    parent_id=current_node.node_id,
                    parent_choice_id=choice.get("choice_id"),
                    generated_at=datetime.now().isoformat()
                )

                # 生成响应文本
                child_node.narrative = self._generate_response(choice, new_state)

                # 更新导演上下文（最近选择 / 响应 / 节拍）
                try:
                    beat_meta = None
                    if self.guided_mode and self.plot_skeleton is not None:
                        beat = self._beat_for_depth(depth + 1)
                        if beat is not None:
                            beat_meta = {
                                "depth": depth + 1,
                                "beat_type": getattr(beat, "beat_type", None),
                                "tension_level": getattr(beat, "tension_level", None),
                                "is_critical": getattr(beat, "is_critical_branch_point", None),
                            }
                    self._update_director_context(choice, child_node, beat_meta)
                except Exception:
                    pass

                # 检查是否结局；guided 模式下根据骨架控制结局出现位置
                child_node.is_ending = self._check_ending(new_state)
                if self.guided_mode and child_node.is_ending:
                    # 若骨架不允许当前深度出现结局，则强制改为非结局继续推进
                    if not self._allow_ending_for_depth(depth + 1):
                        child_node.is_ending = False

                if child_node.is_ending:
                    child_node.ending_type = self._determine_ending_type(new_state)
                else:
                    # 生成下一批选择
                    child_node.choices = self._generate_choices(child_node)

                return {
                    "type": "new",
                    "parent_id": current_node.node_id,
                    "choice": choice,
                    "child": child_node
                }

            # 并发执行扩展
            results: List[dict] = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
                futures = [executor.submit(_expand_choice, c) for c in choices_batch]
                for fut in concurrent.futures.as_completed(futures):
                    try:
                        results.append(fut.result())
                    except Exception as e:
                        print(f"⚠️  子节点生成异常: {e}")

            # 汇总结果（保证数据一致性）
            for res in results:
                if res["type"] == "reuse":
                    choice_id = res["choice_id"]
                    existing_node_id = res["existing_node_id"]
                    parent_node_id = res["parent_id"]
                    for parent_choice in dialogue_tree[parent_node_id]["choices"]:
                        if parent_choice.get("choice_id") == choice_id:
                            parent_choice["next_node_id"] = existing_node_id
                            break
                    continue

                child_node: DialogueNode = res["child"]
                choice = res["choice"]

                # 分配唯一ID（线程安全）
                with id_lock:
                    child_node.node_id = f"node_{node_counter:04d}"
                    node_counter += 1

                # 添加到树
                dialogue_tree[child_node.node_id] = child_node.to_dict()
                self.state_manager.register_state(child_node.state_hash, child_node.node_id)
                self.state_manager.register_scene_index(child_node.game_state, child_node.state_hash)
                choice["next_node_id"] = child_node.node_id

                # 记录父子关系
                parent_node_id = current_node.node_id
                dialogue_tree[parent_node_id]["children"].append(child_node.node_id)
                for parent_choice in dialogue_tree[parent_node_id]["choices"]:
                    if parent_choice.get("choice_id") == choice.get("choice_id"):
                        parent_choice["next_node_id"] = child_node.node_id
                        break

                # 加入队列
                if not child_node.is_ending:
                    queue.append((child_node.to_dict(), depth + 1))

                # 增量日志记录
                self._append_incremental_log({
                    "event": "add_node",
                    "node": child_node.to_dict()
                })

                # 更新进度
                self.progress_tracker.update(
                    current_depth=depth + 1,
                    node_count=len(dialogue_tree),
                    current_branch=f"{child_node.scene} → {choice.get('choice_text', '')[:20]}..."
                )

            # Beam：收缩前沿，优先保留更“推进”的节点
            if self.beam_mode and len(queue) > self.beam_width:
                try:
                    ranked = sorted(list(queue), key=lambda t: -self._score_node(t[0], t[1]))
                    queue = deque(ranked[: self.beam_width])
                except Exception:
                    pass

            # 定期保存检查点（包含完整状态）
            if len(dialogue_tree) % self.checkpoint_interval == 0:
                self._save_full_checkpoint(
                    dialogue_tree,
                    queue,
                    node_counter,
                    checkpoint_path
                )

            # 全局节点上限保护（避免在低质量上下文中无限扩张）
            if len(dialogue_tree) >= self.max_total_nodes:
                print(f"⚠️  达到全局节点上限（{self.max_total_nodes}），停止本轮扩展")
                break

        # 验证 + 持续扩展（同一轮）
        print("📊 验证游戏时长...")
        report = self.time_validator.get_validation_report(dialogue_tree)

        print(f"   总节点数: {report['total_nodes']}")
        print(f"   主线深度: {report['main_path_depth']}")
        print(f"   预计时长: {report['estimated_duration_minutes']} 分钟")
        print(f"   结局数量: {report['ending_count']}")
        print(f"   结局达标: {'是' if report.get('passes_endings_check') else '否'} (≥ {self.time_validator.min_endings})")

        def _passes(r: Dict[str, Any]) -> bool:
            return (
                r['passes_duration_check']
                and r['main_path_depth'] >= self.min_main_path_depth
                and r.get('passes_endings_check', True)
            )

        # 允许在同一轮内继续扩展，直至达标或达到尝试上限
        # 说明：EXTEND_ON_FAIL_ATTEMPTS 完全是 v3 legacy heuristics，通过环境放宽“死磕”次数；
        # guided 模式仅允许一次轻量扩展，不参与这个升级游戏。
        extend_attempts = int(os.getenv("EXTEND_ON_FAIL_ATTEMPTS", "2"))
        if self.guided_mode and extend_attempts > 1:
            extend_attempts = 1
        attempt_idx = 0
        plateau_rounds = 0
        last_metrics = (
            report['main_path_depth'],
            report['estimated_duration_minutes'],
            report['ending_count']
        )
        while not _passes(report) and attempt_idx < extend_attempts:
            attempt_idx += 1
            print(f"⏩ 扩展尝试 {attempt_idx}/{extend_attempts}：继续从叶子节点加深主线/增加时长...")

            # 选取可扩展的叶子（非结局、无子节点、深度未到上限），按深度降序优先加深
            leaves: List[Any] = []
            for nid, node in dialogue_tree.items():
                if not isinstance(node, dict):
                    continue
                if node.get("is_ending"):
                    continue
                if len(node.get("children", [])) > 0:
                    continue
                if int(node.get("depth", 0)) >= self.max_depth:
                    continue
                leaves.append((nid, node))

            if not leaves:
                print("ℹ️  没有可扩展的叶子节点，终止扩展。")
                break

            leaves.sort(key=lambda x: int(x[1].get("depth", 0)), reverse=True)

            # 基于叶子重建队列并继续 BFS 扩展（顺序执行，保证稳定性）
            queue = deque([(dialogue_tree[nid], int(node.get("depth", 0))) for nid, node in leaves])

            import threading
            id_lock = threading.Lock()

            while queue:
                current_node_dict, depth = queue.popleft()
                current_node = DialogueNode.from_dict(current_node_dict)

                if self.state_manager.should_prune(current_node.game_state, depth, max_depth):
                    continue

                choices_all = list(current_node.choices or [])
                if self.skeleton_mode and choices_all:
                    def _score_choice2(ch: dict) -> int:
                        score = 0
                        if ch.get("choice_type") == "critical" or ch.get("critical") is True:
                            score += 100
                        cons = ch.get("consequences") or {}
                        if isinstance(cons, dict):
                            if cons.get("critical") is True:
                                score += 80
                            for k in ("next_scene", "CT", "next_event"):
                                if k in cons:
                                    score += 50
                            for k in ("time", "timestamp", "time_skip"):
                                if k in cons:
                                    score += 20

                        txt = (ch.get("choice_text") or "")
                        if any(kw in txt for kw in ("前往", "推进", "直接", "关键")):
                            score += 10
                        return -score
                    try:
                        choices_all.sort(key=_score_choice2)
                    except Exception:
                        pass
                choices_batch = choices_all[:self.max_branches_per_node]

                for choice in choices_batch:
                    # 创建新状态
                    new_state = self.state_manager.update_state(
                        current_node.game_state,
                        choice.get("consequences", {})
                    )

                    # 计算状态哈希与去重/近似合并
                    state_hash = self.state_manager.get_state_hash(new_state)
                    existing_node_id = self.state_manager.get_node_by_state(state_hash)
                    if existing_node_id:
                        for parent_choice in dialogue_tree[current_node.node_id]["choices"]:
                            if parent_choice.get("choice_id") == choice.get("choice_id"):
                                parent_choice["next_node_id"] = existing_node_id
                                break
                        continue

                    approx_node_id = self.state_manager.find_approximate(new_state)
                    if approx_node_id:
                        for parent_choice in dialogue_tree[current_node.node_id]["choices"]:
                            if parent_choice.get("choice_id") == choice.get("choice_id"):
                                parent_choice["next_node_id"] = approx_node_id
                                break
                        continue

                    # 创建新节点并生成内容
                    child_node = DialogueNode(
                        node_id="",
                        scene=new_state.get("current_scene", current_node.scene),
                        depth=depth + 1,
                        game_state=new_state,
                        state_hash=state_hash,
                        parent_id=current_node.node_id,
                        parent_choice_id=choice.get("choice_id"),
                        generated_at=datetime.now().isoformat()
                    )

                    child_node.narrative = self._generate_response(choice, new_state)
                    child_node.is_ending = self._check_ending(new_state)
                    if child_node.is_ending:
                        child_node.ending_type = self._determine_ending_type(new_state)
                    else:
                        child_node.choices = self._generate_choices(child_node)

                    with id_lock:
                        child_node.node_id = f"node_{node_counter:04d}"
                        node_counter += 1

                    # 挂接到树
                    dialogue_tree[child_node.node_id] = child_node.to_dict()
                    self.state_manager.register_state(child_node.state_hash, child_node.node_id)
                    self.state_manager.register_scene_index(child_node.game_state, child_node.state_hash)

                    for parent_choice in dialogue_tree[current_node.node_id]["choices"]:
                        if parent_choice.get("choice_id") == choice.get("choice_id"):
                            parent_choice["next_node_id"] = child_node.node_id
                            break
                    dialogue_tree[current_node.node_id]["children"].append(child_node.node_id)

                    # 入队继续扩展
                    if not child_node.is_ending:
                        queue.append((child_node.to_dict(), depth + 1))

                    # 增量日志 & 进度
                    self._append_incremental_log({"event": "add_node", "node": child_node.to_dict()})
                    self.progress_tracker.update(
                        current_depth=depth + 1,
                        node_count=len(dialogue_tree),
                        current_branch=f"{child_node.scene} → {choice.get('choice_text', '')[:20]}..."
                    )

                # Beam：收缩前沿
                if self.beam_mode and len(queue) > self.beam_width:
                    try:
                        ranked = sorted(list(queue), key=lambda t: -self._score_node(t[0], t[1]))
                        queue = deque(ranked[: self.beam_width])
                    except Exception:
                        pass

            # 扩展一轮后再次验证
            report = self.time_validator.get_validation_report(dialogue_tree)
            print("📊 扩展后再次验证...")
            print(f"   总节点数: {report['total_nodes']}")
            print(f"   主线深度: {report['main_path_depth']}")
            print(f"   预计时长: {report['estimated_duration_minutes']} 分钟")
            print(f"   结局数量: {report['ending_count']}")
            print(f"   结局达标: {'是' if report.get('passes_endings_check') else '否'} (≥ {self.time_validator.min_endings})")

            # 进展检测：若主线深度/预计时长/结局数量均无提升，计为平台期
            current_metrics = (
                report['main_path_depth'],
                report['estimated_duration_minutes'],
                report['ending_count']
            )
            if current_metrics <= last_metrics:
                plateau_rounds += 1
                print(f"ℹ️  本轮无显著进展（平台 {plateau_rounds}/{self.progress_plateau_limit}）")
                if plateau_rounds >= self.progress_plateau_limit:
                    print("⚠️  连续多轮无进展，停止扩展以避免死循环")
                    break
            else:
                plateau_rounds = 0
                last_metrics = current_metrics
            print(f"   结局达标: {'是' if report.get('passes_endings_check') else '否'} (≥ {self.time_validator.min_endings})")

        # 最终判定
        # 说明：
        # - v3 兼容模式（非 guided）：仍作为硬性 gating，未达标时抛异常；
        # - v4 guided 模式：TimeValidator 只做 sanity check，未达标时打印告警，
        #   由上层基于 story_report 决定是否视为“合格故事”，不再在此处直接终止流水线。
        strict_mode = (not self.test_mode) and (not self.guided_mode)

        if not report['passes_duration_check']:
            if not strict_mode:
                print(
                    f"⚠️  [结构告警] 预计时长未达标："
                    f"{report['estimated_duration_minutes']} 分钟 < {self.time_validator.min_duration_minutes} 分钟"
                )
            else:
                # 自动降级策略（一次性尝试，仅 v3 legacy）
                downgraded = False
                est = report['estimated_duration_minutes']
                if est >= 9 and est < self.time_validator.min_duration_minutes:
                    # 1) 降低最小游戏时长到 10（仅非 guided 模式）
                    os.environ['MIN_DURATION_MINUTES'] = '10'
                    downgraded = True
                if not downgraded and self.progress_plateau_limit > 2:
                    # 2) 增加扩展轮次 +2（仅非 guided 模式）
                    cur = int(os.getenv('EXTEND_ON_FAIL_ATTEMPTS', '2'))
                    os.environ['EXTEND_ON_FAIL_ATTEMPTS'] = str(cur + 2)
                    downgraded = True
                if not downgraded:
                    # 3) 加速 critical 注入（仅非 guided 模式）
                    os.environ['FORCE_CRITICAL_INTERVAL'] = '2'
                    downgraded = True
                if downgraded:
                    print("🔧 [v3 legacy] 触发自动降级策略（通过环境变量放宽阈值），建议重跑同轮以尝试达标")
                # 明确结束本轮追踪
                self.progress_tracker.finish(success=False)
                raise ValueError(
                    f"游戏时长不足：{report['estimated_duration_minutes']} 分钟 < {self.time_validator.min_duration_minutes} 分钟"
                )

        if report['main_path_depth'] < self.min_main_path_depth:
            if not strict_mode:
                print(
                    f"⚠️  [结构告警] 主线深度未达标："
                    f"{report['main_path_depth']} < {self.min_main_path_depth}"
                )
            else:
                # 明确结束本轮追踪（仅 v3 兼容路径）
                self.progress_tracker.finish(success=False)
                try:
                    from ..utils.logging_utils import get_logger
                    get_logger()[0].error(
                        "验证失败：主线深度不足 depth=%s < min=%s",
                        report['main_path_depth'],
                        self.min_main_path_depth,
                    )
                except Exception:
                    pass
                raise ValueError(f"主线深度不足：{report['main_path_depth']} < {self.min_main_path_depth}")

        # 结局数量门槛
        if not report.get('passes_endings_check', True):
            if not strict_mode:
                print(
                    f"⚠️  [结构告警] 结局数量未达标："
                    f"{report['ending_count']} < {self.time_validator.min_endings}"
                )
            else:
                # 自动降级：加速 critical 注入（仅 v3 legacy）
                os.environ['FORCE_CRITICAL_INTERVAL'] = '2'
                print("🔧 [v3 legacy] 触发自动降级：FORCE_CRITICAL_INTERVAL=2，仅旧结构模式生效")
                self.progress_tracker.finish(success=False)
                raise ValueError(f"结局数量不足：{report['ending_count']} < {self.time_validator.min_endings}")

        # 完成追踪与清理检查点
        self.progress_tracker.finish(success=True)
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            print(f"💾 检查点已清理：{checkpoint_path}\n")

        # 关闭增量日志
        self._close_incremental_log()

        return dialogue_tree

    def _score_node(self, node_dict: Dict[str, Any], depth: int) -> int:
        """为 Beam/Skeleton 计算节点优先级分数。

        目标：主线推进优先。
        简化启发：
        - 深度越大分越高
        - 子节点中存在 critical/时间推进/场景推进的选项 → 加分
        - 结局节点不入队，这里无需额外惩罚
        """
        try:
            score = depth * 100
            # 观察该节点可用选择，估计可推进性
            choices = node_dict.get("choices") or []
            has_critical = any((c.get("choice_type") == "critical") or (c.get("critical") is True) for c in choices)
            if has_critical:
                score += 80
            for c in choices:
                cons = c.get("consequences") or {}
                if isinstance(cons, dict):
                    if cons.get("critical") is True:
                        score += 50
                    if any(k in cons for k in ("next_scene", "CT", "next_event")):
                        score += 40
                    if any(k in cons for k in ("time", "timestamp", "time_skip")):
                        score += 15
                txt = (c.get("choice_text") or "")
                if any(kw in txt for kw in ("前往", "推进", "直接", "关键")):
                    score += 5
            return int(score)
        except Exception:
            return depth * 100

    def _generate_opening(self) -> str:
        """生成开场叙事"""
        # 使用现有的开场生成逻辑
        try:
            from crewai import Agent, Task, Crew, LLM

            kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
            kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
            kimi_model = os.getenv("KIMI_MODEL_OPENING", "kimi-k2-0905-preview")

            llm = LLM(
                model=kimi_model,
                api_key=kimi_key,
                base_url=kimi_base
            )

            prompt = f"""根据以下故事简介，生成一段引人入胜的开场叙事（300-500字）：

{self.synopsis}

要求：
1. 使用第二人称视角（"你"）
2. 介绍主角身份和任务
3. 营造恐怖悬疑氛围
4. 为后续选择做铺垫

只返回叙事文本，不要其他内容。"""

            agent = Agent(
                role="恐怖故事作家",
                goal="创作引人入胜的开场",
                backstory=f"你已经阅读了完整的故事背景：\n{self.main_story[:2000]}",
                llm=llm,
                verbose=False
            )

            task = Task(
                description=prompt,
                agent=agent,
                expected_output="开场叙事文本"
            )

            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()

            return str(result).strip()

        except Exception as e:
            print(f"⚠️  开场生成失败，使用默认文本：{e}")
            return f"深夜，{self.city}的街道笼罩在诡异的氛围中。作为{self.synopsis[:50]}，你开始了这段不寻常的经历..."

    def _generate_choices(self, node: DialogueNode) -> List[Dict[str, Any]]:
        """生成选择点"""
        if not self.choice_generator:
            return []

        try:
            # 转换为 GameState 对象（简化版）
            from ..engine.state import GameState

            state = GameState()
            state.PR = node.game_state.get("PR", 5)
            state.GR = node.game_state.get("GR", 0)
            state.WF = node.game_state.get("WF", 0)
            state.current_scene = node.scene
            state.inventory = node.game_state.get("inventory", [])
            state.flags = node.game_state.get("flags", {})
            state.time = node.game_state.get("time", "00:00")

            # 构造简化叙事上下文：上一节点叙事 + 最近一次选择，作为“避免重复”的提示
            last_narrative = node.narrative or ""
            last_choice = ""
            try:
                # 在 game_state 中查找上一选择文本（由 _expand_choice 写入）
                last_choice = node.game_state.get("last_choice_text", "")
            except Exception:
                last_choice = ""

            narrative_context = last_narrative
            if last_choice:
                narrative_context = f"{last_narrative}\n\n[上一选择] {last_choice}"

            # 最近一轮已出现的选项文本（上一层节点写入到 game_state）
            recent_choices: List[str] = []
            try:
                recent_raw = node.game_state.get("last_choices_texts") or []
                if isinstance(recent_raw, list):
                    recent_choices = [str(x) for x in recent_raw if x]
            except Exception:
                recent_choices = []

            # guided 模式下：根据节点深度查找下一层对应的骨架节拍信息
            beat_type = None
            tension_level = None
            is_critical = None
            beat_leads_to_ending = None
            if self.guided_mode and self.plot_skeleton is not None:
                try:
                    beat = self._beat_for_depth(node.depth + 1)
                    if beat is not None:
                        beat_type = getattr(beat, "beat_type", None)
                        tension_level = getattr(beat, "tension_level", None)
                        is_critical = getattr(beat, "is_critical_branch_point", None)
                except Exception:
                    beat_type = None
                    tension_level = None
                    is_critical = None
                try:
                    if beat is not None:
                        beat_leads_to_ending = getattr(beat, "leads_to_ending", None)
                except Exception:
                    beat_leads_to_ending = None

            # 调用生成器（注意参数顺序：scene, state）
            choices = self.choice_generator.generate_choices(
                node.scene,
                state,
                narrative_context=narrative_context,
                beat_type=beat_type,
                tension_level=tension_level,
                is_critical_beat=is_critical,
                beat_leads_to_ending=beat_leads_to_ending,
                recent_choices=recent_choices,
            )

            # 转换为字典格式
            return [
                {
                    "choice_id": choice.choice_id,
                    "choice_text": choice.choice_text,
                    "choice_type": choice.choice_type,
                    "consequences": choice.consequences,
                    "preconditions": choice.preconditions
                }
                for choice in choices
            ]

        except Exception as e:
            print(f"⚠️  选择生成失败：{e}")
            return self._get_default_choices()

    def _generate_response(self, choice: Dict[str, Any], new_state: Dict[str, Any]) -> str:
        """生成响应文本"""
        if not self.response_generator:
            return f"你选择了：{choice.get('choice_text', '')}..."

        try:
            # 转换为 GameState 对象
            from ..engine.state import GameState

            state = GameState()
            state.PR = new_state.get("PR", 5)
            state.GR = new_state.get("GR", 0)
            state.WF = new_state.get("WF", 0)
            state.current_scene = new_state.get("current_scene", "S1")
            state.inventory = new_state.get("inventory", [])
            state.flags = new_state.get("flags", {})
            state.time = new_state.get("time", "00:00")

            # 创建简化的 Choice 对象
            from ..engine.choices import Choice

            choice_obj = Choice(
                choice_id=choice.get("choice_id", "A"),
                choice_text=choice.get("choice_text", ""),
                choice_type=choice.get("choice_type", "normal"),
                consequences=choice.get("consequences", {}),
                preconditions=choice.get("preconditions", {})
            )

            # 调用生成器
            response = self.response_generator.generate_response(
                choice_obj,
                state,
                apply_consequences=False,
                director_context=self.director_context,
            )
            return response

        except Exception as e:
            print(f"⚠️  响应生成失败：{e}")
            return f"你选择了{choice.get('choice_text', '')}，故事继续发展..."

    def _update_director_context(
        self,
        choice: Dict[str, Any],
        node: DialogueNode,
        beat_meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """更新导演上下文（最近若干步的选择 / 响应 / 节拍）。

        说明：
        - 这是一个纯粹的“摘要”结构，不参与状态判定；
        - 仅供 Choice/Response Prompt 用于避免重复和保持节奏一致。
        """
        try:
            txt = str(choice.get("choice_text", "") or "").strip()
            if txt:
                self.director_context["recent_choices"].append(txt)

            nar = str(node.narrative or "").strip()
            if nar:
                self.director_context["recent_responses"].append(nar)

            if beat_meta:
                self.director_context["recent_beats"].append(beat_meta)

            # 窗口裁剪
            w = max(1, int(self.director_context_window or 5))
            for key in ("recent_choices", "recent_responses", "recent_beats"):
                seq = self.director_context.get(key) or []
                if len(seq) > w:
                    self.director_context[key] = seq[-w:]
        except Exception:
            # 完全不影响主流程
            pass

    def _check_ending(self, state: Dict[str, Any]) -> bool:
        """检查是否到达结局"""
        # 1. PR 过高
        if state.get("PR", 0) >= 100:
            return True

        # 2. 有结局标志
        flags = state.get("flags", {})
        if any(k.startswith("结局_") for k in flags.keys()):
            return True

        return False

    def _determine_ending_type(self, state: Dict[str, Any]) -> str:
        """判断结局类型"""
        flags = state.get("flags", {})

        # 查找结局标志
        for flag_name in flags.keys():
            if flag_name.startswith("结局_"):
                return flag_name.replace("结局_", "")

        # 根据 PR/GR 判断
        pr = state.get("PR", 0)
        gr = state.get("GR", 0)

        if pr >= 100:
            return "恐惧崩溃"
        elif gr >= 80:
            return "真相大白"
        elif gr >= 50:
            return "部分真相"
        else:
            return"未知结局"

    def _get_default_choices(self) -> List[Dict[str, Any]]:
        """获取默认选择（当生成失败时）"""
        return [
            {
                "choice_id": "A",
                "choice_text": "继续调查",
                "choice_type": "normal",
                "consequences": {"GR": 5, "time": "+5min"},
                "preconditions": {}
            },
            {
                "choice_id": "B",
                "choice_text": "离开此地",
                "choice_type": "normal",
                "consequences": {"PR": -3, "time": "+5min"},
                "preconditions": {}
            }
        ]

    def _save_full_checkpoint(
        self,
        dialogue_tree: Dict[str, Any],
        queue: deque,
        node_counter: int,
        checkpoint_path: str
    ):
        """
        保存完整检查点（包含队列和状态管理器）

        Args:
            dialogue_tree: 当前对话树
            queue: BFS 队列
            node_counter: 节点计数器
            checkpoint_path: 检查点文件路径
        """
        import json
        from pathlib import Path

        # 序列化队列（deque -> list）
        queue_data = list(queue)

        # 构建检查点数据
        checkpoint = {
            "generated_at": datetime.now().isoformat(),
            "nodes_count": len(dialogue_tree),
            "current_depth": self.progress_tracker.current_depth,
            "total_tokens": self.progress_tracker.total_tokens,
            "elapsed_time": time.time() - self.progress_tracker.start_time,
            "tree": dialogue_tree,
            "queue": queue_data,
            "node_counter": node_counter,
            "state_cache": self.state_manager.state_cache,
            "scene_index": self.state_manager.scene_index,
            "max_depth": self.max_depth,
            "min_main_path_depth": self.min_main_path_depth
        }

        # 确保目录存在
        checkpoint_file = Path(checkpoint_path)
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        # 保存到文件
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        print(f"💾 [检查点] 已保存 {len(dialogue_tree)} 个节点 → {checkpoint_path}")

    def _open_incremental_log(self):
        """打开增量 JSONL 日志文件（追加模式）"""
        from pathlib import Path
        Path(self.incremental_log_path).parent.mkdir(parents=True, exist_ok=True)
        self._inc_log_file = open(self.incremental_log_path, 'a', encoding='utf-8')

    def _append_incremental_log(self, record: Dict[str, Any]):
        """写入一条增量记录"""
        if not self._inc_log_file:
            return
        import json
        record_with_ts = {"ts": datetime.now().isoformat(), **record}
        self._inc_log_file.write(json.dumps(record_with_ts, ensure_ascii=False) + "\n")
        self._inc_log_file.flush()

    def _close_incremental_log(self):
        """关闭增量日志文件"""
        try:
            if self._inc_log_file:
                self._inc_log_file.close()
        finally:
            self._inc_log_file = None
