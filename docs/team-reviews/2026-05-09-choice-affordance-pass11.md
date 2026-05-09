# 评审团报告: 选择意图与风险提示 Pass 11

日期: 2026-05-09
任务: `TASK_CHOICE_AFFORDANCE_PASS11`
决议: 修改后放行

---

## 1. Chief Editor

结论:放行,但必须避免数值化。

现在的问题很具体:玩家点选项前不知道它是观察、移动、取证、曝光还是高风险行动。开放沙盒如果没有 affordance,就会像一串菜单。加短标签是合理的,但不要把 PR/GR 数字露出来。

---

## 2. State Architect

结论:放行。

只能读取 `choice.effects` 和 `_picker_kind`,不能新增状态字段。标签是渲染层派生信息,不是规则源。`EffectApplier` 仍然是唯一状态写入位置。

---

## 3. Meta-Game Designer

结论:修改后放行。

标签不能替玩家优化路线。建议显示“心理高压 / 异常升高 / 路线留痕”这种模糊意图,不显示 `PR +8`。玩家应该知道风险性质,但不该拿到完整算盘。

---

## 4. UX Designer

结论:修改后放行。

CLI 和 TUI 都要短。最多 2 个标签,放在选项文本后。不能多行解释,不能把选择列表撑成表格。

---

## 5. Lore Keeper

结论:放行。

“记录信息 / 路线留痕 / 关系推进”这些标签符合本作档案、夜班、审判的语境。不要使用现代产品味很重的标签。

---

## 6. Topology Designer

结论:放行。

地图 picker 的 travel / tool / endshift 也要有标签。否则普通场景变清楚了,地图 hub 仍像功能菜单。

---

## 7. QA / Path Tester

结论:修改后放行。

测试纯 formatter 和轻量 stdout,不要启动完整 `play()`。TUI 只测 label formatter 或 `Option` 文本构造相关 helper,不要启动 Textual pilot。

---

## 8. 风险清单

- 数值剧透:不输出精确 PR/GR;
- 标签噪音:最多 2 个;
- 旧树兼容:无 effects 时原样;
- TUI markup:继续转义外部文本;
- 范围膨胀:不改剧本数据。

---

## 9. 决议

修改后放行。

执行顺序:
1. 新增 Task / Issue / milestone;
2. 实现共享 formatter;
3. 接入 CLI/TUI;
4. 新增测试并挂入统一测试;
5. 跑审计和完整测试;
6. 回写 Task / Issue / PR。
