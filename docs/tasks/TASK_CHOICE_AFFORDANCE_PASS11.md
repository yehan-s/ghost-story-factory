# TASK: 选择意图与风险提示 Pass 11

版本: v0.1
状态: Active
关联:
- GitHub Issue: `#43`
- GitHub Milestone: `v7 选择意图与反馈可见`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/team-reviews/2026-05-09-choice-affordance-pass11.md`

---

## 0. 问题判断

正式树当前有 444 个选择,其中 345 个带 `effects`。这些选择会改变 PR / GR / 道具 / flag / 地标 / 拼图,但 CLI 和 TUI 默认只显示选择文本。

坏味道不是“玩家看不到具体数值”。具体数值全露出来会把灵异 VN 打成数值表。真正问题是玩家做选择前缺少最小意图提示,容易把开放沙盒误读成普通菜单,不知道哪些是观察、移动、取证、曝光、绕开或高风险行动。

【核心判断】
✅ 值得做:这是互动感缺口。数据已在 `effects` 里,运行时只需要用非剧透标签给玩家一点可读 affordance。

【关键洞察】
- 数据结构:`choice.effects` 已经是选择后果的单一真相源,无需新增 schema。
- 复杂度:做共享 formatter,CLI/TUI 复用;不改状态应用、不改选择跳转。
- 风险点:不能暴露精确 PR/GR 数字,否则恐怖叙事会退化为优化题。

---

## 1. 目标

- 在 v5 CLI 选择列表中显示非剧透意图标签;
- 在 v7 TUI 选择列表中显示同一套标签;
- 标签来自 `effects` / `_picker_kind`,不新增剧本字段;
- 标签保持短、少、可关闭;
- 旧选择无 effects 时保持原样。

---

## 2. 非目标

- 不暴露精确 PR / GR 数值;
- 不新增 DB schema;
- 不改 `EffectApplier`;
- 不改 `resolve_next`;
- 不改正式剧本 JSON。

---

## 3. 标签契约

最小标签:

- `观察`: stay / detail;
- `移动`: travel;
- `工具`: tool;
- `收班`: endshift;
- `取得线索`: inv_add;
- `交出物件`: inv_remove;
- `记录信息`: know.* flags;
- `路线留痕`: route.* / oneshot.* / landmark_visited;
- `关系推进`: arc.* flags;
- `拼图`: puzzle_add;
- `绕开`: landmark_skipped / shifts_skipped;
- `心理高压`: PR 上升较高;
- `异常升高`: GR 上升较高。

显示限制:
- 默认最多 2 个标签;
- 环境变量 `GHOST_CHOICE_HINTS=0` 可关闭;
- 不显示 `+5`、`PR`、`GR` 这类精确数值。

---

## 4. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 新增本 Task;
- 新增团队评审报告;
- 创建 GitHub issue 和 milestone;
- 更新 roadmap。

### M2: 共享选择标签 formatter

状态: Done

- 在 `src/ghost_story_factory/v5/player.py` 增加纯函数;
- 输入 choice,输出短标签列表和展示文本;
- 支持环境变量关闭;
- 不依赖状态对象。

### M3: CLI / TUI 接入

状态: Done

- v5 CLI `render_choices()` 显示标签;
- v7 TUI 选项 label 复用同一 formatter;
- TUI 输出前沿用 Rich 字面量转义。

### M4: 测试与验证

状态: Done

- 新增 `tests/test_choice_affordance.py`;
- 更新 `tools/run_all_tests.py`;
- 执行:
  - `.venv/bin/python -m pytest tests/test_choice_affordance.py -q`;
  - `bash tools/audit_all.sh`;
  - `.venv/bin/python tools/run_all_tests.py`;
- 测试污染 `database/ghost_stories_test.db` 时恢复。

---

## 5. 代码入口

- CLI: `src/ghost_story_factory/v5/player.py`
- TUI: `src/ghost_story_factory/v7/tui_player.py`
- 测试: `tests/test_choice_affordance.py`
- 测试入口: `tools/run_all_tests.py`

---

## 6. 完成记录

- 2026-05-09: 记录问题:大量选择带后果,但玩家做选择前看不到最小意图提示。
- 2026-05-09: 创建 GitHub Issue `#43` 与 milestone `v7 选择意图与反馈可见`。
- 2026-05-09: v5 CLI / v7 TUI 已接入选择意图标签,默认最多 2 个,可用 `GHOST_CHOICE_HINTS=0` 关闭。
- 2026-05-09: 新增 `tests/test_choice_affordance.py`,覆盖旧选择静默、非剧透标签、CLI 分组编号、锁定项不泄露、TUI 转义。
- 2026-05-09: 验证通过:`.venv/bin/python -m pytest tests/test_choice_affordance.py -q`、`bash tools/audit_all.sh`、`.venv/bin/python tools/run_all_tests.py`。
