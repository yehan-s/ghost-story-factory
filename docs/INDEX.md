# Ghost Story Factory - 文档索引

**最后更新**: 2025-10-25
**项目版本**: v3.0

---

## 📚 快速导航

### 🚀 快速开始
- [../README.md](../README.md) - **从这里开始！** 项目主文档
  - 动态模式：`python3 play_game_full.py`
  - 预生成模式：`./start_pregenerated_game.sh` / `python3 play_game_pregenerated.py`

### 📋 规格文档 (Specifications)
位于 `docs/specs/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [SPEC.md](specs/SPEC.md) | 项目原始规格书 | 开发者、贡献者 |
| [SPEC_TODO.md](specs/SPEC_TODO.md) | 待开发功能完整规格 | 开发者、项目管理 |
| [PREGENERATION_DESIGN.md](../docs/PREGENERATION_DESIGN.md) | 预生成系统设计 | 工程师、设计师 |
| [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md) | **命令行游戏开发路线图** ⭐ | 游戏引擎开发者 |

**推荐阅读顺序**: README → CLI_GAME_ROADMAP（如果要开发游戏引擎）→ SPEC_TODO

---

### 📖 使用指南 (Guides)
位于 `docs/guides/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [USAGE.md](guides/USAGE.md) | 详细使用说明 | 所有用户 |
| [WORKFLOW.md](guides/WORKFLOW.md) | 完整工作流程 | 内容创作者 |
| [QUICK_REFERENCE.md](guides/QUICK_REFERENCE.md) | 命令速查卡 | 经常使用者 |
| 预生成模式：参见 [PREGENERATION_DESIGN.md](../docs/PREGENERATION_DESIGN.md) | 模式说明 | 所有用户 |

**推荐阅读顺序**: USAGE → WORKFLOW → QUICK_REFERENCE

---

