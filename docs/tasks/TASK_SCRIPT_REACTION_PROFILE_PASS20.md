# TASK: 跨周目联动与行为画像反喂 variants Pass 20

版本: v0.1
状态: Done
创建时间: 2026-05-13
完成时间: 2026-05-13
关联:
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md` §M17
- `docs/team-reviews/2026-05-13-next-direction-survey.md`(7 人评审 5 票共振)
- GitHub Issue #15(audit_reactions 跨 story_id 引用降级)
- ADR-007 / ADR-008(单一真相源 / 反应契约)
- ADR-010(沙盒拓扑契约)

---

## 0. 背景

Pass 19 完成主角身份泄漏清扫后,2026-05-13 评审团 7 人共振给出短名单:

- **轴一(5 票)**:既有真相源榨干 / 0 新字段路线
- **轴二(3 票)**:linmou Act 1 沙盒化(留 Pass 21)
- **轴三(2 票)**:audit 工具语义化(留 Pass 22)

Pass 20 落地轴一——把行为画像 7 维(救人/取证/替班/曝光/命名/删痕/审判)从"打标签"变成"反向喂 variants",
并修 #15 让 endings_seen 跨周目联动真正生效。

【核心判断】
✅ 值得做:数据底座完备(endings_seen + 行为画像 + reaction_contracts),消费侧极薄;
✅ 0 新字段:`behavior_profile_axes(state)` 是从既有 flags/state 派生的视图,纯派生量。

---

## 1. 目标

- 把 `behavior_profile` 作为 require 协议加入 `RequirementEvaluator.meets_clause`;
- 修 `audit_reactions` 把 ending_seen.ending_id 当作 ending_TYPE 验证(原代码误当 node_id),并加跨 story_id skip 兜底(close #15);
- 至少 3 个 G-273 NPC 节点新增 `behavior_profile` 分化 variant;
- 至少 2 个 hangzhou ending 节点新增"上周目你判了谁"二周目回咬 variant(组合 `ending_seen` + `behavior_profile`);
- 新增引擎单元测试覆盖 has / has_any / dominant / 组合 4 种用法;
- 不引入新 flag 字段、不动 DB schema、不修 player.py 状态字段。

---

## 2. 非目标

- 不重写行为画像引擎(`behavior_profile_axes`);
- 不动 reaction_contracts schema;
- 不在 player.py 加 dominant_tag 持久字段(画像是派生量,落地就双真相源);
- 不开新角色周目(留 Pass 21+);
- 不动 UI/UX 层。

---

## 3. 已落地里程碑

### M1: 评审与方案 — Done(2026-05-13)

- 评审团 7 人共振,5 票点名"既有真相源榨干"路线;
- 短名单顺序:Pass 20(数据榨干)→ Pass 21(linmou 沙盒)→ Pass 22(audit 语义化);
- 入账 `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md` §M17。

### M2: `audit_reactions` 修 #15 — Done(commit `6335fca`)

- `DEAD_ENDING_SEEN` 改查 ending_type 集合,不再误当 node_id;
- 加跨 story_id skip + 历史命名兼容(`杭州_v7` ↔ `hangzhou_yebanbaoan`);
- 修后 audit_reactions 0 problems。

### M3: 引擎接入 `behavior_profile` — Done(commit `6335fca`)

- `RequirementEvaluator._meets_behavior_profile` 实现 has / has_any / dominant 三种协议;
- 懒加载 `behavior_profile_axes` 避免循环 import;
- 新增 5 个测试 case 在 `tests/test_behavior_profile.py`。

### M4: 剧本 5 节点 variant 写入 — Done(commit `6335fca`)

| 节点 | 触发条件 | 反咬主题 |
|---|---|---|
| `n_npc_forum_lurkers` | `behavior_profile.has: 曝光` | 论坛潜水者预生成你拍的图 |
| `n_npc_cleaner_null` | `behavior_profile.has: 删除` | 清洁工擦你工牌影子 |
| `n_scene_evaluator_room` | `behavior_profile.dominant: 审判` | 评议会反审判玩家 |
| `n_end_neutral` | `ending_seen=E_TRUTH ∧ behavior_profile.has: 审判` | 打卡机记得你上周目公开真相 |
| `n_end_truth` | `ending_seen=E_DATA ∧ behavior_profile.has: 曝光` | 服务器主动打招呼,论坛等回复 |

### M5: 验证 — Done(commit `6335fca`)

- `python3 tools/merge_fragments.py` ✅
- `bash tools/audit_all.sh` ✅(8/8 全绿)
- `.venv/bin/python tools/run_all_tests.py` ✅(7/7 全绿,12 个 behavior_profile 测试)
- `git diff --check` ✅(无空白错误)

---

## 4. 验收对照

| M17 验收条款 | 现状 |
|---|---|
| reaction_contracts 出现 behavior_profile 派生条件 | ✅ `RequirementEvaluator._meets_behavior_profile` |
| G-273 至少 3 个 NPC 节点读这一条件分化 | ✅ forum_lurkers / cleaner_null / evaluator_room |
| endings_seen 跨周目引用在 audit_reactions 全部 pass | ✅ 0 problems |
| 至少 2 个 hangzhou ending 二周目回咬 | ✅ n_end_neutral / n_end_truth |
| audit_all 与统一测试通过 | ✅ 8/8 + 7/7 全绿 |

---

## 5. 代码入口

- 引擎:`src/ghost_story_factory/runtime/contracts.py:_meets_behavior_profile`
- 行为画像派生量:`src/ghost_story_factory/v5/player.py:behavior_profile_axes`(无改动,纯复用)
- 审计修复:`tools/audit_reactions.py:DEAD_ENDING_SEEN`
- 剧本 5 节点:`stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
- 测试:`tests/test_behavior_profile.py` + 引擎层 5 个新 case

---

## 6. 后续

- Pass 21:linmou Act 1 沙盒化(ADR-009 还债),独立分支推进;
- Pass 22:audit 三件套语义化(foreshadow_chain / cross_run_continuity / variant_trigger),可与 Pass 21 并行;
- 长线挂账:Lore "红衣女孩 / 8 棺自己" 通用化警告(触及对应节点时执行);Meta "结局图鉴 + Memory Echo"(Pass 22 落地后评估)。
