"""游戏主循环

整合所有引擎组件，实现完整的游戏循环：
1. 生成当前场景的选择点（支持预加载优化）
2. 显示给玩家并等待输入
3. 验证选择合法性
4. 应用后果并更新状态
5. 生成运行时响应
6. 异步预生成下一批选择点（用户读文本时后台执行）
7. 检查结局条件
8. 重复或结束
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from .state import GameState
from .choices import Choice, ChoiceType, ChoicePointsGenerator
from .response import RuntimeResponseGenerator

# 预生成模式导入（延迟导入以避免循环依赖）
try:
    from ..runtime.dialogue_loader import DialogueTreeLoader
    PREGENERATED_AVAILABLE = True
except ImportError:
    PREGENERATED_AVAILABLE = False


class GameEngine:
    """游戏引擎

    管理游戏的主循环，协调所有子系统
    """

    def __init__(
        self,
        city: str,
        gdd_path: Optional[str] = None,
        lore_path: Optional[str] = None,
        main_story_path: Optional[str] = None,
        save_dir: str = "saves",
        dialogue_loader: Optional['DialogueTreeLoader'] = None
    ):
        """初始化游戏引擎

        Args:
            city: 城市名称
            gdd_path: GDD 文件路径（可选）
            lore_path: Lore v2 文件路径（可选）
            main_story_path: 主线故事文件路径（可选，用于会话级缓存）
            save_dir: 存档目录
            dialogue_loader: 对话树加载器（如果提供，则使用预生成模式）
        """
        self.city = city
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)

        # 🎮 判断模式
        self.dialogue_loader = dialogue_loader
        self.mode = "pregenerated" if dialogue_loader else "realtime"

        if self.mode == "pregenerated":
            # 预生成模式：从对话树读取，零等待
            print("🎮 [预生成模式] 已加载对话树，零等待游戏体验！")
            self.current_node_id = "root"  # 当前对话节点

            # 预生成模式不需要这些资源
            self.gdd = ""
            self.lore = ""
            self.main_story = ""
            self.choice_generator = None
            self.response_generator = None
        else:
            # 实时模式：使用 LLM 生成
            print("🎮 [实时模式] 使用 LLM 即时生成内容")

            # 加载故事资源
            self.gdd = self._load_gdd(gdd_path)
            self.lore = self._load_lore(lore_path)
            self.main_story = self._load_main_story(main_story_path)

            # 初始化生成器（传入主线故事）
            self.choice_generator = ChoicePointsGenerator(self.gdd, self.lore, self.main_story)
            self.response_generator = RuntimeResponseGenerator(self.gdd, self.lore, self.main_story)

        # 初始化游戏状态
        self.state = GameState()

        # 运行时变量
        self.is_running = False
        self.last_action_time = time.time()
        self.current_choices: List[Choice] = []

        # 预加载优化（仅实时模式）
        if self.mode == "realtime":
            self.preload_enabled = True
            self.preloaded_choices: Optional[List[Choice]] = None
            self.preload_future: Optional[Future] = None
            self.executor = ThreadPoolExecutor(max_workers=1)
            self.story_initialized = False

    def _load_gdd(self, gdd_path: Optional[str]) -> str:
        """加载 GDD 文件

        Args:
            gdd_path: GDD 文件路径，如果为 None 则自动查找

        Returns:
            str: GDD 内容
        """
        if gdd_path and Path(gdd_path).exists():
            with open(gdd_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 自动查找：examples/{city}/{city}_GDD.md
        auto_path = Path(f"examples/{self.city}/{self.city}_GDD.md")
        if auto_path.exists():
            with open(auto_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 查找 deliverables
        deliverable_path = Path(f"deliverables/程序-{self.city}/{self.city}_GDD.md")
        if deliverable_path.exists():
            with open(deliverable_path, 'r', encoding='utf-8') as f:
                return f.read()

        raise FileNotFoundError(
            f"无法找到 {self.city} 的 GDD 文件。\n"
            f"请提供 gdd_path 参数，或确保文件位于 examples/{self.city}/ 或 deliverables/程序-{self.city}/ 目录下。"
        )

    def _load_lore(self, lore_path: Optional[str]) -> str:
        """加载 Lore v2 文件

        Args:
            lore_path: Lore 文件路径，如果为 None 则自动查找

        Returns:
            str: Lore 内容
        """
        if lore_path and Path(lore_path).exists():
            with open(lore_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 自动查找：examples/{city}/{city}_lore_v2.md
        auto_path = Path(f"examples/{self.city}/{self.city}_lore_v2.md")
        if auto_path.exists():
            with open(auto_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 查找 JSON 格式
        json_path = Path(f"examples/{self.city}/{self.city}_lore.json")
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                lore_data = json.load(f)
                # 转换为文本格式
                return json.dumps(lore_data, ensure_ascii=False, indent=2)

        raise FileNotFoundError(
            f"无法找到 {self.city} 的 Lore 文件。\n"
            f"请提供 lore_path 参数，或确保文件位于 examples/{self.city}/ 目录下。"
        )

    def _load_main_story(self, main_story_path: Optional[str]) -> str:
        """加载主线故事文件（用于会话级缓存）

        Args:
            main_story_path: 主线故事文件路径，如果为 None 则自动查找

        Returns:
            str: 主线故事内容
        """
        if main_story_path and Path(main_story_path).exists():
            with open(main_story_path, 'r', encoding='utf-8') as f:
                return f.read()

        # 尝试自动查找
        story_candidates = [
            f"examples/{self.city}/{self.city}_main_thread.md",
            f"examples/{self.city}/main_thread.md",
            f"examples/{self.city}/{self.city}_story.md",
            f"examples/{self.city}/story.md",
            f"examples/{self.city}/杭州_main_thread.md",
            f"examples/{self.city}/杭州_story.md",
        ]

        for candidate in story_candidates:
            if Path(candidate).exists():
                with open(candidate, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"📚 [会话缓存] 加载主线故事: {candidate} ({len(content)} 字符)")
                    return content

        print("💡 [会话缓存] 未找到主线故事文件，将使用精简模式（Prompt 优化）")
        return ""

    def _preload_choices_async(self) -> None:
        """异步预加载下一批选择点（在后台线程中执行）"""
        try:
            if self.preload_enabled and self.is_running:
                print("🔄 [后台] 正在预生成下一批选择点...")
                choices = self.choice_generator.generate_choices(
                    self.state.current_scene,
                    self.state
                )
                self.preloaded_choices = choices
                print("✅ [后台] 选择点预生成完成！")
        except Exception as e:
            print(f"⚠️  [后台] 预加载失败: {e}")
            self.preloaded_choices = None

    def _show_loading_animation(self, message: str, future: Future, check_interval: float = 0.5) -> None:
        """显示等待动画（带进度提示）

        Args:
            message: 等待消息
            future: 要等待的 Future 对象
            check_interval: 检查间隔（秒）
        """
        import sys

        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        idx = 0
        elapsed = 0

        print()  # 空行
        while not future.done():
            spinner_char = spinner[idx % len(spinner)]
            elapsed_str = f"{elapsed:.1f}s" if elapsed > 0 else "0.0s"
            sys.stdout.write(f"\r{spinner_char} {message} ({elapsed_str})")
            sys.stdout.flush()
            time.sleep(check_interval)
            idx += 1
            elapsed += check_interval

        # 清除动画行
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    def _get_choices(self) -> List[Choice]:
        """获取当前场景的选择点（优先使用预加载）

        Returns:
            List[Choice]: 选择点列表
        """
        # 如果有预加载的选择点，直接使用
        if self.preloaded_choices is not None:
            print("⚡ 使用预加载的选择点（无需等待）")
            choices = self.preloaded_choices
            self.preloaded_choices = None  # 清空缓存
            return choices

        # 如果预加载任务还在运行，等待完成
        if self.preload_future is not None and not self.preload_future.done():
            print("\n" + "═" * 70)
            print("⏳ 你的阅读速度太快了！AI 还在后台生成选择点...")
            print("═" * 70)

            # 显示等待动画
            self._show_loading_animation(
                "正在等待 Kimi AI 完成生成",
                self.preload_future,
                check_interval=0.3
            )

            # 获取结果
            self.preload_future.result()  # 等待完成

            if self.preloaded_choices is not None:
                print("✅ 生成完成！选择点已准备好\n")
                choices = self.preloaded_choices
                self.preloaded_choices = None
                return choices

        # 没有预加载，正常生成（会有等待）
        print("\n" + "═" * 70)
        print("🔄 正在生成选择点...")
        print("═" * 70)
        print()

        return self.choice_generator.generate_choices(
            self.state.current_scene,
            self.state
        )

    def run(self) -> str:
        """主游戏循环（支持实时和预生成两种模式）

        Returns:
            str: 游戏结束原因（结局类型或退出原因）
        """
        # 🎮 根据模式选择不同的主循环
        if self.mode == "pregenerated":
            return self.run_pregenerated()
        else:
            return self.run_realtime()

    def run_pregenerated(self) -> str:
        """预生成模式主循环（零等待）

        Returns:
            str: 游戏结束原因（结局类型或退出原因）
        """
        self.is_running = True

        print(f"\n🎭 开始游戏：{self.city}\n")
        print(self._get_title_screen())

        # 显示开场叙事（从对话树读取）
        opening_narrative = self.dialogue_loader.get_narrative(self.current_node_id)
        print(f"\n{opening_narrative}\n")

        # 主循环
        while self.is_running:
            try:
                # 1. 获取当前节点的选择（从对话树）
                choices_data = self.dialogue_loader.get_choices(self.current_node_id)

                if not choices_data:
                    # 没有选择了，达到结局
                    print("\n" + "=" * 70)
                    print("🎬 故事结束")
                    print("=" * 70)
                    self.is_running = False
                    break

                # 转换为 Choice 对象（简化版）
                self.current_choices = self._convert_choices(choices_data)

                # 2. 显示选择点并获取玩家输入
                selected_choice = self._prompt_player(self.current_choices)

                if selected_choice is None:
                    # 玩家选择退出
                    self.is_running = False
                    return "player_quit"

                # 3. 根据选择跳转到下一个节点
                next_node_id = self.dialogue_loader.select_choice(selected_choice.choice_id)

                if not next_node_id:
                    print("\n❌ 无效的选择")
                    continue

                self.current_node_id = next_node_id

                # 4. 显示下一个节点的叙事
                narrative = self.dialogue_loader.get_narrative(self.current_node_id)
                print(f"\n{narrative}\n")

            except KeyboardInterrupt:
                print("\n\n⚠️  游戏中断")
                self.is_running = False
                return "interrupted"

            except Exception as e:
                print(f"\n❌ 发生错误：{e}")
                import traceback
                traceback.print_exc()
                self.is_running = False
                return "error"

        return "ending_reached"

    def _convert_choices(self, choices_data: List[Dict[str, Any]]) -> List[Choice]:
        """将对话树中的选择数据转换为 Choice 对象

        Args:
            choices_data: 对话树中的选择数据列表

        Returns:
            List[Choice]: Choice 对象列表
        """
        choices = []
        for choice_data in choices_data:
            # 创建简化的 Choice 对象（预生成模式不需要完整的 Choice 功能）
            choice = Choice(
                choice_id=choice_data.get("choice_id", ""),
                choice_text=choice_data.get("choice_text", ""),
                choice_type=ChoiceType.NORMAL,  # 预生成模式暂不区分类型
                tags=choice_data.get("tags", []),
                preconditions={},
                consequences=choice_data.get("consequences", {})
            )
            choices.append(choice)
        return choices

    def run_realtime(self) -> str:
        """实时模式主循环（LLM 即时生成）

        Returns:
            str: 游戏结束原因（结局类型或退出原因）
        """
        self.is_running = True

        print(f"\n🎭 开始游戏：{self.city}\n")
        print(self._get_title_screen())

        # 显示初始状态
        self._display_state()

        # 🚀 立即在后台预加载第一批选择点（用户阅读开场文本时）
        if self.preload_enabled:
            print("\n🔄 [后台] 开始预生成第一批选择点...")
            self.preload_future = self.executor.submit(self._preload_choices_async)

        # 显示开场叙事（在预加载的同时生成）
        print("\n" + "=" * 70)
        print("✍️  生成开场故事...")
        print("=" * 70)
        opening_narrative = self._get_opening_narrative()
        print(f"\n{opening_narrative}\n")

        if self.preload_enabled:
            print("\n💡 提示：在你阅读开场的同时，选择点已在后台生成\n")

        # 主循环
        while self.is_running and not self._check_ending():
            try:
                # 1. 获取当前场景的选择点（使用预加载优化）
                self.current_choices = self._get_choices()

                # 2. 显示选择点并获取玩家输入
                selected_choice = self._prompt_player(self.current_choices)

                if selected_choice is None:
                    # 玩家选择退出
                    self.is_running = False
                    return "player_quit"

                # 3. 生成响应并更新状态
                print("\n" + "═" * 70)
                print("✍️  Kimi AI 正在根据你的选择创作剧情...")
                print("═" * 70)
                print("💭 思考中：分析你的选择 → 推进剧情 → 营造氛围...")
                print()

                response = self.response_generator.generate_response(
                    selected_choice,
                    self.state,
                    apply_consequences=True
                )

                print("✅ 剧情生成完成！\n")

                # 4. 显示响应
                self._display_response(response)

                # 5. 显示当前状态
                self._display_state()

                # 6. 检查是否需要切换场景
                self._check_scene_transition()

                # 7. 🚀 启动后台预加载下一批选择点（用户读文本时AI在后台工作）
                if self.preload_enabled and self.is_running:
                    self.preload_future = self.executor.submit(self._preload_choices_async)

                # 更新最后行动时间
                self.last_action_time = time.time()

            except KeyboardInterrupt:
                print("\n\n⚠️  游戏中断")
                self._offer_save()
                self.is_running = False
                self._cleanup()
                return "interrupted"

            except Exception as e:
                print(f"\n❌ 发生错误：{e}")
                self._offer_save()
                self.is_running = False
                self._cleanup()
                return "error"

        # 8. 清理资源
        self._cleanup()

        # 9. 显示结局
        ending_type = self._show_ending()
        return ending_type

    def _cleanup(self) -> None:
        """清理资源（关闭线程池等）"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
            print("🧹 后台任务已清理")

    def _get_title_screen(self) -> str:
        """获取标题画面"""
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║                    🎭 {self.city}·灵异故事                        ║
║                  交互式恐怖游戏体验                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

    def _get_opening_narrative(self) -> str:
        """获取开场叙事（生成详细的背景故事）"""
        # 使用 LLM 生成开场叙事
        try:
            from crewai import Agent, Task, Crew, LLM
            import os
        except ImportError:
            # 回退到默认开场
            return self._get_default_opening()

        # 配置 Kimi LLM（开场叙事专用模型）
        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
        # 开场叙事：使用高质量模型（可单独配置）
        kimi_model = os.getenv("KIMI_MODEL_OPENING") or os.getenv("KIMI_MODEL", "kimi-k2-0905-preview")

        llm = LLM(
            model=kimi_model,
            api_key=kimi_key,
            base_url=kimi_base
        )

        print(f"🤖 [开场] 使用模型: {kimi_model}")

        # 🎯 混合方案：开场使用完整故事背景
        if self.main_story:
            backstory = self._build_opening_backstory_with_story()
            print("📚 [开场] 使用完整故事背景（高质量模式）")
        else:
            backstory = "你擅长营造氛围和悬念，让读者立即沉浸其中"
            print("💡 [开场] 使用精简模式")

        # 提取 GDD 开场信息
        opening_context = self._extract_opening_context(self.gdd)

        prompt = f"""
你是一个专业的恐怖故事作家。请生成游戏的开场叙事（300-500字）。

## 背景信息

{opening_context}

## 当前状态
- 时间：{self.state.timestamp}
- 场景：{self.state.current_scene}

---

## 写作要求

1. **第二人称视角**（使用"你"），让玩家有代入感
2. **介绍主角身份**和今晚的任务（例如："你是顾栖迟，特检院工程师..."）
3. **描写环境**：天气、时间、地点的感官细节
4. **营造悬念**：暗示即将发生的异常事件
5. **300-500字**，使用 Markdown 格式

重要：必须使用"你"而不是"我"，例如：
- ✅ "你站在观景台上..."
- ❌ "我站在观景台上..."

请生成开场叙事（只输出叙事文本，不要包含标题或其他格式）：
"""

        agent = Agent(
            role="恐怖故事作家",
            goal="生成引人入胜的开场叙事",
            backstory=backstory,
            verbose=False,
            allow_delegation=False,
            llm=llm
        )

        task = Task(
            description=prompt,
            expected_output="第一人称开场叙事（300-500字）",
            agent=agent
        )

        print("✍️  Kimi AI 正在创作开场故事...")
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        result = crew.kickoff()

        return str(result)

    def _build_opening_backstory_with_story(self) -> str:
        """构建包含完整故事的开场 backstory（混合方案）

        Returns:
            包含故事背景的 backstory 文本
        """
        # 截取主线故事的前 5000 字符（约 6000 tokens）
        story_excerpt = self.main_story[:5000] if len(self.main_story) > 5000 else self.main_story

        return f"""你是一个专业的恐怖故事作家，已经阅读了完整的故事背景：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【故事背景】
{story_excerpt}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

你的任务：
基于上述故事背景，生成引人入胜的开场叙事。

你的风格：
- 第二人称视角（使用"你"）
- 营造悬念和氛围
- 符合故事设定

重要：
- 必须遵循故事背景中的设定
- 准确介绍主角身份和任务
- 为后续剧情做好铺垫
"""

    def _extract_opening_context(self, gdd: str) -> str:
        """提取开场相关的 GDD 信息"""
        lines = gdd.split('\n')
        context_lines = []

        # 查找开场、背景、主角等相关内容
        keywords = ['开场', '背景', '主角', '任务', '设定', 'S1', '场景1']
        for i, line in enumerate(lines[:100]):  # 只看前100行
            if any(kw in line for kw in keywords):
                context_lines.append(line)
                # 收集后续几行
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip():
                        context_lines.append(lines[j])

        result = '\n'.join(context_lines)[:800]
        return result if result else f"{self.city} 的一个夜晚，你是夜班工作人员"

    def _get_default_opening(self) -> str:
        """默认开场（当 LLM 不可用时）"""
        return f"""
**{self.city}·深夜**

你是{self.city}的一名夜班工作人员。今夜的任务刚刚开始。

窗外的雨刚停，空气中弥漫着潮湿的土腥味。时钟指向凌晨 00:00。

你知道，这将是一个不平静的夜晚...
"""

    def _display_state(self) -> None:
        """显示当前游戏状态"""
        print("\n" + "━" * 70)

        # 状态条
        pr_bar = self._render_bar(self.state.PR, 100, 20)
        gr_bar = self._render_bar(self.state.GR, 100, 20)
        wf_bar = self._render_bar(self.state.WF, 10, 10)

        print(f"📊 个人共鸣度 {pr_bar} {self.state.PR}/100")
        print(f"🌍 全局共鸣度 {gr_bar} {self.state.GR}/100")
        print(f"⏱️  世界疲劳值 {wf_bar} {self.state.WF}/10")

        print(f"\n⏰ 时间: {self.state.timestamp}  |  📍 场景: {self.state.current_scene}")

        if self.state.inventory:
            print(f"🎒 道具: {', '.join(self.state.inventory)}")

        print("━" * 70 + "\n")

    def _render_bar(self, value: int, max_value: int, bar_length: int) -> str:
        """渲染进度条"""
        filled = int(value / max_value * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        return f"[{bar}]"

    def _prompt_player(self, choices: List[Choice]) -> Optional[Choice]:
        """显示选择列表并获取玩家输入

        Args:
            choices: 选择点列表

        Returns:
            Choice: 玩家选择的选项，如果选择退出则返回 None
        """
        print("\n【抉择点】请选择你的行动：\n")

        # 显示选项
        available_choices = []
        for i, choice in enumerate(choices, 1):
            if choice.is_available(self.state):
                available_choices.append(choice)
                display_text = choice.get_display_text(self.state)

                # 添加后果预览
                consequence_preview = choice.get_consequence_preview()
                if consequence_preview:
                    display_text += f"\n     └─ 后果：{consequence_preview}"

                print(f"  {i}. {display_text}\n")
            else:
                # 显示不可用的选项（灰色）
                print(f"  {i}. 🔒 {choice.choice_text} (条件不满足)\n")

        # 添加系统选项
        print(f"  {len(choices) + 1}. 💾 保存进度")
        print(f"  {len(choices) + 2}. 🚪 退出游戏\n")

        print("━" * 70)

        # 获取输入
        while True:
            try:
                user_input = input(f"\n请输入选项编号 [1-{len(choices) + 2}]: ").strip()

                if not user_input:
                    continue

                choice_num = int(user_input)

                # 系统选项
                if choice_num == len(choices) + 1:
                    # 保存进度
                    self.save_game()
                    print("✅ 进度已保存\n")
                    continue

                elif choice_num == len(choices) + 2:
                    # 退出游戏
                    confirm = input("确定要退出吗？(y/n): ").strip().lower()
                    if confirm == 'y':
                        return None
                    continue

                # 选择点
                if 1 <= choice_num <= len(choices):
                    selected = choices[choice_num - 1]

                    # 检查是否可用
                    if selected.is_available(self.state):
                        return selected
                    else:
                        print("❌ 该选项当前不可用（条件不满足）")
                        continue
                else:
                    print(f"❌ 请输入 1-{len(choices) + 2} 之间的数字")

            except ValueError:
                print("❌ 请输入有效的数字")
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"❌ 输入错误：{e}")

    def _display_response(self, response: str) -> None:
        """显示叙事响应

        Args:
            response: 响应文本
        """
        print("\n" + "━" * 70 + "\n")
        print(response)
        print("\n" + "━" * 70)

    def _check_scene_transition(self) -> None:
        """检查是否需要切换场景"""
        # TODO: 根据 GDD 定义的场景转换规则判断
        # 目前简化版：由选择点的后果直接控制场景切换
        pass

    def _check_ending(self) -> bool:
        """检查是否达成结局

        Returns:
            bool: 是否已达成结局条件
        """
        # TODO: 根据 GDD 定义的结局条件判断
        # 简化版实现

        # 条件 1: 达到最终场景
        if self.state.current_scene == "S6" or self.state.current_scene.startswith("结局"):
            return True

        # 条件 2: 超时（游戏内时间超过 06:00）
        if self._parse_time(self.state.timestamp) >= self._parse_time("06:00"):
            return True

        # 条件 3: 共鸣度达到 100（失衡状态）
        if self.state.PR >= 100:
            return True

        return False

    def _parse_time(self, time_str: str) -> int:
        """解析时间字符串为分钟数

        Args:
            time_str: 时间字符串，如 "03:45"

        Returns:
            int: 总分钟数
        """
        try:
            h, m = map(int, time_str.split(':'))
            return h * 60 + m
        except:
            return 0

    def _show_ending(self) -> str:
        """显示结局

        Returns:
            str: 结局类型
        """
        print("\n\n" + "=" * 70)
        print("                          【 结 局 】")
        print("=" * 70 + "\n")

        # 判断结局类型
        ending_type = self._determine_ending_type()

        # 显示结局文本
        ending_text = self._get_ending_text(ending_type)
        print(ending_text)

        # 显示统计信息
        self._show_statistics()

        print("\n" + "=" * 70)
        print("                      感谢游玩！")
        print("=" * 70 + "\n")

        return ending_type

    def _determine_ending_type(self) -> str:
        """判断结局类型

        Returns:
            str: 结局类型标识
        """
        # TODO: 根据 GDD 定义的结局条件判断
        # 简化版实现

        # 检查后果树中的关键选择
        has_core = "失魂核心" in self.state.inventory
        has_played_audio = "录音_已播放" in self.state.flags

        if has_core and has_played_audio:
            return "ending_completion"  # 补完结局
        elif not has_core and has_played_audio:
            return "ending_observer"    # 旁观结局
        elif self.state.PR >= 100:
            return "ending_lost"        # 迷失结局
        elif self._parse_time(self.state.timestamp) >= self._parse_time("06:00"):
            return "ending_timeout"     # 超时结局
        else:
            return "ending_unknown"     # 未知结局

    def _get_ending_text(self, ending_type: str) -> str:
        """获取结局文本

        Args:
            ending_type: 结局类型

        Returns:
            str: 结局文本
        """
        endings = {
            "ending_completion": """
**【补完结局】**

你持有失魂核心，播放了录音。
那些失魂者...终于找到了归宿。

这座城市的裂缝，被你修补了。
至少，暂时如此。
""",
            "ending_observer": """
**【旁观结局】**

你播放了录音，但没有核心。
你只是一个见证者。

那些失魂者仍在游荡，
而你...活了下来。
""",
            "ending_lost": """
**【迷失结局】**

共鸣度达到 100%。
你的意识...溶解了。

你成为了第九个失魂者。
""",
            "ending_timeout": """
**【超时结局】**

天亮了。
早班员工到来，你离开了这里。

但你知道，今晚发生的一切，
都是真的。
""",
            "ending_unknown": """
**【未知结局】**

你的故事，以一种意想不到的方式结束了。
"""
        }

        return endings.get(ending_type, endings["ending_unknown"])

    def _show_statistics(self) -> None:
        """显示统计信息"""
        print("\n**【统计数据】**\n")
        print(f"- 最终 PR：{self.state.PR}/100")
        print(f"- 最终 GR：{self.state.GR}/100")
        print(f"- 最终 WF：{self.state.WF}/10")
        print(f"- 游戏时长：{self.state.timestamp}")
        print(f"- 做出选择：{len(self.state.consequence_tree)} 次")
        print(f"- 获得道具：{len(self.state.inventory)} 个")

    def save_game(self, filename: Optional[str] = None) -> str:
        """保存游戏进度

        Args:
            filename: 存档文件名（可选）

        Returns:
            str: 存档文件路径
        """
        if filename is None:
            # 自动生成文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.city}_{self.state.current_scene}_{timestamp}.save"

        filepath = self.save_dir / filename
        self.state.save(str(filepath))

        return str(filepath)

    def load_game(self, filepath: str) -> None:
        """加载游戏进度

        Args:
            filepath: 存档文件路径
        """
        self.state = GameState.load(filepath)
        print(f"✅ 已加载存档：{filepath}")

    def _offer_save(self) -> None:
        """提示玩家是否保存进度"""
        try:
            save = input("\n是否保存当前进度？(y/n): ").strip().lower()
            if save == 'y':
                filepath = self.save_game()
                print(f"✅ 进度已保存至：{filepath}")
        except:
            pass


def main():
    """命令行入口（用于测试）"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python -m ghost_story_factory.engine.game_loop <城市名>")
        print("示例: python -m ghost_story_factory.engine.game_loop 杭州")
        sys.exit(1)

    city = sys.argv[1]

    try:
        engine = GameEngine(city)
        engine.run()
    except FileNotFoundError as e:
        print(f"❌ 错误：{e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n游戏已中断")
        sys.exit(0)


if __name__ == "__main__":
    main()