### 🏗️ 架构文档 (Architecture)
位于 `docs/architecture/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [ARCHITECTURE.md](architecture/ARCHITECTURE.md) | 项目整体架构 | 开发者、架构师 |
| [GAME_ENGINE.md](architecture/GAME_ENGINE.md) | 游戏引擎设计 | 游戏引擎开发者 |
| [NEW_PIPELINE.md](architecture/NEW_PIPELINE.md) | **新架构流程图谱 (v3.0)** ⭐ | 开发者、维护者 |

**推荐阅读顺序**: ARCHITECTURE → NEW_PIPELINE → GAME_ENGINE

---

### 🔧 技术文档 (Technical)
位于 `docs/`

| 文档 | 说明 | 适用人群 |
|------|------|----------|
| [PROTAGONIST_CONSTRAINTS.md](PROTAGONIST_CONSTRAINTS.md) | 主角强约束机制 ⭐ | 开发者、内容创作者 |

**重要**：如果遇到主角生成错误（如使用了"保安"而非真实主角），请阅读此文档

---

### 📦 旧文档 (Legacy)
位于 `docs/legacy/`

这些文档已被新文档替代，仅作历史参考：

| 文档 | 说明 | 替代文档 |
|------|------|----------|
| get-story.md | 旧命令说明 | guides/USAGE.md |
| get-struct.md | 旧命令说明 | guides/USAGE.md |
| lore.md | 旧设计文档 | templates/lore-v1.design.md |
| role-beats.md | 旧设计文档 | templates/protagonist.design.md |
| set-city.md | 旧命令说明 | guides/USAGE.md |

**不建议阅读**，仅供历史追溯。

---

## 🎭 示例故事 (Examples)

位于 `examples/`，包含已生成的城市故事：

### hangzhou/杭州（完整示例）⭐
位于 `examples/hangzhou/`
- ✅ 候选列表: `杭州_candidates.json`
- ✅ 故事结构: `杭州_struct.json`
- ✅ Lore v1: `杭州_lore.json`
- ✅ 主角分析: `杭州_protagonist.md`
- ✅ Lore v2: `杭州_lore_v2.md`
- ✅ GDD: `杭州_GDD.md`
- ✅ 主线故事: `杭州_main_thread.md`
- ✅ 简化版: `杭州_story.md`

**故事简介**: 北高峰缆车空厢 - 特检院工程师调查午夜缆车异响

---

### wuhan/武汉（部分示例）
位于 `examples/wuhan/`
- ✅ 候选列表: `武汉_candidates.json`
- ✅ Lore v1: `武汉_lore.json`
- ✅ 故事: `武汉_story.md`
- ✅ 主角分析: `武汉_role_夜跑者.json`
- ✅ 故事结构: `武汉_struct.json`

---

### guangzhou/广州（经典故事）
位于 `examples/guangzhou/`
- ✅ 经典故事: `广州_荔湾广场_第七块玻璃.md`

**故事简介**: 荔湾广场灵异传说 - 第七块玻璃与"借光"仪式

---

### test-city/测试城（测试数据）
位于 `examples/test-city/`
- ✅ Lore v1: `测试城_lore.json`
- ✅ 主角分析: `测试城_role_保安.json`

---

## 📝 模板库 (Templates)

位于 `templates/`，包含 35 个设计模板文件。

**重要文档**:
- [templates/README.md](../templates/README.md) - 模板库总览
- [templates/00-architecture.md](../templates/00-architecture.md) - 架构总览
- [templates/00-index.md](../templates/00-index.md) - 上下文管理策略

**详细模板**: 参见 [templates/00-index.md](../templates/00-index.md)

---

## 🔍 按角色查找文档

### 👨‍💻 开发者
1. 先读 [README.md](../README.md)
2. 了解架构 [ARCHITECTURE.md](architecture/ARCHITECTURE.md)
3. 查看规格 [SPEC_TODO.md](specs/SPEC_TODO.md)
4. 开发游戏引擎参考 [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md)

### ✍️ 内容创作者
1. 先读 [README.md](../README.md)
2. 学习使用 [USAGE.md](guides/USAGE.md)
3. 了解流程 [WORKFLOW.md](guides/WORKFLOW.md)
4. 参考示例 `examples/杭州/`

### 🎮 游戏设计师
1. 阅读templates [templates/README.md](../templates/README.md)
2. 学习设计 [templates/00-architecture.md](../templates/00-architecture.md)
3. 参考 GDD [examples/杭州/杭州_GDD.md](../examples/杭州/杭州_GDD.md)
4. 研究引擎 [GAME_ENGINE.md](architecture/GAME_ENGINE.md)

### 📊 项目管理
1. 查看规格 [SPEC_TODO.md](specs/SPEC_TODO.md)
2. 跟踪路线图 [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md)
3. 审查架构 [ARCHITECTURE.md](architecture/ARCHITECTURE.md)

---

## 🆘 常见问题

### Q: 从哪里开始？
A: 阅读项目根目录的 [README.md](../README.md)

### Q: 如何生成第一个故事？
A: 按顺序阅读：
1. [USAGE.md](guides/USAGE.md)
2. [WORKFLOW.md](guides/WORKFLOW.md)
3. 参考 `examples/杭州/` 的完整示例

### Q: 如何开发游戏引擎？
A: 按顺序阅读：
1. [CLI_GAME_ROADMAP.md](specs/CLI_GAME_ROADMAP.md) ⭐
2. [GAME_ENGINE.md](architecture/GAME_ENGINE.md)
3. [SPEC_TODO.md](specs/SPEC_TODO.md)

### Q: templates太多，怎么高效使用？
A: 阅读 [templates/00-index.md](../templates/00-index.md)，了解分层加载策略

---

## 📞 获取帮助

- **GitHub Issues**: 提交 Bug 或功能请求
- **文档问题**: 检查 [USAGE.md](guides/USAGE.md) 的 FAQ 章节
- **技术问题**: 参考 [ARCHITECTURE.md](architecture/ARCHITECTURE.md)

---

**最后提醒**: 所有文档都使用相对路径链接，可以在 GitHub 或本地 Markdown 阅读器中正常浏览。

