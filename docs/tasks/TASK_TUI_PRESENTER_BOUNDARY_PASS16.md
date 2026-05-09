# TASK: TUI 表达层边界拆分 Pass 16

版本: v1.0
状态: Done
关联:
- GitHub Issue: `#53`
- GitHub Milestone: `v7 TUI 病根拆分`
- `docs/tasks/TASK_TUI_EXPERIENCE_PASS14.md`
- `docs/tasks/TASK_TUI_SCENE_VIEW_PASS15.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/team-reviews/2026-05-10-tui-presenter-boundary-pass16.md`

---

## 0. 病根判断

Pass 14/15 修掉了 TUI 的几个明显症状:状态倾倒、重复刷屏、滚动日志。但继续看代码,病根不是这些症状本身。

真正的病根是:`GhostStoryApp` 同时承担了太多责任:

- 状态推进;
- 存档副作用;
- Rich 文本转义;
- 选择标签格式化;
- 状态页 / 结局复盘格式化;
- 地图与 narrative 渲染;
- Textual widget 操作。

这导致每一次体验改进都要继续往一个大类里塞逻辑。坏味道不在“某行写得丑”,而在边界错了。

【核心判断】
✅ 值得做:这是 TUI 后续持续迭代的结构性风险。

【关键洞察】
- 数据结构:纯表达函数不需要 App 实例,只需要 `tree / state / save_manager / choice`。
- 复杂度:先抽出 presenter 模块,不重写 Textual App。
- 风险点:不能把 CLI formatter 一起搬动;本轮只拆 TUI。

---

## 1. 目标

- 新增 TUI presenter 模块;
- 将 Rich 转义、narrative 高亮、选择 badge、场景条、状态页、结局复盘、过门反馈迁入 presenter;
- `tui_player.py` 只保留 Textual widget 操作和状态流控制;
- 保持现有 TUI 行为不变;
- 新增 presenter 边界测试。

---

## 2. 非目标

- 不改 CLI;
- 不改正式剧本 JSON / fragments;
- 不新增 DB schema;
- 不重写 `GhostStoryApp`;
- 不做完整 MVC / MVVM 框架。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 新增本 Task;
- 新增团队评审报告;
- 创建 GitHub issue 和 milestone;
- 更新文档索引与 roadmap。

### M2: Presenter 模块

状态: Done

- 新增 `src/ghost_story_factory/v7/tui_presenter.py`;
- 迁移纯表达函数;
- 不依赖 Textual widget。

### M3: TUI 接线

状态: Done

- `tui_player.py` 导入 presenter 函数;
- 移除本文件内重复 formatter;
- 保持外部测试可通过。

### M4: 边界测试

状态: Done

- 新增 `tests/test_tui_presenter.py`;
- 覆盖 Rich 转义、过门反馈、状态页不泄露内部 flag;
- 更新 `tools/run_all_tests.py`。

### M5: 验证

状态: Done

- 执行:
  - `.venv/bin/python -m pytest tests/test_tui_presenter.py tests/test_tui_experience_pass14.py -q`;
  - `bash tools/audit_all.sh`;
  - `.venv/bin/python tools/run_all_tests.py`;
  - `git diff --check`;
- 测试污染 `database/ghost_stories_test.db` 时恢复。

---

## 4. 代码入口

- 新增: `src/ghost_story_factory/v7/tui_presenter.py`
- TUI: `src/ghost_story_factory/v7/tui_player.py`
- 测试: `tests/test_tui_presenter.py`
- 测试入口: `tools/run_all_tests.py`

---

## 5. 完成记录

- 2026-05-10: 记录病根: TUI App 类混合状态推进、存档副作用、表达格式化和 widget 操作。
- 2026-05-10: 创建 GitHub Issue `#53` 与 milestone `v7 TUI 病根拆分`。
- 2026-05-10: 新增 `tui_presenter.py`,集中 Rich 转义、选择标签、场景条、状态页、结局复盘和过门反馈。
- 2026-05-10: `tui_player.py` 改为导入 presenter 纯函数,保留 Textual App 的状态流和 widget 操作。
- 2026-05-10: 新增 `tests/test_tui_presenter.py`,并接入 `tools/run_all_tests.py` 的 v7 回归组。
- 2026-05-10: 验证通过:
  - `.venv/bin/python -m pytest tests/test_tui_presenter.py tests/test_tui_experience_pass14.py tests/test_choice_affordance.py tests/test_behavior_profile.py tests/test_player_presentation.py -q`
  - `bash tools/audit_all.sh`
  - `.venv/bin/python tools/run_all_tests.py`
