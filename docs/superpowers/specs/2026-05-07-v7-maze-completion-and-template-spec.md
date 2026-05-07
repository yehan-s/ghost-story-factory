# v7 Maze · 剧本完善与模板抽取 Spec

**日期**: 2026-05-07
**状态**: Active(team `ghost-v7-maze` 收尾阶段)
**Lead**: yehan + Claude Opus 4.7
**前置**: `2026-05-07-v7-maze-master-spec.md`

---

## 0. 文档目的(双重用途)

这份文档**既是 v7 剧本完善 plan,也是未来开新故事的脚手架**。

- **完善目的**:把 v7(《断桥残雪·夜班外卖》)从「可玩」推到「玩通后没有遗憾」。
- **模板目的**:抽出"换故事不换结构"的部分,以后做第 2、第 3 个城市夜班故事时,只换内容资产,不动引擎/工作流/拓扑约束。

读这份文档的人,可以是:
- 后续 session 的 Claude(继续干活的 lead)
- 未来 dispatch 的 v8 writer agent
- 用户自己(决定接下来玩还是继续推)

---

## 1. v7 当前现状(诚实诊断)

### 1.1 数据快照(2026-05-07)

| 指标 | 数 | 评价 |
|---|---|---|
| 总节点数 | 109 | OK(规划 150-200 上限) |
| 8 主结局 | 全部可达 | ✅ |
| 9 mini-ending | 全部可达 | ✅ |
| 节点 100% 可达 | 是 | ✅ |
| 0 悬空引用 / 0 孤儿 | 是 | ✅ |
| ending narrative variants 总数 | 32 | ✅ 多样性达标 |
| 共享 NPC variants 覆盖率 | 5/13 = **38%** | 🔴 不及格 |
| 共享场景 variants 覆盖率 | 1/7 = **14%** | 🔴 不及格 |
| 内部 loop hub variants 覆盖率 | ~4/20 = **20%** | 🟡 偏低 |

### 1.2 用户反馈(已识别痛点)

按优先级:

**痛点 1:选项太少 / 汇合太快 / 节点不够深**
- 某些"我不要 / 退回"选项立刻汇合到 `n_landmark_picker`(37 入边过载)
- S2-S6 地标节点数 16,低于 S1 标杆 22
- 部分分叉节点出度 ≤ 2,违反"每选项后 2-4 层子选项"原则

**痛点 2:narrative_variants 覆盖不全**
- 玩家从 S1 / S3 / S6 三个方向到达 `n_scene_lake_underwater`,看到的都是同一段水下文字(违反 v7 设计 — 共享节点必须区分"从哪里来")
- 共享 NPC 大部分没区分"哪个地标来的"
- loop hub 重访时 narrative 不变,丢失"你又回来了"的存在感

**痛点 3:多角色伏笔基础设施缺失**
- 用户**未来玩法**:多角色体验,A 视角不懂的事,B 角色玩时揭晓
- 现有 v7 的 8 棺(`n_npc_eight_self`)已经埋了 8 个不同年份的"另一个你",可作为多角色 roster
- 但现有 narrative 的"悬念点"没有标记 → 将来 B/C/D 角色想接入时,要重新通读全文找钩子,不可持续

---

## 2. 完善目标(可验证的成功标准)

完成后必须能通过以下验收:

| # | 验收项 | 怎么验证 |
|---|---|---|
| V1 | 共享 NPC variants 覆盖率 100% | grep `narrative_variants` × `n_npc_*` |
| V2 | 共享场景 variants 覆盖率 100% | 同上 × `n_scene_*` |
| V3 | 没有节点出度 < 3 (除死胡同 / ending) | path_explorer 自动输出 |
| V4 | 没有"立刻汇合到 picker"的非退出选项 | 人工审 + 标记 |
| V5 | 8 棺 roster 每个年份对应至少 2 个现有节点的伏笔钩子 | _foreshadow_slot 元数据交叉引用 |
| V6 | player.py 支持 character + meta_flags(默认值不破坏 v7) | 单元测试:不指定 character 时玩通 v7 与现状一致 |
| V7 | 模板文档可被新故事直接复用(只改命名,不改 schema) | 用模板生成"上海·外滩夜班"骨架,~30 节点能跑 |

---

## 3. 完善任务清单(顺序执行)

### Phase A — narrative_variants 补完(用户痛点 2)

> 这一阶段不动拓扑,只补文字。验证简单。

