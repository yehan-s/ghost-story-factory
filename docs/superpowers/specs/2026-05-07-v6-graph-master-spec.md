# v6 Graph · Master Spec

**日期**: 2026-05-07
**状态**: Superseded by v7 Maze(2026-05-07 后仅作历史设计参考)
**Lead**: yehan + Claude Opus 4.7 (主 session)
**问题**: v5 tree 是"branch-immediately-merge-immediately",选项不影响后续剧情,只调整数值。

## 目标(本次交付)

把 v5 的 50 节点线性 tree 重写为 **图结构**,~120-140 节点,3 条主路线,8 个结局。
玩家选择 A/B/C/D **决定接下来 3-5 步的剧情走向**(节点不同、NPC 不同、可触发道具不同),不只是数值差。

## 图拓扑(顶层)

```text
                       n_intro
                         │
                    n_briefing
                         │
                    n_s1_arrive  ← 路线分叉点 (A/B/C/D 真分叉)
              ┌──────────┼──────────┐
        [Investigator] [Witness] [Survivor]
         调查派         围观派      逃避派
              │          │          │
        S1→S3→S4    S1→S2→S5   S1→S2 跳/S5 跳
        ~30 节点    ~30 节点     ~25 节点
              │          │          │
              └────────┬─┴──────────┘
                       │
                  n_s6_hub  ← 收敛枢纽 (盾构井)
                       │
                  n_s7_b3   ← 终局枢纽
                       │
                ┌──────┼──────┬──────┐
              E_TRUE E_DATA E_TRUTH ...8 结局
```

**关键不变量:**
- `n_s1_arrive` 之前是共享头(2 节点)
- `n_s1_arrive` 是路线分叉点,A/B/C 真分到不同子图,**没有汇合点直到 n_s6_hub**
- `n_s6_hub`、`n_s7_b3` 是收敛枢纽,所有路线必经
- 各路线之间有少量"叛逃节点"允许跨线(代价:失去路线专属道具)

## 三条路线设计

### 1. 调查派 (Investigator)
**心理:** "我要搞清楚 G-273 是谁,这工号背后的事必须查到底。"
**地标顺序:** S1 长椅 → S3 理安寺 → S4 羊血弄 → (跨线选择 S2/S5) → S6 盾构井 → S7 B3
**关键道具:** 林副科长账本残页 / ⺶ 符文 / 一次性铜锈护符 / 1987 录像带
**核心张力:** 真相 vs 安全。每个地标都有"深挖"或"撤退"两个分支;深挖会获得拼图碎片(揭真相用),但 PR 暴涨。
**专属结局:** E_TRUE(关闭常数)/ E_TRUTH(揭真相但拒绝献祭)
**节点估算:** ~30

### 2. 围观派 (Witness)
**心理:** "我是个观察者。我拍下来,我发出去,但我不亲手碰它。"
**地标顺序:** S1 长椅 → S2 307 阶 → S5 留下小学 → (跨线选择 S3/S4) → S6 盾构井 → S7 B3
**关键道具:** 1987 录像带 / 1959-043 磁带 / 倒带背书声(冻结弹)/ 论坛流量
**核心张力:** 距离 vs 卷入。每个地标都有"上传/广播"或"私藏"分支;广播会削弱实体,但提高被实体识别的概率。
**专属结局:** E_BROADCAST(成为下一个 G-273 的传说)/ E_DATA(献祭后被广播)
**节点估算:** ~30

### 3. 逃避派 (Survivor)
**心理:** "我只想下班。我不去想,不去看,不去管。"
**地标顺序:** S1 长椅(无视)→ 跳过 S2/S3 → 被动遭遇 S4 或 S5 → S6 盾构井 → S7 B3
**关键道具:** 几乎无,反而是"丢弃"驱动 — 主动扔掉记录表/工牌/钥匙
**核心张力:** 漏卡风险 vs 平安下班。每漏一卡 +1 shifts_skipped,≥3 强制 E_BAD_1987;但漏得少 + S7 选 D = 平安下班。
**专属结局:** E_NEUTRAL / E_BAD_1987 / E_BAD_DROWN
**节点估算:** ~25

### 共享节点
- `n_intro` / `n_briefing` (2 节点,头部共享)
- `n_s6_hub` 多入口收敛 (~5 节点变体)
- `n_s7_b3` 多入口收敛 (~10 节点 mainframe + 4 路径选择)
- 8 结局节点
**节点估算:** ~25

**总计:** 30 + 30 + 25 + 25 = **~110 节点**(预留 10-20 buffer)

## 八个结局

