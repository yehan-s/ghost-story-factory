# 2026-05-08 Pass 3 Task 1 完成报告 — 变体密度爆破

> Tag: `pass3-task1-complete`
> 设计文档: `docs/superpowers/specs/2026-05-08-variant-density-explosion-design.md`
> 评审决议: spec-document-reviewer Approved (8/8 评审项)
> 起源痛点: 用户反馈"游戏一点沙盒味都没有,灵异和悬疑元素也不够,开放沙盒互动元素也不够也不够自由"

---

## § 1. 摘要

不加 flag、不加节点、不加 reaction_contracts,**仅在 8 个热点节点 narrative_variants 列表插入 visit_count 3 桶切档(vibe B/C/D),原 narrative 字段做 vibe A default**。共 24 新 variants。

**Linus 三问**:
- 真问题? ✅ Survey 反直觉发现 — 47/144 节点已有 variants,Top10 入度全有,但**触发条件交叉浅**(没人用 visit_count 切档)
- 最简方案? ✅ 零代码、零新 flag、零新节点、零新 reaction_contracts
- 零破坏? ✅ 所有 audit 全绿,孤儿/死路基线不变

---

## § 2. 落地清单(8 节点 × 3 桶 = 24 variants)

| 节点 | Fragment | 入度 | v 数变化 | 状态 |
|---|---|---|---|---|
| `n_landmark_picker` | shared | 57 | 4 → 7 | ✅ P0-1 |
| `n_scene_lake_underwater` | shared | 15 | 1 → 4 | ✅ P0-2 |
| `n_scene_lost_archive` | shared | 13 | 6 → 9 | ✅ P0-3 |
| `n_npc_predecessor_voice` | shared | 11 | 6 → 9 | ✅ P0-4 |
| `n_l1985_landmark_picker` | linmou_1985 | 13 | 2 → 5 | ✅ P1-1 |
| `n_npc_eight_self` | shared | 11 | 5 → 8 | ✅ P1-2 |
| `n_s1_arrive` | landmark_s1 | 10 | 4 → 7 | ✅ P1-3 |
| `n_npc_red_dress_girl` | shared | 9 | 5 → 8 | ✅ P1-4 |

**Variant 列表全局顺序契约**(实际落地遵守):
```
1. reaction (ending_seen / theme_resolved / shifts_completed_min)
2. flag (oneshot.* / arc.* / saw_*)
3. visit_count.min: 3 → 2 → 1  ← 本次新增
4. default (无 if 或 if:{})
```

---

## § 3. vibe 矩阵实际落地

| vibe 桶 | 锚点信号 | 代表片段 |
|---|---|---|
| **B (visit ≥ 1)** 物理被记住 | 留痕 / 位置变化 / 数量变化 | "[03] 九溪的红圈,今天比上次画得更深" |
| **C (visit ≥ 2)** 灵异密度 | 声响 / 影子 / 不对劲 | "地图后面的墙里有铅笔慢慢写字声" |
| **D (visit ≥ 3)** 都市传说底牌 | lore 锚点串接 / "忽然懂了" 悟性句 | "G-273 制图人 / 1985-10-18 第 8 班 / 林副科长交接 / 二轻物资 7+1 工人 lore" |

### 跨节点 lore 串接(D 桶专属)

通过 vibe D 串起一条**隐藏 lore 主线**:

```
landmark_picker D     → G-273 编号 + 林副科长 1985 交接 + 7+1 工人
lake_underwater D     → 「H = 1987」=「工」字 + G-001 在湖底 + 272 中间补位
lost_archive D        → 27 份档案 ⇄ 27 联签 ⇄ 第 28 份是你
predecessor_voice D   → 27 联签盖章节奏 + 你按对讲机 = 第 27 签
s1_arrive D           → 1985-10-18 23:40 = 林某投湖时刻 + 工牌字迹换人
l1985_landmark_picker D → 5 行林志诚自签 (10-18 → 10-22) 都是你字迹
eight_self D          → 8 棺 = 1959 (G-001) → 2024 (G-273) 历代补位
red_dress_girl D      → 她也姓林 / 血脉的债 11 岁开始还
```

玩家**回访 4 次以上同一节点**才能解锁的"忽然懂了"瞬间,串成一个跨节点的暗线 — 沙盒的"层层揭开"质感由此产生。

---

## § 4. 验证结果

### 自动化(全绿)

| 检查 | 期望 | 实际 |
|---|---|---|
| `audit_reactions.py` | 0 红线 | ✅ 0 problems |
| `audit_paths_linmou.py` | 0 problems(INV-1~5) | ✅ 0 problems |
| `pytest -q`(259 用例) | 全过 | ✅ 259 passed |
| 孤儿数 | 不上升(基线 5) | ✅ 5(不变)|
| 死路数 | 不上升(基线 5) | ✅ 5(不变)|
| flag 总量 | ≤ 75(零新) | ✅ 73 / 75(不变)|
| 节点数 | 144(零新) | ✅ 144(不变)|

### 人工(待用户跑)

| 项 | 方法 | 状态 |
|---|---|---|
| visit_count 切档 smoke test(高入度) | `n_landmark_picker` 反复 4 次 | ⏳ 待跑 |
| visit_count 切档 smoke test(低入度) | `n_s1_arrive` 反复 2 次 | ⏳ 待跑 |
| 一致性人审 | 通玩 1 条 E_TRUE 路径 | ⏳ 待跑 |
| linmou 联动 | 通 G-273 hidden truth → linmou Act 1 | ⏳ 待跑 |

---

## § 5. Lore 白名单使用清单

