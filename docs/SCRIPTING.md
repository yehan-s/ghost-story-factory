# SCRIPTING — 给想自己写剧本的人

本文档面向**想写一个新故事 / 改这个故事 / 加角色**的人。不读源码,
读完这一份你就能写出 audit_all 全绿的剧本。

---

## 1. 工作流概览

```
你编辑 → _fragment_v7_*.json     ← 手写
       ↓
tools/merge_fragments.py         ← 合并 9 个 fragment
       ↓
stories/<story>/tree.json        ← 引擎读这一份
       ↓
python play_tui.py              ← 玩
```

每改完 fragment,**必须做这两步**:
```bash
python tools/merge_fragments.py    # 编译 tree.json
bash tools/audit_all.sh             # 跑 13 项审计,全绿才算改完
```

---

## 2. 数据形态(Linus 风格:先讲数据,再讲代码)

整个剧本就是一棵 `tree.json`,结构:

```jsonc
{
  "story_id": "杭州_v7",
  "start_node": "n_intro",

  "characters": { "G-273": {...}, "linmou_1985": {...} },
  "endings": { "E_TRUE": "...展示名", "E_TRUTH": "...", ... },

  "reaction_contracts": {
    "deductions":   { "predecessor_loop": {...} },
    "foreshadows":  { "lakeside_drown":   {...} },
    "themes":       { "hangzhou_constant":{...} }
  },

  "nodes": {
    "n_intro": { "narrative": "...", "choices": [...] },
    "n_landmark_picker": { "_is_map_picker": true, ... },
    ...
  }
}
```

**节点 = 一段叙事 + 一组选择**。玩家进入一个节点,看到叙事文本,
从 `choices` 里选一项,引擎根据 `effects` 修改状态,跳到 `next` 指向的下一个节点。

---

## 3. 沙盒拓扑 — 这是第一公理(ADR-010)

**坏剧本** = 线性单链 entry → A → B → C → ending。
**好剧本** = 沙盒:玩家可以在一个 hub 横向探索,反复访问,做累积。

写新角色的最小沙盒骨架(少一条都不行):

| 必备元素 | 含义 | 例子 |
|---|---|---|
| 1 个 `_is_map_picker: true` hub | 玩家从这里挑去哪 | `n_landmark_picker` |
| ≥ 4 个地标,每个 ≥ 1 条 `connections` 邻边 | 地标之间能横向跳,不是辐射 | `n_l1985_abacus_01` 邻 `n_l1985_boiler_01` |
| ≥ 2 个 `_is_tool: true` 节点 | 可反复使用的工具(对讲机 / 论坛 / ...) | `n_npc_predecessor_voice` |
| ≥ 1 处 `effects.stay: true` | 工具用完留在原地,不强制跳走 | 翻论坛后还在论坛页 |
| ≥ 1 处反应 clause variants | 看过某线索后,这个节点文案自动变 | 见 § 5 |

参考实现:G-273 周目(`n_landmark_picker` 56 入边 + 7 地标 + 9 工具)。

**绝对禁止**:
- ❌ 加 `flags` 镜像伏笔/推论解开(违反 ADR-007/008 单一真相源)
- ❌ 加 state 字段表达"玩家见过 X"——查 `endings_seen` / `foreshadows_seen` / `deductions_resolved` 就够
- ❌ 工具节点 `next` 直接跳走(应该 `effects.stay: true`)
- ❌ NPC 反复访问 narrative 不变(应该 `narrative_variants` 切档)

`audit_sandbox.py` 一键检 ADR-010 合规。

---

## 4. 节点写法

### 4.1 普通对话节点

```jsonc
{
  "n_scene_lakeside": {
    "narrative": "湖边没有人。风从对岸吹过来,带着潮味。",
    "choices": [
      {
        "label": "走近湖边",
        "next": "n_scene_lakeside_close",
        "effects": { "GR": 1, "landmark_visited": "S2" }
      },
      {
        "label": "原路返回",
        "next": "n_landmark_picker",
        "require": { "inv_lacks": ["对讲机"] }
      }
    ]
  }
}
```

**关键字段**:
- `narrative` — 默认文案(如果有 `narrative_variants` 且某条命中,优先用那条)
- `choices[].label` — 玩家看到的选项文字
- `choices[].next` — 跳到哪个节点
- `choices[].effects` — 选这条会改什么状态(见 § 4.3)
- `choices[].require` — 满足条件才显示这个选项(见 § 4.4)

### 4.2 picker hub(地图中枢)

```jsonc
{
  "n_landmark_picker": {
    "_is_map_picker": true,
    "narrative": "你又站在地图前。",
    "landmark_map": {
      "S1": "n_s1_arrive",
      "S2": "n_s2_arrive",
      ...
    },
    "connections": {
      "S1": ["S2", "S6"],
      "S2": ["S1", "S3"],
      ...
    }
  }
}
```