| ID | 名 | 触发条件 |
|---|---|---|
| **E_TRUE** | 关闭杭州常数 | 调查派完成 + ⺶ 符文 + 7 人归航 + S7 选归还 |
| **E_TRUTH** | 揭穿真相 | 调查派完成 + 5 拼图碎片 + S7 拒绝选择 |
| **E_DATA** | 数据化 雪花频道 | 任意路线 + S7 献祭 |
| **E_BROADCAST** | 永生于夜班论坛 | 围观派完成 + 论坛点赞 ≥ 1987 + S7 掠夺 |
| **E_BAD_1987** | 无尽 1987 | shifts_skipped ≥ 3,或 红衣女孩 dominated |
| **E_BAD_DROWN** | 沉船替死鬼 | 任意路线 + 拾取 7 顶安全帽 |
| **E_NEUTRAL** | 平安下班 | 逃避派 + 漏卡 < 3 + S7 选 D |
| **E_HIDDEN** | 幽灵保安重投胎 | 三路均集齐 1 件路线专属物品 + 触发隐藏闸 |

## Schema 升级(player.py 必须支持)

向后兼容 v5,但新增能力:

### 1. 动态 narrative variants
```json
"n_s6_hub": {
  "narrative_variants": [
    {"if": {"flags": {"investigator_route": true}}, "text": "..."},
    {"if": {"flags": {"witness_route": true}}, "text": "..."},
    {"if": {"flags": {"survivor_route": true}}, "text": "..."}
  ],
  "narrative": "(fallback) ..."
}
```

### 2. 条件 next(选项的目标节点根据状态变化)
```json
"choices": [
  {
    "text": "进电梯。",
    "next_variants": [
      {"if": {"shifts_skipped_min": 3}, "next": "n_end_bad_1987"},
      {"if": {"flags": {"drown_marked": true}}, "next": "n_end_bad_drown"}
    ],
    "next": "n_s7_b3"
  }
]
```

### 3. require 升级(支持嵌套 OR / AND 组合)
现在的 require 是 AND-only,新增:
```json
"require": {
  "any_of": [
    {"flags": {"investigator_route": true}},
    {"inv_has": ["林副科长账本残页"]}
  ]
}
```

### 4. 路线 affinity 字段(state)
```json
"initial_state": {
  "PR": 0, "GR": 0,
  "route": null,        // null | "investigator" | "witness" | "survivor"
  "skipped_landmarks": [],
  "visited_landmarks": [],
  "puzzle_pieces": []   // 调查派揭真相用,最多 5 片
}
```

## Style Guide(写作规范 — 所有 content writer 严格遵守)

1. **第二人称代入,B 站 UP 主夜班长文风格**
2. **每节点 narrative 150-300 字**(密度高,避免水分)
3. **保留素材具体细节**:工号 G-273 / 1987 / 1996 / DK30+477 / 1959-043 等
4. **不写"你感到害怕"这种心理描述,用感官细节代替**(湿气、铜锈味、雪花声、心跳节奏)
5. **每节点至少 1 个时间戳**(20:27、22:50、01:00 等),保持夜班节奏
6. **结尾留钩子**(下一个动作未完成感,或一句让玩家头皮发麻的留白)
7. **选项文本简短,15-25 字**,避免比 narrative 还长
8. **HUD 数字反馈写在 effects 字段,不在 narrative 里写"PR +5"**(让引擎反馈)

**禁忌:**
- 不写"你想了想"、"你犹豫了"(玩家自己想)
- 不剧透下一个地标(用暗示)
- 不让 narrative 包含选项 letter(A/B/C),由 choices 字段表达
- 不堆叠形容词(夜班的 + 阴森的 + 诡异的 → 选一个最准的)

## 任务拆分(供 team 认领)

| ID | 标题 | Owner |
|---|---|---|
| T1 | 升级 player.py 支持新 schema | engine-upgrade |
| T2 | 写 path-explorer validator 工具 | validator |
| T3 | 写"调查派"路线 ~30 节点 | content-investigator |
| T4 | 写"围观派"路线 ~30 节点 | content-witness |
| T5 | 写"逃避派"路线 ~25 节点 | content-survivor |
| T6 | 写共享节点(intro/s6_hub/s7_b3/8 结局)~25 节点 | lead(我自己) |
| T7 | 整合所有 JSON + 端到端测试 | lead |
| T8 | 更新 README + V5_PLAY_NOW.md | lead |

**依赖关系:**
- T1 必须先完成(content writer 才知道新 schema 怎么写)
- T2 可与 T1 并行
- T3/T4/T5 三 writer 必须等 T1 完成 + T6 头部完成
- T7/T8 最后

## 不在本次范围

- 老代码 5400 行清理(玩通了再说)
- 多故事框架(等这个故事完美再讲)
- UI 美化 / 存档读档
- 状态加 visited_set 之外的扩展