- **A.1** 给 8 个共享 NPC 加 `narrative_variants`,每个 NPC 至少 3 种 variant,根据「从哪个地标来」/「玩家身上有什么 inv」区分。
- **A.2** 给 6 个共享场景加 `narrative_variants`,同样根据来源 / 状态区分。
- **A.3** 给 ~16 个内部 loop hub 节点(`n_<landmark>_<sub>` 中入度 ≥ 3 的)加重访 variants,反映"你刚才已经走过这里"。
- **A.M** merge + path_explorer 验证(每完成一类后跑一次)。

### Phase B — 深度加密(用户痛点 1)

> 这一阶段动拓扑,要谨慎。

- **B.1** path_explorer 增加 "出度分布"输出,识别出度 < 3 的非死胡同节点(预计 10-20 个)。
- **B.2** 人工审查每个 "退回 picker" 选项 — 如果选项的语境是"放弃整个地标",保留;如果只是"退回看看",改成回到地标内某个 hub。
- **B.3** 给 S2-S6 各加 4 节点(从 16 增到 20),专补"选 X 后还能选 X.a/X.b/X.c"的子树空间。S1 22 节点为标杆不动。
- **B.M** merge + path_explorer 验证 + 实跑取样(随机 5 条路径)。

### Phase C — 多角色伏笔基础设施(用户痛点 3)

> 只留接口,不写内容。给 v8 多角色铺路。

- **C.1** `player.py.State` 加字段:`character: str = "G-273"`、`meta_flags: dict = {}`。
- **C.2** require schema 扩展支持 `character`、`meta_flags`。所有现有 require 缺省时仍然 match(向后兼容)。
- **C.3** `tree.json` 顶层加 `characters` 字段,定义每个未来角色的 `start_node`、`initial_inv`、`initial_flags`。v7 默认 `G-273` 起点 `n_intro`。
- **C.4** 给现有节点的"悬念点"加 `_foreshadow_slot` 元数据(player 忽略,人类可读)。例如:
  ```json
  {
    "narrative": "...账本里 27 笔贪污款,只有第 13 笔是我做的。其他 26 笔,是另一个人...",
    "_foreshadow_slot": ["1985_linmou_other26"],
    "_foreshadow_solved_by": "C_linmou_route"
  }
  ```
- **C.5** 8 棺 roster 详细规划文档 — 每个年份对应未来角色的设计草图。

### Phase D — 模板抽取(可复用)

> 把「换故事不换结构」的部分剥出来。

- **D.1** 抽取节点结构 schema 到独立文件 `templates/maze_node.schema.json`。
- **D.2** 抽取共享 NPC 设计模板:每个 NPC 必有 4-6 个 variants,3 个 choice 出口分别通向 a) 给 puzzle/inv b) 引向另一共享场景 c) 回到 picker。
- **D.3** 抽取地标迷宫子图模板:入口 + 3 主选项 + 每主选项至少 2-3 子选项 + ≥1 mini-ending + ≥4 跨流出口。
- **D.4** 写《用 v7 模板做新故事》指南,放在 `docs/templates/maze_story_kit.md`。

---

## 4. 设计模板(可复用部分)

> 以下是模板,跟具体故事(杭州 / 夜班外卖)无关。

### 4.1 节点命名空间(铁律)

```
n_<landmark>_<sub>     # 地标内部节点,如 n_s1_pocket_book
n_npc_<who>            # 共享 NPC,可被多地标到达
n_scene_<what>         # 共享场景,跨地标
n_end_<id>             # 结局
n_<role>_<sub>         # (v8 多角色预留)非主角节点,如 n_linmou_drown
```

### 4.2 真迷宫子图模板(每地标必满足)

```
入口节点 n_<land>_arrive
  ├── A. <主探索选项> → A1 → A1.a / A1.b / A1.c
  ├── B. <对抗/挑战选项> → B1 → B1.a / B1.b
  ├── C. <礼物/拾取选项> → C1 → 共享 NPC
  └── D. <跳过> → n_landmark_picker

环结构(必有 5 种中的 3 种):
  ① 状态环回:深选项 → 入口(narrative_variants 反映状态)
  ② 跨地标出口:深选项 → 另地标深节点
  ③ 共享 NPC 入口:多选项 → 同一 n_npc_*
  ④ 死胡同 / mini-ending:不可逆死亡分支
  ⑤ 多入口汇合:某节点 ≥3 入边
```

### 4.3 narrative_variants 模板

