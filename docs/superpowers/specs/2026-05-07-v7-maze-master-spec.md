# v7 Maze · Master Spec

**日期**: 2026-05-07
**状态**: Active(team `ghost-v6-graph` 重新启动 v7 阶段)
**Lead**: yehan + Claude Opus 4.7
**起源**: v6 还是太规整 — 三条路线 95% 平行,只在 S6 汇合。用户要的是真正的环环相扣有机迷宫。

## 死掉的旧概念

- ❌ **"调查派 / 围观派 / 逃避派"路线** — 整个 route 字段不再使用
- ❌ **"S1→S2→...→S7" 顺序** — 玩家不再按固定顺序走地标
- ❌ **"分支立刻汇合"** — 每个选项后必须再有 ≥3 层子选项,才能允许汇合

## 活下来的概念

- ✅ State / inv / flag / PR / GR 系统(沿用 v6 的 player.py)
- ✅ narrative_variants(同一节点根据状态显示不同文本)
- ✅ next_variants(同一选项根据状态跳到不同节点)
- ✅ 嵌套 require(any_of / all_of / not)

## 新数据结构

### 节点命名空间(铁律)

- `n_<landmark>_<sub>` — 地标内部节点,如 `n_s1_pocket_book`
- `n_npc_<who>` — **共享 NPC 节点**,可被多个地标到达,如 `n_npc_faceless_coat`、`n_npc_predecessor_voice`
- `n_scene_<what>` — **共享场景节点**,跨地标的特殊场景,如 `n_scene_lake_27th_floor`、`n_scene_b3_corridor`
- `n_end_<id>` — 结局节点

### 图结构(顶层)

```
                          n_intro
                             │
                       n_briefing
                             │
                     n_landmark_picker  ← 玩家选择第一个地标(7 选 1)
                       /  |  |  |  |  |  \
                      v   v  v  v  v  v   v
                     S1  S2  S3  S4  S5  S6  S7
                     ╳   ╳   ╳   ╳   ╳   ╳   ╳
                       ↘ ↙ ↘ ↙ ↘ ↙   ↘ ↙
                     共享 NPC / 共享场景(跨地标深层节点)
                       ↘     ↙       ↘     ↙
                          [终局区]
                       /   |   |   |   \
                  E_TRUE E_TRUTH E_DATA ... E_HIDDEN
```

**关键不变量:**
- **每个地标 = 一个迷宫子图,15-25 节点,内部有真分支 / 环 / 死胡同 / 跨地标出口**
- **共享 NPC / 共享场景节点是网络的"枢纽"** — 玩家从不同地标都可能到达同一个 NPC
- **玩家可以同夜多次回到同一地标**(但 narrative_variant 反映状态变化)
- **不强制 7 地标都走完** — 玩家可能 3 个地标就走到终局,也可能在一个地标转半天

## 必须有的环结构(具象描述)

每个地标内部至少要有这些环 / 跨流模式中的 3 种:

1. **状态环回**:某个深处选项 → 回到地标入口节点(但 narrative_variant 显示玩家身上多了什么 / 选项可见性变了)
2. **跨地标出口**:某个深层选项 → 跳到另一个地标的某个深层节点(不是入口)
3. **共享 NPC 入口**:多个不同选项都通向同一个 `n_npc_*` 节点(同一 NPC 从多个方向被遇到)
4. **死胡同**:某个选项导致 -PR / 损失物品 / 跳回地标入口,玩家明确感到"这里走错了"
5. **多入口汇合**:某个地标内部节点有 ≥3 个入边(从地标内不同分支到达)

## 共享 NPC / 共享场景列表(由 lead 写,所有 writer 引用)

### 共享 NPC(13 个)

| 节点 ID | 谁 | 哪些地标可到 | 作用 |
|---|---|---|---|
| `n_npc_faceless_coat` | 空风衣实体(无脸版) | S1(主入口)、S3 跨流、S7 终局 | 给账本碎片 / 引向 1985 真相 |
| `n_npc_predecessor_voice` | 前任 G-273 的电话/对讲机声音 | S1、S2、S5、共享场景 | 暗示玩家自己的命运 |
| `n_npc_drowned_official` | 1985 投湖林副科长 | S1、S3 水下、共享场景 | 给完整账本 / 揭真相 |
| `n_npc_red_dress_girl` | 红衣电视女孩 | S2(主)、S5、S7 | 27F 通道钥匙 |
| `n_npc_yang_butcher` | 无头黑山羊 | S4(主)、S6 跨流 | 给 ⺶ 符文 / 标记待宰 |
| `n_npc_helmet_workers` | 7 个工人 | S6(主)、S3 水下、共享场景 | 7 人归航 / 沉船标记 |
| `n_npc_piano_ghost` | 1991 留下小学女生 | S5(主)、S2 跨流 | 给磁带 / 慢半拍 |
| `n_npc_corrosion_face` | 铜锈侧脸 | S3(主)、S7 | 一次性护符 |
| `n_npc_forum_lurkers` | 夜班论坛匿名观众 | 任何拍照行为后 | 论坛点赞反馈 |
| `n_npc_evaluator_chair` | 夜班评议会(声音 only) | 任何关键选择后 | 给候补判官章 |
| `n_npc_eight_self` | 8 棺残片里的"另一个你" | S7、共享场景 | 揭真相 / 引向 E_TRUTH |
| `n_npc_cleaner_null` | 不存在的清洁工 | 任何"摄像头死角累积"触发 | 删物品 / 数据化 |
| `n_npc_ghost_guard` | 上一任 G-273(已数据化) | S7、共享场景 | 给 27F 钥匙 |

