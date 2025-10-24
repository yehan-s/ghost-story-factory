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


class DialogueTreeBuilder:
    """对话树构建器"""

    def __init__(
        self,
        city: str,
        synopsis: str,
        gdd_content: str,
        lore_content: str,
        main_story: str,
        test_mode: bool = False
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

        # 核心组件
        self.state_manager = StateManager()
        self.progress_tracker = ProgressTracker()
        self.time_validator = TimeValidator()

        # LLM 生成器（延迟初始化，复用现有的）
        self.choice_generator = None
        self.response_generator = None

        # 配置
        self.max_depth = 20
        self.min_main_path_depth = 15
        self.max_branches_per_node = 3  # 每个节点最多 3 个选择
        self.checkpoint_interval = 50  # 每 50 个节点保存一次检查点

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

        # 初始化生成器
        if not self.choice_generator:
            self._init_generators()

        # 🔄 尝试加载检查点
        checkpoint = self.progress_tracker.load_checkpoint(checkpoint_path)

        if checkpoint:
            print("\n✅ 发现未完成的检查点！正在恢复...")
            dialogue_tree = checkpoint.get("tree", {})
            queue_data = checkpoint.get("queue", [])
            node_counter = checkpoint.get("node_counter", 1)
            state_registry = checkpoint.get("state_registry", {})

            # 恢复队列
            queue = deque([(node_data, depth) for node_data, depth in queue_data])

            # 恢复状态管理器
            self.state_manager.state_registry = state_registry

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

        # BFS 遍历
        while queue:
            current_node_dict, depth = queue.popleft()
            current_node = DialogueNode.from_dict(current_node_dict)

            # 检查终止条件
            if self.state_manager.should_prune(current_node.game_state, depth, max_depth):
                continue

            # 为每个选择生成子节点
            for choice in current_node.choices[:self.max_branches_per_node]:
                # 创建新状态
                new_state = self.state_manager.update_state(
                    current_node.game_state,
                    choice.get("consequences", {})
                )

                # 计算状态哈希
                state_hash = self.state_manager.get_state_hash(new_state)

                # 检查状态是否已存在（去重）
                existing_node_id = self.state_manager.get_node_by_state(state_hash)
                if existing_node_id:
                    # 复用已有节点
                    choice["next_node_id"] = existing_node_id

                    # 同步更新父节点中的choice（确保next_node_id被保存）
                    parent_node_id = current_node.node_id
                    for parent_choice in dialogue_tree[parent_node_id]["choices"]:
                        if parent_choice.get("choice_id") == choice.get("choice_id"):
                            parent_choice["next_node_id"] = existing_node_id
                            break
                    continue

                # 创建新节点
                child_node = DialogueNode(
                    node_id=f"node_{node_counter:04d}",
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

                # 检查是否结局
                child_node.is_ending = self._check_ending(new_state)
                if child_node.is_ending:
                    child_node.ending_type = self._determine_ending_type(new_state)
                else:
                    # 生成下一批选择
                    child_node.choices = self._generate_choices(child_node)

                # 添加到树
                dialogue_tree[child_node.node_id] = child_node.to_dict()
                self.state_manager.register_state(state_hash, child_node.node_id)
                choice["next_node_id"] = child_node.node_id

                # 更新父节点的子节点列表和选择
                parent_node_id = current_node.node_id
                dialogue_tree[parent_node_id]["children"].append(child_node.node_id)

                # 同步更新父节点中的choice（确保next_node_id被保存）
                for parent_choice in dialogue_tree[parent_node_id]["choices"]:
                    if parent_choice.get("choice_id") == choice.get("choice_id"):
                        parent_choice["next_node_id"] = child_node.node_id
                        break

                # 加入队列（如果不是结局）
                if not child_node.is_ending:
                    queue.append((child_node.to_dict(), depth + 1))

                node_counter += 1

                # 更新进度
                self.progress_tracker.update(
                    current_depth=depth + 1,
                    node_count=len(dialogue_tree),
                    current_branch=f"{child_node.scene} → {choice.get('choice_text', '')[:20]}..."
                )

                # 定期保存检查点（包含完整状态）
                if len(dialogue_tree) % self.checkpoint_interval == 0:
                    self._save_full_checkpoint(
                        dialogue_tree,
                        queue,
                        node_counter,
                        checkpoint_path
                    )

        # 完成追踪
        self.progress_tracker.finish(success=True)

        # 🗑️ 删除检查点文件（生成成功）
        import os
        if os.path.exists(checkpoint_path):
            os.remove(checkpoint_path)
            print(f"💾 检查点已清理：{checkpoint_path}\n")

        # 验证游戏时长
        print("📊 验证游戏时长...")
        report = self.time_validator.get_validation_report(dialogue_tree)

        print(f"   总节点数: {report['total_nodes']}")
        print(f"   主线深度: {report['main_path_depth']}")
        print(f"   预计时长: {report['estimated_duration_minutes']} 分钟")
        print(f"   结局数量: {report['ending_count']}")

        if not report['passes_duration_check']:
            raise ValueError(f"游戏时长不足：{report['estimated_duration_minutes']} 分钟 < 15 分钟")

        if not report['passes_depth_check']:
            raise ValueError(f"主线深度不足：{report['main_path_depth']} < 15")

        return dialogue_tree

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

            # 调用生成器（注意参数顺序：scene, state）
            choices = self.choice_generator.generate_choices(node.scene, state)

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
            response = self.response_generator.generate_response(choice_obj, state)
            return response

        except Exception as e:
            print(f"⚠️  响应生成失败：{e}")
            return f"你选择了{choice.get('choice_text', '')}，故事继续发展..."

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
                "consequences": {"GR": 5},
                "preconditions": {}
            },
            {
                "choice_id": "B",
                "choice_text": "离开此地",
                "choice_type": "normal",
                "consequences": {"PR": -3},
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
            "state_registry": self.state_manager.state_registry,
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

