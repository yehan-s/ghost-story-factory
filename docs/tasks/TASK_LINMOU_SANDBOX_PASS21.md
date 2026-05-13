# TASK: linmou Act 1 沙盒骨架补齐 Pass 21

版本: v0.1
状态: Done
创建时间: 2026-05-13
完成时间: 2026-05-13
关联:
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md` §M18
- `docs/team-reviews/2026-05-13-next-direction-survey.md`(Chief / State / Topology 共振 3 票)
- ADR-009(linmou 周目契约 + sandbox debt 章节)
- ADR-010(沙盒拓扑契约)

---

## 0. 背景

ADR-009 P0 落地后 Topology Designer 在 2026-05-08 追加"Sandbox Debt"章节,
诚实记录 linmou Act 1 的拓扑缺口:

| Sandbox 原语 | G-273 参考 | linmou Act 1 现状 |
|---|---|---|
| picker hub | 1 个 | ✅ 1 个 |
| 地标 connections | 网状 | manifest 层已网状(L1-L4) |
| `_is_tool` 工具节点 | 9 | **0** |
| `effects.stay: true` 自循环 | 9 | **0** |
| reaction variant clause | 11 | ✅ 1(picker variant[1]) |

ADR-009 原决议:"**Act 1 不必回炉**(已合入,死代码),Act 2/3 偿还"。
本次评审团 2026-05-13 改判:**先把 Act 1 缺口最小入侵补齐**——优先级
高于 Act 2/3 内容扩张,且账册包/搪瓷缸已被 ADR-009 点名为 tool 候选,
现在就升级是最廉价方案。

【核心判断】
✅ 值得做:linmou 是第二可玩角色,沙盒骨架不齐违反 ADR-010 第一公理。
✅ 最小入侵:不回炉 27 节点叙事,只新增 2 个 tool 节点 + picker 加 2 个 choice。
✅ 必死不变量保留:tool 节点是叙事增强,不参与 ending 路径。

---

## 1. 目标

- linmou 子图独立满足 ADR-010 五项最小骨架(picker / connections / tool / stay / reaction);
- 复用 ADR-009 点名的 **账册包** + **搪瓷缸** 为 tool 节点;
- 每个 tool 节点带 1 处 `effects.stay: true` 自循环;
- 每个 tool 节点带 reaction variant(读 G-273 `ending_seen E_TRUTH`),
  形成跨周目双向联动的最小 demo;
- 保留 `audit_paths_linmou` 必死不变量(INV-1 到 INV-5);
- 不重写既有 27 节点叙事内容。

---

## 2. 非目标

- 不开 Act 2/3 内容(留待后续 Pass);
- 不引入新结局(4 个 ending canon 不动);
- 不打破 INV-1/2/3/4/5 任何必死不变量;
- 不改 G-273 周目;
- 不动 DB schema。

---

## 3. 已落地里程碑

### M1: 现状盘点 + 设计 — Done(2026-05-13)

读 ADR-009 Sandbox Debt 表 + 评审报告 5 项共振 → 决定走"最小入侵"路径。

### M2: 新增 2 个 tool 节点 — Done(commit `697e814`)

- `n_l1985_tool_account_satchel`(账册包):蓝布外皮 / 26 联签复印件 / 1983 年针脚
- `n_l1985_tool_enamel_cup`(搪瓷缸):1976 厂庆款 / 「为人民服务」漆掉一半 / 老李廉价绿茶

每个 tool 节点:
- `_is_tool: True` + `_tool_id` + `_tool_label`
- 2 个 choices:`{effects: {stay: True}, next: 自身}` + 回 picker
- 2 个 narrative_variants:`ending_seen E_TRUTH` reaction + 空 if fallback
- `presentation: {camera: close, cg_intent: tool_inspect}`

### M3: picker 连接 — Done(commit `697e814`)

`n_l1985_landmark_picker` 加 2 个 choice([06] 摸账册包 / [07] 看搪瓷缸),
原 5 个选项不动。

### M4: 测试 — Done(commit `697e814`)

新增 `test_linmou_subgraph_meets_adr010_sandbox_skeleton`:
从 `n_l1985_entry` BFS linmou 子图,独立验证 5 项骨架。

### M5: 验证 — Done(commit `697e814`)

- merge_fragments ✅
- audit_all.sh 8/8 ✅(tool 10→12, stay 9→11, reaction 19→21)
- run_all_tests 7/7 ✅
- audit_paths_linmou 0 problems(必死不变量保持)

---

## 4. 验收对照

| M18 验收条款 | 现状 |
|---|---|
| ≥ 1 `_is_map_picker: true` hub | ✅ `n_l1985_landmark_picker`(已有) |
| ≥ 4 地标,每个 ≥ 1 条 connections | ✅ L1-L4,manifest 层全网状 |
| ≥ 2 个 `_is_tool: true` 节点 | ✅ account_satchel + enamel_cup |
| ≥ 1 处 `effects.stay: true` 自循环 | ✅ 2 处(两个 tool 都有) |
| ≥ 1 处 reaction clause variant | ✅ 3 处(picker + 2 tool 各 1) |
| audit_sandbox 在 linmou Act 1 通过 | ✅ 子图骨架测试通过 |
| audit_paths_linmou 必死不变量绿 | ✅ 0 problems |
| audit_all 与统一测试通过 | ✅ 8/8 + 7/7 全绿 |

---

## 5. 代码入口

- 剧本:`stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json`
  - 新增 `n_l1985_tool_account_satchel` / `n_l1985_tool_enamel_cup`
  - `n_l1985_landmark_picker.choices` +2
- 测试:`tests/test_audit_paths_linmou.py::test_linmou_subgraph_meets_adr010_sandbox_skeleton`

---

## 6. ADR-009 sandbox debt 更新

ADR-009 §"Sandbox Debt(ADR-010 后追加,2026-05-08)"中:

| 原行 | 更新为 |
|---|---|
| `_is_tool` 工具节点 0 个 / Act 2 偿还 | ✅ 2 个 / **Pass 21 已偿还** |
| `effects.stay: true` 自循环 0 处 / Act 2 偿还 | ✅ 2 处 / **Pass 21 已偿还** |
| 总节点数 27 / 目标 50 | 27 + 2 tool = 29(目标 50 留 Act 2) |

"Act 1 不必回炉"决议保留——Pass 21 是**追加 2 个 tool 节点**而非回炉。

---

## 7. 后续

- ADR-009 P1 Act 2/3 仍是未来工作(本 Pass 不动);
- Pass 22:audit 三件套语义化,可校验本次 reaction clause 的实际触发率;
- 长线挂账:linmou 4 地标内部叙事(_01 节点的 27 节点深度内容)是否值得二次扩写,留团队评估。
