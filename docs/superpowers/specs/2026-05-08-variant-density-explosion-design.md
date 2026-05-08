# 变体密度爆破(Pass 3 候选首任务)— 设计文档

> Status: **Proposed**(等 spec-document-reviewer 通过 + 用户复核)
> Date: 2026-05-08
> 关联 ADR: ADR-007(状态空间契约) / ADR-008(戏剧化反应机制) / ADR-009(linmou 周目契约) / ADR-010(沙盒拓扑契约)

---

## § 0. Context

### 痛点

用户反馈"游戏一点沙盒味都没有,灵异和悬疑元素也不够"。Survey 后定位到具体表现:

> **同一节点反复进去,文本一模一样**(`visit_count` 维度上 variant 切档浅)

### 现状数据

- 144 节点中 47 个已有 `narrative_variants`(33% 覆盖)
- 入度 Top10 节点**全部已有** variants(`n_landmark_picker` in=57 / `n_scene_lake_underwater` in=15 / ...)
- `reaction_contracts`: deductions=3 / foreshadows=1 / themes=2(共 6 个,对 144 节点触发频率过低)
- flag 总量 73 / 75(剩 2 名额),其中 know.* 13,oneshot.* 46,arc.* 14
- linmou Act 1 仅 1 处反应 clause(ADR-009 § Sandbox Debt 已自承 "节点 = 单点决策机")

### 反直觉发现

variants **数量不稀疏**(平均 2-6 / 节点),问题在**触发条件交叉浅**。已有 variants 大多基于 reaction / flag 条件,**没有 visit_count 切档**——这正是用户痛点。

### 目标

不加 flag、不加节点、不加 reaction_contracts,**仅在现有热点节点 narrative_variants 列表头部插入 visit_count 切档 variants**,基于 4 vibe 信号(心理 / 物理 / 灵异 / 都市传说)分桶。

---

## § 1. 核心架构

### 数据结构(纯利用现有契约,零新字段)

```json
{
  "narrative_variants": [
    {"if": {"visit_count": {"min": 3}}, "text": "<vibe D: 都市传说底牌>"},
    {"if": {"visit_count": {"min": 2}}, "text": "<vibe C: 灵异密度>"},
    {"if": {"visit_count": {"min": 1}}, "text": "<vibe B: 物理被记住>"},
    {"text": "<vibe A: 心理新鲜 / default>"}
  ]
}
```

### vibe 桶映射规则(visit_count 单调递进)

| visit 桶 | 主 vibe | 写作锚点 |
|---|---|---|
| 0(初访 / default)| **A. 心理新鲜** | 第一人称感官 + 场景陌生感 + 1 个微细节 |
| 1(回访)| **B. 物理被记住** | 场景细节"留痕"(灯/门/物件位置变化)+ 内心一闪过的"咦,刚才不是这样" |
| 2(三访)| **C. 灵异密度** | 诡异密度升级(声响/影子/不对劲),仍维持"素净眼"风格 |
| 3+(沉浸)| **D. 都市传说底牌** | lore 内幕(羊符/铜锈/二轻物资/G-273 编号),一句"忽然懂了"的悟性句 |

### 判定顺序

引擎 `_meets_clause` 按列表顺序匹配,第一个 `if` 通过的 variant 胜出。所以列表必须**从 specific 到 general**(`min:3` → `min:2` → `min:1` → default)。

### Variant 列表全局顺序契约

写作时严格遵守(否则触发优先级混乱):

```
1. reaction 优先(deduction_resolved / foreshadow_resolved / theme_resolved / ending_seen)
2. flag 次之(know.* / oneshot.* / arc.*)
3. visit_count.min: 3 → 2 → 1(本次新增层)
4. default(无 if,兜底)
```

理由:reaction 是"剧情解开"语义最重;visit_count 是"次数"信号,排在后面兜补未触发剧情条件的回访场景。

### 契约一致性

- ADR-007 `visit_count` 已是节点派生字段,不新增
- 引擎 `_meets_clause` 已支持 `visit_count.min`(无引擎改动)
- audit_state / audit_reactions 不破坏(都不扫 visit_count 条件)
- ADR-010 沙盒契约:不增删节点,不动 picker / connections / stay,不破坏沙盒原语

---

## § 2. 节点选择 + 优先级

### Top 10 入度热点

