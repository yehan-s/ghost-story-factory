# 评审团报告: TUI 当前场景视图与过门反馈 Pass 15

日期: 2026-05-10
任务: `TASK_TUI_SCENE_VIEW_PASS15`
决议: 修改后放行

---

## 1. Chief Editor

结论:修改后放行。

TUI 现在最大的问题是主阅读区还在累积整局历史。视觉小说应当让玩家读“眼前这一幕”,不是翻终端日志。

---

## 2. State Architect

结论:放行。

不需要新状态结构。用一个内存级 `_pending_transition_lines` 保存上一选择的过门反馈即可。不要写存档,不要改 DB。

---

## 3. Meta-Game Designer

结论:放行。

过门反馈是好东西:它告诉玩家“刚才那一步已经写进路线账本”,又不会把旧场景全部留在当前阅读区里。

---

## 4. UX Designer

结论:修改后放行。

清屏只发生在节点跳转。`stay` / detail 是当前场景内观察,必须原地追加,否则玩家会觉得自己刚看到的细节被吃掉。

---

## 5. Lore Keeper

结论:放行。

“过门反馈”应保持值班记录语气,不要变成系统日志。选择文本和路线账本足够,不要泄露 PR / GR。

---

## 6. Topology Designer

结论:放行。

地图 picker 切换也应该清屏,否则现场视图会堆叠。手机地图 Modal 不在本轮范围内。

---

## 7. QA / Path Tester

结论:修改后放行。

必须测三件事:

- `_render_node()` 会调用 `RichLog.clear()`;
- pending 过门反馈会在下一节点顶部显示并清空;
- `stay` 分支不调用 `_render_node()`,不清屏,访问计数不增加。

---

## 8. 风险清单

- 清掉玩家刚刚选择的反馈:用 pending 过门补回来;
- 清掉 detail 文本:stay 不走清屏路径;
- 测试脆弱:用 mock log 的 `clear()` 计数,不要依赖真实终端。

---

## 9. 决议

修改后放行。

执行顺序:
1. Task / Issue / milestone / 团队评审同步;
2. 加 pending 过门缓冲;
3. `_render_node()` 清屏并渲染过门;
4. `_apply_choice()` 非 stay 分支写入过门;
5. TUI 回归测试;
6. 审计与统一测试。
