# 2026-05-09 Pass 8 NPC 关系账本与终局前回咬团队评审

关联 Task: `docs/tasks/TASK_SCRIPT_NPC_ACCOUNTABILITY_PASS8.md`
关联 Issue: `#36`

---

## 0. 结论

【核心判断】
✅ 值得做。当前剧本已经能跑,但共享 NPC 的“记账感”仍不够硬。论坛、清洁工、评价室分别代表传播、删除、审判,它们应该读同一组玩家行为,形成一套可感知的身份系统。

【关键洞察】
- 数据结构:现有 `flags / puzzle / PR / GR / narrative_variants` 已够用,不需要新增好感度或 DB schema;
- 复杂度:不要造“NPC 关系系统”,只把已有行为状态在关键 NPC 和终局前节点读出来;
- 风险点:最危险的是新增一堆镜像 flag,把状态空间变脏。

---

## 1. 剧本主笔

当前最薄弱的不是恐怖意象,而是 NPC 对玩家行为的态度还不够持续。论坛、清洁工、评价室都应该能说出玩家“今晚到底把死人当人,还是当素材”。

建议优先改:
- `n_npc_forum_lurkers`
- `n_npc_cleaner_null`
- `n_npc_evaluator_chair`
- `n_scene_evaluator_room`
- `n_scene_b3_corridor`
- `n_scene_morning_lakeside`

---

## 2. 玩法设计

玩家不需要看到数值面板。玩家需要看到后果。

Pass 8 应该复用现有行为输入:
- 取证: `arc.all_archives_photoed`
- 曝光: `oneshot.posted_photo`, `oneshot.live_streaming`, `oneshot.forum_posted`
- 删痕: `oneshot.s6_no_fingerprint`, `oneshot.sacrificed_id`
- 等系统: `know.phone_called_1987`
- 自审: `route.behavior_self_audit`
- 救人/命名: `oneshot.s5_freed_yeh`, `arc.seven_returned`, `arc.named_the_dead`

不要新增通用好感度。

---

## 3. 状态架构

本轮不新增 DB schema。新增 flag 也要极度克制。

允许:
- 新增或修改 `narrative_variants`;
- 修改 choice 文案;
- 在必要时复用已有 effects。

禁止:
- 新增 NPC 好感度数值;
- 新增一组 `npc.*.trust` 镜像状态;
- 用新 flag 代替已有 `oneshot/arc/know` 状态。

---

## 4. UX

文本过渡要像“被世界认出来”,不是像系统提示。

好体验:
- NPC 说出玩家刚才做过的具体事;
- B3 或晨湖把玩家路线变成判词;
- 结局前至少一次让玩家意识到“开放路线不是自由无痕,而是每一步都被记录”。

坏体验:
- HUD 直接宣布“你是曝光型玩家”;
- NPC 重复解释规则;
- 终局才突然结算。

---

## 5. VN 演出

本轮主要改文本,但不能破坏 Pass 7 演出契约。

关键节点已有 `camera / cg_intent / transition_intent`,只要不新增资源引用,审计应保持稳定。

---

## 6. QA

必须跑:
- `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json >/dev/null`
- `python3 tools/merge_fragments.py`
- `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json`
- `bash tools/audit_all.sh`
- `.venv/bin/python tools/run_all_tests.py`

重点看:
- dangling refs 不能新增;
- orphan 口径不能回退;
- `undifferentiated_revisit_nodes` 仍为空;
- presentation intent warning 不能回归。

---

## 7. 发布/文档

需要同步:
- Task 文档状态;
- Issue checklist / 评论;
- `TASK_NEXT_VN_SANDBOX_GOALS.md` 的进度记录;
- PR 描述写明“不新增 DB schema / 不新增真实素材”。