| 优先级 | 节点 | 入度 | 现有 v | 类型 |
|---|---|---|---|---|
| **P0** | `n_landmark_picker` | 57 | 4 | G-273 picker hub |
| **P0** | `n_scene_lake_underwater` | 15 | 1 | 场景(湖底)|
| **P0** | `n_scene_lost_archive` | 13 | 6 | 场景(档案室)|
| **P0** | `n_npc_predecessor_voice` | 11 | 6 | NPC(前任声音)|
| **P1** | `n_l1985_landmark_picker` | 13 | 2 | linmou picker |
| **P1** | `n_npc_eight_self` | 11 | 5 | NPC(第八自己)|
| **P1** | `n_s1_arrive` | 10 | 4 | 场景(入口)|
| **P1** | `n_npc_red_dress_girl` | 9 | 5 | NPC(红衣女孩)|
| ~~P2~~ | ~~`n_npc_ghost_guard`~~ | 8 | ? | 推到 Pass 4 |
| ~~P2~~ | ~~`n_end_data`~~ | 8 | ? | 推到 Pass 4(ending 重访价值低)|

### MVP 范围(本次)

**P0 + P1 = 8 节点 × 4 visit 桶 = 32 variants**(~3 天写作)

`n_npc_ghost_guard` / `n_end_data` 推迟到 Pass 4,理由:
- ghost_guard ROI 待评估(入度第 9)
- ending 节点重访路径需要 endings_seen 跨周目联动配合(Approach 3 + reaction_contracts 扩展时再做)

---

## § 3. 数据流 + 写作模板 + Fragment 分布

### 8 节点 → 3 fragment 文件

| Fragment | 节点 | 现 v 数 |
|---|---|---|
| `_fragment_v7_shared.json` | `n_landmark_picker` / `n_scene_lake_underwater` / `n_scene_lost_archive` / `n_npc_predecessor_voice` / `n_npc_eight_self` / `n_npc_red_dress_girl` | 4 / 1 / 6 / 6 / 5 / 5 |
| `_fragment_v7_landmark_s1.json` | `n_s1_arrive` | 4 |
| `_fragment_v7_linmou_1985.json` | `n_l1985_landmark_picker` | 2 |

**重灾区**:`n_scene_lake_underwater` 仅 1 v(default),`n_l1985_landmark_picker` 仅 2 v(linmou Act 1 sandbox debt 具象表现)。

### 写作 → 验证流水线

每节点完工后跑一遍:

```bash
# 1. 编辑 _fragment_v7_*.json(在 narrative_variants 列表头部插入 visit_count variants)
# 2. 重 build
.venv/bin/python tools/merge_fragments.py --story-dir stories/hangzhou_yebanbaoan
# 3. 主 tree audit(预期 0 红线)
.venv/bin/python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json
# 4. linmou 路径 audit(预期 0 problems)
.venv/bin/python tools/audit_paths_linmou.py stories/hangzhou_yebanbaoan/tree.json
# 5. 全套回归(预期 259 passed)
.venv/bin/pytest --ignore=tests/test_story_generator_modes.py \
  --ignore=tests/test_pregenerated_mode.py \
  --ignore=tests/test_response_llmclient.py \
  --ignore=tests/test_choices_llm_wrapper.py \
  --ignore=tests/test_skeleton_generator.py \
  --ignore=tests/test_tree_builder_guided.py -q
```

### 写作模板(每节点 4 个 vibe variants 结构)

| vibe 桶 | 参考字数(±20% 浮动) | 必备元素 | 禁忌 |
|---|---|---|---|
| **A. 心理新鲜**(visit 0 / default)| ~80 (64-96) | 第一人称感官 + 场景陌生 + 1 个微细节 | 不剧透、不引用未发生事 |
| **B. 物理被记住**(visit ≥ 1)| ~100 (80-120) | 与 A 比"留痕"(灯/门/物件位置变化)+ "咦,刚才不是这样" | 不破第四面墙(不写"这是第二次了")|
| **C. 灵异密度**(visit ≥ 2)| ~120 (96-144) | 诡异升级(声响/影子/不对劲)+ 维持"素净眼"风格 | 不直接撞鬼(留 D 桶);不重复 B 的细节 |
| **D. 都市传说底牌**(visit ≥ 3)| ~150 (120-180) | lore 内幕(羊符/铜锈/二轻物资/G-273/1985-10-18)+ "忽然懂了"的悟性句 | 不直接交代谜底(留 ending 揭开)|

