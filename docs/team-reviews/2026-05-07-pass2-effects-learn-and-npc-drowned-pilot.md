# 2026-05-07 Pass 2 首任务候选 — `effects.learn` 知识反馈条 + 试点 NPC `n_npc_drowned_official`(林副科长)

> 评审团:script-review-team
> 任务 slug:pass2-effects-learn-and-npc-drowned-pilot
> 报告生成时间:2026-05-07

---

## § 1. 任务描述

Pass 2 首任务候选,两件事打包:

1. **`effects.learn` 知识反馈条**:玩家通过对话/物件/推理获得新知识(`know.*` flag)时,UI 弹一行可见反馈,
   让"我知道了什么"从隐式 flag 变成玩家可感知的体验。
2. **试点 NPC `n_npc_drowned_official`(林副科长)**:用 4-variant `narrative_variants`
   矩阵实现"NPC 对玩家已知信息的渐进反应",作为 Pass 2 沙盒方向的一个完整 NPC 样例。

**任务影响范围**:多层(剧本 + 引擎 + UX + lore)

依据上游决策:
- ADR-007(状态契约,Pass 1 已落地 71 flags / 6 命名空间)
- `docs/team-reviews/2026-05-07-linmou-arc.md`(林孟 1985 周目设定)
- `docs/team-reviews/2026-05-07-dramatic-reaction.md`(伏笔/推论/母题契约)

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与

**层级判定**:多层(剧本 + 引擎 + UX + lore)

**意见**:

任务方向正确——把"知识获得"从隐式 flag 升格为玩家可感知的体验,是 Pass 2 沙盒化的关键一步。
但在落地细节上,六位评审有两处显著分歧需要 Chief Editor 决议;
另外 4 variant 矩阵和反馈条文案需要把六人意见 **合并成单一可执行规范**,否则实施会跑偏。

**剧情连续性风险**:

- **真相唯一可解性**:V4(小赵切换)是 1985 真相揭示节点,必须经过 deduction 节点而非单一 know flag 触发,
  否则元游戏作弊。Lore Keeper 红线必须接受。
- **报纸 1985-10-19 信源链**:`know.linmou_corruption` 必须有报纸前置,否则知识凭空出现。
- **首次 vs 复读**:玩家二次进入不应被二次"教学",否则破坏 1985 沉浸。

**产出**:

见 § 9 综合建议——四 variant 矩阵 + 反馈条文案规则 + 三个冲突的处理方案。

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与

**意见**:

复用 `set_flags` + `know.*` 命名空间识别机制,**不新增 `effects.learn` 字段**。
引擎在 `apply_effects` 检测 `flag.startswith("know.")` 且 false→true 瞬时跳变时弹反馈条,
重复 set 静默。`reaction_contracts` 不扩字段,`know.*` 已能通过 `_meets_clause` 引用,
`deduction_resolved` 是推理闭环语义层,职责不同,不能混用。

**生命周期**:`know.*` 一经 set 永不 unset(知识不可遗忘),
跨周目继承走 `profile.learned`,周目内走 `current_run.learned`,二者分桶。

**产出**:

- 新增 flags:**0 个**(零新增字段是底线)
- 引擎扩展需求:
  - `apply_effects` 增加"`know.*` false→true 跳变 → emit `KnowledgeLearned` 事件"
  - 事件走现有 effects pipeline,不引入新字段或新表
- 红线:
  - **R-S1**:反馈条只在 `know.*` false→true 跳变时弹
  - **R-S2**:禁止新增 `effects.learn` 字段(命名易引入"`learn` 是新维度"的错觉)

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:深度参与

**意见**:

- **剧透风险**:反馈条文案(如 `▌ 知道 · X ▐`)= `know.X` 字面值,**禁止携带"未来可解锁"暗示**,
  否则破坏发现感。
- **复读问题**:必须区分 `first_learn`(弹) / `re_learn`(静默)。
  `current_run.learned`(周目内)与 `profile.learned`(跨周目)分桶,二者解耦。
- **CG Codex 接口**:林试点应通过独立 **`met.*` 信号**(如 `met.n_npc_drowned_official`)
  与 `know.*` 解耦,否则 Codex 后续要清洗数据。

**产出**:

- 周目机制变更:无(反馈条只是切面,不是新维度)
- 收集本(Codex)调整:
  - 新增"已遇 NPC"分组,信源 = `met.*`(下游决议为 `visit_counts > 0` 派生,见 § 9 冲突 1)
  - 知识条目分组,信源 = `know.*`
  - 二者**解耦**,Codex 不可只接 `know.*`
