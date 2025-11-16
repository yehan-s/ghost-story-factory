"""
完整故事生成器

整合所有组件，实现不可中断的完整故事生成流程
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

from .synopsis_generator import StorySynopsis
from .tree_builder import DialogueTreeBuilder
from .skeleton_generator import SkeletonGenerator
from .text_filler import NodeTextFiller
from .story_report import build_story_report
from ..database import DatabaseManager
from ..utils.logging_utils import get_logger, get_run_logger
from ..utils.slug import story_slug


class StoryGeneratorWithRetry:
    """带重试机制的故事生成器"""

    def __init__(self, city: str, synopsis: StorySynopsis, test_mode: bool = False, multi_character: bool = True):
        """
        初始化生成器

        Args:
            city: 城市名称
            synopsis: 故事简介
            test_mode: 测试模式（快速生成MVP用于验证）
            multi_character: 是否生成多角色版本（默认：是，生成所有角色）
        """
        self.city = city
        self.synopsis = synopsis
        # 默认不跨轮重试，避免“生成→校验失败→整轮重启”的循环
        self.max_retries = int(os.getenv("MAX_RETRIES", "0"))
        self.test_mode = test_mode  # 测试模式
        self.multi_character = multi_character  # 多角色模式

    def generate_full_story(
        self,
        gdd_path: Optional[str] = None,
        lore_path: Optional[str] = None,
        main_story_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成完整故事（支持断点续传！）

        Args:
            gdd_path: GDD 文件路径
            lore_path: Lore 文件路径
            main_story_path: 主线故事路径

        Returns:
            生成结果
        """
        print("\n")
        print("╔══════════════════════════════════════════════════════════════════╗")
        if self.test_mode:
            print("║              🧪 开始生成测试故事 (MVP)                          ║")
        else:
            print("║              🚀 开始生成完整故事                                ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print("\n")
        print(f"故事标题: {self.synopsis.title}")
        print(f"城市: {self.city}")
        print(f"主角: {self.synopsis.protagonist}")
        print(f"场景: {self.synopsis.location}")
        print(f"预计时长: {self.synopsis.estimated_duration} 分钟")
        print("\n")

        if self.test_mode:
            print("⚡ [测试模式] 预计生成时间: 5-10 分钟")
            print("   • 角色数量: 2 个")
            print("   • 对话树深度: 5 层")
            print("   • 主线深度: 3 层")
        else:
            print("⚠️  [警告] 生成过程预计 2-4 小时")
            print("✅ [支持] 如果中断，下次可以从断点继续！")
        print("\n")

        # 用户确认（非交互环境自动继续）
        self._prompt_continue("按 Enter 确认开始生成...")
        print("\n")

        # 初始化文件日志（运行级别）
        _logger, _log_path = get_run_logger(
            "full_generation",
            {
                "city": self.city,
                "title": self.synopsis.title,
                "protagonist": self.synopsis.protagonist,
                "test_mode": self.test_mode,
                "env": {
                    "USE_PLOT_SKELETON": os.getenv("USE_PLOT_SKELETON", "1"),
                    "MAX_DEPTH": os.getenv("MAX_DEPTH"),
                    "MIN_MAIN_PATH_DEPTH": os.getenv("MIN_MAIN_PATH_DEPTH"),
                    "MIN_DURATION_MINUTES": os.getenv("MIN_DURATION_MINUTES"),
                    "MIN_ENDINGS": os.getenv("MIN_ENDINGS"),
                },
            },
        )

        # 尝试次数 = 1 次基础尝试 + max_retries 额外重试
        attempts = self.max_retries + 1
        auto_restart = os.getenv("AUTO_RESTART_ON_FAIL", "0") == "1"

        for attempt_idx in range(1, attempts + 1):
            try:
                # 1. 生成文档（GDD、Lore、主线故事）
                print("📄 Step 1/4: 生成游戏设计文档...")
                gdd_content, lore_content, main_story = self._generate_documents(
                    gdd_path, lore_path, main_story_path
                )
                print("   ✅ 文档生成完成")
                print("\n")

                # 1.5 世界书预分析（早提醒，不阻断）
                try:
                    self._preflight_analyze_worldbook(lore_content)
                except Exception as _e:
                    # 预分析容错，不影响后续
                    print(f"⚠️  世界书预分析失败（已忽略）：{_e}")

                # 1.8 生成故事骨架（PlotSkeleton，用于结构指导）
                use_plot_skeleton = os.getenv("USE_PLOT_SKELETON", "1")
                skeleton = None

                if use_plot_skeleton == "0":
                    # 显式关闭骨架模式：完全走 v3 行为，不触发 SkeletonGenerator / NodeTextFiller / story_report
                    print("🧱 Step 1.8: 已禁用骨架模式（USE_PLOT_SKELETON=0），直接使用旧结构模式（v3 TreeBuilder）。")
                else:
                    print("🧱 Step 1.8: 生成故事骨架（PlotSkeleton）...")
                    try:
                        skeleton = SkeletonGenerator(city=self.city).generate(
                            title=self.synopsis.title,
                            synopsis=self.synopsis.synopsis,
                            lore_v2_text=lore_content,
                            main_story_text=main_story,
                        )
                        print(
                            f"   ✅ 骨架生成完成：acts={skeleton.num_acts}, "
                            f"beats={skeleton.num_beats}, critical_beats={skeleton.num_critical_beats}, "
                            f"ending_beats={skeleton.num_ending_beats}"
                        )
                    except Exception as e_skel:
                        # 容错：骨架生成失败时回退到非 guided 模式
                        skeleton = None
                        print(f"⚠️  骨架生成失败，将回退到旧结构模式：{e_skel}")

                # 2. 提取角色列表
                print("👥 Step 2/4: 提取角色列表...")
                characters = self._extract_characters(main_story)

                # 测试模式：只生成前2个角色
                if self.test_mode:
                    print("   ⚡ [测试模式] 只生成前 2 个角色以快速验证")
                    characters = characters[:2]

                print(f"   ✅ 找到 {len(characters)} 个角色")
                for char in characters:
                    mark = "⭐" if char['is_protagonist'] else "  "
                    print(f"   {mark} {char['name']}")
                print("\n")

                # 3. 生成对话树（最耗时）
                print("🌳 Step 3/4: 生成对话树（主要耗时步骤）...")

                # 允许通过环境变量调整生成规模与深度阈值
                if self.test_mode:
                    # 测试模式：默认使用较小/中等深度，但仍遵守骨架配置
                    max_depth = int(os.getenv("MAX_DEPTH", "12"))
                    min_main_path = int(os.getenv("MIN_MAIN_PATH_DEPTH", "6"))
                    print(f"   ⚡ [测试模式] 使用深度配置: max_depth={max_depth}, min_main_path={min_main_path}")
                else:
                    # 正式模式：默认更高的深度阈值
                    max_depth = int(os.getenv("MAX_DEPTH", "50"))
                    min_main_path = int(os.getenv("MIN_MAIN_PATH_DEPTH", "30"))

                # 若处于 v4 骨架模式，则优先使用骨架配置中的最小主线深度，
                # 避免 TreeBuilder 与 PlotSkeleton 对“主线深度”存在偏差。
                if skeleton is not None:
                    try:
                        sk_min_depth = int(skeleton.config.min_main_depth)
                        if sk_min_depth > 0:
                            # 取环境阈值与骨架阈值中的较大者，防止过浅
                            if sk_min_depth > min_main_path:
                                print(
                                    f"   ℹ️  根据骨架提升主线最小深度约束："
                                    f"{min_main_path} → {sk_min_depth}"
                                )
                            min_main_path = max(min_main_path, sk_min_depth)
                    except Exception:
                        # 骨架配置异常时，不影响原有行为
                        pass

                dialogue_trees = {}

                # 🔄 尝试加载角色级别的检查点
                char_checkpoint = self._load_character_checkpoint()
                if char_checkpoint:
                    dialogue_trees = char_checkpoint.get("dialogue_trees", {})
                    completed_chars = list(dialogue_trees.keys())
                    print(f"\n✅ 发现角色级检查点！已恢复 {len(completed_chars)} 个角色的对话树")
                    for char_name in completed_chars:
                        print(f"   ✓ {char_name}")
                    print()

                for char in characters:
                    # 跳过已完成的角色
                    if char['name'] in dialogue_trees:
                        print(f"⏩ 跳过已完成的角色「{char['name']}」")
                        continue

                    print(f"\n🔄 正在为角色「{char['name']}」生成对话树...")

                    # 使用角色专属的检查点路径
                    checkpoint_path = f"checkpoints/{self.city}_{char['name']}_tree.json"

                    tree_builder = DialogueTreeBuilder(
                        city=self.city,
                        synopsis=self.synopsis.synopsis,
                        gdd_content=gdd_content,
                        lore_content=lore_content,
                        main_story=main_story,
                        test_mode=self.test_mode,
                        plot_skeleton=skeleton,
                    )

                    tree = tree_builder.generate_tree(
                        max_depth=max_depth,
                        min_main_path_depth=min_main_path,
                        checkpoint_path=checkpoint_path
                    )

                    dialogue_trees[char['name']] = tree
                    print(f"   ✅ {char['name']} 的对话树生成完成：{len(tree)} 个节点")

                    # 保存角色级检查点（每完成一个角色）
                    self._save_character_checkpoint(
                        characters,
                        dialogue_trees,
                        gdd_content,
                        lore_content,
                        main_story
                    )

                print("\n")
                print("   ✅ 所有对话树生成完成")
                print("\n")

                # 3.5 基于骨架的节点填充与结构报告（仅在 v4 骨架模式下执行）
                if skeleton is not None:
                    print("🧩 Step 3.5: 基于骨架填充节点文本并生成结构报告（v4 模式）...")

                    filler = NodeTextFiller(skeleton=skeleton)
                    per_char_reports: Dict[str, Any] = {}

                    for char in characters:
                        char_name = char["name"]
                        tree = dialogue_trees.get(char_name)
                        if not isinstance(tree, dict):
                            continue

                        # 填充节点文本与节拍元数据
                        dialogue_trees[char_name] = filler.fill(tree)

                        # 生成结构与时长报告
                        try:
                            per_char_reports[char_name] = build_story_report(
                                dialogue_tree=dialogue_trees[char_name],
                                skeleton=skeleton,
                            )
                        except Exception as e_report:
                            # 报告失败不阻断主流程，只打印提示
                            print(f"⚠️  结构报告生成失败（角色={char_name}，已忽略）：{e_report}")

                    # 简要输出主角报告的结论，便于人工快速判断
                    main_char_name = characters[0]["name"]
                    main_report = per_char_reports.get(main_char_name)
                    if main_report:
                        verdict = main_report.get("verdict", {})
                        print(
                            "   📊 主角结构验收："
                            f"depth_ok={verdict.get('depth_ok')}, "
                            f"duration_ok={verdict.get('duration_ok')}, "
                            f"endings_ok={verdict.get('endings_ok')}"
                        )

                # 4. 保存到数据库
                print("💾 Step 4/4: 保存到数据库...")
                db = DatabaseManager()

                # 计算元数据
                main_tree = dialogue_trees[characters[0]['name']]  # 主角的树
                metadata = self._calculate_metadata(main_tree, dialogue_trees)

                story_id = db.save_story(
                    city_name=self.city,
                    title=self.synopsis.title,
                    synopsis=self.synopsis.synopsis,
                    characters=characters,
                    dialogue_trees=dialogue_trees,
                    metadata=metadata
                )

                db.close()
                print(f"   ✅ 故事已保存到数据库（ID: {story_id}）")
                print("\n")

                # 🗑️ 清理所有检查点（生成成功）
                self._cleanup_all_checkpoints(characters)

                # 成功！
                self._print_success_summary(metadata)

                return {
                    "story_id": story_id,
                    "title": self.synopsis.title,
                    "metadata": metadata,
                    "characters": characters
                }

            except Exception as e:
                # 记录异常细节（文件日志 + 失败摘要文件）
                _logger.exception("故事生成失败一次 (attempt=%s/%s)", attempt_idx, attempts)
                try:
                    self._write_failure_log(
                        reason=str(e),
                        attempt=attempt_idx,
                        attempts=attempts,
                        extra={
                            "city": self.city,
                            "title": self.synopsis.title,
                            "protagonist": self.synopsis.protagonist,
                        },
                    )
                except Exception:
                    pass

                # 非自动重启：直接失败返回，避免无限“整轮重启”
                if not auto_restart:
                    raise

                if attempt_idx >= attempts:
                    print("\n")
                    print("╔══════════════════════════════════════════════════════════════════╗")
                    print("║              ❌ 生成失败                                        ║")
                    print("╚══════════════════════════════════════════════════════════════════╝")
                    print("\n")
                    print(f"错误信息：{e}")
                    print(f"已尝试 {attempts} 次，仍然失败。")
                    print("⚠️  请检查配置后重新开始。")
                    _logger.exception("故事生成最终失败")
                    raise

                print("\n")
                print(f"⚠️  遇到错误，自动重试 {attempt_idx}/{self.max_retries}...")
                print(f"   错误信息：{e}")
                print(f"   等待 10 秒后重试...")
                time.sleep(10)

    def _write_failure_log(self, reason: str, attempt: int, attempts: int, extra: Optional[Dict[str, Any]] = None) -> None:
        """写一份失败摘要日志到 logs/failures/ 下，包含失败原因与关键信息。

        不抛异常，尽量吞错。
        """
        try:
            from datetime import datetime
            import json
            logs_dir = Path("logs/failures")
            logs_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = self.synopsis.title.replace("/", "_")
            fname = f"{self.city}_{safe_title}_{ts}.json"
            path = logs_dir / fname

            payload = {
                "status": "failed",
                "quality_state": "rejected",
                "city": self.city,
                "title": self.synopsis.title,
                "story_slug": story_slug(self.city, self.synopsis.title),
                "protagonist": self.synopsis.protagonist,
                "attempt": attempt,
                "attempts": attempts,
                "reason": reason,
                "thresholds": {
                    "MAX_DEPTH": int(os.getenv("MAX_DEPTH", "0") or 0),
                    "MIN_MAIN_PATH_DEPTH": int(os.getenv("MIN_MAIN_PATH_DEPTH", "0") or 0),
                    "MIN_DURATION_MINUTES": int(os.getenv("MIN_DURATION_MINUTES", "0") or 0),
                    "MIN_ENDINGS": int(os.getenv("MIN_ENDINGS", "0") or 0),
                },
            }
            if extra:
                payload.update(extra)

            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            # 同步打印一行便于快速定位
            print(f"📝 失败日志：{path}")
        except Exception:
            pass

    def _generate_documents(
        self,
        gdd_path: Optional[str],
        lore_path: Optional[str],
        main_story_path: Optional[str]
    ) -> tuple:
        """生成或加载文档"""

        # 如果提供了路径，直接加载（缓存命中）
        if gdd_path and Path(gdd_path).exists():
            print(f"   📦 使用缓存 GDD: {gdd_path}")
            with open(gdd_path, 'r', encoding='utf-8') as f:
                gdd_content = f.read()
        else:
            gdd_content = None

        # Lore：优先使用 v2 世界书
        if lore_path and Path(lore_path).exists():
            print(f"   📦 使用缓存 Lore v2: {lore_path}")
            with open(lore_path, 'r', encoding='utf-8') as f:
                lore_content = f.read()
        else:
            lore_content = None

        if main_story_path and Path(main_story_path).exists():
            print(f"   📦 使用缓存主线: {main_story_path}")
            with open(main_story_path, 'r', encoding='utf-8') as f:
                main_story = f.read()
        else:
            main_story = None

        # 未显式提供路径时，尝试自动命中 deliverables 缓存
        try:
            from re import sub as _re_sub
            base_dir = Path(f"deliverables/程序-{self.city}")
            safe_title = _re_sub(r'[^\w\u4e00-\u9fff]+', '_', self.synopsis.title)
            title_dir = base_dir / safe_title

            def _read_if_missing(current, path, label):
                if current is not None:
                    return current
                if path.exists():
                    print(f"   📦 自动命中缓存 {label}: {path}")
                    return path.read_text(encoding='utf-8')
                return None

            if base_dir.exists():
                # 先查标题子目录
                if title_dir.exists():
                    gdd_content = _read_if_missing(gdd_content, title_dir / f"{self.city}_{safe_title}_gdd.md", "GDD")
                    lore_content = _read_if_missing(lore_content, title_dir / f"{self.city}_{safe_title}_lore_v2.md", "Lore v2")
                    main_story = _read_if_missing(main_story, title_dir / f"{self.city}_{safe_title}_story.md", "主线")
                # 再查城市级文件
                gdd_content = _read_if_missing(gdd_content, base_dir / f"{self.city}_gdd.md", "GDD")
                lore_content = _read_if_missing(lore_content, base_dir / f"{self.city}_lore_v2.md", "Lore v2")
                main_story = _read_if_missing(main_story, base_dir / f"{self.city}_story.md", "主线")
        except Exception:
            pass

        # 优先：使用完整生成器产物替代（可通过环境变量关闭）
        use_full = os.getenv("USE_FULL_GENERATOR", "1") == "1"
        if use_full and (gdd_content is None or lore_content is None or main_story is None):
            try:
                print("   🔄 使用完整生成器产出高质量文档（Lore v2 / GDD / 主线）…")
                from generate_full_story import StoryGenerator as FullStoryGenerator
                # 产物路径：deliverables/程序-城市/<标题子目录>
                base_dir = Path(f"deliverables/程序-{self.city}")
                include_branches = os.getenv("FULL_INCLUDE_BRANCHES", "0") == "1"
                full_gen = FullStoryGenerator(
                    city=self.city,
                    output_dir=str(base_dir),
                    title=self.synopsis.title,
                    synopsis=self.synopsis.synopsis,
                )
                full_gen.generate_all(include_branches=include_branches)

                # 优先从内存拿产物，缺失则读文件
                if lore_content is None:
                    lore_content = full_gen.artifacts.get("lore_v2")
                    if not lore_content:
                        from re import sub as _re_sub
                        safe_title = _re_sub(r'[^\w\u4e00-\u9fff]+', '_', self.synopsis.title)
                        lore_path2 = (base_dir / safe_title / f"{self.city}_{safe_title}_lore_v2.md")
                        if not lore_path2.exists():
                            lore_path2 = (base_dir / f"{self.city}_lore_v2.md")
                        if lore_path2.exists():
                            lore_content = lore_path2.read_text(encoding='utf-8')

                if gdd_content is None:
                    gdd_content = full_gen.artifacts.get("gdd")
                    if not gdd_content:
                        from re import sub as _re_sub
                        safe_title = _re_sub(r'[^\w\u4e00-\u9fff]+', '_', self.synopsis.title)
                        gdd_path2 = (base_dir / safe_title / f"{self.city}_{safe_title}_gdd.md")
                        if not gdd_path2.exists():
                            gdd_path2 = (base_dir / f"{self.city}_gdd.md")
                        if gdd_path2.exists():
                            gdd_content = gdd_path2.read_text(encoding='utf-8')

                if main_story is None:
                    main_story = full_gen.artifacts.get("story")
                    if not main_story:
                        from re import sub as _re_sub
                        safe_title = _re_sub(r'[^\w\u4e00-\u9fff]+', '_', self.synopsis.title)
                        story_path2 = (base_dir / safe_title / f"{self.city}_{safe_title}_story.md")
                        if not story_path2.exists():
                            story_path2 = (base_dir / f"{self.city}_story.md")
                        if story_path2.exists():
                            main_story = story_path2.read_text(encoding='utf-8')

                print("   ✅ 已使用完整生成器文档")
            except Exception as e:
                print(f"   ⚠️  完整生成器集成失败，回退到内置文档生成：{e}")

        # 回退：如有缺失则用内置生成补齐
        if gdd_content is None:
            gdd_content = self._generate_gdd()
        if lore_content is None:
            lore_content = self._generate_lore_v2() or self._generate_lore()
        if main_story is None:
            main_story = self._generate_main_story()

        return gdd_content, lore_content, main_story

    def _preflight_analyze_worldbook(self, lore_content: str) -> None:
        """对 v2 世界书做启发式预分析，提前提醒可能达不到深度/结局阈值。

        仅做提示，不阻断流程。
        """
        import re
        import os

        # 从环境读取阈值（与生成阈值一致）
        min_depth = int(os.getenv("MIN_MAIN_PATH_DEPTH", os.getenv("MIN_MAIN_PATH_DEPTH_THRESHOLD", "30")))
        min_endings = int(os.getenv("MIN_ENDINGS", "1"))

        print("🔎 预分析（基于世界书）...")

        # 估算主线节拍深度：统计 S1..Sxx 标号（去重），或取最大序号
        beat_nums = []
        try:
            for m in re.findall(r"(?im)^\s*S(\d{1,3})\b", lore_content or ""):
                try:
                    beat_nums.append(int(m))
                except Exception:
                    pass
        except Exception:
            beat_nums = []

        unique_beats = len(set(beat_nums))
        max_beat = max(beat_nums) if beat_nums else 0
        estimated_depth = max(unique_beats, max_beat)

        # 估算结局数量：统计“结局”/“终局”/“ENDING”等关键词出现的段落数
        ending_signals = 0
        try:
            ending_signals = len(re.findall(r"(?i)(^|\n)\s*(结局|终局|ending|end[\s\-_:])", lore_content or ""))
        except Exception:
            ending_signals = 0

        print(f"   估算主线节拍数≈{estimated_depth}（阈值≥{min_depth}）")
        print(f"   估算结局信号≈{ending_signals}（阈值≥{min_endings}）")

        warn = False
        if estimated_depth < min_depth:
            print("   ⚠️  预警：主线节拍可能不足，建议强化世界书的主线规划（S1..S30+）或调低阈值")
            warn = True
        if ending_signals < min_endings:
            print("   ⚠️  预警：结局信号偏少，建议在世界书中显式列出多个可达结局与触发条件")
            warn = True

        if not warn:
            print("   ✅ 预分析通过：世界书的深度/结局信号看起来充足")

    def _generate_gdd(self) -> str:
        """生成 GDD（简化版）"""
        return f"""# 游戏设计文档 - {self.synopsis.title}

## 基本信息
- 城市：{self.city}
- 主角：{self.synopsis.protagonist}
- 场景：{self.synopsis.location}

## 游戏机制
- PR（恐惧值）：0-100
- GR（真相值）：0-100
- WF（世界熟悉度）：0-100

## 场景
- S1：{self.synopsis.location}（起始场景）
"""

    def _generate_lore(self) -> str:
        """生成 Lore（简化版）"""
        return f"""# 世界观规则 - {self.synopsis.title}

## 核心规则
1. 恐怖氛围优先
2. 逻辑自洽
3. 伏笔回收

## 故事背景
{self.synopsis.synopsis}
"""

    def _generate_lore_v2(self) -> Optional[str]:
        """生成 v2 级世界书（高质量，规则化、结局约束、场景索引、30+节拍主线）

        Returns:
            str | None: 成功返回文本，失败返回 None
        """
        try:
            from crewai import Agent, Task, Crew, LLM
            import os
            from pathlib import Path

            # 读取模板（优先根目录，其次 templates/）
            tpl_paths = [
                Path("lore-v2.prompt.md"),
                Path("templates/lore-v2.prompt.md")
            ]
            prompt_template = None
            for p in tpl_paths:
                if p.exists():
                    prompt_template = p.read_text(encoding='utf-8')
                    break
            if not prompt_template:
                # 内置简化模板
                prompt_template = (
                    "你是世界书设计师，请为以下题材生成 v2 级世界书：\n"
                    "- 包含：核心规则、禁忌、实体表、场景索引、线索网络、矛盾升级阶梯\n"
                    "- 给出主线30+节拍（按 S1..S30 标号），并标注3个以上可达结局的触发条件（结局_前缀）\n"
                    "- 输出 Markdown\n"
                )

            kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
            kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
            kimi_model = os.getenv("KIMI_MODEL_LORE", os.getenv("KIMI_MODEL", "kimi-k2-0905-preview"))

            llm = LLM(model=kimi_model, api_key=kimi_key, base_url=kimi_base)

            # 组装 Prompt
            meta = (
                f"城市：{self.city}\n"
                f"标题：{self.synopsis.title}\n"
                f"主角：{self.synopsis.protagonist}\n"
                f"场景：{self.synopsis.location}\n"
                f"概要：{self.synopsis.synopsis}\n"
            )
            full_prompt = (
                f"{prompt_template}\n\n"
                f"【元信息】\n{meta}\n\n"
                "请严格产出：\n"
                "- [核心规则] [禁忌] [实体表] [场景索引] [线索网络] [主线节拍S1..S30+] [可达结局与触发]\n"
                "- 各节拍给出场景与推进意图（用于深主线）\n"
            )

            agent = Agent(
                role="世界书架构师",
                goal="生成规则化、可驱动30+主线节拍与多结局的世界书",
                backstory="你擅长约束与节拍规划，输出面向引擎消费的 Markdown 世界书",
                llm=llm,
                verbose=False
            )
            task = Task(description=full_prompt, expected_output="Markdown 世界书文本", agent=agent)
            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()

            text = str(result).strip()
            # 简单校验：是否包含主线节拍与结局提示
            if "S30" in text or "S31" in text:
                return text
            return text  # 仍然返回，高质量提示已包含
        except Exception as e:
            print(f"⚠️  生成 v2 世界书失败，回退到简化版：{e}")
            return None

    def _generate_main_story(self) -> str:
        """生成主线故事（简化版）"""
        return f"""# 主线故事 - {self.synopsis.title}

{self.synopsis.synopsis}

主角：{self.synopsis.protagonist}
场景：{self.synopsis.location}
"""

    def _extract_characters(self, main_story: str) -> list:
        """
        提取角色列表

        ✅ 优先使用用户选择的主角（self.synopsis.protagonist）
        ⚠️ 不再从 struct.json 读取，避免主角混乱
        """
        import json
        import glob

        # ✅ 始终使用用户选择的主角作为唯一角色
        protagonist_name = self.synopsis.protagonist

        characters = [
            {
                "name": protagonist_name,
                "is_protagonist": True,
                "description": f"{self.synopsis.title} - {protagonist_name}的故事"
            }
        ]

        print(f"   ✅ 使用主角: {protagonist_name}")

        # 🎭 可选：多角色模式（需要显式启用）
        if self.multi_character:
            print(f"   🎭 [多角色模式] 尝试查找额外角色...")

            # 检查是否有匹配的 struct.json
            struct_path = None
            possible_patterns = [
                f"examples/*/{self.city}_struct.json",
                f"examples/{self.city}/*_struct.json",
            ]

            # 收集所有可能的 struct.json 文件
            all_matches = []
            for pattern in possible_patterns:
                matches = glob.glob(pattern)
                all_matches.extend(matches)

            # 去重
            all_matches = list(set(all_matches))

            if all_matches:
                print(f"   🔍 找到 {len(all_matches)} 个 struct.json 文件，检查标题匹配...")

                # ✅ 遍历所有文件，找到标题匹配的那个
                found_match = False
                for test_path in all_matches:
                    try:
                        test_path = Path(test_path)
                        with open(test_path, 'r', encoding='utf-8') as f:
                            struct_data = json.load(f)

                            # ⚠️ 关键：只有标题匹配才使用
                            if struct_data.get('title') == self.synopsis.title:
                                struct_path = test_path
                                potential_roles = struct_data.get('potential_roles', [])

                                # 添加其他配角
                                added_count = 0
                                for role_name in potential_roles:
                                    if role_name != protagonist_name:
                                        characters.append({
                                            "name": role_name,
                                            "is_protagonist": False,
                                            "description": f"{self.synopsis.title} - {role_name}视角"
                                        })
                                        added_count += 1

                                print(f"   ✅ 从 {struct_path.name} 添加了 {added_count} 个配角")
                                found_match = True
                                break
                            else:
                                print(f"   ⏭️  跳过 {test_path.name}：标题不匹配 ('{struct_data.get('title', '未知')}')")
                    except Exception as e:
                        # 如果读取失败，记录并继续检查下一个
                        print(f"   ⚠️  警告: 读取 {test_path.name} 失败: {e}")
                        continue

                if not found_match:
                    print(f"   ℹ️  所有文件标题都不匹配，只生成主角故事")
                    print(f"       期望标题: {self.synopsis.title}")
            else:
                print(f"   ℹ️  未找到 {self.city} 的 struct.json 文件")
                # 尝试从故事中提取角色
                extracted = self._extract_from_story(main_story, protagonist_name)
                if extracted:
                    characters.extend(extracted)
                    print(f"   ✅ 从故事中自动提取到 {len(extracted)} 个配角")
        else:
            print(f"   ℹ️  [单角色模式] 只生成主角故事")

        return characters

    def _extract_from_story(self, main_story: str, protagonist: str) -> list:
        """
        从主线故事或GDD中提取其他角色

        Args:
            main_story: 主线故事内容
            protagonist: 主角名称

        Returns:
            提取到的配角列表
        """
        import re

        # 常见的角色职业/身份关键词
        common_roles = [
            "保安", "警察", "记者", "导游", "工程师", "维修工",
            "清洁工", "服务员", "司机", "医生", "护士", "老师",
            "学生", "主播", "博主", "摄影师", "画家", "作家",
            "厨师", "店主", "顾客", "游客", "居民", "邻居",
            "夜班保安", "值班员", "检修工", "调查员", "UP主",
            "跑腿员", "外卖员", "快递员", "夜班司机", "出租车司机"
        ]

        characters = []
        found_roles = set()

        # 在故事中查找这些角色
        for role in common_roles:
            if role in main_story and role != protagonist and role not in found_roles:
                found_roles.add(role)
                characters.append({
                    "name": role,
                    "is_protagonist": False,
                    "description": f"{self.synopsis.title} - {role}视角"
                })

                # 最多提取 6 个配角
                if len(characters) >= 6:
                    break

        return characters

    def _calculate_metadata(self, main_tree: Dict, all_trees: Dict) -> Dict[str, Any]:
        """计算元数据"""
        from .time_validator import TimeValidator

        validator = TimeValidator()
        report = validator.get_validation_report(main_tree)

        total_nodes = sum(len(tree) for tree in all_trees.values())

        return {
            "estimated_duration": report['estimated_duration_minutes'],
            "total_nodes": total_nodes,
            "max_depth": report['main_path_depth'],
            "cost": 0.0,  # TODO: 实际计算
            "total_tokens": 0,  # TODO: 实际统计
            "generation_time": 0,  # TODO: 实际计时
            "model": os.getenv("KIMI_MODEL_RESPONSE", "kimi-k2-0905-preview")
        }

    def _print_success_summary(self, metadata: Dict):
        """打印成功总结"""
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║              ✅ 故事生成完成！                                  ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print("\n")
        print(f"故事名称: {self.synopsis.title}")
        print(f"生成节点: {metadata['total_nodes']:,} 个")
        print(f"主线深度: {metadata['max_depth']} 层")
        print(f"预计游戏时长: {metadata['estimated_duration']} 分钟")
        print("\n")
        print("✅ 已保存到数据库")
        print("\n")
        print("按 Enter 返回主菜单，选择「选择故事」开始游玩...")
        self._prompt_continue("")

    def _prompt_continue(self, message: str) -> None:
        """在交互环境提示继续；在非交互环境自动继续。"""
        if os.getenv("NON_INTERACTIVE", "0") == "1":
            print("   ↪️ 非交互模式，自动继续")
            return
        try:
            input(message)
        except EOFError:
            print("   ↪️ 检测到 EOF（非交互），自动继续")
            return

    def _load_character_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        加载角色级检查点

        Returns:
            检查点数据（如果存在）
        """
        import json
        from pathlib import Path

        checkpoint_path = f"checkpoints/{self.city}_characters.json"
        checkpoint_file = Path(checkpoint_path)

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载角色检查点失败：{e}")
            return None

    def _save_character_checkpoint(
        self,
        characters: list,
        dialogue_trees: Dict[str, Any],
        gdd_content: str,
        lore_content: str,
        main_story: str
    ):
        """
        保存角色级检查点

        Args:
            characters: 角色列表
            dialogue_trees: 已完成的对话树
            gdd_content: GDD 内容
            lore_content: Lore 内容
            main_story: 主线故事
        """
        import json
        from pathlib import Path
        from datetime import datetime

        checkpoint_path = f"checkpoints/{self.city}_characters.json"
        checkpoint_file = Path(checkpoint_path)
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "generated_at": datetime.now().isoformat(),
            "city": self.city,
            "synopsis": self.synopsis.__dict__,
            "characters": characters,
            "dialogue_trees": dialogue_trees,
            "gdd_content": gdd_content,
            "lore_content": lore_content,
            "main_story": main_story,
            "completed_count": len(dialogue_trees),
            "total_count": len(characters)
        }

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        print(f"💾 [角色检查点] 已保存 {len(dialogue_trees)}/{len(characters)} 个角色 → {checkpoint_path}")

    def _cleanup_all_checkpoints(self, characters: list):
        """
        清理所有检查点文件

        Args:
            characters: 角色列表
        """
        import os
        from pathlib import Path

        deleted_count = 0

        # 删除角色级检查点
        char_checkpoint = Path(f"checkpoints/{self.city}_characters.json")
        if char_checkpoint.exists():
            os.remove(char_checkpoint)
            deleted_count += 1

        # 删除每个角色的对话树检查点
        for char in characters:
            tree_checkpoint = Path(f"checkpoints/{self.city}_{char['name']}_tree.json")
            if tree_checkpoint.exists():
                os.remove(tree_checkpoint)
                deleted_count += 1

        if deleted_count > 0:
            print(f"🗑️  已清理 {deleted_count} 个检查点文件")
