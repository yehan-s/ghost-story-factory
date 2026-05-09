# TASK: 选择后反馈闭环与本轮行为画像 Pass 13

版本: v1.0
状态: Done
关联:
- GitHub Issue: `#47`
- GitHub Milestone: `v7 选择后反馈闭环`
- `docs/tasks/TASK_VN_SANDBOX_IMPROVEMENT_PLAN_PASS12.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/team-reviews/2026-05-10-behavior-profile-pass13.md`

---

## 0. 问题判断

Pass 11 已经让玩家在选择前看到非剧透意图,但选择之后还缺少稳定反馈。玩家知道自己点了“观察 / 取证 / 曝光 / 绕开”,却不总能看到“这一步已经被系统记住”。

这会削弱开放沙盒的核心承诺:每一步都会变成下一步的地形。

【核心判断】
✅ 值得做:这是互动闭环问题,不是文案润色。

【关键洞察】
- 数据结构:现有 `effects / flags / State._last_events / puzzle_pieces / visited_landmarks` 足够派生本轮行为画像,不需要新增 schema。
- 复杂度:做纯 formatter,CLI/TUI 复用;关键节点自动显示短账本。
- 风险点:不能把行为画像做成数值面板。玩家需要感到“被记住”,不是看到优化表。

---

## 1. 目标

- 选择后显示短反馈,提示路线账本已经记住这一步;
- 在地图 hub / B3 / 评价室 / 晨湖 / 结局节点显示本轮行为画像;
- 至少覆盖 4 类行为倾向:
  - 取证;
  - 曝光;
  - 救援 / 命名;
  - 审判 / 删除;
  - 漏卡 / 绕开。
- 不暴露精确 PR / GR;
- 不新增 DB schema;
- 不改正式剧本 JSON。

---

## 2. 非目标

- 不做完整结局复盘;
- 不做 gallery / archive 新 UI;
- 不新增好感度系统;
- 不把行为画像写入存档;
- 不修改 story fragments。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 新增本 Task;
- 新增团队评审报告;
- 创建 GitHub issue 和 milestone;
- 更新 roadmap。

### M2: 行为画像 formatter

状态: Done

- 在 `src/ghost_story_factory/v5/player.py` 增加纯函数;
- 从 `State` 派生行为画像短文本;
- 不输出 PR / GR 数字;
- 无行为痕迹时静默。

### M3: 选择后反馈

状态: Done

- 复用 `choice_affordance_tags`;
- 玩家选择后显示 1 行“路线账本”反馈;
- CLI/TUI 都显示;
- stay 选项也能反馈。

### M4: 关键节点画像展示

状态: Done

- 在以下节点自动显示行为画像:
  - `n_landmark_picker`;
  - `n_l1985_landmark_picker`;
  - `n_scene_b3_corridor`;
  - `n_scene_evaluator_room`;
  - `n_scene_morning_lakeside`;
  - 所有结局节点。

### M5: 测试与验证

状态: Done

- 新增 `tests/test_behavior_profile.py`;
- 更新 `tools/run_all_tests.py`;
- 执行:
  - `.venv/bin/python -m pytest tests/test_behavior_profile.py -q`;
  - `bash tools/audit_all.sh`;
  - `.venv/bin/python tools/run_all_tests.py`;
- 测试污染 `database/ghost_stories_test.db` 时恢复。

---

## 4. 代码入口

- CLI: `src/ghost_story_factory/v5/player.py`
- TUI: `src/ghost_story_factory/v7/tui_player.py`
- 测试: `tests/test_behavior_profile.py`
- 测试入口: `tools/run_all_tests.py`

---

## 5. 完成记录

- 2026-05-10: 记录问题:选择前意图已可见,选择后仍缺少稳定行为画像反馈。
- 2026-05-10: 创建 GitHub Issue `#47` 与 milestone `v7 选择后反馈闭环`。
- 2026-05-10: 增加行为画像纯 formatter,覆盖取证 / 曝光 / 救援 / 审判 / 删除 / 漏卡等路线痕迹。
- 2026-05-10: CLI 与 TUI 在选择后输出路线账本反馈,关键节点与结局节点显示本轮行为画像。
- 2026-05-10: 新增 `tests/test_behavior_profile.py`,并挂入 `tools/run_all_tests.py` 的 v7 回归测试组。

验证记录:
- `.venv/bin/python -m pytest tests/test_behavior_profile.py -q`: 7 passed。
- `bash tools/audit_all.sh`: 通过。
- `.venv/bin/python tools/run_all_tests.py`: 全部通过。
- `git diff --check`: 通过。
