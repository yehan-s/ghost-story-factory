# v7 Maze Story Kit · 用模板做新故事

> 把杭州·夜班外卖换成上海·外滩夜班 / 北京·胡同夜班 / 武汉·江堤夜班 / ......
> 不动引擎,不动 schema,只换内容资产。

---

## 0. 你在哪里

这份 kit 假设你已经:

- 玩过 v7 杭州故事(至少一个结局)
- 看过 `2026-05-07-v7-maze-master-spec.md`(总设计)
- 看过 `2026-05-07-v7-maze-completion-and-template-spec.md`(完善 plan)
- 知道什么是 narrative_variants / next_variants / 嵌套 require
- 准备好做 v8 多角色,或者做第二个城市的故事

---

## 1. 模板文件清单

```
docs/templates/v7_maze/
├── maze_node.schema.json              ← JSON schema(节点 / 选项 / require / effects)
├── shared_npc_template.json           ← 共享 NPC 节点模板
├── landmark_maze_template.json        ← 地标迷宫子图模板(15-25 节点结构)
└── maze_story_kit.md                  ← (本文件)使用指南

docs/superpowers/specs/
├── 2026-05-07-v7-maze-master-spec.md           ← 拓扑设计原则
├── 2026-05-07-v7-maze-completion-and-template-spec.md  ← 完善 plan
└── 2026-05-07-v8-character-roster-spec.md      ← 多角色 roster 草案
```

---

## 2. 开新故事的工作流(11 步)

### Step 1:写一份 master spec

放在 `docs/superpowers/specs/<日期>-<主题>-master-spec.md`,定义:

- 城市 / 时间段 / 主角职业
- 7 个地标(每个一句话主题)
- 8-10 个共享 NPC(每个一句话特征)
- 5-7 个共享场景
- 8 个结局(主结局)
- 风格指南(时间戳、人称、长度)

**核心要求**:这份 spec 完成时,任何 writer agent 拿到它,**不需要再问设计上的问题**。

### Step 2:lead 写头部 + 1 个标杆地标

类似 v7 的 S1 长椅 — 22 节点的标杆。其他 writer 必须模仿密度。

头部包括:
- `n_intro` — 主角入职 / 接到任务
- `n_briefing` — 任务说明 / 装备清单
- `n_landmark_picker` — 7 选 1 入口

### Step 3:lead 写 13 个共享 NPC + 7 个共享场景

照 `shared_npc_template.json` 把 13 个 NPC 写完。
每个 NPC ≥ 4 个 narrative_variants(根据从哪个地标来 / 玩家身上有什么)。

### Step 4:lead 写 8 主结局

每个结局 ≥ 3 个 narrative_variants(根据玩家行为差异)。

### Step 5:dispatch 6 个 writer agent 并行写其他 6 个地标

**重要**:writer agent 是 in-process,不跨 session。如果 lead session 中断,writer 会死。
所以 dispatch 前要确保 lead session 至少有 4-6 小时连续运行。

Writer prompt 模板(参考 v7 实际 dispatch):
```
你是 v7 maze writer,team `xxx`,负责写 **<S2 主题>** 完整迷宫。

## 必读
1. `<master spec 路径>`
2. `stories/<新故事>/_fragment_v7_landmark_s1.json` ← 标杆!严格模仿密度
3. `stories/<新故事>/_fragment_v7_shared.json`
4. `<lore 路径>`

## 输出
`stories/<新故事>/_fragment_v7_landmark_s2.json`

## 入口
`n_s2_arrive`

## 密度铁律(同标杆)
15-25 节点 / 每选项 2-4 层子选项 / ≥5 环 / ≥3 多入口 / ≥3 死胡同 / ≥4 跨流出口 / ≥1 narrative_variants

## 引用共享节点
- <主 NPC ID>
- <跨流 NPC IDs>
- <共享场景 IDs>
- n_landmark_picker

## 主题
<200 字主题描述>

## Style
第二人称,150-300 字,<时间戳>,感官细节(<具体感官 list>)

## 完成
JSON 合法 → SendMessage to "team-lead"。
开始。
```

### Step 6:整合

```bash
python tools/merge_fragments.py
```

应该看到:
```
找到 N 个 fragment:...
📊 节点统计:
   总节点数: ~150
   结局节点: ~17
   悬空引用: 0
   孤儿节点: 0
✅ 已写入 stories/<新故事>/tree.json
```

如果有悬空引用 / 孤儿,修。

### Step 7:跑 path_explorer

```bash
python tools/path_explorer.py stories/<新故事>/tree.json
```

确认:
- 所有 8 主结局可达
- 100% 节点覆盖
- PR/GR 边界 OK