字数仅作参考,Lore Keeper 评审时**不按字数否决**,优先看必备元素 + 禁忌满足 + 文本质量。

### 一致性原则

1. **单调累积**:visit 2 看到的诡异 ⊇ visit 1 留痕 ⊇ visit 0 印象。不能 visit 2 比 visit 1 还轻。
2. **vibe 不互斥**:visit 1 文本里 70% 物理 + 30% 心理(玩家"咦"一下);visit 2 70% 灵异 + 20% 物理留痕 + 10% 心理麻木;visit 3+ 60% lore + 30% 灵异 + 10% 心理麻木。
3. **Lore 锚点白名单**:vibe D 引用元素必须在 `data/linmou_act1_lore.json`(linmou)/ `data/lore.json`(主)已有清单内,**不新增 lore**(否则 Lore Keeper 否决)。
4. **节点类型修饰**:NPC 节点 vibe 重在"NPC 反应玩家",场景节点 vibe 重在"场景反应玩家"。

### 错误处理

- variant 之间矛盾 → 按列表顺序(specific 优先),后面的不会触发
- visit_count 桶边界(visit=0 走 default,visit=1/2/3 各走对应桶)→ 引擎已支持
- 极端情况(visit=10+)→ 兜底走 visit≥3 桶,无新桶

---

## § 4. 测试与回归

### 自动化(已有套件,不写新测试)

每节点完工后必跑(已在 § 3 流水线):

| 测试 | 期望 | 角色 |
|---|---|---|
| `pytest -q`(259 用例)| 全过 | 全套回归 |
| `audit_reactions.py tree.json` | 0 红线 | 反应式 variant 死代码守门 |
| `audit_paths_linmou.py tree.json` | 0 problems | INV-1~5 全绿 |
| `path_explorer.py tree.json` | 8 主结局可达,孤儿/死路数量不上升 | 拓扑结构 |

### 人工(MVP 完成后)

| 项 | 方法 |
|---|---|
| visit_count 切档 smoke test(高入度) | 启 game,在 `n_landmark_picker` 反复回访 4 次,确认 4 vibe 文本依次出现 |
| visit_count 切档 smoke test(低入度) | 在 `n_s1_arrive` 反复回访 2 次,确认 visit=0(default A)/ visit=1(B)切档正确(避免高入度节点 visit_count 过早 ≥4 掩盖低桶 bug)|
| 一致性人审 | 通玩 1 条 E_TRUE 路径,记录每节点 4 vibe 是否单调累积 |
| linmou 联动 | 通 G-273 hidden truth → 进 linmou Act 1,确认 picker 触发跨周目 variant |

### 不写新自动化测试的理由

Pass 3 是**纯数据改动**(JSON variants 写作),引擎逻辑不变。已有 audit + pytest 套件足够守门。新写一致性自动化测试 = 用代码定义"vibe 单调"是 over-engineering(Linus 简洁原则)。

---

## § 5. 完整示例(以 `n_scene_lake_underwater` 为例)

### 改动前(1 v,只有 default 触发条件 oneshot.s1_jumped_lake)

```json
{
  "narrative_variants": [
    {
      "if": {"flags": {"oneshot.s1_jumped_lake": true}},
      "text": "你跳进西湖。\n\n你以为水会淹没你。\n\n水没有。\n\n你在湖底,可以呼吸。\n\n8 口 1987 年冷冻舱浮在水里,像 8 个透明灯笼。\n\n每口舱里,躺着一个你。"
    }
  ]
}
```

### 改动后(5 v,visit_count 4 桶 + 原 default 兜底)

```json
{
  "narrative_variants": [
    {"if": {"flags": {"oneshot.s1_jumped_lake": true}},
     "text": "你跳进西湖。\n\n你以为水会淹没你。水没有。\n\n你在湖底,可以呼吸。\n\n8 口 1987 年冷冻舱浮在水里,像 8 个透明灯笼。每口舱里,躺着一个你。"},

    {"if": {"visit_count": {"min": 3}},
     "text": "<vibe D 都市传说>第四次了。\n\n8 口冷冻舱里的'你',现在你看清了——他们身上都穿着二轻物资财务科 1985 款工装。\n\n胸口工号 G-273 的铜牌,锈成铜绿。\n\n你忽然想起师父说过:'西湖底下,锁着一个还没下班的人'。"},

    {"if": {"visit_count": {"min": 2}},
     "text": "<vibe C 灵异密度>第三次到湖底了。\n\n这次水底有声音——是老式半导体收音机的滋滋声,夹杂着新闻联播片头曲,但被水放慢了 30%。\n\n8 口舱里的'你'同时把头转过来,看你。\n\n他们的眼睛里都没有眼白。"},

    {"if": {"visit_count": {"min": 1}},
     "text": "<vibe B 物理被记住>你又一次站在湖底。\n\n第二次比第一次更冷。\n\n你注意到 8 口舱排列的位置变了——上次是圆形,这次是北斗七星加一颗。\n\n第八颗,正对你。"},

    {"text": "<vibe A 心理新鲜>你站在湖底。\n\n这是不可能的——但你站着。\n\n水从你周围 20 厘米处停下,像有看不见的玻璃罩着。\n\n8 口透明的舱子在水里慢慢飘,你不敢看舱里。"}
  ]
}
```

