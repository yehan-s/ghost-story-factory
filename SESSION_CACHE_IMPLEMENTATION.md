# 会话级缓存实现方案

## 🎯 目标
实现"一次性记忆"：LLM 第一次读取完整故事，后续调用复用此会话

## 📊 预期效果

| 阶段 | Token | 时间 | 成本 |
|------|-------|------|------|
| 第1次（开场） | ~8,000 | 22秒 | $0.10 |
| 第2-60次 | ~300 | **5秒** | **$0.005** |
| **平均** | **~500** | **~6秒** | **$0.01** |

## 🔧 实现步骤

### 1. ✅ GameEngine - 加载主线故事
- 添加 `main_story_path` 参数
- 添加 `_load_main_story()` 方法
- 传递给生成器

### 2. ✅ ChoicePointsGenerator - 添加会话支持
- 添加 `main_story` 参数
- 添加 `crew` 和 `session_initialized` 属性

### 3. 🔄 ChoicePointsGenerator - 实现会话初始化
- 添加 `_initialize_session()` 方法
- 首次调用时加载完整故事
- 后续调用复用 Crew

### 4. 🔄 ChoicePointsGenerator - 修改生成逻辑
- 检测是否首次调用
- 首次：完整加载
- 后续：简短 Prompt

### 5. 🔄 RuntimeResponseGenerator - 同样的修改
- 添加会话支持
- 实现会话初始化
- 修改生成逻辑

### 6. 🔄 play_game_full.py - 更新调用
- 无需修改（自动加载）

## 🎮 使用方式

用户无需任何更改！
- 如果有主线故事文件：自动启用会话缓存
- 如果没有：使用现有的 Prompt 优化

## 📝 当前进度
- [x] GameEngine 添加主线加载
- [x] ChoicePointsGenerator 添加会话属性
- [ ] ChoicePointsGenerator 实现会话初始化
- [ ] ChoicePointsGenerator 修改生成逻辑  
- [ ] RuntimeResponseGenerator 相同修改
- [ ] 测试验证