- true ending 解锁条件变化:无(本任务不动结局门)
- 红线:
  - **R-M1**:首次 vs 复读必须区分,引擎层判定
  - **R-M2**:NPC "已遇" 信号与 "知识"信号分桶——具体实现路线见 § 9 冲突 1 决议

---

## § 5. UX Designer — 文字体验设计师

**相关度**:深度参与

**意见**:

- **字符规范**:`▌▐` 是 HUD 风格,过重,不贴 1985 夜班质感。推荐 `· 记下了:X ·`(中点柔和),
  备选 `〔记下〕X`(更书面)。否决游戏化符号。
- **位置**:正文段落结束后**独占一行**,左缩进 2 字符,灰色(dim)。**不要**状态栏 / 浮窗 / 弹窗。
- **时长**:**常驻不淡出**(玩家自己翻页);重复触发降级到 1 秒淡出 `· 已知 ·`。
- **节奏**:正文打字结束 → 停顿 400ms → 反馈条**整行淡入(不逐字打字)**,与正文区别开。
- **林副科长 variant 切换**:玩家**不应感知切换**。同一选项 2 次进入显示完全不同文本会碎沉浸。
  建议 variant 只在不同 `know` 前置满足时切换,**反馈条只弹"新增"知识**,这样切换隐形。
  否则 4 variant 砍到 2 个。

**产出**:

- TUI/CLI 草图:

  ```
  林副科长抿了口冷茶,没看你。
  "那晚……算了,不说了。"

    · 记下了:林副科长在隐瞒什么 ·
  ```

- 排版规范:
  - 反馈条独占一行,首行缩进 2 字符,灰色(`dim` style)
  - 不与正文混排,不出现在状态栏 / 浮窗
  - 节奏:正文结束 → 400ms 停顿 → 反馈条整行淡入
  - 重复触发:1 秒淡出 `· 已知 ·`,不阻塞正文
- 玩家旅程节点:
  - 入口:对话节点 / 物件检视 / 推理结算
  - 关键节点:`know.*` flag 写入 → 引擎检测 false→true → emit `KnowledgeLearned`
  - 反馈循环:UI 接事件 → 渲染反馈条
- 红线:
  - **R-U1**:视觉必须降级(dim + 缩进),不抢正文戏
  - **R-U2**:首次 vs 重复必须 UI 层区分(常驻 vs 1 秒淡出)

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与

**意见**:

- **4 variant 锚点**:
  - **V1 陌生**(`visit_count == 1` 且无任何 `know.linmou_*`):
    "小同志,这么晚还在转?"——客气但保持距离
  - **V2 见过遗物**(`know.linmou_badge` ∨ `know.linmou_archive_1985`):
    "小鬼,你翻那箱子做什么"——警觉,降辈分压制
  - **V3 知贪污**(`know.linmou_corruption` + `know.read_newspaper_1985_10_19`):
    "……报纸都登了。小同志,你说我冤不冤?"——自辩,情绪软化
  - **V4 解开真相**(`deduction.predecessor_loop == "resolved"`):
    "……小赵。这次轮到你了"——**唯一切换点,必须 V3 + deduction 双解**
- **唯一可解性铁律**:V4 中"小赵"称呼 ≠ know flag 单触发,**必须经过 deduction 节点**完成推理闭环。
  这是 1985 真相揭示的最后一道关,绝不可省略。
- **1985 代词规范**:小同志 / 小鬼 / 小赵;禁用"同志"(平辈,违反辈分)、"小张"(玩家姓赵,锚点表确认)。
- **报纸 1985-10-19** 是 V3 的解锁前置,否则"贪污"知识无信源 = 元游戏作弊。
- **反馈条污染**:🔴 `▌▐` 等游戏化符号在 1985 夜班保安视角下违和。
  夜班保安没有"知识条目"的元概念,改为 1985 物件落地——**"(你在值班记录本上记下:X)"** 或
  **"档案补遗 · X"**——以 1985 文物为载体。

**产出**:

- 新增元素考据清单:
  - 值班记录本(夜班保安每晚必填,1985 单位制硬通货,作为反馈条隐喻载体合理)
  - "档案补遗"(单位档案室术语,V2/V3 触发后可用)
  - 林副科长辈分代词(小同志/小鬼/小赵)
- lore 不一致警告:
  - 严禁"同志"(平辈)和"小张"(姓氏不符)
  - V4 不可绕过 deduction 节点
- 命名建议:
  - `n_npc_drowned_official` 内部 ID 保留,玩家可见名"林副科长"
  - 反馈条载体:值班记录本(默认) / 档案补遗(V2/V3 知识)
