# TASK: 主结局跨周目反咬补完 Pass 23

版本: v0.1
状态: Done
创建时间: 2026-05-13
完成时间: 2026-05-13
关联:
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md` §M20
- `docs/tasks/TASK_AUDIT_SEMANTIC_PASS22.md`(本 Pass 由 audit_cross_run_continuity 揭示)
- `docs/tasks/TASK_SCRIPT_REACTION_PROFILE_PASS20.md`(沿用 Pass 20 反咬模式)
- ADR-010(沙盒拓扑契约 / 跨周目联动)

---

## 0. 背景

Pass 22 落地 `audit_cross_run_continuity.py` 后,工具立刻揭示 4 处主结局
在二周目无任何反咬:

| ending_type | 节点 |
|---|---|
| E_TRUE | n_end_true |
| E_BROADCAST | n_end_broadcast |
| E_NEUTRAL | n_end_neutral |
| E_HIDDEN | n_end_hidden |

Pass 20 时已加 2 处反咬(n_end_neutral 引 E_TRUTH、n_end_truth 引 E_DATA),
现在沿用同一模式延展到剩余 4 个 ending_type。

【核心判断】
✅ 值得做:沙盒第一公理是"跨周目联动",4 处主结局无反咬是直接违反。
✅ 0 新字段:沿用 Pass 20 的 `ending_seen` + 节点 narrative_variants 模式。
✅ 选址自然:每条反咬放在玩家二周目大概率经过的高频节点。

---

## 1. 目标

- 给 4 个 ending_type(E_TRUE / E_BROADCAST / E_NEUTRAL / E_HIDDEN)各补 1 处反咬 variant;
- 放在叙事合理的高频节点(入口 / 地图 hub / 论坛 / 评议会),让玩家二周目自然撞见;
- 不新增 flag / DB schema / 引擎扩展;
- audit_cross_run_continuity 从 4 problems 降到 0。

---

## 2. 非目标

- 不引入新结局;
- 不重写既有节点叙事;
- 不修引擎/audit 工具本体;
- 不动 BAD ending(默认豁免);
- 不动 linmou ending(本 Pass 聚焦 G-273 主线)。

---

## 3. 已落地里程碑

### M1: 反咬节点选址 — Done(2026-05-13)

每个 ending 选 1 处玩家二周目自然遇到的反咬节点:

| 上周目 ending | 反咬节点 | 主题 |
|---|---|---|
| `E_TRUE` | `n_intro` 入职简报 | HR 念稿时口型对你"上次你做完了" |
| `E_BROADCAST` | `n_npc_forum_lurkers` 论坛 | 论坛置顶帖"广播流量主回归,第二季" |
| `E_NEUTRAL` | `n_landmark_picker` 地图 hub | 地图标"无明显异常",把没看见等同于没事 |
| `E_HIDDEN` | `n_scene_evaluator_room` 评议会 | 「已收过此人。本年第二次。」(1985/2024/1957 同位) |

### M2: 4 处反咬 variant 写入 — Done(commit `b3171d6`)

每条 variant 插入到对应节点 `narrative_variants[0]`(最高优先匹配)。
触发条件统一:`{ending_seen: {story_id: "杭州_v7", ending_id: <X>}}`。

### M3: 验证 — Done(commit `b3171d6`)

- merge_fragments ✅
- audit_all.sh 12/12 全绿 ✅(cross_run_continuity 从 4 problems → 0)
- run_all_tests 7/7 全绿 ✅
- audit_paths_linmou 必死不变量保持

---

## 4. 验收对照

| 验收条款 | 现状 |
|---|---|
| 4 个主结局都被 ending_seen 引用 | ✅ E_TRUE / E_BROADCAST / E_NEUTRAL / E_HIDDEN 各 1 处 |
| 0 新字段 | ✅ 纯 narrative_variants 工作 |
| 节点选址自然(玩家二周目大概率遇到) | ✅ 入口 / hub / 论坛 / 评议会 |
| audit_cross_run_continuity 全绿 | ✅ 0 problems |
| audit_all + run_all_tests 全绿 | ✅ 12/12 + 7/7 |

---

## 5. 代码入口

- 剧本:`stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
  - `n_intro` variant[0]
  - `n_landmark_picker` variant[0]
  - `n_npc_forum_lurkers` variant[0]
  - `n_scene_evaluator_room` variant[0]
- 守门工具:`tools/audit_cross_run_continuity.py`(Pass 22 落地)

---

## 6. 反咬密度统计(Pass 20 + Pass 23 合计)

| ending_type | 反咬节点数 | 反咬来源 |
|---|---|---|
| E_TRUTH | 1 | n_end_neutral(Pass 20) |
| E_DATA | 1 | n_end_truth(Pass 20) |
| E_TRUE | 1 | n_intro(Pass 23) |
| E_BROADCAST | 1 | n_npc_forum_lurkers(Pass 23) |
| E_NEUTRAL | 1 | n_landmark_picker(Pass 23) |
| E_HIDDEN | 1 | n_scene_evaluator_room(Pass 23) |
| E_LINMOU_GRIEVANCE | 1 | n_scene_lost_archive(既有) |
| E_LINMOU_REGRET | 1 | n_landmark_picker(既有) |

`E_BAD_*` 默认豁免(audit_cross_run_continuity 内置)。
`E_LINMOU_RELEASE / EXPOSED` 当前未被引用,但 linmou ending 不在主线审计强约束内,
留待后续 linmou Act 2 扩展时一并考虑。

---

## 7. 后续

- 长线:可继续给反咬 variant 叠 `behavior_profile` 组合条件,实现"上周目结局 × 本周目人格"二维矩阵(参考 Pass 20 n_end_neutral / n_end_truth 已有的组合);
- 长线:linmou ending 跨周目反咬(若开 Act 2);
- 短名单 Pass 20-23 全部落地,下一阶段建议开二轮评审团调研路线第二批。
