"""选择点生成器

根据当前场景和游戏状态生成3种类型的选择点：
- 微选择（MICRO）：日常互动，低风险
- 普通选择（NORMAL）：情节推进
- 关键选择（CRITICAL）：结局分支
"""

# 兼容模式：pydantic 可选依赖（MVP/最小环境可运行）
try:
    from pydantic import BaseModel, Field
except Exception:
    class BaseModel:  # type: ignore
        def __init__(self, **data):
            for k, v in data.items():
                setattr(self, k, v)
        def model_dump(self):
            return self.__dict__
    def Field(default=None, description: str = "", default_factory=None, **kwargs):
        if default_factory is not None and default is None:
            try:
                return default_factory()
            except Exception:
                return None
        return default
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import json

from .state import GameState


class ChoiceType(str, Enum):
    """选择点类型"""
    MICRO = "micro"          # 微选择：日常互动
    NORMAL = "normal"        # 普通选择：情节推进
    CRITICAL = "critical"    # 关键选择：结局分支


class Choice(BaseModel):
    """选择点数据模型

    Attributes:
        choice_id: 唯一标识，如 "S3_C1"
        choice_text: 显示给玩家的选项文本
        choice_type: 选择类型（micro/normal/critical）
        preconditions: 前置条件（可选），如 {"PR": ">=40", "items": ["道具1"]}
        consequences: 后果（可选），如 {"PR": "+5", "items": ["道具2"]}
        tags: 标签列表，用于分类，如 ["保守", "遵守手册"]
        timeout: 超时时间（秒），仅用于 CRITICAL 类型
        can_skip: 是否可跳过
    """

    choice_id: str = Field(..., description="唯一标识，如 S3_C1")
    choice_text: str = Field(..., description="显示文本")
    choice_type: ChoiceType = Field(default=ChoiceType.NORMAL, description="选择类型")

    preconditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="前置条件，如 {'PR': '>=40', 'items': ['道具1']}"
    )
    consequences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="后果，如 {'PR': '+5', 'items': ['道具2'], 'flags': {'flag1': True}}"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="标签列表，如 ['保守', '遵守手册']"
    )

    timeout: Optional[int] = Field(
        default=None,
        description="超时时间（秒），仅用于 CRITICAL 类型"
    )
    can_skip: bool = Field(
        default=False,
        description="是否可跳过"
    )

    def is_available(self, game_state: GameState) -> bool:
        """检查选项是否可用

        Args:
            game_state: 当前游戏状态

        Returns:
            bool: 是否满足前置条件
        """
        if not self.preconditions:
            return True
        return game_state.check_preconditions(self.preconditions)

    def get_display_text(self, game_state: GameState) -> str:
        """生成显示文本（含可用性标记）

        Args:
            game_state: 当前游戏状态

        Returns:
            str: 格式化的显示文本
        """
        # 检查是否可用
        if not self.is_available(game_state):
            return f"🔒 {self.choice_text} (条件不满足)"

        # 根据类型添加图标
        icon_map = {
            ChoiceType.MICRO: "💬",
            ChoiceType.NORMAL: "💼",
            ChoiceType.CRITICAL: "⚠️"
        }
        icon = icon_map.get(self.choice_type, "•")

        # 添加标签提示
        tag_hint = ""
        if self.tags:
            tag_hint = f" [{', '.join(self.tags)}]"

        return f"{icon} {self.choice_text}{tag_hint}"

    def get_consequence_preview(self) -> str:
        """获取后果预览（用于UI提示）

        Returns:
            str: 后果预览文本
        """
        if not self.consequences:
            return ""

        previews = []

        # PR 变化
        if "PR" in self.consequences:
            pr_change = self.consequences["PR"]
            previews.append(f"PR {pr_change}")

        # 道具变化
        if "items" in self.consequences:
            items = self.consequences["items"]
            if items:
                previews.append(f"获得道具 x{len(items)}")

        # 时间消耗
        if "timestamp" in self.consequences:
            previews.append("消耗时间")

        return " | ".join(previews) if previews else ""


