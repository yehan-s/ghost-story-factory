# 并行生成功能说明

## 📚 概述

本项目支持**智能并行生成**多个角色的对话树，可以显著提高生成效率。

## 🚀 可用脚本

### 1. `generate_mvp.py` - MVP 快速测试（单角色/2角色）
- **用途**：快速测试，生成 1-2 个角色
- **特点**：顺序生成，简单直接
- **时长**：5-10 分钟
- **日志**：自动记录到 `logs/generate_mvp_*.log`

```bash
python3 generate_mvp.py
```

### 2. `generate_smart_parallel.py` - 智能并行生成（多角色）⭐
- **用途**：同时生成多个角色的对话树
- **特点**：
  - 🔥 **动态工作队列**：保持 2 个角色同时生成，完成一个立即开始下一个
  - ⚡ **最大化效率**：不浪费等待时间
  - 🔄 **自动重试**：失败自动重试 2 次
  - 📊 **实时进度**：显示每个角色的生成状态
  - 📝 **完整日志**：所有错误自动写入日志文件
- **时长**：取决于角色数量和并发配置
- **日志**：自动记录到 `logs/generate_smart_parallel_*.log`

```bash
python3 generate_smart_parallel.py
```

### 3. `generate_full_story.py` - 完整故事生成（CrewAI 流程）
- **用途**：从零开始生成完整故事（素材→世界书→角色→GDD→故事）
- **特点**：CrewAI 多 Agent 协作，生成所有设计文档
- **时长**：较长（取决于 LLM 速度）
- **日志**：自动记录到 `logs/generate_full_story_*.log`

```bash
python generate_full_story.py --city 武汉
```

## ⚙️ 配置说明

### `generate_smart_parallel.py` 配置参数

编辑文件顶部的配置区域：

```python
# ==================== 配置参数 ====================
CITY = "杭州"
STORY_TITLE = "断桥残血-智能并行测试"

# 并发配置
MAX_CONCURRENT = 2  # 同时生成的角色数量（推荐 2-4）
MAX_RETRIES = 2     # 失败重试次数

# 测试模式
TEST_MODE = True    # True=快速测试，False=完整生成
MAX_DEPTH = 5 if TEST_MODE else 20
MIN_MAIN_PATH = 3 if TEST_MODE else 15
```

**关键参数说明**：

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `MAX_CONCURRENT` | 同时生成的角色数 | 2-4（取决于 API 限速） |
| `TEST_MODE` | 测试模式开关 | 初次使用建议 `True` |
| `MAX_DEPTH` | 对话树最大深度 | 测试：5，完整：20 |

## 📊 性能对比

假设生成 8 个角色，每个角色需要 10 分钟：

| 方式 | 耗时 | 说明 |
|------|------|------|
| 顺序生成 | 80 分钟 | 8 × 10 分钟 |
| 并行生成（2并发） | **40 分钟** | 效率提升 50% ⚡ |
| 并行生成（4并发） | **20 分钟** | 效率提升 75% 🚀 |

> ⚠️ 注意：并发数不宜过高，受 API 速率限制影响

## 🎯 使用示例

### 场景 1：快速测试（2个角色）

```bash
# 1. 编辑 generate_smart_parallel.py
TEST_MODE = True
MAX_CONCURRENT = 2

# 2. 运行
python3 generate_smart_parallel.py

# 3. 查看日志
ls -lt logs/generate_smart_parallel_*.log
```

### 场景 2：完整生成（8个角色）

```bash
# 1. 编辑 generate_smart_parallel.py
TEST_MODE = False  # 完整模式
MAX_CONCURRENT = 2  # 保守并发

# 2. 确保有足够的 API 配额

# 3. 运行（预计 2-4 小时）
python3 generate_smart_parallel.py
```

## 📝 日志系统

所有脚本都会自动记录日志到 `logs/` 目录：

```bash
logs/
├── generate_mvp_20251024_134500.log
├── generate_smart_parallel_20251024_140000.log
└── generate_full_story_20251024_150000.log
```

**日志内容**：
- ✅ 每个步骤的开始和完成
- ⚠️ 警告和重试信息
- ❌ 错误和完整堆栈跟踪
- 📊 性能统计

**查看日志**：
```bash
# 查看最新日志
tail -f logs/generate_smart_parallel_*.log

# 查看错误
grep -i error logs/*.log
```

## 🔧 故障排查

### 问题 1：并发失败率高

**症状**：多个角色生成失败

**原因**：API 速率限制

**解决**：
```python
# 降低并发数
MAX_CONCURRENT = 1  # 从 2 降到 1
```

### 问题 2：找不到角色配置

**症状**：`❌ 错误：未找到 杭州 的角色配置`

**原因**：缺少 `examples/hangzhou/杭州_struct.json`

**解决**：
1. 确认文件存在
2. 检查文件格式（需要包含 `potential_roles` 字段）
3. 或使用 `generate_mvp.py`（不依赖 struct.json）

### 问题 3：生成中断

**症状**：进程被杀死或网络断开

**解决**：
- ✅ 检查点系统会自动保存进度
- ✅ 重新运行会自动从断点继续
- ✅ 查看 `checkpoints/` 目录确认

## 📖 相关文档

- [快速开始](../QUICK_START.md)
- [命令手册](COMMANDS.md)
- [角色提取说明](BUG_FIX_CHARACTER_EXTRACTION.md)
- [预生成设计](PREGENERATION_DESIGN.md)

## ✨ 最佳实践

1. **初次使用**：先用 `generate_mvp.py` 测试单角色
2. **小规模测试**：用 `TEST_MODE=True` 验证流程
3. **正式生成**：再切换到 `TEST_MODE=False` 完整生成
4. **监控日志**：使用 `tail -f logs/*.log` 实时查看进度
5. **保守并发**：初期使用 `MAX_CONCURRENT=2`，稳定后可增加
6. **检查配额**：确保 API 有足够的配额和速率限制

## 🎉 总结

- 🚀 **智能并行**可以显著提升生成效率（2-4倍速度）
- 📝 **完整日志**确保所有错误都有记录可查
- 🔄 **自动重试**提高成功率
- 💾 **检查点续传**保护长时间生成任务

选择合适的脚本开始您的故事生成之旅！🎭

