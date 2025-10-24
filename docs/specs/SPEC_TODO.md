# Ghost Story Factory - 待开发功能规格书

**文档版本**: v1.1
**创建日期**: 2025-10-24
**最后更新**: 2025-10-24
**项目状态**: Stage 1-3 已完成，Stage 4 核心功能已完成（P0/P1）

---

## 🎉 最新进展 (2025-10-24)

### ✅ Phase 1 已完成！交互式游戏引擎核心

**实现日期**: 2025-10-24
**总代码量**: ~3,000 行
**测试状态**: 所有核心功能测试通过

#### 已完成模块
1. ✅ **GameState 状态管理器** (`src/ghost_story_factory/engine/state.py` - 374行)
2. ✅ **ChoicePointsGenerator 选择点生成器** (`src/ghost_story_factory/engine/choices.py` - 368行)
3. ✅ **RuntimeResponseGenerator 响应生成器** (`src/ghost_story_factory/engine/response.py` - 279行)
4. ✅ **GameEngine 游戏主循环** (`src/ghost_story_factory/engine/game_loop.py` - 467行)
5. ✅ **IntentMappingEngine 意图映射引擎** (`src/ghost_story_factory/engine/intent.py` - 383行)
6. ✅ **GameCLI 命令行界面** (`src/ghost_story_factory/ui/cli.py` - 489行)
7. ✅ **EndingSystem 多结局系统** (`src/ghost_story_factory/engine/endings.py` - 478行)

#### 新增文档
- ✅ GAME_ENGINE_README.md - 游戏引擎总览
- ✅ GAME_ENGINE_USAGE.md - 详细 API 文档
- ✅ INSTALLATION.md - 安装指南
- ✅ IMPLEMENTATION_SUMMARY.md - 实现总结
- ✅ TEST_RESULTS.md - 测试报告
- ✅ FINAL_SUMMARY.md - 完整总结
- ✅ QUICK_START.md - 快速入门指南

#### 新增依赖
- ✅ pydantic>=2.5.0 - 数据验证
- ✅ rich>=13.7.0 - CLI 美化

#### 新增命令
- ✅ `ghost-story-play` - 启动交互式游戏

#### 演示脚本
- ✅ `demo_game.py` - 自动演示完整流程
- ✅ `play_game_correct.py` - 可玩版本（基于真实杭州故事）
- ✅ `test_flow_simple.py` - 核心功能测试

**查看详情**:
- 技术实现: `cat IMPLEMENTATION_SUMMARY.md`
- 测试结果: `cat TEST_RESULTS.md`
- 快速开始: `cat QUICK_START.md`

---

## 📋 目录