- 红线:
  - **R-L1**:🔴 V4 小赵切换必须经过 deduction 节点(`deduction.predecessor_loop == "resolved"`)
  - **R-L2**:🔴 反馈条禁用游戏化符号(`▌▐` / `[get]` 等),必须落到 1985 物件

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:深度参与

**意见**:

**反对引入 `learn` 新字段**。`know.*` 已经是命名空间,`learn` 只是 `set_flags` 的可观测切面,
不是状态维度。**零新增字段、零新增持久化维度**是 Pass 2 的底线——Pass 1 把 flag_total 从 234 砍到 71,
绝不能在 Pass 2 第一刀就反弹。

**可达性**:4 variants 必须有 fallback variant(无任何 `know` 前置时也能触发),否则首次访问卡死。
若 `path_explorer` 在新林试点上 variant 命中率 < 80%,视为拓扑塌陷,必须回滚。

**产出**:

- 节点结构变更:
  - `n_npc_drowned_official` 节点扩 4 variants(V1-V4),无新增节点
  - V1 = fallback,引擎在所有前置不满足时必须命中 V1
- 状态维度调整:
  - 全局维度:0 新增(`know.*` 复用,`met` 信号派生,见 § 9 冲突 1)
  - 局部维度:0 新增
- 可达性证明:
  - V1:`visit_count == 1` 且无 `know.linmou_*` → 必命中(fallback)
  - V2:`know.linmou_badge` ∨ `know.linmou_archive_1985` → 已存在 set 点(从 archive 节点)
  - V3:`know.linmou_corruption` ∧ `know.read_newspaper_1985_10_19` → 报纸节点是前置
  - V4:`deduction.predecessor_loop == "resolved"` → 已有 deduction 节点
  - 所有 variant 的 require 都能从现有节点 set 端到达,无新增 set 点除 `asked_predecessor_name`(补在 V2)
- 红线:
  - **R-T1**:flag_total = 71 是底线,Pass 2 只能降不能升
  - **R-T2**:必须有 fallback variant(V1),`path_explorer` 命中率 ≥ 80%
  - **R-T3**:`asked_predecessor_name` 的 set 点补在林副科长 V2(玩家追问"前任是谁"分支)

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与

**意见**:

- **可观测性**:不要 stdout grep(脆弱)。在 `apply_effects` 的 `know.*` 写端 emit 事件
  `KnowledgeLearned(key, source_node, is_first_time)`,测试用 event capture 断言,TUI 反馈条单独 snapshot 测试。
- **新单测**:必须新增 4 variant 单测——构造 4 套前置 flag 集 → 跑 picker → 断言命中预期 variant_id。
  fallback 单测必须存在(空 flag 集 → 命中 V1)。
- **`audit_paths_linmou` 扩 INV-5**:林试点不得让 `linmou_dead == False` 通过结局门——林必死零退让。
- **回归套件**:高危 `test_audit_reactions` / `test_path_explorer`(基线漂移敏感)。
  新入口:`tests/test_effects_learn.py` + `tests/test_npc_drowned_official_variants.py`。

**产出**:

- 测试路径序列:
  - 路径 A(V1 fallback):空 flag → 访问林副科长 → 断言 variant_id == "V1"
  - 路径 B(V2 警觉):set `know.linmou_badge` → 访问 → 断言 variant_id == "V2",反馈条只弹 1 次
  - 路径 C(V3 自辩):set `know.linmou_corruption` + `know.read_newspaper_1985_10_19` → 断言 V3
  - 路径 D(V4 真相):路径 C 之后过 deduction 节点 → 断言 V4 + 出现"小赵"称呼
  - 路径 E(复读):任意 variant 二次访问 → 断言反馈条静默(re_learn 路径)
- Bug 清单(分等级):
  - **阻断**:V4 不经 deduction 直接由 know flag 触发(若发生)
  - **阻断**:`linmou_dead == False` 通过任何结局门
  - **严重**:variant 命中率 < 80%
  - **严重**:首次/复读判定失误(re_learn 弹反馈)
  - **一般**:反馈条字符样式偏离规范
- 回归测试入口:
  - `pytest tests/test_audit_reactions.py`(基线)
  - `pytest tests/test_path_explorer.py`(基线)
  - `pytest tests/test_effects_learn.py`(新)
  - `pytest tests/test_npc_drowned_official_variants.py`(新)
  - `python tools/audit_paths_linmou.py`(扩 INV-5 后)
