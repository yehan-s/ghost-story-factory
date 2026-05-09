# 评审团报告: TUI 体验收束与停留选项去重 Pass 14

日期: 2026-05-10
任务: `TASK_TUI_EXPERIENCE_PASS14`
决议: 修改后放行

---

## 1. Chief Editor

结论:修改后放行。

这轮不要再写 CLI。玩家说的是 TUI 体验,那就把 TUI 当正式游玩入口处理。最先修的是阅读节奏:观察一个细节不应该把整段场景重新刷出来。

---

## 2. State Architect

结论:放行。

不需要新增状态。`State` 已经有 `visit_counts / flags / puzzle_pieces / visited_landmarks / skipped_landmarks`,足够驱动 TUI 状态页和行为画像。问题在渲染路径,不是数据不足。

---

## 3. Meta-Game Designer

结论:修改后放行。

TUI 状态页不要像调试器。玩家需要看到“路线账本”和“档案进度”,不是 `oneshot.*` / `arc.*` 这种内部钥匙串。

---

## 4. UX Designer

结论:修改后放行。

三件事最影响手感:

1. stay/detail 选项不能重复刷 narrative;
2. 选项需要可扫读的 badge;
3. 顶部要有当前场景锚点。

颜色和边框是后话,先把信息架构修正。

---

## 5. Lore Keeper

结论:放行。

“路线账本 / 本轮行为画像 / 档案”符合灵异夜班语境。内部 flag 不符合角色视角,应该从常规状态页移除。

---

## 6. Topology Designer

结论:放行。

地图 hub 是拓扑中心,但 TUI 内任何节点都应知道“我现在在哪”。场景条应优先展示地标 header / map picker / ending / node id。

---

## 7. QA / Path Tester

结论:修改后放行。

不要为了测 TUI 开完整人工交互。优先测 helper:

- choice badge 格式和 Rich 转义;
- status lines 不泄露内部 flags;
- stay 分支调用选项刷新而不是整节点重渲染;
- scene strip 输出稳定。

---

## 8. 风险清单

- CLI 偏航:本轮不改 CLI;
- 重复刷屏:stay 不能再走整段 `_render_node()`;
- 调试泄露:状态页不显示内部 flag key;
- 测试脆弱:避免依赖真实终端尺寸和 Textual animation。

---

## 9. 决议

修改后放行。

执行顺序:
1. Task / Issue / milestone / 团队评审同步;
2. TUI helper 拆分;
3. stay/detail 去重;
4. 场景条与状态页整理;
5. TUI 单测;
6. 审计与统一测试。
