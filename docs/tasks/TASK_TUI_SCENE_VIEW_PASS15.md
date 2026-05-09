# TASK: TUI 当前场景视图与过门反馈 Pass 15

版本: v1.0
状态: Done
关联:
- GitHub Issue: `#51`
- GitHub Milestone: `v7 TUI 当前场景视图`
- `docs/tasks/TASK_TUI_EXPERIENCE_PASS14.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/team-reviews/2026-05-10-tui-scene-view-pass15.md`

---

## 0. 问题判断

Pass 14 修掉了 TUI 的状态弹层、停留选项重复渲染和选择 badge,但主阅读区仍是滚动日志。玩家切换节点后,新场景会压在旧场景下面,这不是视觉小说的阅读节奏。

【核心判断】
✅ 值得做:这是 TUI 主体验问题,不是样式微调。

【关键洞察】
- 数据结构:`RichLog.clear()` 已可用,不需要改故事树或存档结构。
- 复杂度:新增一个“过门反馈”缓冲,换节点时清屏并在顶部显示上一选择摘要。
- 风险点:`stay` / detail 是当前节点内动作,不能清屏;结局页仍要保留复盘。

---

## 1. 目标

- 新节点渲染前清空主阅读区;
- 上一选择与选择后反馈作为过门显示在下一屏顶部;
- `stay` / detail 仍原地追加,不清屏;
- 结局页仍显示本轮复盘;
- 不改 CLI;
- 不改正式剧本 JSON / fragments;
- 新增 TUI 回归测试。

---

## 2. 非目标

- 不做完整历史日志界面;
- 不做真实图片 / 音频资产渲染;
- 不改 Textual 主菜单;
- 不新增 DB schema;
- 不改 `v5/player.py`。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 新增本 Task;
- 新增团队评审报告;
- 创建 GitHub issue 和 milestone;
- 更新文档索引与 roadmap。

### M2: 当前场景清屏

状态: Done

- `_render_node()` 开始时清空主阅读区;
- 首次渲染和节点跳转都只显示当前节点;
- 错误节点仍能显示错误。

### M3: 过门反馈

状态: Done

- 选择后把选择文本、路线账本反馈、地图新增提示写入缓冲;
- 下一节点顶部显示缓冲;
- 不暴露 PR / GR 数值和内部 flag。

### M4: stay / detail 保持原地动作

状态: Done

- `stay` 不触发清屏;
- `stay` 不重复访问计数;
- `stay` 刷新选项与状态。

### M5: 测试与验证

状态: Done

- 更新 `tests/test_tui_experience_pass14.py` 或新增 Pass 15 测试;
- 执行:
  - `.venv/bin/python -m pytest tests/test_tui_experience_pass14.py -q`;
  - `bash tools/audit_all.sh`;
  - `.venv/bin/python tools/run_all_tests.py`;
  - `git diff --check`;
- 测试污染 `database/ghost_stories_test.db` 时恢复。

---

## 4. 代码入口

- TUI: `src/ghost_story_factory/v7/tui_player.py`
- 测试: `tests/test_tui_experience_pass14.py`
- 测试入口: `tools/run_all_tests.py`

---

## 5. 完成记录

- 2026-05-10: 记录问题:Pass 14 后 TUI 主阅读区仍像滚动日志,不是当前场景视图。
- 2026-05-10: 创建 GitHub Issue `#51` 与 milestone `v7 TUI 当前场景视图`。
- 2026-05-10: `_render_node()` 切换节点时清空主阅读区,让当前屏只显示当前场景。
- 2026-05-10: 新增 `_pending_transition_lines / _pending_transition_events`,上一选择与路线账本反馈会作为过门显示在下一屏顶部。
- 2026-05-10: `stay` / detail 保持原地追加,不触发清屏,不重复访问计数。
- 2026-05-10: 扩展 TUI 回归测试,锁定清屏、过门反馈和 stay 原地行为。

验证记录:
- `.venv/bin/python -m pytest tests/test_tui_experience_pass14.py -q`: 8 passed。
- `.venv/bin/python -m pytest tests/test_tui_experience_pass14.py tests/test_choice_affordance.py tests/test_behavior_profile.py tests/test_player_presentation.py -q`: 28 passed。
- `bash tools/audit_all.sh`: 通过。
- `.venv/bin/python tools/run_all_tests.py`: 全部通过。
- `git diff --check`: 通过。
