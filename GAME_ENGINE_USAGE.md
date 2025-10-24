# Ghost Story Factory - 交互式游戏引擎使用指南

**版本**: v1.0
**更新日期**: 2025-10-24

---

## 🎮 简介

Ghost Story Factory 现已支持交互式游戏模式！你不仅可以生成故事，还可以直接游玩。

### 核心功能

- ✅ **P0 核心功能**（已完成）:
  - 游戏状态管理器 (GameState)
  - 选择点生成器 (ChoicePointsGenerator)
  - 运行时响应生成器 (RuntimeResponseGenerator)
  - 游戏主循环 (GameEngine)

- ✅ **P1 增强功能**（已完成）:
  - 意图映射引擎 (IntentMappingEngine)
  - 命令行界面 (CLI UI with Rich)
  - 多结局系统 (EndingSystem)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 如果还没有安装，先安装项目
pip install -e .

# 或者使用 uv
uv pip install -e .
```

新增依赖：
- `pydantic>=2.5.0` - 数据验证
- `rich>=13.7.0` - CLI 美化

### 2. 生成游戏资源

在开始游玩前，需要先生成 GDD 和 Lore v2：

```bash
# 方式 1: 使用完整流水线
gen-complete --city "杭州" --index 1

# 方式 2: 分步生成
set-city --city "杭州"
get-struct --city "杭州" --index 1
gen-lore-v2 --city "杭州"
gen-gdd --city "杭州"
```

### 3. 开始游戏

```bash
# 启动游戏（自动查找 examples/杭州/ 下的资源）
ghost-story-play 杭州

# 或者指定资源路径
ghost-story-play 杭州 --gdd examples/杭州/杭州_GDD.md --lore examples/杭州/杭州_lore_v2.md
```

---

## 🎯 游戏界面

### 状态显示

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 个人共鸣度 [████████░░░░░░░░░░] 45/100
🌍 全局共鸣度 [████████████░░░░░░] 63/100
⏱️  世界疲劳值 [█░░░░░░░░░] 1/10

⏰ 时间: 02:30  |  📍 场景: S4
🎒 道具: 手电筒, 对讲机
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 选择点示例

```
【抉择点】请选择你的行动：

  1. 💼 走过去检查声音来源 [调查, 主动]
     └─ 后果：PR +15 | 消耗时间

  2. 💼 返回中控室查看监控 [保守, 安全]
     └─ 后果：PR +5 | 消耗时间

  3. 🔒 使用念佛机 (条件不满足)

  4. 💾 保存进度
  5. 🚪 退出游戏

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请输入选项编号 [1-5]: _
```

---

## 📖 核心系统说明

### 1. 游戏状态管理 (GameState)

**管理的状态**:
- `PR` (个人共鸣度): 0-100，代表与灵异世界的连接程度
- `GR` (全局共鸣度): 0-100，服务器级别的共享状态
- `WF` (世界疲劳值): 0-10，世界的损耗程度
- `timestamp`: 游戏内时间 (00:00-04:00)
- `inventory`: 道具栏
- `flags`: 事件标志位
- `consequence_tree`: 历史选择记录

**使用示例**:
```python
from ghost_story_factory.engine import GameState

state = GameState(PR=5, current_scene="S1")

# 更新状态
state.update({
    "PR": "+10",
    "inventory": ["暗号:36-3=33"],
    "flags": {"失魂者_已拍照": True}
})

# 检查前置条件
can_use = state.check_preconditions({
    "PR": ">=40",
    "items": ["暗号:36-3=33"]
})

# 保存/读档
state.save("saves/杭州_S4_02:30.save")
loaded_state = GameState.load("saves/杭州_S4_02:30.save")
```

### 2. 选择点生成器 (ChoicePointsGenerator)

**选择点类型**:
- `MICRO`: 微选择，日常互动，低风险
- `NORMAL`: 普通选择，情节推进
- `CRITICAL`: 关键选择，结局分支

**使用示例**:
```python
from ghost_story_factory.engine import ChoicePointsGenerator, GameState

generator = ChoicePointsGenerator(gdd_content, lore_content)

choices = generator.generate_choices(
    current_scene="S3",
    game_state=state
)

for choice in choices:
    print(f"{choice.choice_id}: {choice.choice_text}")
    print(f"  类型: {choice.choice_type}")
    print(f"  后果: {choice.consequences}")
```

### 3. 运行时响应生成器 (RuntimeResponseGenerator)

**生成内容**:
- 物理反馈（确认玩家行为）
- 感官细节（视觉/听觉/嗅觉/触觉）
- 心理暗示（反映共鸣度变化）
- 引导暗示（提示下一步）

**使用示例**:
```python
from ghost_story_factory.engine import RuntimeResponseGenerator

generator = RuntimeResponseGenerator(gdd_content, lore_content)

response = generator.generate_response(
    choice=selected_choice,
    game_state=state,
    apply_consequences=True  # 自动应用后果
)

print(response)
```

### 4. 游戏主循环 (GameEngine)

**完整的游戏流程管理**:

```python
from ghost_story_factory.engine import GameEngine

# 初始化引擎
engine = GameEngine(
    city="杭州",
    gdd_path="examples/杭州/杭州_GDD.md",
    lore_path="examples/杭州/杭州_lore_v2.md"
)