注:示例文本是**写作示范**,实际写作时由 lore canon 文档核校。`<vibe X>` 标签只是 spec 标注,**实际 JSON 不含**。

---

## § 6. 风险 / Out of Scope

### 风险

| 风险 | 等级 | Mitigation |
|---|---|---|
| 写作偏离 vibe(写飞)| 中 | 写作模板 + Lore 白名单 + Lore Keeper 评审 |
| 单调累积破坏(visit 2 比 visit 1 弱)| 中 | 一致性原则 § 3 钉死,人审兜底 |
| variant 列表顺序错乱(reaction 被 visit_count 截胡)| 低 | 列表顺序契约 § 1,merge_fragments 重 build 后 audit 不会报但要人审 |
| flag 名额耗尽(73/75 → 75/75 写作时不忍诱惑加新 flag)| 中 | spec 明示零新 flag,script-review-team 评审一票否决 |
| linmou Act 1 sandbox debt 误以为本任务偿还 | 高 | spec 明示**只补 variants 不补 connections / _is_tool**,sandbox debt 仍挂 ADR-009,Act 2 偿还 |

### Out of Scope(本任务不做)

- ❌ 加 reaction_contracts(deductions / foreshadows / themes)
- ❌ 加 flag(know.* / oneshot.*)
- ❌ 加节点(picker / NPC / 场景)
- ❌ 改 connections(linmou Act 1 沙盒债)
- ❌ 加 `_is_tool` 工具节点
- ❌ 改写 ending 节点 narrative(ending 重访意义需 Pass 4 配合)
- ❌ 任何引擎改动(`_meets_clause` / SaveManager / player.py)

---

## § 7. 验收标准

任务完成的可验证条件(Done = Done):

1. ✅ 8 节点(P0 + P1)narrative_variants 列表头部各加 4 个 visit_count variants,共 32 新 variants
2. ✅ `audit_reactions.py` 0 红线(DEAD_REACTION / UNREACHABLE_REACTION / DEAD_ENDING_SEEN 全 0)
3. ✅ `audit_paths_linmou.py` INV-1~5 全 0 problems
4. ✅ `pytest -q` 259 passed(无新增/删除测试)
5. ✅ `path_explorer.py` 8 主结局可达,孤儿数 / 死路数**不超过基线快照**(写作前跑 `path_explorer.py` 记录当前基线,验收时对比"不上升")
6. ✅ flag 总量 ≤ 75(零新增)
7. ✅ 节点数 144(零新增)
8. ✅ Lore Keeper 通过 vibe D variants(lore 锚点白名单内)
9. ✅ 人工 smoke test:n_landmark_picker 反复 4 次,4 vibe 文本依次出现

完成后:打 tag `pass3-task1-complete`,写完成报告 `docs/team-reviews/YYYY-MM-DD-pass3-completion.md`。

---

## § 8. 后续(Pass 3 后续 / Pass 4)

| 任务 | 优先级 | 触发条件 |
|---|---|---|
| Approach 3 体系扩展(reaction_contracts 6→12)| Pass 3.2 | 本任务 P0+P1 完工后 |
| `n_npc_ghost_guard` + `n_end_data` 补齐 | Pass 4 | endings_seen 跨周目联动 spec 出后 |
| linmou Act 1 sandbox debt 偿还(connections / _is_tool)| Pass 4 / Act 2 | ADR-009 Act 2 spec 出后 |
| 物件互动层(B 方向)| Pass 5 | linmou Act 2 上线时一并做 |
| 都市传说挖深(C 方向)| Pass 6 | lore canon 扩展决议后 |