```json
{
  "narrative": "<默认文本(第一次到达 / 全部条件不满足时)>",
  "narrative_variants": [
    {"if": {"flags": {"<from_landmark_X>": true}}, "text": "<从 X 进来时的版本>"},
    {"if": {"flags": {"<from_landmark_Y>": true}}, "text": "<从 Y 进来时的版本>"},
    {"if": {"inv_has": ["<key_item>"]}, "text": "<手里有钥匙物时的版本>"},
    {"if": {"meta_flags": {"<played_as_role_B>": true}}, "text": "<玩过 B 角色后的揭晓版本>"}
  ]
}
```

**铁律**:variants 按顺序匹配,**最具体的写最前**。最后是默认 narrative。

### 4.4 伏笔槽元数据规范(为 v8 多角色铺路)

```json
{
  "narrative": "...含悬念的文本...",
  "_foreshadow_slot": ["<slot_name_1>", "<slot_name_2>"],
  "_foreshadow_solved_by": "<role_name>_route"
}
```

- `_foreshadow_slot`:这段文字里的悬念点(列表)。例如 `"1985_linmou_other26"`。
- `_foreshadow_solved_by`:玩哪个角色能解释这个悬念。
- player.py **忽略**这些字段,不影响玩法。
- 人类(包括未来的 lead/agent)用 grep 就能找到所有伏笔槽,做一致性检查。

### 4.5 8 棺多角色 roster 模板

```
n_npc_eight_self 节点列出 8 + 主角 = 9 个不同年份的"你"
每个棺对应一个未来可玩角色:

棺# | 年份 | 候选角色      | 解释的悬念槽
1   | 1980 | G-早任       | (待定)
2   | 1985 | 林副科长     | 1985_linmou_other26 / 1986_lin_coin
3   | 1986 | 沉船工人     | 1986_lin_coin / 1986_no_eighth
4   | 1987 | 踩踏死者 13  | 1987_red_dress_truth
5   | 1991 | 叶某         | 1991_yeh_classmate
6   | 1996 | 红衣女孩     | 1996_red_girl_truth
7   | 1998 | G-某         | (待定)
8   | 2009 | G-某         | (待定)
9   | 2024 | G-273 赵某   | 主角,埋槽
```

每个候选角色的设计需独立 spec,不在本文档展开。

### 4.6 角色定义模板(v8 预留)

```json
{
  "characters": {
    "G-273": {
      "label": "赵某 · 现役夜班保安",
      "start_node": "n_intro",
      "initial_inv": [],
      "initial_flags": {}
    },
    "linmou_1985": {
      "label": "林副科长 · 1985-10-18 投湖前夜",
      "start_node": "n_linmou_office",
      "initial_inv": ["林副科长账本完整版", "钢笔"],
      "initial_flags": {"is_linmou": true, "year": 1985}
    }
  }
}
```

---

## 5. 验收 / 测试

每个 Phase 完成后,跑:

```bash
python tools/merge_fragments.py                                    # 合并 + 引用完整性
python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json # 全路径分析
echo "q" | GHOST_FAST=1 python play.py                             # 启动冷启动测试
```

每个 Phase 还要额外通过自定义验收(见 §2 V1-V7)。

---

## 6. 不在范围

- v8 多角色**实际实现**(只留 schema 接口、伏笔槽元数据)
- UI / 存档 / 多故事框架
- LLM 在线生成
- 真正写第二个城市的故事(只验证模板可用)

---

## 7. 风险与缓解

| 风险 | 缓解 |
|---|---|
| Phase A variants 写作量爆炸 | 分批做,A.1 → A.2 → A.3,每批合并测一次 |
| Phase B 加深度引入新孤儿节点 | 每次 merge 后立刻 path_explorer |
| Phase C schema 改动破坏 v7 | character 缺省值 "G-273",所有 require 缺字段时自动 pass |
| 模板抽取过早(D 阶段) | 先完成 A+B+C,然后再做 D。D 不阻塞 v7 玩通 |
| 用户中途反悔多角色玩法 | Phase C 只动 schema 不写内容,沉没成本可控 |

---

## 8. 执行顺序(本次直接开始)

```
现在 → A.1 共享 NPC variants(8 个 NPC)
     → A.M 验证
     → A.2 共享场景 variants(6 个场景)
     → A.M 验证
     → A.3 loop hub variants(~16 个节点)
     → A.M 验证
     → B.1 出度分析
     → B.2 退回选项审查
     → B.3 S2-S6 加密
     → B.M 验证
     → C.1-C.5 多角色 schema + 伏笔槽
     → C.M 验证
     → D.1-D.4 模板抽取
     → 完工
```

每完成一个 sub-task,都更新 todo list,跑相关验证。
