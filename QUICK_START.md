# 🎮 快速入门指南

## 🚀 5分钟上手 Ghost Story Factory

---

## 📋 前置准备

### 1. 检查 Python 版本
```bash
python3 --version  # 需要 Python 3.8+
```

### 2. 创建虚拟环境（推荐）
```bash
# 在项目根目录
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows
```

### 3. 安装基础依赖
```bash
# 只需要两个包就能运行核心功能
pip install pydantic rich
```

---

## 🎯 使用方式

### 方式 1: 运行演示（推荐新手）✨

**最简单的方式 - 立即体验完整游戏流程**

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 运行游戏演示
python3 demo_game.py
```

**你会看到**：
- 🎭 精美的游戏标题
- 📊 实时进度条
- 📖 沉浸式叙事文本
- 🎯 交互式选择点
- 💾 保存/读档功能
- 🏆 结局系统演示

---

### 方式 2: 测试核心功能

**验证所有组件是否正常**

```bash
python3 test_flow_simple.py
```

**测试内容**：
- ✅ GameState - 状态管理
- ✅ Choice - 选择点
- ✅ IntentMapping - 意图映射
- ✅ EndingSystem - 结局系统
- ✅ CLI - 用户界面

---

### 方式 3: 开发自己的故事

#### 步骤 1: 准备故事资源

你需要两个文件：
- `城市名_GDD.md` - 游戏设计文档
- `城市名_lore_v2.md` - 世界观设定

**选项 A: 使用现有资源（杭州故事）**
```bash
ls examples/杭州/
# 已有：杭州_GDD.md, 杭州_lore_v2.md
```

**选项 B: 生成新故事**
```bash
# 需要安装完整依赖（见下文"完整安装"）
gen-complete --city "你的城市" --index 1
```

#### 步骤 2: 编写游戏脚本

创建 `my_game.py`：

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ghost_story_factory.engine import GameEngine

# 创建游戏引擎
engine = GameEngine(
    city="杭州",
    gdd_path="examples/杭州/杭州_GDD.md",
    lore_path="examples/杭州/杭州_lore_v2.md"
)

# 运行游戏（需要 CrewAI）
engine.run()
```

#### 步骤 3: 运行
```bash
python3 my_game.py
```

---

### 方式 4: 使用独立模块

**只使用状态管理**：
```python
from ghost_story_factory.engine import GameState

state = GameState(PR=5, current_scene="S1")
state.update({"PR": "+10", "inventory": ["手电筒"]})
print(f"当前PR: {state.PR}")  # 输出: 15

# 保存
state.save("my_save.save")

# 加载
loaded = GameState.load("my_save.save")
```

**只使用选择点**：
```python
from ghost_story_factory.engine import Choice, ChoiceType

choice = Choice(
    choice_id="test",
    choice_text="调查房间",
    choice_type=ChoiceType.NORMAL,
    consequences={"PR": "+5"}
)

# 检查是否可用
if choice.is_available(state):
    print("可以选择")
```

**只使用结局系统**：
```python
from ghost_story_factory.engine import EndingSystem, GameState

system = EndingSystem()
state = GameState(PR=100)

ending = system.check_ending(state)
if ending:
    print(f"达成结局: {ending.value}")
```

---

## 🎨 自定义界面

### 使用 CLI 界面

```python
from ghost_story_factory.ui import GameCLI
from ghost_story_factory.engine import GameState

cli = GameCLI(use_rich=True)

# 显示标题
cli.display_title("我的城市", "主角名字")

# 显示状态
state = GameState(PR=45, GR=63)
cli.display_state(state)

# 显示叙事文本
cli.display_narrative("""
## 场景描述

你走进了一间昏暗的房间...
""")

# 显示选择
choices = [...]  # 你的选择列表
cli.display_choices(choices, state)
```

---

## 📊 查看游戏数据

```python
from ghost_story_factory.engine import GameState

state = GameState.load("saves/my_save.save")

print(f"PR: {state.PR}/100")
print(f"场景: {state.current_scene}")
print(f"时间: {state.timestamp}")
print(f"道具: {state.inventory}")
print(f"标志: {state.flags}")
print(f"选择历史: {state.consequence_tree}")
```