`landmark_map` 是 picker 到地标的映射;`connections` 是地标之间的邻接图,
让玩家能从 S1 直接跳 S2 而不必回 picker。

### 4.3 effects(选择后果)

```jsonc
{
  "effects": {
    "PR": 5,                          // 玩家分数 +5(取证/秩序倾向)
    "GR": -3,                          // 鬼分数 -3(被同情倾向)
    "inv_add": ["⺶ 符文"],            // 加道具
    "inv_remove": ["工牌 G-273"],      // 减道具
    "flags": { "arc.named_the_dead": true },  // 设标志
    "landmark_visited": "S3",          // 标记地标已访
    "shifts_completed": 1,             // 班次完成 +1
    "shifts_skipped": 0,
    "puzzle_add": "P3",                // 拼图碎片 +1
    "npc_move": { "predecessor": "n_lore_predecessor_office" },
    "stay": true                       // 工具节点:执行完留在原地
  }
}
```

**flags 命名规范**(ADR-007):
- `arc.*` — 长期人格弧线(`arc.named_the_dead` / `arc.became_judge`)
- `know.*` — 已知信息(`know.saw_8_zhao`)
- `oneshot.*` — 一次性事件(`oneshot.posted_photo`)
- `route.*` — 路径走过(`route.behavior_self_audit`)

### 4.4 require(满足才显示 / 才跳转)

```jsonc
{
  "require": {
    "PR_min": 30,                                // PR ≥ 30
    "inv_has": ["对讲机", "工牌 G-273"],          // 同时有这俩
    "inv_lacks": ["羊血"],                        // 没有羊血
    "flags": { "arc.named_the_dead": true },      // 此 flag 已 true
    "puzzle_pieces_min": 3,                       // 至少 3 个拼图碎片
    "shifts_completed_min": 2,                    // 已完成 2 个班
    "landmark_visited": ["S3"],                   // 访过 S3
    "visit_count_min": { "n_npc_drowned": 2 },    // 访过 n_npc_drowned 至少 2 次
    "deduction_resolved": "predecessor_loop",     // 解开了某推论(见 § 6)
    "foreshadow_resolved": "lakeside_drown",      // 解开了某伏笔
    "theme_resolved": "hangzhou_constant",        // 解开了某母题
    "ending_seen": { "story_id": "杭州_v7", "ending_id": "E_TRUE" },  // 跨周目(见 § 7)

    // 组合逻辑:
    "any_of": [ {...}, {...} ],   // 任一满足
    "all_of": [ {...}, {...} ],   // 都要满足
    "not":    { ... }              // 反向
  }
}
```

---

## 5. 反应式 variants — NPC / 场景的"看过会变"

```jsonc
{
  "n_npc_predecessor_voice": {
    "narrative": "对讲机滋滋响,前任的声音从远处传来。",
    "narrative_variants": [
      {
        "if": { "ending_seen": { "story_id": "杭州_v7", "last": "E_DATA" } },
        "text": "对讲机接通。背景**只有键盘敲击的连音**——前任先报字段名问你 schema..."
      },
      {
        "if": { "deduction_resolved": "predecessor_loop" },
        "text": "你按下对讲机。这次另一头先沉默了一拍——很长的一拍..."
      }
    ]
  }
}
```

**first-match 顺序**:引擎从 `narrative_variants[0]` 开始遍历,
第一个 `if` 满足的就用它的 `text`,都不满足才 fallback 到 `narrative`。
**所以最具体 / 最稀有的条件放前面**。

`audit_variants.py` 检"反复访问 narrative 不变"的节点(那是死剧本红线)。

---

## 6. reaction_contracts — 伏笔 / 推论 / 母题

```jsonc
"reaction_contracts": {
  "deductions": {
    "predecessor_loop": {
      "_label": "前任在 1985 年没下班",
      "consumer_nodes": ["n_npc_predecessor_voice", "n_intro"],
      "trigger_type": "per_run"
    }
  },
  "foreshadows": {
    "lakeside_drown": {
      "_label": "湖边的影子",
      "consumer_nodes": ["n_scene_lakeside"],
      "trigger_type": "per_run"
    }
  },
  "themes": {
    "hangzhou_constant": {
      "_label": "杭州常数",
      "manifestations": ["lakeside_drown", "predecessor_loop"],
      "consumer_nodes": ["n_intro", "n_landmark_picker"]
    }
  }
}
```

`_label` 是人类可读名(audit_foreshadow_chain 要求必填);
`consumer_nodes` 声明"我打算被这些节点 require 消费";
`trigger_type` 决定生效范围(`per_run` 本周目 / `cross_run` 跨周目)。

写一条 deduction/foreshadow/theme 进来,**必须**有节点的 require 真的引用它,
否则 `audit_foreshadow_chain.py` 会报 `CONSUMER_NOT_CONSUMING`。