- 红线:
  - **R-Q1**:`audit_paths_linmou` INV-1~INV-5 全绿,林必死零退让
  - **R-Q2**:192 测试不变红;variants 触发率 ≥ 36.9%(基线),目标 > 40%
  - **R-Q3**:所有断言走 event capture,禁止 stdout grep

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行**

任务方向六人共识——把"知识获得"从隐式 flag 升格为可感知的体验是 Pass 2 沙盒化的正确切入,
试点 NPC 林副科长选得也精准(已有 4 个不同知识层级 + deduction 节点,天然适配 variant 矩阵)。
但落地前必须先解决三个冲突 + 锁定四份合并规范,否则实施会跑偏。

---

### 决议:三个冲突的处理方式

**冲突 1:Meta 主张加 `met.*` flag vs Topology 反对总量上升**

→ **采用折中方案 ③:用 `visit_counts[node_id]` 派生 `met` 信号**

**理由**(Linus 第一准则——消除特殊情况优于增加新维度):
- `visit_counts` 是 Pass 1 已存在的运行时数据,**零新增字段**,满足 Topology 的 R-T1 红线
- Codex 接 `visit_counts.get(node_id, 0) > 0` 即可判定 "met",**与 `know.*` 物理解耦**,
  满足 Meta 的 R-M2 红线
- 派生方式不影响周目继承——`profile.met_npcs` 单独从 `visit_counts` 在周目结算时聚合
- 拒绝方案 ①(加 `met.*` flag):违反 R-T1,在 Pass 1 减负成果上反弹,代价过高
- 拒绝方案 ②(只接 `know.*`):违反 R-M2,Codex 数据耦合,后续要清洗

**契约**:
- Codex "已遇 NPC" 信号 = `runtime.visit_counts.get(npc_node_id, 0) > 0`
- Codex "知识条目" 信号 = `state.flags.get("know.X", False)`
- 两者派生路径不同,语义解耦

**冲突 2:UX 主张 4 variant 切换玩家不应感知 vs Lore 给 4 variant 完整矩阵**

→ **不冲突,合并采纳**

Lore 的 4 variant 各由不同 `know` / `deduction` 前置触发,UX 的"反馈条只弹新增知识"
正好实现"variant 切换隐形"——玩家感知的不是"NPC 切换台词",而是"我学到了新东西所以 NPC 反应不同"。
两份意见在实施层面是同一件事的两个角度。

**冲突 3:反馈条文案——UX(`· 记下了:X ·`)vs Lore(`(你在值班记录本上记下:X)`)**

→ **采用 Lore 方案为主,UX 方案为简化备选**

文案规则见下方"反馈条文案规则"小节。

---

### 4 variant 矩阵 if 条件(综合 Lore + State + Topology)

```
n_npc_drowned_official.narrative_variants:

  V4 (小赵真相):
    when: deduction.predecessor_loop == "resolved"
    text: "……小赵。这次轮到你了"
    优先级: 最高(Lore R-L1 红线,必须经 deduction)

  V3 (自辩):
    when: know.linmou_corruption == True
       AND know.read_newspaper_1985_10_19 == True
    text: "……报纸都登了。小同志,你说我冤不冤?"

  V2 (警觉):
    when: know.linmou_badge == True
       OR  know.linmou_archive_1985 == True
    text: "小鬼,你翻那箱子做什么"
    set_flags: { asked_predecessor_name: True }  # Topology R-T3:此处补 set 点

  V1 (陌生 / fallback):
    when: <无前置,缺省命中>
    text: "小同志,这么晚还在转?"
```

picker 顺序:V4 → V3 → V2 → V1(从严到松,首个匹配命中)。
fallback V1 必须存在,否则 `path_explorer` 命中率塌陷(Topology R-T2)。

---

### 反馈条文案规则(综合 UX + Lore + Meta)

**载体优先级**(从 Lore 1985 物件出发):

1. **默认载体**:值班记录本
   - 文案模板:`(你在值班记录本上记下:{know_text})`
   - 视觉:独占一行 / 左缩进 2 字符 / 灰色(dim)/ 整行淡入

2. **档案知识**(`know.linmou_archive_*` / `know.linmou_corruption` 等单位档案类):
   - 文案模板:`档案补遗 · {know_text}`
   - 视觉:同上

3. **复读触发**(re_learn 路径):
   - 文案模板:`(已知 · {know_text})`
   - 视觉:1 秒淡出(不常驻)

**禁用清单**(Lore R-L2):
- ❌ `▌ 知道 · X ▐` 等 HUD 游戏化符号
- ❌ `[get]` / `[unlock]` 等英文标签
- ❌ 携带"未来可解锁"暗示的文案(Meta 剧透红线)