---

## 🔧 完整安装（可选）

如果你想使用 LLM 驱动的内容生成：

```bash
# 方式 1: 使用 pip（推荐）
pip install pydantic rich crewai langchain-community langchain-openai python-dotenv

# 方式 2: 安装整个项目
pip install -e .
```

**配置 API Key**：
```bash
# 创建 .env 文件
echo "OPENAI_API_KEY=your_key_here" > .env
```

**使用完整功能**：
```bash
# 注册的命令（需要 pip install -e .）
ghost-story-play 杭州

# 或直接运行
python3 -m ghost_story_factory.engine.game_loop 杭州
```

---

## 🆘 常见问题

### Q: 运行时提示 "No module named 'pydantic'"
```bash
# 确保在虚拟环境中
source venv/bin/activate
pip install pydantic rich
```

### Q: 演示能运行，但完整游戏报错
**原因**：完整游戏需要 CrewAI 生成动态内容

**解决**：
1. 使用演示模式（预设内容）：`python3 demo_game.py`
2. 或安装完整依赖（可能有版本冲突）

### Q: 如何保存游戏进度？
```python
# 在游戏中
state.save("saves/my_game.save")

# 下次加载
state = GameState.load("saves/my_game.save")
engine.state = state
```

### Q: 如何创建自己的选择点？
```python
from ghost_story_factory.engine import Choice, ChoiceType

my_choice = Choice(
    choice_id="custom_1",
    choice_text="你的选项文本",
    choice_type=ChoiceType.NORMAL,
    tags=["调查"],
    preconditions={"PR": ">=30"},  # 可选
    consequences={"PR": "+10", "flags": {"event_1": True}}
)
```

### Q: 如何添加新结局？
查看 `src/ghost_story_factory/engine/endings.py`，在 `_parse_endings_from_gdd()` 中添加新结局定义。

---

## 📚 进阶学习

### 推荐阅读顺序

1. **QUICK_START.md** （本文件）- 快速上手
2. **GAME_ENGINE_README.md** - 游戏引擎概览
3. **GAME_ENGINE_USAGE.md** - 详细 API 文档
4. **TEST_RESULTS.md** - 测试报告和架构验证
5. **IMPLEMENTATION_SUMMARY.md** - 技术实现细节

### 示例代码

所有示例都在：
- `demo_game.py` - 完整游戏流程演示
- `test_flow_simple.py` - 组件单独使用
- `tests/test_game_engine.py` - 单元测试

---

## 🎮 推荐学习路径

### 新手路径 🌱
1. 运行 `python3 demo_game.py` 体验完整流程
2. 阅读 `demo_game.py` 源码，理解各组件如何协作
3. 修改演示脚本，添加自己的选择点
4. 运行 `test_flow_simple.py` 了解各组件

### 进阶路径 🚀
1. 创建自己的城市故事（GDD + Lore）
2. 编写自定义的选择点生成逻辑
3. 设计新的结局条件
4. 扩展 CLI 界面（添加新功能）

### 高级路径 🔥
1. 集成 CrewAI 实现 LLM 驱动生成
2. 开发 Web UI（FastAPI + React）
3. 实现实体 AI 系统
4. 添加多人模式

---

## ✨ 快速测试命令

```bash
# 1. 创建虚拟环境并安装依赖
python3 -m venv venv && source venv/bin/activate && pip install pydantic rich

# 2. 运行演示
python3 demo_game.py

# 3. 运行测试
python3 test_flow_simple.py

# 一行搞定（复制粘贴即可）
python3 -m venv venv && source venv/bin/activate && pip install pydantic rich && python3 demo_game.py
```

---

## 🎯 下一步

- ✅ 你已经了解基本用法
- 📖 查看 [GAME_ENGINE_USAGE.md](GAME_ENGINE_USAGE.md) 学习详细 API
- 🎮 运行 `python3 demo_game.py` 开始体验
- 💡 修改 `demo_game.py` 创建自己的故事

**准备好了吗？开始你的灵异冒险吧！** 👻✨

---

**最后更新**: 2025-10-24
**难度**: ⭐ 简单
**时间**: 5分钟上手