---

## 7. 跨周目联动(0 新存档字段)

存档里有一个不可妥协的真相源:
```json
{
  "endings_seen": {
    "杭州_v7": ["E_TRUTH", "E_DATA", "E_TRUE"]
  }
}
```

按通关顺序追加,**重复通关时移到末尾**——所以 `list[-1]` 永远是最近一次。

剧本端用两种形式消费:

| 形式 | 语义 | 用途 |
|---|---|---|
| `ending_seen.ending_id: "E_X"` | "曾经通关过 E_X"(历史里出现) | 物质遗迹("纸袋还在")、广义反咬 |
| `ending_seen.last: "E_X"` | "**最近一次**通关是 E_X" | 人格惯性、开场残影 |
| `ending_seen.ending_id: "*"` | "本 story 通关过任意 ending" | 二周目入口 |

`audit_profile_inheritance.py` 强制 5 个 main ending(E_TRUE/TRUTH/BROADCAST/DATA/HIDDEN)
都必须有 ≥ 1 个非结局节点用 `.last` 反咬。BAD/NEUTRAL/LINMOU ending 不在此约束范围。

ADR-011 列了 5 条 main ending 的人格画像参考映射。

---

## 8. 结局节点

```jsonc
{
  "n_end_true": {
    "is_ending": true,
    "ending_type": "E_TRUE",
    "narrative": "天快亮了。你回到 G-273 工位,把工牌放下..."
  }
}
```

`is_ending: true` + `ending_type` 唯一标识。tree 顶层的 `endings` 字段给展示名。

**linmou 前传线**(1985 年的林某)有"必死不变量"——所有 `E_LINMOU_*` ending 节点
都必须有 `_lore_canon.must_die: true`,见 ADR-009。`audit_paths_linmou.py` 守门。

---

## 9. 13 项审计速查

`bash tools/audit_all.sh` 一键跑:

| # | 工具 | 守什么 |
|---|---|---|
| 1 | `audit_playability` | GameTree 可玩闭环(每个节点都能走到 ending) |
| 2 | `audit_sandbox` | ADR-010 沙盒五项骨架 |
| 3 | `audit_script_depth` | Pass 9 厚度(节点数 / 演出意图 / 林某线深度) |
| 4 | `audit_tree` | 节点引用完整性 + lore 红线 |
| 5 | `audit_state` | flags / inv 引用矩阵(写没人读的 flag 会报) |
| 6 | `audit_variants` | 反复访问 narrative 不变的节点 |
| 7 | `audit_reactions` | ADR-008 反应契约三红线 |
| 8 | `audit_paths_linmou` | linmou 必死不变量 |
| 9 | `audit_foreshadow_chain` | 伏笔链条完整性(_label / consumer_nodes 真消费) |
| 10 | `audit_cross_run_continuity` | 跨周目消费侧覆盖 |
| 11 | `audit_variant_trigger` | variant 触发难度(防"写了没人见到") |
| 12 | `audit_protagonist_behavior` | G-273 每个 ending 必须识别玩家(behavior_profile / *_resolved / flags / inv_has) |
| 13 | `audit_profile_inheritance` | 5 main ending 必须有 `.last` 反咬 |

---

## 10. ADR 索引(契约本体)

| ADR | 内容 |
|---|---|
| ADR-007 | 状态空间契约 + Flag 命名规范 |
| ADR-008 | 反应机制 + 跨周目认知继承 |
| ADR-009 | linmou_1985 周目契约(必死不变量) |
| ADR-010 | **沙盒拓扑(第一公理)— 这是沙盒不是死剧本** |
| ADR-011 | 人格惯性 `ending_seen.last` 协议 |

详见 `docs/architecture/`。

---

## 11. 工作清单(写新角色 / 新场景前打钩)

- [ ] 角色注册在 `tree.start_node` 或 `characters.<id>.start_node`
- [ ] picker hub 节点存在,`_is_map_picker: true`
- [ ] ≥ 4 个地标,`connections` 邻接图至少覆盖一遍
- [ ] ≥ 2 个 `_is_tool: true` 工具节点
- [ ] ≥ 1 处 `effects.stay: true`
- [ ] ≥ 1 处 `narrative_variants` 反应切档
- [ ] 不引入新 flag 镜像伏笔/推论(查 `audit_state.py`)
- [ ] 主结局都有 `behavior_profile` / `*_resolved` / `flags` / `inv_has` 识别玩家
- [ ] 跨周目主结局有 `.last` 反咬(`audit_profile_inheritance`)
- [ ] `merge_fragments.py` 跑通,`audit_all.sh` 13/13 全绿

每一条都对应一个 audit 工具——audit 全绿 = 剧本进引擎不会崩、能玩出层次。