1. [项目现状](#项目现状)
2. [待开发功能清单](#待开发功能清单)
3. [优先级划分](#优先级划分)
4. [详细需求规格](#详细需求规格)
5. [技术架构](#技术架构)
6. [开发路线图](#开发路线图)

---

## ✅ 项目现状

### 已完成功能 (Stage 1-3: 静态故事生成)

#### 核心命令
- ✅ `set-city` - 设置城市并生成候选故事列表
- ✅ `get-struct` - 选择故事并生成结构
- ✅ `get-lore` - 生成 Lore v1（世界观基础）
- ✅ `gen-protagonist` - 生成主角分析报告
- ✅ `gen-lore-v2` - 生成 Lore v2（含游戏系统）
- ✅ `gen-gdd` - 生成 AI 导演任务简报
- ✅ `gen-main-thread` - 生成主线完整故事
- ✅ `gen-branch` - 生成分支故事
- ✅ `gen-complete` - 自动化完整流程

#### 文档系统
- ✅ 35 个templates模板（design/example/prompt 三件套）
- ✅ 架构文档（00-architecture.md, README.md）
- ✅ 上下文管理策略（00-index.md）
- ✅ 项目 README 和 WORKFLOW 文档

#### 技术实现
- ✅ CrewAI + LiteLLM 集成
- ✅ Kimi/OpenAI API 支持
- ✅ JSON 容错处理
- ✅ 模块化 prompt 系统
- ✅ CLI 命令注册与参数解析

---

## 🚧 待开发功能清单

### ✅ Phase 1: 交互式游戏引擎核心 (Stage 4 基础) - 已完成！

#### ✅ 1.1 选择点生成器（Choice Points Generator）
**状态**: ✅ 已完成 (2025-10-24)
**优先级**: P0（最高）
**依赖**: 需要 GDD + Lore v2
**实现文件**: `src/ghost_story_factory/engine/choices.py`

**功能需求**:
- 根据当前游戏状态生成 3 种类型的选择点：
  - 微选择（Micro Choices）：日常互动，低风险
  - 普通选择（Normal Choices）：情节推进
  - 关键选择（Critical Choices）：结局分支
- 每个选择点包含：
  - `choice_id`: 唯一标识
  - `choice_text`: 显示文本
  - `choice_type`: micro/normal/critical
  - `preconditions`: 前置条件（共鸣度、道具等）
  - `consequences`: 预定义后果（PR/GR/WF 变化、触发事件等）
- 选择点需符合"四重笼子设计"：
  1. 选项数量限制（3-5 个）
  2. 物理边界限制（角色能力范围内）
  3. 后果透明度（玩家可预判）
  4. 强制抉择点（无法跳过）

**技术实现**:
```python
class ChoicePointsGenerator:
    def __init__(self, gdd: str, lore_v2: str, prompt_template: str):
        pass

    def generate_choices(
        self,
        current_scene: str,
        game_state: GameState
    ) -> List[Choice]:
        """基于当前场景和游戏状态生成选择点"""
        pass
```

**输出格式**:
```json
{
  "scene_id": "S3",
  "choices": [
    {
      "choice_id": "S3_C1",
      "choice_text": "拍照失魂者 → 获得暗号",
      "choice_type": "normal",
      "preconditions": {"PR": ">=40"},
      "consequences": {
        "PR": "+5",
        "items": ["暗号:36-3=33"],
        "flags": ["失魂者_已拍照"]
      }
    }
  ]
}
```

---

#### ✅ 1.2 游戏状态管理器（State Manager）
**状态**: ✅ 已完成 (2025-10-24)
**优先级**: P0（最高）
**依赖**: 无
**实现文件**: `src/ghost_story_factory/engine/state.py`

**功能需求**:
- 管理核心游戏变量：
  - **个人共鸣度 (PR)**: 0-100
  - **全局共鸣度 (GR)**: 服务器/存档级别
  - **世界疲劳值 (WF)**: 0-10
  - **时间戳**: 游戏内时间（00:00-04:00）
  - **道具栏**: List[Item]
  - **标志位**: Dict[str, bool]（事件触发记录）
  - **当前场景**: scene_id
  - **后果树节点**: 历史选择记录
- 提供状态查询、更新、回滚接口
- 支持状态持久化（保存/读档）
- 校验状态合法性（例如 PR 不能超过 100）

**技术实现**:
```python
@dataclass
class GameState:
    PR: int = 5  # 个人共鸣度
    GR: int = 0  # 全局共鸣度（多人共享）
    WF: int = 0  # 世界疲劳值
    timestamp: str = "00:00"
    inventory: List[str] = field(default_factory=list)
    flags: Dict[str, bool] = field(default_factory=dict)
    current_scene: str = "S1"
    consequence_tree: List[str] = field(default_factory=list)

    def update(self, changes: Dict[str, Any]) -> None:
        """应用状态变化并校验"""
        pass

    def check_preconditions(self, preconditions: Dict) -> bool:
        """检查前置条件是否满足"""
        pass

    def save(self, filepath: str) -> None:
        """保存状态到文件"""
        pass

    @classmethod
    def load(cls, filepath: str) -> 'GameState':
        """从文件加载状态"""
        pass
```

---

#### ✅ 1.3 运行时响应生成器（Runtime Response Generator）
**状态**: ✅ 已完成 (2025-10-24)
**优先级**: P0（最高）
**依赖**: GDD + Lore v2 + State Manager
**实现文件**: `src/ghost_story_factory/engine/response.py`

**功能需求**:
- 根据玩家选择生成动态叙事响应：
  - 场景描述（第一人称，氛围营造）
  - 实体交互（根据 PR 触发不同 Tier）
  - 后果反馈（PR/GR/WF 变化的叙事化表达）
  - 下一步引导（暗示可用选择点）
- 响应风格需符合templates标准：
  - 沉浸式第一人称
  - 恐怖氛围营造（细节描写、感官刺激）
  - 节奏把控（留白、暗示）
- 每次响应后自动更新游戏状态

**技术实现**:
```python
class RuntimeResponseGenerator:
    def __init__(self, gdd: str, lore_v2: str, prompt_template: str):
        pass

    def generate_response(
        self,
        choice: Choice,
        game_state: GameState
    ) -> str:
        """生成玩家选择后的叙事响应"""
        pass
```

**输出示例**:
```markdown
我按下快门，"咔嚓"一声，照片 EXIF 写入暗号：36-3=33。
失魂者消失，像被风抽走。我手心全是汗，金属锤柄滑得像一条蛇。

【系统提示】
- PR +5 → 当前 45
- 获得道具：【暗号:36-3=33】
- 标志位：失魂者_已拍照
```

---

#### ✅ 1.4 意图映射引擎（Intent Mapping Engine）
**状态**: ✅ 已完成 (2025-10-24)
**优先级**: P1（高）
**依赖**: State Manager
**实现文件**: `src/ghost_story_factory/engine/intent.py`

**功能需求**:
- **选项交互式游戏的核心任务**：
  - 验证选项合法性（前置条件检查）
  - 提取选项意图层级（物理动作 → 心理动机 → 叙事意义）
  - 绑定后果树节点
  - 返回校验结果和映射后的意图对象
- **可选扩展（自由输入式游戏）**：
  - 解析自由文本输入
  - 将自然语言映射到标准化意图
  - 需要 NLU 模块支持

**技术实现**:
```python
class IntentMappingEngine:
    def __init__(self, prompt_template: str):
        pass

    def validate_choice(
        self,
        choice: Choice,
        game_state: GameState
    ) -> ValidationResult:
        """验证选项是否可用"""
        pass

    def extract_intent(self, choice: Choice) -> Intent:
        """提取选项的意图层级"""
        pass

    # 可选：自由输入式支持
    def parse_free_text(self, user_input: str) -> Intent:
        """解析自由文本输入（未来扩展）"""
        pass
```

---

### ✅ Phase 2: 游戏引擎整合与 UI - 已完成！

#### ✅ 2.1 游戏主循环（Game Loop）
**状态**: ✅ 已完成 (2025-10-24)
**优先级**: P0（最高）
**依赖**: 1.1-1.4 全部完成
**实现文件**: `src/ghost_story_factory/engine/game_loop.py`

**功能需求**:
- 加载 GDD、Lore v2、初始化游戏状态
- 主循环：
  1. 生成当前场景的选择点
  2. 显示给玩家并等待输入
  3. 验证选择合法性
  4. 应用后果并更新状态
  5. 生成运行时响应
  6. 检查结局条件
  7. 重复或结束
- 支持保存/读档
- 支持多结局分支

**技术实现**:
```python
class GameEngine:
    def __init__(self, city: str, gdd_path: str, lore_path: str):
        self.gdd = self._load(gdd_path)
        self.lore = self._load(lore_path)
        self.state = GameState()
        self.choice_generator = ChoicePointsGenerator(...)
        self.response_generator = RuntimeResponseGenerator(...)
        self.state_manager = StateManager()
        self.intent_mapper = IntentMappingEngine(...)

    def run(self):
        """主游戏循环"""
        while not self.check_ending():
            # 1. 生成选择点
            choices = self.choice_generator.generate_choices(
                self.state.current_scene,
                self.state
            )

            # 2. 显示并获取玩家输入
            selected_choice = self.prompt_player(choices)

            # 3. 验证并应用
            if self.intent_mapper.validate_choice(selected_choice, self.state):
                # 4. 更新状态
                self.state.update(selected_choice.consequences)

                # 5. 生成响应
                response = self.response_generator.generate_response(
                    selected_choice,
                    self.state
                )
                self.display(response)

        # 6. 结局
        self.show_ending()
```

---

#### ✅ 2.2 命令行界面（CLI UI）
**状态**: ✅ 已完成 (2025-10-24)
**优先级**: P1（高）
**依赖**: 2.1 完成
**实现文件**: `src/ghost_story_factory/ui/cli.py`

**功能需求**:
- 美化的命令行输出：
  - 使用 `rich` 库渲染 Markdown
  - 彩色高亮（选择点、系统提示、危险警告）
  - 进度条（PR/GR/WF 可视化）
  - 表格显示（选择列表）
- 交互式选择菜单（上下键选择）
- 支持历史记录查看（`/history` 命令）
- 支持快捷键（`/save`, `/load`, `/quit`）

**技术实现**:
```python
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.progress import Progress

class GameUI:
    def __init__(self):
        self.console = Console()

    def display_narrative(self, text: str):
        """显示叙事文本（Markdown 渲染）"""
        self.console.print(Markdown(text))

    def display_choices(self, choices: List[Choice]) -> Choice:
        """显示选择列表并获取玩家输入"""
        # 使用 rich.table 渲染选择列表
        pass

    def display_state(self, state: GameState):
        """显示游戏状态（PR/GR/WF）"""
        # 使用 progress bar 渲染状态条
        pass
```

---

#### 2.3 Web UI（可选）
**状态**: 未开发
**优先级**: P2（中）
**依赖**: 2.1 完成

**功能需求**:
- 使用 FastAPI + WebSocket 构建 Web 服务
- 前端使用 React/Vue 实现：
  - 沉浸式阅读界面（类似 AI Dungeon）
  - 按钮式选择点
  - 状态仪表盘（PR/GR/WF 实时更新）
  - 历史记录侧边栏
  - 存档管理
- 支持多人在线（共享 GR）

**技术实现**:
```python
# backend/api.py
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/game/{city}")
async def game_session(websocket: WebSocket, city: str):
    await websocket.accept()
    engine = GameEngine(city, ...)

    while True:
        # 发送选择点
        choices = engine.get_current_choices()
        await websocket.send_json({"type": "choices", "data": choices})

        # 接收玩家选择
        choice_id = await websocket.receive_json()

        # 处理并返回响应
        response = engine.process_choice(choice_id)
        await websocket.send_json({"type": "response", "data": response})
```

---

### Phase 3: 高级功能

#### 3.1 实体 AI 系统
**状态**: 未开发
**优先级**: P2（中）
**依赖**: 2.1 完成

**功能需求**:
- 实现世界书 2.0 定义的实体行为等级（Tiers）：
  - **不存在的清洁工**：T0-T4
  - **失魂者**：T0-T4
- 根据 PR/GR 动态触发不同 Tier 行为
- 实体交互逻辑：
  - 对话系统（实体可响应玩家行动）
  - 敌对/友好状态切换
  - 掉落道具系统

**技术实现**:
```python
class Entity:
    def __init__(self, name: str, tier_definitions: Dict):
        self.name = name
        self.tier_definitions = tier_definitions

    def get_current_tier(self, PR: int) -> int:
        """根据 PR 计算当前 Tier"""
        if PR < 20: return 0
        elif PR < 40: return 1
        elif PR < 60: return 2
        elif PR < 80: return 3
        else: return 4

    def interact(self, action: str, game_state: GameState) -> str:
        """处理玩家与实体的交互"""
        tier = self.get_current_tier(game_state.PR)
        behavior = self.tier_definitions[tier]
        # 调用 LLM 生成动态响应
        pass
```

---

#### ✅ 3.2 多结局系统
**状态**: ✅ 已完成 (2025-10-24)
**优先级**: P1（高）
**依赖**: 2.1 完成
**实现文件**: `src/ghost_story_factory/engine/endings.py`

**功能需求**:
- 实现 3 个主要结局：
  1. **补完**：持有失魂核心 + 播放录音
  2. **旁观**：无核心 + 播放录音
  3. **迷失**：未播放录音 + 超时
- 根据后果树计算最终结局
- 结局渲染：
  - 结局特定的叙事文本
  - 成就解锁
  - 统计数据（通关时间、PR 峰值、选择统计）

**技术实现**:
```python
class EndingSystem:
    def __init__(self, gdd: str):
        self.ending_definitions = self._parse_endings(gdd)

    def check_ending(self, game_state: GameState) -> Optional[str]:
        """检查是否达成结局条件"""
        for ending_id, conditions in self.ending_definitions.items():
            if self._match_conditions(conditions, game_state):
                return ending_id
        return None

    def render_ending(self, ending_id: str, game_state: GameState) -> str:
        """生成结局叙事"""
        # 调用 LLM 基于 ending_id 和 game_state 生成动态结局
        pass
```

---

#### 3.3 动态气象系统
**状态**: 未开发
**优先级**: P2（中）
**依赖**: 2.1 完成

**功能需求**:
- 接入真实天气 API（如和风天气）
- 根据世界书规则判断触发条件：
  - 杭州：雨停 + 东风 3-4 级
  - 其他城市：根据 Lore v1 定义
- 若自然条件不满足，提示使用"雨夜东风模拟器"
- 模拟器使用会增加 WF

**技术实现**:
```python
import requests

class WeatherSystem:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def check_conditions(self, city: str, required: Dict) -> bool:
        """检查当前天气是否满足触发条件"""
        weather = requests.get(f"https://api.weather.com/{city}").json()
        # 解析 required 条件并匹配
        pass

    def simulate(self, game_state: GameState):
        """使用模拟器强制触发"""
        game_state.WF += 1
        return True
```

---

#### 3.4 多人模式（可选）
**状态**: 未开发
**优先级**: P3（低）
**依赖**: 2.3 Web UI 完成

**功能需求**:
- 共享全局共鸣度 (GR) 和世界疲劳值 (WF)
- 玩家可以看到其他玩家的选择影响
- 实现"玩家失魂者"系统：
  - 被夺魂的玩家成为游荡 NPC
  - 其他玩家可见并交互
- 服务器事件广播

---

### Phase 4: 内容扩展工具

#### 4.1 故事编辑器
**状态**: 未开发
**优先级**: P2（中）
**依赖**: 无

**功能需求**:
- 可视化编辑 GDD：
  - 场景编辑器（添加/删除场景）
  - 选择点编辑器（设置前置条件和后果）
  - 实体编辑器（定义 Tiers 行为）
- 实时预览
- 导出为标准 Markdown 格式

---

#### 4.2 城市故事库
**状态**: 未开发
**优先级**: P2（中）
**依赖**: 无

**功能需求**:
- 建立城市故事数据库
- 支持用户上传自定义故事
- 投票/评分系统
- 热门故事排行

---

## 🎯 优先级划分

### ✅ P0（最高优先级）- 核心交互功能 - 全部完成！
- [x] ✅ 1.1 选择点生成器
- [x] ✅ 1.2 游戏状态管理器
- [x] ✅ 1.3 运行时响应生成器
- [x] ✅ 2.1 游戏主循环

### ✅ P1（高优先级）- 用户体验 - 全部完成！
- [x] ✅ 1.4 意图映射引擎
- [x] ✅ 2.2 命令行界面（CLI UI）
- [x] ✅ 3.2 多结局系统

### ✅ P1.5（紧急）- 完整游戏体验 - 已完成！
- [x] ✅ **2.4 完整游戏引擎** - 使用 LLM 动态生成完整主线（15-30分钟游玩时长）
  - ✅ 实现完整的 S1-S6 主线场景
  - ✅ 集成 ChoicePointsGenerator + RuntimeResponseGenerator
  - ✅ 基于 GDD 和 Lore 动态生成所有内容
  - ✅ 支持 Kimi API
  - ✅ 目标：20-30+ 个动态场景
  - **实现文件**: `play_game_full.py` + `start_full_game.sh`
  - **文档**: `FULL_GAME_GUIDE.md` + `README_FULL_GAME.md`

### P2（中优先级）- 增强功能
- [ ] 2.3 Web UI
- [ ] 3.1 实体 AI 系统
- [ ] 3.3 动态气象系统
- [ ] 4.1 故事编辑器
- [ ] 4.2 城市故事库

### P3（低优先级）- 可选扩展
- [ ] 3.4 多人模式
- [ ] 自由输入式游戏支持（Intent Mapping 扩展）

---

## 🏗️ 技术架构

### 目录结构（建议）
```
ghost-story-factory/
├── src/
│   └── ghost_story_factory/
│       ├── main.py              # CLI 入口（已有）
│       ├── generators/          # 静态内容生成器（已有）
│       ├── engine/              # 游戏引擎（待开发）
│       │   ├── __init__.py
│       │   ├── game_loop.py     # 主循环
│       │   ├── state.py         # 状态管理
│       │   ├── choices.py       # 选择点生成
│       │   ├── response.py      # 运行时响应
│       │   └── intent.py        # 意图映射
│       ├── entities/            # 实体系统（待开发）
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── janitor.py       # 不存在的清洁工
│       │   └── soullost.py      # 失魂者
│       ├── ui/                  # 用户界面（待开发）
│       │   ├── __init__.py
│       │   ├── cli.py           # CLI UI
│       │   └── web/             # Web UI
│       │       ├── api.py
│       │       └── static/
│       └── utils/
│           ├── weather.py       # 天气系统
│           └── endings.py       # 结局系统
├── templates/                        # 模板库（已有）
├── tests/                       # 测试（待完善）
└── pyproject.toml
```

### 技术栈

#### 核心依赖（已有）
- `crewai`: AI Agent 编排
- `litellm`: 多模型支持
- `python-dotenv`: 环境变量管理

#### 新增依赖（待安装）
```toml
[project.dependencies]
# 已有的保持不变
# ...

# 游戏引擎相关
rich = "^13.7.0"              # CLI 美化
prompt-toolkit = "^3.0.43"    # 交互式输入
pydantic = "^2.5.0"           # 数据校验

# Web UI（可选）
fastapi = "^0.109.0"
uvicorn = "^0.27.0"
websockets = "^12.0"

# 工具库
requests = "^2.31.0"          # HTTP 请求（天气 API）
```

---

## 🗓️ 开发路线图

### Milestone 1: 核心游戏引擎（约 2-3 周）
**目标**: 实现最小可玩版本

- Week 1:
  - [ ] 实现 GameState 类
  - [ ] 实现 ChoicePointsGenerator（基础版）
  - [ ] 编写单元测试
- Week 2:
  - [ ] 实现 RuntimeResponseGenerator
  - [ ] 实现 IntentMappingEngine
  - [ ] 集成测试
- Week 3:
  - [ ] 实现 GameLoop 主循环
  - [ ] 基础 CLI UI
  - [ ] 端到端测试（用杭州故事测试）

**交付物**: 可通过命令行玩完整游戏的 MVP

---

### Milestone 2: 用户体验优化（约 1-2 周）
**目标**: 提升游戏体验

- Week 4:
  - [ ] 美化 CLI UI（rich 集成）
  - [ ] 添加保存/读档功能
  - [ ] 优化响应生成质量
- Week 5:
  - [ ] 实现多结局系统
  - [ ] 添加成就系统
  - [ ] 统计数据面板

**交付物**: 具备完整用户体验的命令行游戏

---

### Milestone 3: 高级功能（约 2-3 周）
**目标**: 实现世界书 2.0 的高级特性

- Week 6-7:
  - [ ] 实体 AI 系统（清洁工、失魂者）
  - [ ] 动态气象系统
  - [ ] Tier 行为触发逻辑
- Week 8:
  - [ ] 后果树可视化
  - [ ] 调试工具
  - [ ] 性能优化

**交付物**: 功能完整的单机游戏引擎

---

### Milestone 4: Web 版本（可选，约 3-4 周）
**目标**: 支持 Web UI 和多人模式

- Week 9-10:
  - [ ] FastAPI 后端
  - [ ] WebSocket 实时通信
  - [ ] 数据库集成（存档管理）
- Week 11-12:
  - [ ] React 前端开发
  - [ ] 多人模式（共享 GR/WF）
  - [ ] 部署脚本

**交付物**: 可部署的 Web 应用

---

## 📝 开发规范

### 代码风格
- 遵循 PEP 8
- 使用类型注解（Type Hints）
- 编写 Docstring（Google 风格）

### 测试要求
- 单元测试覆盖率 ≥ 80%
- 每个 Generator 需要独立测试
- 集成测试覆盖主要流程

### 文档要求
- 每个模块需要 README
- API 文档自动生成（Sphinx）
- 更新 CHANGELOG

---

## 🔍 参考资料

### 内部文档
- `templates/00-architecture.md` - 架构概览
- `templates/choice-points.design.md` - 选择点设计
- `templates/runtime-response.design.md` - 运行时响应设计
- `templates/state-management.design.md` - 状态管理设计
- `templates/intent-mapping.design.md` - 意图映射设计

### 外部参考
- AI Dungeon: https://play.aidungeon.io/
- Disco Elysium: 技能系统与对话树设计
- 《世界书系统设计》: https://docs.google.com/document/d/...

---

## ❓ 常见问题

### Q: 为什么不直接用现成的游戏引擎？
A: 本项目专注于**叙事驱动**和**LLM 生成内容**，需要深度定制。现成引擎如 Unity/Godot 不适合纯文本交互。

### Q: 如何保证 LLM 生成质量？
A: 通过 3 层保障：
1. 高质量templates模板（35 个 design/example/prompt）
2. 结构化输出（JSON Schema 校验）
3. 后处理过滤（敏感内容、逻辑校验）

### Q: 多人模式如何同步状态？
A: 使用 Redis 存储共享 GR/WF，WebSocket 广播事件，每个玩家的 PR 独立。

---

## 📞 联系方式

如有问题或建议，请提交 Issue 或 PR：
- GitHub: https://github.com/your-repo/ghost-story-factory
- Email: your-email@example.com

---

**最后更新**: 2025-10-24
**维护者**: @yehan