class ChoicePointsGenerator:
    """选择点生成器

    根据当前场景和游戏状态，调用 LLM 生成合适的选择点列表
    """

    def __init__(self, gdd_content: str, lore_content: str, main_story: str = ""):
        """初始化生成器

        Args:
            gdd_content: GDD（AI 导演任务简报）内容
            lore_content: Lore v2（世界观）内容
            main_story: 主线故事内容（可选，用于会话级缓存）
        """
        self.gdd = gdd_content
        self.lore = lore_content
        self.main_story = main_story
        self.prompt_template = self._load_prompt_template()

        # 会话级缓存
        self.crew = None  # 持久的 Crew 实例（保留占位）
        self.session_initialized = False  # 是否已初始化会话
        self._llm = None  # 复用 LLM 实例
        self._kimi_model_choices = None  # 记录模型名用于日志
        self._scene_memory = {}  # 场景 -> 锚点摘要与规则缓存
        import os, threading
        self._sem = threading.Semaphore(int(os.getenv("KIMI_CONCURRENCY_CHOICES", os.getenv("KIMI_CONCURRENCY", "4"))))

    def _load_prompt_template(self) -> str:
        """加载 prompt 模板

        优先从项目根目录加载，如果不存在则从 templates 目录加载

        Returns:
            str: Prompt 模板内容
        """
        # 尝试从项目根目录加载
        root_prompt = Path("choice-points.prompt.md")
        if root_prompt.exists():
            with open(root_prompt, 'r', encoding='utf-8') as f:
                return f.read()

        # 回退到 templates 目录
        template_prompt = Path("templates/choice-points.prompt.md")
        if template_prompt.exists():
            with open(template_prompt, 'r', encoding='utf-8') as f:
                return f.read()

        # 如果都不存在，返回内置的简化模板
        return self._get_builtin_template()

    def _get_builtin_template(self) -> str:
        """获取内置模板（当文件不存在时的回退）"""
        return """
你是一个专业的"选择点生成器"，负责在关键剧情节点生成合适的选项。

## 你的任务

基于当前场景和游戏状态，生成 2-4 个选择点。

## 选择点分类

- MICRO：微选择，日常互动
- NORMAL：普通选择，情节推进
- CRITICAL：关键选择，结局分支

## 输出格式（JSON）

```json
{
  "scene_id": "S3",
  "choices": [
    {
      "choice_id": "S3_C1",
      "choice_text": "选项文本",
      "choice_type": "normal",
      "preconditions": {"PR": ">=40"},
      "consequences": {
        "PR": "+5",
        "items": ["道具1"],
        "flags": {"flag1": true}
      },
      "tags": ["保守", "安全"],
      "timeout": null,
      "can_skip": false
    }
  ]
}
```

## 注意事项

1. 每个选项都应该是"可行的"
2. 至少 2 个选项是"合理的"
3. 后果应该"可预见"
4. 选项数量：2-4 个
5. 不给玩家"跳出框架"的选项
"""

    def generate_choices(
        self,
        current_scene: str,
        game_state: GameState,
        narrative_context: Optional[str] = None
    ) -> List[Choice]:
        """生成选择点

        Args:
            current_scene: 当前场景 ID，如 "S3"
            game_state: 当前游戏状态
            narrative_context: 当前叙事上下文（可选），由 RuntimeResponseGenerator 提供

        Returns:
            List[Choice]: 选择点列表
        """
        # 延迟导入 CrewAI（避免基础功能依赖）
        try:
            from crewai import Agent, Task, Crew, LLM
            import os
        except ImportError:
            print("⚠️  CrewAI 未安装，无法生成选择点，返回默认选择点")
            return self._get_default_choices(current_scene)

        # 复用 Kimi LLM 实例（选择点生成专用模型）
        llm = self._get_llm()
        print(f"🤖 [选择点] 使用模型: {self._kimi_model_choices}")

        # 构建 prompt（使用场景记忆缓存/RAG锚点）
        prompt = self._build_prompt(current_scene, game_state, narrative_context)
        # 在 prompt 尾部加入结局引导与世界书约束，提升通向结局的倾向
        endings_hint = (
            "\n\n[结局与规则]\n"
            "- 至少提供 1 个会推进至关键线索或结局的选项（标记为 'critical'）\n"
            "- 遵循世界书规则与主线伏笔，避免烂尾\n"
        )
        prompt = prompt + endings_hint

        # 创建 Agent（使用 Kimi LLM）
        agent = Agent(
            role="选择点设计师",
            goal="生成符合场景的选择点，引导玩家在框架内做出选择",
            backstory=(
                "你精通叙事设计和玩家心理学。"
                "你擅长设计有意义的选择点，让玩家感觉'我在控制剧情'，"
                "但实际上所有选择都在设计好的框架内。"
            ),
            verbose=False,
            allow_delegation=False,
            llm=llm  # 使用 Kimi LLM
        )

        # 创建任务
        task = Task(
            description=prompt,
            expected_output="严格的 JSON 对象（仅一段），不要额外文本",
            agent=agent
        )

        # 执行（带一次重试，二次更严格提示）
        result_text = self._call_llm_with_retry(
            agent,
            task,
            retry_suffix="\n\n重要：仅输出一个 JSON 对象，不要任何解释或额外文本。"
        )

        # 空响应防护：直接回退到本地默认选择，避免解析报错
        if not result_text or not str(result_text).strip():
            return self._get_default_choices(current_scene)

        # 解析结果
        try:
            choices_data = self._parse_result(result_text)
            # 标准化所有 choice 字段
            raw_choices = [self._normalize_choice_fields(c) for c in choices_data.get('choices', [])]

            # 强制推进与结局注入策略（避免平台化）：
            # - 每 N 个场景（默认3）至少提供一个 critical 选项
            # - 若不存在 critical，则追加一个“直面关键线索”的 critical 选项
            import os, re
            force_every = int(os.getenv("FORCE_CRITICAL_INTERVAL", "3"))
            scene_num = 0
            m = re.search(r"S(\d+)", str(current_scene))
            if m:
                try:
                    scene_num = int(m.group(1))
                except Exception:
                    scene_num = 0

            has_critical = any(str(c.get('choice_type', 'normal')).lower() == 'critical' for c in raw_choices)
            need_force = (force_every > 0 and scene_num > 0 and (scene_num % force_every == 0))

            if not has_critical and need_force:
                raw_choices.append({
                    "choice_id": f"{current_scene}_E1",
                    "choice_text": "直面关键线索（可能触发结局）",
                    "choice_type": "critical",
                    "consequences": {"timestamp": "+12min", "flags": {"结局_线索达成": True}},
                    "tags": ["主线推进", "关键线索"]
                })

            # 提升 critical 的时间推进（默认至少 +10min）
            for c in raw_choices:
                if str(c.get('choice_type', 'normal')).lower() == 'critical':
                    cons = c.get('consequences') or {}
                    ts = str(cons.get('timestamp', '')).strip()
                    if not ts:
                        cons['timestamp'] = "+10min"
                    c['consequences'] = cons

            return [Choice(**choice) for choice in raw_choices]
        except Exception as e:
            print(f"⚠️  解析选择点失败: {e}")
            # 返回默认选择点
            return self._get_default_choices(current_scene)

    def _get_llm(self):
        """获取（并复用）LLM 实例"""
        if self._llm is not None:
            return self._llm

        from crewai import LLM
        import os

        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
        self._kimi_model_choices = os.getenv("KIMI_MODEL_CHOICES") or os.getenv("KIMI_MODEL", "moonshot-v1-32k")

        self._llm = LLM(
            model=self._kimi_model_choices,
            api_key=kimi_key,
            base_url=kimi_base
        )
        return self._llm

    def _get_scene_memory(self, scene: str) -> str:
        """获取场景锚点摘要与规则（缓存）"""
        if scene in self._scene_memory:
            return self._scene_memory[scene]

        # 提取当前场景相关的 GDD 片段（最多 500 字）
        scene_gdd = self._extract_scene_context(self.gdd, scene, max_chars=500)
        # 提取核心 Lore 规则（最多 300 字）
        core_lore = self._extract_core_lore(self.lore, max_chars=300)

        memory = f"{scene_gdd}\n\n[规则摘要]\n{core_lore}"
        # 控制整体大小（~600-800字），但不做激进截断以保证质量
        memory = memory[:1200]
        self._scene_memory[scene] = memory
        return memory

    def _call_llm_with_retry(self, agent, task, retry_suffix: str = "", max_retries: int = 1) -> str:
        """执行 LLM 任务，失败后附加严格提示进行一次重试"""
        from crewai import Crew, Task
        # 首次
        crew = Crew(agents=[agent], tasks=[task], verbose=False)
        with self._sem:
            result = crew.kickoff()
        text = str(result)
        # 解析试探
        try:
            _ = self._parse_result(text)
            return text
        except Exception:
            if max_retries <= 0:
                return text
        # 重试一次，附加更严格的输出要求
        strict_task = Task(
            description=task.description + (retry_suffix or ""),
            expected_output="严格 JSON（仅一个对象）",
            agent=agent
        )
        crew2 = Crew(agents=[agent], tasks=[strict_task], verbose=False)
        with self._sem:
            result2 = crew2.kickoff()
        return str(result2)

    def _build_prompt(
        self,
        current_scene: str,
        game_state: GameState,
        narrative_context: Optional[str]
    ) -> str:
        """构建完整的 prompt（优化版：只发送相关内容）"""
        context = narrative_context or "玩家刚进入该场景。"
        # 使用场景记忆（RAG锚点）
        scene_memory = self._get_scene_memory(current_scene)

        return f"""
你是一个专业的选择点设计师。请根据当前场景和游戏状态，生成 2-4 个选择点。

## 当前状态

**场景**: {current_scene}
**上下文**: {context}
**PR**: {game_state.PR}/100 | **时间**: {game_state.timestamp}
**道具**: {', '.join(game_state.inventory[:3]) if game_state.inventory else '无'}

---

## 场景锚点与规则（缓存）

{scene_memory}

---

## 输出要求

**必须**输出 JSON 格式，包含 2-4 个选择：

```json
{{
  "scene_id": "{current_scene}",
  "choices": [
    {{
      "id": "A",
      "text": "选项文本",
      "tags": ["标签1", "标签2"],
      "immediate_consequences": {{
        "resonance": "+10",
        "flags": {{"flag_name": true}}
      }}
    }}
  ]
}}
```

请生成符合当前场景的选择点。务必只输出一个 JSON 对象，不要包含额外文本。
"""

    def _extract_scene_context(self, gdd: str, scene: str, max_chars: int = 500) -> str:
        """提取当前场景相关的 GDD 片段

        Args:
            gdd: 完整 GDD
            scene: 场景 ID
            max_chars: 最大字符数

        Returns:
            str: 场景相关的 GDD 片段
        """
        # 简单实现：查找包含场景 ID 的段落
        lines = gdd.split('\n')
        relevant_lines = []
        in_relevant_section = False

        for i, line in enumerate(lines):
            # 如果找到场景标题
            if scene.lower() in line.lower() or f"场景{scene[1:]}" in line:
                in_relevant_section = True
                relevant_lines.append(line)
                # 收集后续行
                for j in range(i + 1, min(i + 20, len(lines))):
                    if lines[j].strip().startswith('#') and lines[j].strip() != line.strip():
                        break  # 遇到下一个标题
                    relevant_lines.append(lines[j])
                break

        result = '\n'.join(relevant_lines)[:max_chars]
        return result if result else f"场景 {scene}（无详细信息）"

    def _extract_core_lore(self, lore: str, max_chars: int = 300) -> str:
        """提取核心 Lore 规则

        Args:
            lore: 完整 Lore
            max_chars: 最大字符数

        Returns:
            str: 核心规则摘要
        """
        # 简单实现：提取前几段或关键规则
        lines = lore.split('\n')
        core_lines = []

        # 收集包含"规则"、"核心"、"必须"等关键词的行
        keywords = ['规则', '核心', '必须', '不可', '禁止', '世界观', 'PR', 'GR']
        for line in lines[:50]:  # 只看前 50 行
            if any(kw in line for kw in keywords):
                core_lines.append(line)
                if len('\n'.join(core_lines)) > max_chars:
                    break

        result = '\n'.join(core_lines)[:max_chars]
        return result if result else "恐怖氛围游戏，注重细节和心理描写。"

    def _parse_result(self, result_text: str) -> Dict:
        """解析 LLM 返回结果（超强版：处理各种异常格式）

        Args:
            result_text: LLM 返回的文本

        Returns:
            Dict: 解析后的数据（标准格式）
        """
        import re

        # 清理文本（归一化与中文标点修复）
        result_text = result_text.strip()
        try:
            import unicodedata, re as _re
            t = unicodedata.normalize("NFKC", result_text)
            # 修复常见 JSON 病毒：中文分隔号、全角逗号/冒号
            t = t.replace('，', ',').replace('：', ':').replace('（', '(').replace('）', ')')
            # 尾随逗号去除
            t = _re.sub(r',\s*([}\]])', r'\1', t)
            result_text = t
        except Exception:
            pass

        # 方法1: 提取 JSON 代码块
        if "```json" in result_text:
            start = result_text.find("```json") + 7
            end = result_text.find("```", start)
            if end != -1:
                result_text = result_text[start:end].strip()
        elif "```" in result_text:
            start = result_text.find("```") + 3
            end = result_text.find("```", start)
            if end != -1:
                result_text = result_text[start:end].strip()

        # 方法2: 查找第一个 { 到对应的结束 } （处理嵌套）
        first_brace = result_text.find('{')
        if first_brace != -1:
            # 使用栈匹配括号
            brace_count = 0
            end_pos = first_brace
            for i in range(first_brace, len(result_text)):
                if result_text[i] == '{':
                    brace_count += 1
                elif result_text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i + 1
                        break
            result_text = result_text[first_brace:end_pos].strip()

        # 清理可能的多余字符
        result_text = result_text.strip()

        # 尝试解析 JSON
        try:
            data = json.loads(result_text)
            # 标准化格式
            return self._normalize_format(data)
        except json.JSONDecodeError as e:
            # 如果解析失败，尝试修复常见问题
            print(f"⚠️  首次JSON解析失败: {e}")
            print(f"📄 原始文本前500字符:\n{result_text[:500]}")

            # 尝试修复：移除注释 / 修复尾随逗号
            result_text = re.sub(r'//.*?\n', '\n', result_text)
            result_text = re.sub(r'/\*.*?\*/', '', result_text, flags=re.DOTALL)
            result_text = re.sub(r',\s*([}\]])', r'\1', result_text)

            # 尝试修复：处理 "Extra data" 错误（只取第一个完整JSON）
            try:
                # 使用 JSONDecoder 的 raw_decode 只解析第一个对象
                decoder = json.JSONDecoder()
                data, idx = decoder.raw_decode(result_text)
                print(f"✅ 使用 raw_decode 成功解析（忽略了后续数据）")
                return self._normalize_format(data)
            except json.JSONDecodeError as e2:
                print(f"❌ 二次JSON解析仍然失败: {e2}")
                raise

    def _normalize_format(self, data: Dict) -> Dict:
        """标准化 JSON 格式（处理 Kimi 可能返回的各种格式）

        Args:
            data: 原始 JSON 数据

        Returns:
            Dict: 标准格式 {"scene_id": "...", "choices": [...]}
        """
        # 格式1: 标准格式（已经是我们想要的）
        if "choices" in data and isinstance(data["choices"], list):
            # 标准化每个 choice 的字段名
            data["choices"] = [self._normalize_choice_fields(c) for c in data["choices"]]
            return data

        # 格式2: 单个选择点对象（不是数组）
        if "choice_id" in data or "choice_text" in data or "id" in data or "text" in data:
            # 包装成标准格式
            return {
                "scene_id": data.get("scene", "unknown"),
                "choices": [self._normalize_choice_fields(data)]
            }

        # 格式3: 直接是选择点数组
        if isinstance(data, list):
            return {
                "scene_id": "unknown",
                "choices": [self._normalize_choice_fields(c) for c in data]
            }

        # 格式4: 其他格式，尝试提取
        # 查找所有可能的选择点字段
        choices = []
        for key in ["options", "choice_points", "选择点", "选项"]:
            if key in data and isinstance(data[key], list):
                choices = data[key]
                break

        if choices:
            return {
                "scene_id": data.get("scene_id", data.get("scene", "unknown")),
                "choices": [self._normalize_choice_fields(c) for c in choices]
            }

        # 实在没办法，原样返回
        print(f"⚠️  无法识别的JSON格式，使用原始数据")
        return data

    def _normalize_choice_fields(self, choice: Dict) -> Dict:
        """标准化单个选择点的字段名

        Args:
            choice: 原始选择点数据

        Returns:
            Dict: 标准化后的选择点
        """
        normalized = {}

        # 字段映射表
        field_mapping = {
            # choice_id 的各种可能名称
            "choice_id": ["choice_id", "id", "option_id", "选项id"],
            # choice_text 的各种可能名称
            "choice_text": ["choice_text", "text", "option_text", "content", "选项文本", "内容"],
            # choice_type 的各种可能名称
            "choice_type": ["choice_type", "type", "option_type", "类型"],
            # 其他字段
            "preconditions": ["preconditions", "pre_conditions", "前置条件"],
            "consequences": ["consequences", "effects", "后果", "immediate_consequences"],
            "tags": ["tags", "labels", "标签"],
            "timeout": ["timeout", "time_limit", "超时"],
            "can_skip": ["can_skip", "skippable", "可跳过"],
        }

        # 映射字段
        for target_field, possible_names in field_mapping.items():
            for name in possible_names:
                if name in choice:
                    normalized[target_field] = choice[name]
                    break

        # 确保必需字段存在
        if "choice_id" not in normalized:
            normalized["choice_id"] = f"choice_{hash(str(choice)) % 10000}"

        if "choice_text" not in normalized:
            normalized["choice_text"] = choice.get("text", "未知选项")

        if "choice_type" not in normalized:
            normalized["choice_type"] = "normal"

        # 后果字段兜底：确保至少有时间推进，避免状态去重导致深度停滞
        if "consequences" not in normalized or not isinstance(normalized.get("consequences"), dict):
            normalized["consequences"] = {"timestamp": "+5min"}
        else:
            cons = normalized["consequences"]
            if (
                not any(k in cons for k in ["timestamp", "time", "scene"]) and
                not any(k in cons for k in ["PR", "GR", "WF", "flags", "inventory"])  # 完全静态则推进时间
            ):
                cons["timestamp"] = "+5min"

        # 保留其他未映射的字段
        for key, value in choice.items():
            if key not in normalized and key not in sum(field_mapping.values(), []):
                normalized[key] = value

        return normalized

    def _get_default_choices(self, current_scene: str) -> List[Choice]:
        """获取默认选择点（当生成失败时的回退）

        Args:
            current_scene: 当前场景 ID

        Returns:
            List[Choice]: 默认选择点列表
        """
        return [
            Choice(
                choice_id=f"{current_scene}_C1",
                choice_text="沿主线线索继续深入",
                choice_type=ChoiceType.NORMAL,
                consequences={"timestamp": "+6min", "GR": "+3"}
            ),
            Choice(
                choice_id=f"{current_scene}_C2",
                choice_text="原地观察环境细节",
                choice_type=ChoiceType.NORMAL,
                consequences={"PR": 5, "timestamp": "+3min"}
            ),
            Choice(
                choice_id=f"{current_scene}_E1",
                choice_text="直面关键线索（可能触发结局）",
                choice_type=ChoiceType.CRITICAL,
                consequences={"timestamp": "+12min", "flags": {"结局_线索达成": True}},
            )
        ]


# 工具函数

def load_choices_from_file(filepath: str) -> List[Choice]:
    """从文件加载预设选择点

    Args:
        filepath: JSON 文件路径

    Returns:
        List[Choice]: 选择点列表
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return [Choice(**choice) for choice in data['choices']]


def save_choices_to_file(choices: List[Choice], filepath: str) -> None:
    """保存选择点到文件

    Args:
        choices: 选择点列表
        filepath: 保存路径
    """
    data = {
        "choices": [choice.model_dump() for choice in choices]
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

