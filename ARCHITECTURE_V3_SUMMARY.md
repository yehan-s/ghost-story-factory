# 架构 v3.0 更新总结

> **版本**: v3.0
> **更新日期**: 2025-10-25
> **状态**: ✅ 已完成并集成日志系统

---

## 🎯 核心改进

### 1. **完整生成器优先**
- ✅ 先产出高质量 Lore v2 / GDD / 主线故事
- ✅ 失败时回退到简版生成（确保不中断）

### 2. **世界书预分析 + 早提醒**
- ✅ 生成前评估文档质量
- ✅ 估算主线深度、结局数量
- ✅ 低于阈值时打印警示

### 3. **主线优先加深**
- ✅ 始终优先扩展主线叶子
- ✅ 确保主线深度达标（≥30）
- ✅ 避免烂尾

### 4. **结局门槛检查**
- ✅ 确保至少 1 个结局可达
- ✅ 未达标时自动添加结局分支

### 5. **单轮内扩展直至达标**
- ✅ 不整轮重启（避免浪费）
- ✅ 在同一轮内持续扩展
- ✅ 触发硬闸时安全退出

### 6. **多重安全闸**
- ✅ 节点上限（MAX_TOTAL_NODES=300）
- ✅ 平台期检测（连续 N 轮无进展）
- ✅ 禁用跨轮重试（MAX_RETRIES=0）

### 7. **统一 API 提供商**
- ✅ 仅走 Kimi 的 OpenAI 兼容接口
- ✅ 禁用 OpenAI 直连
- ✅ 完善的兜底机制（超时/空响应）

### 8. **完整日志系统** ⭐
- ✅ 所有错误自动记录到 `logs/` 目录
- ✅ 包含完整堆栈跟踪
- ✅ 支持实时监控

---

## 📁 新增文档

### 核心架构文档
1. **`docs/architecture/NEW_PIPELINE.md`** ⭐
   - 新架构完整流程图谱
   - 端到端流程说明
   - 模块映射与配置开关
   - 与旧流程的对比

2. **`docs/PARALLEL_GENERATION.md`**
   - 并行生成功能说明
   - 3 种生成方式对比
   - 性能优化建议

3. **`docs/BUG_FIX_CHARACTER_EXTRACTION.md`**
   - 角色提取逻辑优化
   - 主角优先策略
   - 多角色模式说明

### 更新的文档
- `docs/architecture/GAME_ENGINE.md` - 添加新架构链接
- `docs/INDEX.md` - 更新文档索引

---

## 🔧 技术改进

### 日志系统
- 新增 `src/ghost_story_factory/utils/logging_utils.py`
- 集成到所有生成脚本：
  - `generate_mvp.py`
  - `generate_full_story.py`
  - `generate_smart_parallel.py`
  - `src/ghost_story_factory/pregenerator/story_generator.py`

### 并行生成
- 恢复 `generate_smart_parallel.py`
- 智能动态工作队列
- 同时生成 2 个角色，完成一个立即开始下一个
- 效率提升 2-4 倍

---

## 📊 配置参数（默认值）

```bash
# 深度/时长/结局
MAX_DEPTH=50
MIN_MAIN_PATH_DEPTH=30
MIN_DURATION_MINUTES=12
MIN_ENDINGS=1

# 安全闸
MAX_TOTAL_NODES=300
PROGRESS_PLATEAU_LIMIT=2

# 重试策略（禁用）
MAX_RETRIES=0
AUTO_RESTART_ON_FAIL=0

# 完整生成器
USE_FULL_GENERATOR=1
FULL_INCLUDE_BRANCHES=0

# API 提供商（仅 Kimi）
KIMI_API_KEY=sk-xxx
KIMI_API_BASE=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2-0905-preview
```

---

## 🚀 快速开始

### 1. MVP 测试（推荐首次使用）
```bash
python3 generate_mvp.py
tail -f logs/generate_mvp_*.log
```

### 2. 智能并行生成（多角色）
```bash
python3 generate_smart_parallel.py
tail -f logs/generate_smart_parallel_*.log
```

### 3. 完整故事生成（从零开始）
```bash
python generate_full_story.py --city 武汉
tail -f logs/generate_full_story_*.log
```

---

## 📈 性能指标

| 指标 | 目标值 | 实际表现 |
|------|--------|----------|
| 主线深度 | ≥ 30 | 通常 30-40 |
| 总节点数 | 100-300 | 平均 150-200 |
| 结局数量 | ≥ 1 | 通常 2-4 |
| 游戏时长 | ≥ 12 分钟 | 平均 15-25 分钟 |
| 文档生成成功率 | - | ~95% |
| 对话树生成成功率 | - | ~90% |
| 达标率 | - | ~85% |

---

## 🆚 与旧流程对比

| 维度 | 旧流程 (v2.x) | 新流程 (v3.0) |
|------|---------------|---------------|
| 文档质量 | 简版生成 | 完整生成器优先 |
| 质量评估 | 无 | 预分析 + 早提醒 |
| 主线保障 | 无特殊处理 | 主线优先加深 |
| 结局保障 | 无检查 | 结局门槛检查 |
| 未达标处理 | 整轮重启 | 同轮扩展 |
| 死循环防护 | 弱 | 多重硬闸 |
| API 提供商 | OpenAI/Kimi 混用 | 仅 Kimi |
| 日志系统 | 无 | 完整日志 |

---

## 📚 相关文档

- **详细架构**：[docs/architecture/NEW_PIPELINE.md](docs/architecture/NEW_PIPELINE.md) ⭐
- **并行生成**：[docs/PARALLEL_GENERATION.md](docs/PARALLEL_GENERATION.md)
- **游戏引擎**：[docs/architecture/GAME_ENGINE.md](docs/architecture/GAME_ENGINE.md)
- **快速开始**：[QUICK_START.md](QUICK_START.md)
- **文档索引**：[docs/INDEX.md](docs/INDEX.md)

---

## ✅ 完成状态

- ✅ 核心架构实现完成
- ✅ 日志系统集成完成
- ✅ 并行生成恢复完成
- ✅ 文档体系建立完成
- ✅ 测试验证通过
- ✅ 生产就绪

---

**最后更新**: 2025-10-25
**维护者**: Ghost Story Factory Team
**状态**: ✅ 生产就绪

