# 评审团报告: TUI 表达层边界拆分 Pass 16

日期: 2026-05-10
任务: `TASK_TUI_PRESENTER_BOUNDARY_PASS16`
决议: 已按修改后放行落地

---

## 1. Chief Editor

结论:修改后放行。

病根不是 TUI 缺一个新提示,而是 `GhostStoryApp` 太肥。继续往里面加体验逻辑,下一轮还会烂。先把纯表达层抽出去。

---

## 2. State Architect

结论:放行。

Presenter 只读 `tree / state / save_manager / choice`,不拥有状态,不写存档。状态推进仍留在 App / State 里。

---

## 3. Meta-Game Designer

结论:放行。

这次不改变玩法,但能让“选择意图 / 行为画像 / 复盘 / 过门”形成统一语气,避免每次散落生成一套 UI 文案。

---

## 4. UX Designer

结论:修改后放行。

所有玩家可见文案格式都应该在一个地方看见。否则 badge、状态页、复盘、过门会继续互相漂移。

---

## 5. Lore Keeper

结论:放行。

Presenter 可以作为“夜班记录语气”的集中入口。它不负责故事内容,但负责不要把调试语言漏给玩家。

---

## 6. Topology Designer

结论:普通审查。

本轮不改地图拓扑,只要地图新增提示仍能进入过门反馈即可。

---

## 7. QA / Path Tester

结论:修改后放行。

必须新增 presenter 单测。不要只靠 TUI App 测试间接覆盖,否则边界拆了等于没锁住。

---

## 8. 风险清单

- 循环依赖:presenter 不能 import `tui_player`;
- 行为漂移:迁移后现有 TUI 测试必须全部通过;
- CLI 误伤:不要改 `v5/player.py`;
- 过度重构:本轮不重写 App,只抽纯表达。

---

## 9. 决议

已按修改后放行落地。

执行顺序:
1. Task / Issue / milestone / 团队评审同步;
2. 新增 presenter 模块;
3. TUI 导入 presenter;
4. 新增 presenter 单测;
5. 审计与统一测试。

完成记录:

- `src/ghost_story_factory/v7/tui_presenter.py` 已新增,且不依赖 Textual widget;
- `src/ghost_story_factory/v7/tui_player.py` 已改为导入 presenter 纯函数;
- `tests/test_tui_presenter.py` 已覆盖 Rich 转义、状态页、过门反馈与兼容 re-export;
- `bash tools/audit_all.sh` 与 `.venv/bin/python tools/run_all_tests.py` 已通过。