**节奏规则**(UX R-U1 / R-U2):
- 正文打字结束 → 400ms 停顿 → 反馈条整行淡入(**不逐字**)
- 首次:常驻不淡出,玩家翻页时随正文消失
- 复读:1 秒淡出 `(已知 · X)`

**事件源**:`apply_effects` 在 `know.*` flag 发生 false→true 跳变时
emit `KnowledgeLearned(key, source_node, is_first_time)`(State R-S1)。
UI 层订阅事件渲染,不读 flag 字典。

---

### 测试门槛(综合 QA + Topology)

**必须新增**:
- `tests/test_effects_learn.py`——`KnowledgeLearned` 事件 capture 断言,
  覆盖 first_learn 弹 / re_learn 静默两条路径
- `tests/test_npc_drowned_official_variants.py`——4 variant + fallback,共 5 条用例
- `tools/audit_paths_linmou.py` 扩 **INV-5**:林必死零退让
  (任何路径上 `linmou_dead == False` 通过结局门 = 红线触发)

**必须保持**:
- 192 现有测试不变红
- `path_explorer` variant 命中率 ≥ 80%(目标 > 40% 全局触发率,基线 36.9%)
- flag_total ≤ 71(R-T1 底线,只能降不能升)

**禁止**:
- stdout grep 类断言(QA R-Q3)

---

### 关键风险清单(实施前必须先调整)

按严重度排序,**全部解决后才能进入编码**:

1. **🔴 V4 小赵切换必须经 deduction 节点**
   (Lore R-L1 + State 推理闭环语义)
   - 实施前确认:`deduction.predecessor_loop == "resolved"` 是 V4 的**唯一**触发条件,
     不可由任何 `know.*` 单 flag 替代
   - 风险后果:绕过 deduction 直接由 know 触发 = 1985 真相元游戏作弊,Lore 一致性破产

2. **🔴 反馈条禁用游戏化符号,落到 1985 物件**
   (Lore R-L2 + UX R-U1)
   - 实施前确认:文案模板严格按"反馈条文案规则"小节执行
   - 风险后果:`▌▐` 类符号让 1985 夜班保安视角碎裂,沉浸感破产

3. **🔴 零新增字段,Codex `met` 信号走 `visit_counts` 派生**
   (Topology R-T1 + 冲突 1 决议)
   - 实施前确认:不引入 `met.*` flag,不引入 `effects.learn` 字段,
     Codex 接 `visit_counts.get(node_id, 0) > 0`
   - 风险后果:Pass 1 减负成果反弹,flag_total 突破 71

4. **🟡 fallback V1 必须存在,picker 顺序 V4→V3→V2→V1**
   (Topology R-T2)
   - 实施前确认:V1 缺省命中,`path_explorer` 命中率 ≥ 80%

5. **🟡 首次 vs 复读必须引擎层判定,UI 层只订阅事件**
   (State R-S1 + Meta R-M1 + UX R-U2)
   - 实施前确认:`KnowledgeLearned` 事件携带 `is_first_time` 字段,
     UI 层不查 flag 字典自己判断

6. **🟡 `asked_predecessor_name` 的 set 点补在林副科长 V2**
   (Topology R-T3 + Pass 1 残留 5 个孤儿 require key 之一)
   - 实施前确认:V2 的 `set_flags` 包含 `asked_predecessor_name: True`,
     Pass 1 完成报告中的孤儿 require 清掉一个

7. **🟡 林必死零退让,`audit_paths_linmou` 扩 INV-5**
   (QA R-Q1)
   - 实施前确认:扩展 INV-5 + 加入回归套件

---

### 后续动作

- 用户接到本报告后,确认决议,然后进入 **`writing-plans`** 写 Pass 2 首任务实施计划
  (拆 ADR / state 引擎扩展 / tree.json patch / 新单测 / `audit_paths_linmou` 扩展 / TUI 反馈条 6 个 PR/commit 范围)
- 实施计划必须把上方"关键风险清单 7 条"逐条映射到 acceptance criteria
- 实施过程中若任一红线松动,QA / State / Lore 三方任一可拉回评审

### 不同意见记录

- **UX**:若 4 variant 在实施中发现切换感无法隐形(玩家 A/B 测试感受到台词替换),
  保留"砍到 2 variant"的回退方案,但需重新走一轮评审,不在本任务实施期内自决
- **Meta**:对 `met` 信号走 `visit_counts` 派生方案接受,但提醒——Codex 后续若需要"已遇但未对话"
  与"已对话"的细分,`visit_counts` 单维度可能不够,届时再评估是否升级数据结构(本任务范围外)