所有 vibe D 引用元素均来自已有 lore canon,**零新增 lore**:

| 元素 | 来源 |
|---|---|
| G-273 / G-001 | 既有角色编号系统(主角工号 + 湖底元祖) |
| 二轻物资(杭州市第二轻工业局物资供应公司财务科) | `data/linmou_act1_lore.json` setting.location_unit |
| 林副科长 / 林志诚 | linmou 角色 + ADR-009 |
| 1985-10-18 23:40(西湖锦带桥东侧投湖) | `data/linmou_act1_lore.json` setting.lake_jump_time |
| 26 联签拨款单 + 27 联签 | linmou Act 1 物件 + 杭州 v7 主线 lore |
| 1996 货梯红衣女孩 | `n_scene_lost_archive` 既有档案条目 |
| 8 棺 1987 冷冻舱 + H=1987 | `n_scene_lake_underwater` + `n_npc_eight_self` 既有 |
| 7+1 工人(7 活 + 1 湖底) | 评审历史 lore 共识 |
| 104 厂夜班汽笛 / 煤油应急灯 / 半导体收音机 | linmou Act 1 audio 清单 |

Lore Keeper 评审验收(Pass 1 评审版): 通过。零通用化风险。

---

## § 6. 偏离 Spec 处(诚实记录)

| Spec 设计 | 实际落地 | 原因 |
|---|---|---|
| 每节点 4 vibe variants(含 vibe A default) | 实际 3 vibe variants(B/C/D)+ 顶级 narrative 字段做 vibe A default | picker 入口节点的顶级 narrative 含必要信息(7 打卡点列表),不能改成"心理戏";其他节点保持顶级 narrative 不动是最小侵入 |
| visit_count.min:3/2/1 + default | 实际同上 + reaction/flag 优先于 visit_count | 列表顺序契约 § 1 已设计,实际落地严格执行 |
| 字数 80/100/120/150 | 实际 ±20% 浮动内 | spec § 3 已加 ±20% 弹性,Lore Keeper 不按字数否决 |

无严重偏离,无 spec § 6 Out of Scope 项被破坏。

---

## § 7. 体验代表片段(给 PM 视角)

### 玩家第一次进 `n_landmark_picker`(visit 0):
> 更衣室外,墙上挂着一张杭州地铁夜班巡逻图。7 个打卡点,用红圈标着...

### 玩家第二次回 `n_landmark_picker`(visit 1):
> 你又站在地图前。地图没换地方,但 [03] 九溪的红圈,今天比上次画得更深...右下角铅笔小字 **「04 不要去」**...你刚才进来时,它没在。

### 玩家第三次回(visit 2):
> 你听见地图后面的墙里有声音——铅笔在硬纸板上慢慢写字。你伸手去掀地图。地图自己**先动了一下**...**「已巡:第 7 班」**。

### 玩家第四次回(visit 3+):
> 制图人那一栏,刻着两个字符:**G-273**。你的工号。但纸边发黄,角落用蓝钢笔写过两行小字:**「1985-10-18 第 8 班 已交接 / 交接人:林副科长」**...师父没醉那次说的:「二轻物资的夜班,从来都是 7 个人轮一个班——第 8 个还在湖底。」

**沙盒的"被记得"质感由此产生** — 用户原话"沙盒一点味道都没有"被这一组矩阵直接命中。

---

## § 8. Pass 3 commits + tag

```
accbdb7 feat(pass3-p1): s1_arrive + l1985_picker + eight_self + red_dress_girl
a30e6e4 feat(pass3-p0-2/3/4): lake_underwater + lost_archive + predecessor_voice
307ed91 feat(pass3-p0-1): n_landmark_picker
ba58048 spec(pass3): 吸收 spec-document-reviewer 3 条建议
5bc4d22 spec(pass3): 变体密度爆破设计文档
🏷️ pass3-task1-complete
```

---

## § 9. 下一步候选

| 任务 | 优先级 | 触发条件 |
|---|---|---|
| **Pass 3.2** Approach 3 体系扩展(reaction_contracts 6→12 + 跨节点联动)| P1 | 用户确认体感后启动 |
| **Pass 4** `n_npc_ghost_guard` + `n_end_data` 补齐(P2 推迟项)| P2 | endings_seen 跨周目联动 spec 出后 |
| **Pass 5** linmou Act 2 sandbox debt 偿还(connections / `_is_tool` / 5 沙盒最小骨架)| P1 | ADR-009 Act 2 spec 出后 |
| **Pass 6** 物件互动层 + 都市传说挖深(B + C 方向)| P2 | linmou Act 2 上线时一并做 |
| **path_explorer 工具债** issues #16 / #17 / #18 | P2 / P3 | 任意时间 |

---

## § 10. 致谢

- Spec 评审: spec-document-reviewer 8/8 通过 + 3 条建议吸收(±20% 字数浮动 / 基线快照 / 低入度 smoke test)
- Survey 数据: `tools/path_explorer.py` 入度 Top10 + Pass 1 后 47 节点 variants 分布
- Lore 锚点白名单: ADR-009 + `data/linmou_act1_lore.json` + Pass 2 Task 5.1 lore canon 共识

**痛点诊断 → 反直觉数据发现 → Approach 1 推荐 → spec 落地 → 8 节点 24 variants** 一气呵成,3 commits + 1 tag 收尾。

> "Bad programmers worry about the code. Good programmers worry about data structures and their relationships." — Linus Torvalds
>
> 本任务的"数据结构"是 visit_count × vibe 矩阵,"关系"是跨节点 lore 串接。零代码改动,纯靠重新组织数据,沙盒"被记得"的质感就长出来了。
