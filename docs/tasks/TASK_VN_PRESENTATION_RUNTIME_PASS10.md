# TASK: VN 演出契约进入运行时 Pass 10

版本: v0.1
状态: Active
关联:
- GitHub Issue: `#41`
- GitHub Milestone: `v7 VN 演出运行时可见`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/tasks/TASK_SCRIPT_DEPTH_BREADTH_PASS9.md`
- `docs/team-reviews/2026-05-09-vn-presentation-runtime-pass10.md`

---

## 0. 问题判断

正式剧本已经给节点补了 `presentation` 字段,并且审计能检查背景、音效、镜头和 CG 意图。

坏味道在运行时:CLI 和 TUI 仍然只渲染 narrative / map / choices。也就是说,演出契约现在只给审计看,不给玩家看。这会让项目继续停在“有 VN 数据,没有 VN 体验”的状态。

【核心判断】
✅ 值得做:这是玩家实际体验缺口,不是臆想优化。数据已经存在,最小修复是让运行层消费它。

【关键洞察】
- 数据结构:`node.presentation` 是节点级演出意图,`tree.assets` 是资产标签表。两者关系已经稳定,不需要新 schema。
- 复杂度:不做真实图片 / 音频引擎,先做文本 fallback。一个共享 formatter,两个渲染入口。
- 风险点:正式树每个节点都有 `presentation`,输出过重会污染叙事。必须压缩成 1-2 行。

---

## 1. 目标

- 在 v5 CLI 播放器中显示节点演出提示;
- 在 v7 TUI 播放器中显示同一套演出提示;
- 用 `tree.assets` 把资产 id 转成更可读的中文 label;
- 缺少 `presentation` 的旧树保持静默,不改变旧节点 narrative 行为;
- 增加测试,锁住格式化、兼容和 TUI markup 安全。

---

## 2. 非目标

- 不加载真实图片;
- 不播放真实音频;
- 不新增数据库 schema;
- 不改 `resolve_narrative()` / `resolve_next()` 状态逻辑;
- 不把 CLI 做成完整 GUI。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 新增本 Task;
- 新增团队评审报告;
- 创建 GitHub issue 和 milestone;
- 将本任务挂入下一阶段 roadmap。

### M2: 共享演出格式化器

状态: Done

- 在 `src/ghost_story_factory/v5/player.py` 增加纯函数;
- 输入 `tree` 和 `node`;
- 输出稳定的纯文本行;
- 支持 `background / bgm / sfx / sprite / expression / transition / camera / cg_intent / transition_intent / cg_unlock`;
- 支持环境变量关闭文本 fallback,用于后续真实资产渲染或玩家偏好。

### M3: CLI / TUI 接入

状态: Done

- v5 CLI 在地图节点和普通节点渲染前显示演出提示;
- v7 TUI 复用同一 formatter;
- TUI 输出前转义 Rich markup,避免资产 label 破坏界面。

### M4: 测试与验证

状态: Done

- 新增 `tests/test_player_presentation.py`;
- 更新 `tools/run_all_tests.py`;
- 执行:
  - `.venv/bin/python -m pytest tests/test_player_presentation.py -q`;
  - `bash tools/audit_all.sh`;
  - `.venv/bin/python tools/run_all_tests.py`;
- 若测试污染 `database/ghost_stories_test.db`,提交前恢复。

---

## 4. 代码入口

- CLI: `src/ghost_story_factory/v5/player.py`
- TUI: `src/ghost_story_factory/v7/tui_player.py`
- 测试: `tests/test_player_presentation.py`
- 测试入口: `tools/run_all_tests.py`

---

## 5. 完成记录

- 2026-05-09: 记录问题:演出契约已存在,运行时未消费,玩家体验仍像纯文字树。
- 2026-05-09: 创建 GitHub Issue `#41` 与 milestone `v7 VN 演出运行时可见`。
- 2026-05-09: v5 CLI / v7 TUI 已接入共享演出格式化器,默认显示文本 fallback,可用 `GHOST_VN_CUES=0` 关闭。
- 2026-05-09: 新增 `tests/test_player_presentation.py`,覆盖 label 解析、旧节点静默、缺省字段、CLI stdout 和 TUI Rich 转义。
- 2026-05-09: 验证通过:`.venv/bin/python -m pytest tests/test_player_presentation.py -q`、`bash tools/audit_all.sh`、`.venv/bin/python tools/run_all_tests.py`。