### 共享场景(7 个)

| 节点 ID | 哪儿 | 入口来源 |
|---|---|---|
| `n_scene_lake_underwater` | 西湖水下 | S1 选 "进湖"、S3 水下回声、S6 沉船备份池 |
| `n_scene_27th_floor_corridor` | 不存在的 27 楼走廊 | S2(电视女孩引导)、S6 hub(b3_unlocked)、S7 |
| `n_scene_b3_corridor` | 平海街 B3 走廊 | S7 入口、S2 跨流(深层)、共享 |
| `n_scene_evaluator_room` | 夜班评议会档案室 | 拿到候补判官章后,任意地标解锁 |
| `n_scene_lost_archive` | 遗失档案室(藏拼图碎片) | S3、S5、共享 |
| `n_scene_red_telephone` | 红色对讲电话亭(打通到前任) | S1、S5、survivor 接电话回调 |
| `n_scene_morning_lakeside` | 6 点湖滨日出 | 多个结局共享前置 |

## 玩家解锁机制(状态驱动)

不再有"路线"标记。玩家通过状态自然分化:

| 状态条件 | 解锁选项 | 暗示路径 |
|---|---|---|
| `inv_has: ["林副科长账本残页"]` | 调查派关键选项 | 拿到完整账本能进 `n_scene_lost_archive` |
| `flags.posted_*` 累积 ≥3 | 围观派关键选项 | 论坛流量解锁 `n_npc_ghost_guard` |
| `shifts_skipped >= 2` | 逃避派关键选项 | 解锁 `n_scene_red_telephone` 求救 |
| `puzzle_pieces >= 3` | 真相揭露选项 | E_TRUTH 前置 |
| `inv_has: ["⺶ 符文", "27F 铜钥匙"]` | E_TRUE 解锁 | 数据化阻止 |

不强制玩家"专走某条线",玩家可以**混搭**(投资几个 + 围观几个 + 逃避几个),最终结局基于状态组合判定,**不基于 route 字段**。

## 节点规模

| 类别 | 数量 | 谁写 |
|---|---|---|
| 共享头部(intro/briefing/landmark_picker) | 5 | lead |
| 7 个地标迷宫(每个 15-25 节点) | 105-175 | 7 个 writer 各 1 |
| 13 个共享 NPC 节点 | 13 | lead |
| 7 个共享场景节点 | 7 | lead |
| 8 结局 | 8 | lead(沿用 v6) |
| **总计** | **~150-200 节点** | |

## Style Guide(沿用 v6 + 强化)

- 第二人称,B 站 UP 主夜班长文
- 每节点 narrative 150-300 字
- **重要新增**:每个地标内部至少 1 个 narrative_variants 节点,根据玩家"是否第二次到达"显示不同文本
- 共享 NPC 节点必须有 4-6 个 narrative_variants(根据"从哪个地标进来"区分)
- 选项不要超过 4 个(避免选择麻痹)
- 选项 next 必须是 v7 命名空间内的合法 ID

## 任务拆分(team `ghost-v6-graph` 重启)

| ID | 标题 | Owner |
|---|---|---|
| W1 | 写 7 个共享场景 + 13 个共享 NPC 节点(20 节点) | lead |
| W2 | 写 S1 长椅迷宫(20-25 节点)— 同时是其他 writer 的样本 | lead(亲自写,设标杆) |
| W3 | 写 S2 307 阶迷宫 | content-witness 复用 |
| W4 | 写 S3 理安寺迷宫 | content-investigator 复用 |
| W5 | 写 S4 羊血弄迷宫 | 新 agent |
| W6 | 写 S5 留下小学迷宫 | 新 agent |
| W7 | 写 S6 盾构井迷宫 | 新 agent |
| W8 | 写 S7 B3 终局迷宫 | content-survivor 复用 |
| W9 | path_explorer + merge 升级支持 v7 schema | validator 复用 |
| W10 | 整合 + 端到端测试 + 文档 | lead |

W2 是关键:**lead 亲自写一个"标杆迷宫",其他 writer 必须模仿密度和环结构**。

## 不在范围

- 删除老代码(v1/v6 都留着,作历史档)
- UI / 存档 / 多故事框架(暂不)

## 风险与缓解

- **写作工作量爆炸**(150-200 节点) → 7 个 writer 并发,W2 标杆先行
- **图变得不可追踪** → path_explorer 升级 + 实测覆盖率
- **玩家迷失** → 每个地标入口给"地标地图"提示(narrative 可包含"你刚从哪里来"暗示)
- **状态爆炸** → 节点 visited 不进 require,只看 inv/flag(已是 player.py 现状)