### Step 8:补 narrative_variants 覆盖率

跑 hub 检测脚本(放在 `tools/find_hubs_without_variants.py`):
```python
import json
tree = json.load(open('stories/<新故事>/tree.json'))
nodes = tree['nodes']
in_degree = {nid: 0 for nid in nodes}
for nid, node in nodes.items():
    for c in node.get('choices', []) or []:
        if c.get('next'): in_degree[c['next']] = in_degree.get(c['next'], 0) + 1
hubs = [(d, nid) for nid, d in in_degree.items()
        if d >= 3 and not nodes[nid].get('narrative_variants')
        and not nodes[nid].get('is_ending')]
hubs.sort(reverse=True)
for d, nid in hubs: print(f'  入度 {d}: {nid}')
```

把找出的 hub 节点都加上 narrative_variants。

### Step 9:埋多角色伏笔槽

给关键悬念点的节点加 `_foreshadow_slot` 元数据(参考 `2026-05-07-v8-character-roster-spec.md` §1)。

### Step 10:实跑 5 条不同路径

人工跑(用不同选择策略),验证:
- 至少 3 个不同 ending 命中
- narrative_variants 触发条件确实生效
- 没有死循环 / 卡死

### Step 11:更新文档

- `stories/<新故事>/README.md` — 玩法 + 数据
- 项目根 `V7_PLAY_NOW.md`(如果是新主线)
- 提 PR

---

## 3. 关键不变量(任何故事都必须遵守)

| 不变量 | 检查方法 |
|---|---|
| 节点 ID 命名空间(`n_<land>_<sub>` / `n_npc_<who>` / `n_scene_<what>` / `n_end_<id>`) | grep 命名 |
| 0 悬空引用 | merge_fragments 输出 |
| 0 孤儿节点 | merge_fragments 输出 |
| 8 主结局全部可达 | path_explorer 输出 |
| 100% 节点覆盖 | path_explorer 输出 |
| 共享 NPC ≥ 4 narrative_variants | 人工或脚本检查 |
| 每地标 15-25 节点 | merge 后按 scene 字段 group_by 计数 |
| PR/GR ∈ [0, 100] | path_explorer 边界检查 |

---

## 4. 反模式(不要做)

- ❌ **写 narrative 时塞太多专有名词** — 玩家是第一次看,要让线索逐步浮现
- ❌ **选项立刻汇合到 picker** — 关键正面动作要有 payoff 节点
- ❌ **某个节点出度 = 1** — 除非是叙事单向通道(死路 / 结局门槛),否则给 ≥ 2 选项
- ❌ **narrative_variants 顺序写错** — 最具体的写最前,fallback 在最后
- ❌ **f-string 里写 JSON 例子** — Python 会把 `{"flag": true}` 解析成 `{"flag": <format spec ' true'>}`,直接报错。用静态字符串
- ❌ **改 player.py 来支持新功能** — schema 已经够用,新需求先在 narrative_variants 内表达
- ❌ **用 visited 判断 require** — 节点 visited 不进 require,只看 inv/flag/PR/GR(player.py 现状)
- ❌ **routes 字段** — v6 遗留,v7 不再使用。玩家通过状态自然分化
- ❌ **每加一个节点就跑 merge** — 太慢。一类节点全写完再 merge

---

## 5. 故事差异化设计(怎么让你的城市跟杭州不一样)

杭州·夜班外卖的核心 motif:
- **西湖水底** = 主体跨地标共享场景(几乎所有线都通过水)
- **「H = 1987」公式** = 时间常数恒等式(贯穿钟 / 帽 / 8 棺)
- **G-273 工号** = 主角与前任的镜像

新故事要找自己的 motif:
- 上海·外滩:外滩源 / 黄浦江打捞 / 1949 撤退档案?
- 北京·胡同:胡同迷宫 / 1976 唐山地震遗留?
- 武汉·江堤:武汉长江大桥 / 1998 抗洪殉职?

每个故事至少:
- 1 个**跨地标的水/光/声共享场景**
- 1 个**核心数字常数**(贯穿多个地标)
- 1 个**主角与前任的关系**

---

## 6. v8 升级点

如果开新故事时已经决定要支持多角色,Step 1 的 master spec 要多写一节:

```markdown
## 8 棺角色 roster
| 棺# | 年份 | 候选角色 | 解释的悬念槽 |
|---|---|---|---|
| 1 | <最早一任> | <ID> | <可解锁的伏笔列表> |
| ... |
| 9 | <现役> | <主角 ID> | (主线) |
```

并且在 Step 9 埋槽时,**精确对照**每个角色能解锁哪些槽。
