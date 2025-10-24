# Ghost Story Factory - 安装指南

## 📦 安装新增的游戏引擎功能

### 方式 1: 使用虚拟环境（推荐）

```bash
# 进入项目目录
cd /Users/yehan/code/ai/ghost-story-factory

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装项目及依赖
pip install -e .

# 或者手动安装依赖
pip install crewai>=0.30.0 langchain-community python-dotenv langchain-openai pydantic>=2.5.0 rich>=13.7.0
```

### 方式 2: 使用 uv（如果已安装）

```bash
# 安装项目及依赖
uv pip install -e .

# 或者
uv sync
```

### 方式 3: 使用 pipx（仅用于命令行工具）

```bash
pipx install -e .
```

### 方式 4: 使用 --user 标志（不推荐，但可用）

```bash
pip3 install --user -e .
```

---

## ✅ 验证安装

### 检查依赖

```bash
python3 -c "import pydantic; print('pydantic:', pydantic.__version__)"
python3 -c "import rich; print('rich:', rich.__version__)"
```

### 运行测试

```bash
# 激活虚拟环境后
python3 tests/test_game_engine.py
```

预期输出：
```
======================================================================
开始测试 Ghost Story Factory 游戏引擎
======================================================================

测试 GameState...
✅ GameState 测试通过

测试 Choice...
✅ Choice 测试通过

测试 IntentMappingEngine...
✅ IntentMappingEngine 测试通过

测试 EndingSystem...
✅ EndingSystem 测试通过

测试 GameCLI...
  Rich 库: ✅ 已安装
✅ GameCLI 测试通过

======================================================================
✅ 所有测试通过！
======================================================================
```

### 检查命令注册

```bash
# 查看已注册的命令
pip show ghost-story-factory

# 尝试运行游戏命令（需要先有故事资源）
ghost-story-play --help
```

---

## 🎮 快速开始

### 1. 生成故事资源

```bash
# 生成完整故事资源
gen-complete --city "杭州" --index 1
```

### 2. 开始游戏

```bash
# 启动交互式游戏
ghost-story-play 杭州
```

---

## 🐛 常见问题

### Q: 提示 "command not found: ghost-story-play"

**A:** 重新安装项目：
```bash
pip install -e .
```

### Q: 提示 "ModuleNotFoundError: No module named 'pydantic'"

**A:** 手动安装依赖：
```bash
pip install pydantic>=2.5.0 rich>=13.7.0
```

### Q: 在 macOS 上提示 "externally-managed-environment"

**A:** 使用虚拟环境（见方式 1）或添加 `--user` 标志。

---

## 📚 更多文档

- [游戏引擎使用指南](GAME_ENGINE_USAGE.md)
- [项目 README](README.md)
- [规格文档](docs/specs/SPEC_TODO.md)

---

**安装完成后，开始你的灵异之旅！** 👻🎮

