# TASK: TUI 体验收束与停留选项去重 Pass 14

版本: v1.0
状态: Done
关联:
- GitHub Issue: `#49`
- GitHub Milestone: `v7 TUI 体验收束`
- `docs/tasks/TASK_BEHAVIOR_PROFILE_PASS13.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/team-reviews/2026-05-10-tui-experience-pass14.md`

---

## 0. 问题判断

用户明确指出:主要问题在 TUI 体验,不要继续把 CLI 当体验主线。

当前 TUI 的坏味道不是“样式不够漂亮”,而是交互数据流不对:

- `stay` / “看一眼”选项会重新调用整段 `_render_node()`,导致同一节点 narrative / map 被重复刷屏;
- 状态页仍暴露内部 flag key,像调试面板,不像视觉小说 / 灵异档案;
- 选择列表只是把 CLI 标签塞进 `OptionList`,没有 TUI 专属的信息层级;
- 顶部只显示库存和进度,缺少当前场景锚点。

【核心判断】
✅ 值得做:这是 TUI 玩家体验闭环问题,不是 CLI 润色。

【关键洞察】
- 数据结构:现有 `node / State / save_manager / foreshadows` 足够,不需要改正式树和 DB schema。
- 复杂度:先拆出 TUI helper 和选择刷新路径,不要改 v5 CLI 渲染。
- 风险点:不要把 TUI 做成调试控制台;内部 flag 不应出现在玩家常规状态页。

---

## 1. 目标

- TUI `stay` / detail 选项不再重复渲染当前节点正文;
- TUI 状态页改为玩家可读的路线账本 / 行为画像 / 档案进度;
- TUI 选择项使用专属 badge,不是简单搬运 CLI 文本;
- 增加顶部场景条,给玩家当前场景锚点;
- 保持 Rich markup 安全;
- 新增 TUI 体验回归测试。

---

## 2. 非目标

- 不改 CLI 体验;
- 不改正式剧本 JSON / fragments;
- 不新增 DB schema;
- 不做真实图像 / 音频资产渲染;
- 不重写 Textual 主菜单。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 新增本 Task;
- 新增团队评审报告;
- 创建 GitHub issue 和 milestone;
- 更新文档索引与 roadmap。

### M2: TUI 选择列表信息架构

状态: Done

- 增加 TUI 专属选择 badge;
- 保留数字快选;
- 不泄露 PR / GR 数值和内部 flag;
- Rich markup 安全。

### M3: stay / detail 去重渲染

状态: Done

- 拆出 TUI 选项收集与刷新 helper;
- `stay` 选项只输出细节文本、状态事件和刷新后的选项;
- 不重复渲染当前节点 narrative / map;
- 不重复累计节点访问次数。

### M4: TUI 场景条与状态页整理

状态: Done

- 新增顶部场景条;
- 状态页移除内部 flags;
- 状态页显示行为画像、路线账本、档案进度。

### M5: 测试与验证

状态: Done

- 新增 `tests/test_tui_experience_pass14.py`;
- 更新 `tools/run_all_tests.py`;
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

- 2026-05-10: 记录用户质疑:主要是 TUI 体验,不要继续围着 CLI 打转。
- 2026-05-10: 创建 GitHub Issue `#49` 与 milestone `v7 TUI 体验收束`。
- 2026-05-10: TUI 选择列表改为专属 badge,保留数字快选,不暴露 PR / GR 与内部 flag。
- 2026-05-10: `stay` / detail 选项不再重跑 `_render_node()`,只刷新选项与状态,避免重复刷 narrative / map。
- 2026-05-10: 新增顶部场景条,状态页改为 Modal,移除内部 flags dump。
- 2026-05-10: 结局页新增本轮复盘,显示行为画像、路线账本、档案进度与下一轮可追项。
- 2026-05-10: 新增 `tests/test_tui_experience_pass14.py`,并挂入统一测试脚本。

验证记录:
- `.venv/bin/python -m pytest tests/test_tui_experience_pass14.py tests/test_choice_affordance.py tests/test_behavior_profile.py tests/test_player_presentation.py -q`: 26 passed。
- `bash tools/audit_all.sh`: 通过。
- `.venv/bin/python tools/run_all_tests.py`: 全部通过。
- `git diff --check`: 通过。