# 运行游戏
ending_type = engine.run()
print(f"游戏结束：{ending_type}")
```

### 5. 多结局系统 (EndingSystem)

**已实现的结局**:
1. **补完结局**: 持有失魂核心 + 播放录音
2. **旁观结局**: 无核心 + 播放录音
3. **迷失结局**: PR 达到 100%
4. **超时结局**: 游戏时间超过 06:00
5. **献祭结局**: 隐藏结局，需要特殊选择

**使用示例**:
```python
from ghost_story_factory.engine import EndingSystem

system = EndingSystem()

# 检查是否达成结局
ending_type = system.check_ending(game_state)

if ending_type:
    # 渲染结局文本
    ending_text = system.render_ending(ending_type, game_state)
    print(ending_text)
```

---

## 🎨 CLI UI 特性

### Rich 库美化

如果安装了 `rich` 库，会自动启用：
- ✨ Markdown 渲染
- 🎨 彩色高亮
- 📊 进度条可视化
- 📋 表格显示
- 🎯 交互式提示

### 降级支持

如果未安装 `rich`，会自动降级为纯文本模式，保证可用性。

---

## 💾 保存/读档

### 保存进度

游戏中选择"保存进度"选项，或：

```python
engine.save_game("saves/my_save.save")
```

### 加载进度

```python
engine.load_game("saves/my_save.save")
engine.run()
```

### 存档格式

存档为 JSON 格式，包含完整的游戏状态：

```json
{
  "PR": 45,
  "GR": 63,
  "WF": 1,
  "current_scene": "S4",
  "timestamp": "02:30",
  "inventory": ["手电筒", "对讲机"],
  "flags": {"场景3_已完成": true},
  "consequence_tree": ["S1_C2", "S2_C1", "S3_C3"]
}
```

---

## 🔧 高级用法

### 1. 自定义结局

```python
from ghost_story_factory.engine import EndingSystem, Ending, EndingCondition, EndingType

system = EndingSystem()

# 注册自定义结局
custom_ending = Ending(
    ending_type=EndingType.UNKNOWN,  # 或自定义
    title="【自定义结局】",
    description="你的自定义结局描述...",
    condition=EndingCondition(
        required_flags={"custom_flag": True},
        required_items=["special_item"],
        pr_range=(80, 100)
    ),
    achievements=["自定义成就"],
    priority=120
)

system.register_ending(custom_ending)
```

### 2. 批量验证选择

```python
from ghost_story_factory.engine.intent import validate_choice_batch

results = validate_choice_batch(choices, game_state)

for choice_id, result in results.items():
    if not result.is_valid:
        print(f"{choice_id}: {result.reason}")
```

### 3. 意图提取

```python
from ghost_story_factory.engine import IntentMappingEngine

engine = IntentMappingEngine()

intent = engine.extract_intent(choice)
print(intent.physical_action)      # 物理动作
print(intent.emotional_motivation)  # 心理动机
print(intent.narrative_meaning)     # 叙事意义
print(intent.risk_level)           # 风险等级
```

---

## 📂 项目结构

```
src/ghost_story_factory/
├── engine/                  # 游戏引擎核心
│   ├── __init__.py
│   ├── state.py            # 状态管理
│   ├── choices.py          # 选择点生成
│   ├── response.py         # 响应生成
│   ├── game_loop.py        # 主循环
│   ├── intent.py           # 意图映射
│   └── endings.py          # 结局系统
├── ui/                      # 用户界面
│   ├── __init__.py
│   └── cli.py              # CLI 界面
└── main.py                  # 原有的故事生成功能
```

---

## 🐛 故障排除

### 问题 1: 找不到 GDD/Lore 文件

**解决方案**:
```bash
# 确保文件存在
ls examples/杭州/杭州_GDD.md
ls examples/杭州/杭州_lore_v2.md

# 或者显式指定路径
ghost-story-play 杭州 --gdd path/to/gdd.md --lore path/to/lore.md
```

### 问题 2: Rich 库未安装

**解决方案**:
```bash
pip install rich>=13.7.0
```

或使用纯文本模式（自动降级）。

### 问题 3: LLM API 调用失败

**解决方案**:
```bash
# 检查环境变量
cat .env

# 确保设置了 API Key
export KIMI_API_KEY="your-api-key"
export KIMI_API_BASE="https://api.moonshot.cn/v1"
```

---

## 📊 性能优化建议

1. **缓存生成结果**: 选择点和响应可以缓存，避免重复调用 LLM
2. **异步生成**: 对于大量选择点，可以使用异步生成
3. **批量处理**: 使用批量验证函数处理多个选择

---

## 🚧 已知限制

1. **自由输入式游戏**: 当前版本仅支持选项式交互，自由文本输入是未来的扩展功能
2. **实体 AI 系统**: 当前简化实现，完整的实体行为等级系统待开发
3. **动态气象系统**: 未接入真实天气 API

---

## 🗺️ 下一步计划

### P2（中优先级）- 增强功能
- [ ] Web UI (FastAPI + WebSocket)
- [ ] 实体 AI 系统（等级 0-4 行为）
- [ ] 动态气象系统
- [ ] 故事编辑器

### P3（低优先级）- 可选扩展
- [ ] 多人模式（共享 GR/WF）
- [ ] 自由输入式游戏支持

---

## 📞 反馈与贡献

如有问题或建议，请提交 Issue 或 PR。

---

**祝你游戏愉快！** 🎮👻


