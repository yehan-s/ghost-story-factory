# 2026-05-14 地图玩法契合度 + UX 痛点深调研

> 评审团:script-review-team
> 任务 slug:map-ux-deep-dive
> 报告生成时间:2026-05-14(路线调研型,非实现任务)

---

## § 1. 任务描述

用户原话:**"你来持续收尾,并且从多方面深入给我接下来方案,比如地图功能,我觉得没有深度契合玩法,并且 UX 方面极其差劲,你来给我调研"**

这是在上一份评审(`2026-05-14-next-wave-direction.md` 推荐 Pass 27/28/29)放行**之后**追加的更深层关切。评审团本轮任务 = **主动挖掘症状,定位首次玩家投诉的真根因,提出方向**。

**任务影响范围**:**多层 — 引擎(map_view 渲染层 + picker_choices 逻辑)+ UX(TUI 表达密度)+ 剧本(picker 节点 variants 分布)**

### 评审团对用户原话的诊断结果

经过 657 行 `map_view.py` + 24 picker variants 触发条件分布 + 首次开局 known_landmarks 范围实测,**用户的不满有四个具体根因**(非"功能缺失"):

| 根因 | 实测证据 | 用户感受 |
|---|---|---|
| 🔴 **首次开局只能去 S1** | `picker_choices:514-518` + `expand_known_landmarks` 逐步解锁逻辑;开局 known_landmarks ⊆ {S1} | **"地图给了我唯一一条路 = 假沙盒"** — 第一印象定调 |
| 🔴 **首周目 picker variants 80% 不可达** | 24 variants 中,**仅 3 个 visit_count_min** 首周目无门槛可触发;其余 21 个需 flags/ending_seen/theme/deduction/foreshadow/inv/shifts/all_of 门槛 | **"反复站在地图前看到一样的字"** — 重复感强 |
| 🔴 **`n_lore_index` 完全退化为 6 项静态菜单** | `_is_map_picker:True` 但 `connections=[]`,picker_choices 退化为只显示 endshift/tools;6 项静态 choices | **"传闻系统是个干瘪菜单"** — "差劲"的最直接来源 |
| 🟡 **`_render_topology` 硬编码 7 地标 ASCII** | line 106-114 写死布局,加 linmou 必须改代码 | 显性 ADR-010 渲染层违反(中长期债) |

**核心翻译**:
> "地图功能不契合玩法 + UX 差劲" = **首次玩家在路径自由度、内容触发密度、传闻分支三处同时撞墙**,加上渲染层硬编码长期债

**已确认非问题(避免误击)**:
- ✅ 数据层 5/5 沙盒合规:11 地标 / 22 connections / 24 picker variants 全部已落地
- ✅ linmou 网状度反而比 G-273 高(L1 连 3 / L3 连 3,全网联通)
- ✅ NPC 浮标 / ❗ 线索 / 工具栏 / 进度条 / 回访标记 / 锁定提示全部已实现
- ✅ picker_choices 自由移动机制是真的(基于 connections 限制可达)

### 评审团修正前一份报告的误判

**上一份(`2026-05-14-next-wave-direction.md`)Pass 28 关切"linmou `landmark_map: {}` 是隐性 sandbox debt"** —— 本次实测发现:`landmark_map` 存在树顶层(不是 picker 节点),linmou 4 地标全部已在顶层注册且 connections 网状真实存在。Topology 上次判断有误,**linmou 数据层无 debt**,真正的 debt 是渲染层硬编码 + 首次玩家路径过窄。

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与(本次调研协调者)

**层级判定**:多层(引擎 picker 逻辑 + UX 表达密度 + 剧本 variants 分布 + 拓扑契约)

**意见**:

通过实测,**用户"地图差劲"的根因不是数据缺失,而是首次玩家心流的三处具体卡点**。前一份报告我们诊断为"渲染层硬编码",虽然是真问题,**但优先级排在首次玩家投诉的三个根因之后**。

### 三个核心痛点(按用户感知严重度排序)

#### 🔴 痛点 1 — 首次开局路径过窄(P0)

`map_view.py:picker_choices` 第 510-518 行:

```python
if current_lid and current_lid in by_id:
    target_ids = list(dict.fromkeys((cur.get("connections") or []) + [current_lid]))
else:
    # 还没去过任何地标 — 只有"已知"的才能去(开局只知道 S1)
    target_ids = [sid for sid in known]
    if not target_ids:
        target_ids = ["S1"]
```

`expand_known_landmarks` 设计为"访问一个地标才解锁它和它的 connections"。**首次玩家进 picker 时 `known_landmarks` ⊆ {S1}**,只能去 S1。

这是**第一印象问题**:玩家在第一次打开地图时看到"1 个选项",直接定调"这是分支剧本不是沙盒"。后续访问 S1 解锁 S4/S5/S7 之后**才**有 4 选项,**但首次印象已固化**。

#### 🔴 痛点 2 — 首周目 picker variants 80% 不可达(P0)

`n_landmark_picker` 有 24 个 narrative_variants,触发条件实测分布:

| 条件类型 | 数量 | 首周目可达? |
|---|---|---|
| flags(行为画像) | 8 | 需累积特定路径 |
| ending_seen | 3 | ❌ 仅第 2+ 周目 |
| **visit_count_min** | **3** | **✅ 首周目第 1/2/3 次访问** |
| theme_resolved | 2 | 推理满足后 |
| inv_has | 2 | 拿道具后 |
| all_of(复合) | 2 | 多条件 |
| deduction_resolved | 1 | 推理 |
| foreshadow_resolved | 1 | 集齐伏笔 |
| shifts_completed_min | 1 | 累计 4 班后 |
| shifts_skipped_min | 1 | 漏卡 |
| **TOTAL** | **24** | **首周目低门槛:3 个** |

**首周目玩家第 4 次进 picker 之后**,如果还没解任何 deduction / 没集任何 foreshadow / 没特殊行为画像,他看到的就是同一段 narrative(visit_count_min=3 已经命中过)。**24 variants 的丰富度 80% 给了多周目玩家,首周目玩家拿到的是"反复站在地图前看到一样的字"的体验**。

#### 🔴 痛点 3 — `n_lore_index` 完全退化为 6 项静态菜单(P0)

`n_lore_index` 节点设置 `_is_map_picker: True`,这会让 tui_player 调用 `picker_choices` 接管选项生成。**但 `n_lore_index` 在 tree 顶层 `landmark_map` 中没有自己的子集** + `connections=[]` 空数组,导致:
- `picker_choices:520-542` 的 travel 分支:**0 个地标可去**
- `picker_choices:545-563` 的 tools 分支:可能显示几个民俗工具节点
- `picker_choices:565-582` 的 endshift:返回主 picker

实际玩家从 `[传闻] 趁地图还没变,翻夜班论坛索引` 选项进入 `n_lore_index` 后,看到的是 **6 个静态 choices**(松木场 / 浙大钟楼 / 武林广场 / 孔雀大厦 / 雷峰塔 + [返回]),**完全没有沙盒感**。这是用户说"UX 差劲"的最直接来源 — "传闻"是一个明显的死菜单分支。

#### 🟡 痛点 4(中长期债)— `_render_topology` 硬编码 7 地标 ASCII

`map_view.py:106-114` 把 G-273 7 地标布局写死代码。详见前一份报告 Pass 30。这是 ADR-010 渲染层契约违反,**但优先级低于上述 3 个用户感知痛点**。

### 上一份报告优先级修正

上一份 `2026-05-14-next-wave-direction.md` 推荐 Pass 27/28/29:

| 上一份 Pass | 关切 | 新评估 |
|---|---|---|
| Pass 27 | Issue #15 + golden file + CLAUDE.md | **保留**,合规债务,与本轮并行 |
| Pass 28 | linmou 肌理(connections 节点层 + flags 改名) | **降级 / 缩 scope** — 实测发现 linmou 数据层无 debt,connections 在 tree 顶层已实现;只剩 flags 改名等小项 |
| Pass 29 | Pass 25 缺席 debt ADR 入档 | **保留**,纯文档清账 |

**新短名单优先级(本轮重定):**
1. **Pass A**(首次开局可见性) — P0,直击首因感受
2. **Pass B**(中阶 variants 补完) — P0,提升首周目密度
3. **Pass C**(lore_index 沙盒化) — P0,修传闻死菜单
4. Pass 27 / Pass 30(渲染层硬编码) — 并行做,中长期债
5. Pass D(node.choices 死字段清理) — 卫生,可挂账

### 产出

- **悖论清单**:无新增。但 `n_landmark_picker.choices` 的 10 项静态字段 + `picker_choices` 动态生成**双轨并存**是显性技术债:作者修改 `choices` 不生效,会误导维护
- **伏笔变更**:无
- **一致性规范**:本轮 Pass A/B/C 必须遵守:① 0 新字段路线 ② 不动 ADR-010 沙盒契约 ③ 首次玩家无状态门槛仍能感受到"有 ≥ 3 个选项 / variants 切换 / 沙盒分支可探"

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与(本轮涉及 known_landmarks 初始化策略)

**意见**(立场延续 + 实测预填):

State 在 2026-05-13 持续坚持"既有真相源榨干、0 新字段"。本轮调研后,有一个**关键判定**需要 State 主动给出:

### Pass A 实施方式辩论

让首次玩家在 picker 看到 ≥ 3 个候选地标,有两种实现:

- **方案 A1(state 初始化扩展)**:开局时 `known_landmarks = [S1, S4, S5, S7]`(把 S1 邻接全部预解锁),让玩家"从手机地图看到 4 个可去点"
- **方案 A2(分离 known / accessible 语义)**:`known_landmarks` 表示"地图上能看到的点",`accessible_landmarks` 表示"实际能去的点"。开局 known = [S1, S4, S5, S7](玩家"听说过"但没去过),accessible = [S1](实际可走)
- **方案 A3(沙盒模式入口选 1)**:开局节点给玩家一个**"今晚先去哪打第一个点"**的选项,4 个地标作为入口候选,选一个作为 S1 替代

**State 立场**:
- ❌ 反对 A2 — **引入新 state 语义层**违反"0 新字段"
- ⚠️ 警惕 A1 — **修改 `known_landmarks` 初始值是 state 语义变更**,可能影响 audit_paths 等下游审计
- ✅ 推荐 **A3** — 用 `_landmark_picker` 之前的 `n_intro` 或新建一个"今晚选起点"节点,通过 `choices.effects.add_known` 把玩家选择的地标加入 known,完全走既有 state 通道,0 新字段
- 0 新 variants 条件 / 0 新 flags

### 产出

- 新增 flags:**无**
- 新增 variants 条件:**无**
- 引擎扩展需求:**无**(A3 走既有 effects.add_known 通道)
- **前置依赖警告**:Pass A3 实施时需确认 `add_known` effects 在 `expand_known_landmarks:421` 正确处理初始状态

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:普通审查(本轮无周目消费侧,但 Pass A 影响首周目体验)

**意见**(立场延续):

Meta 在 2026-05-13 立场:Pass 23 候选(图鉴 / True Ending 门槛)等 Pass 26 观察期满后再启动。本轮地图 UX 改造**对周目消费无直接影响**,Meta **放行**。

但 Meta 关切:**Pass A 的"沙盒入口选 1" 设计**是一个潜在的**周目机制触点**:
- 首次玩家选起点 = "随机播种"
- 第 2 周目玩家如果上次走过 S5,第 2 周目可以**主动避开** S5 起点(沙耶之歌式"我已经知道我不该再走那条路")
- 这是**隐性 Memory Echo** 雏形 — 不需要图鉴系统就能感受周目厚度

Meta 把这个作为 **Pass A 的隐性收益备注**,本轮不立 Pass。

### 产出

- 周目机制变更:**无**(Pass A 是隐性正向收益)
- 收集本调整:**无**
- true ending 解锁条件变化:**无**

---

## § 5. UX Designer — 文字体验设计师

**相关度**:🔥 **深度主导(本轮主笔)**

**意见**:

UX Designer 在本轮**完整提交 8 项症状清单**(主笔产出),把用户原话"UX 极其差劲"翻译成可定位、可修复的代码与数据问题。

### UX 8 项痛点症状清单(实测,按严重度排序)

#### 症状 1 — picker 静态 choices 与动态 picker_choices 双轨并存,**作者文案被静默丢弃** ⛔
- **症状描述**:`n_landmark_picker` 同时有 10 个静态 `choices`(`tree.json`)和动态 `picker_choices()`(`v7/map_view.py:480`)。TUI 走动态路径(`tui_player.py:580`),玩家看到的是 `"→ S1 湖滨 · 湖滨第三把绿色长椅 (20:27)"`,**完全不是作者写的 `"[01] 湖滨长椅 — 把手电调低,先去最近的水边。"`**。作者精心写的 10 段叙事性文案**根本没被玩家看到**
- **代码位置**:`src/ghost_story_factory/v7/tui_player.py:380-396`;`stories/hangzhou_yebanbaoan/tree.json` 的 `n_landmark_picker.choices[]`
- **根因层**:**引擎与数据双轨,作者文案被静默丢弃**
- **严重度**:**阻断**(用户感知"UX 差劲"首要嫌疑)

#### 症状 2 — picker_choices 文案模板化,失去夜班质感 🔴
- **症状描述**:`"→ S1 湖滨 · 湖滨第三把绿色长椅 (20:27)"` — **这是 GPS 导航,不是夜班巡更员的内心独白**
- **代码位置**:`src/ghost_story_factory/v7/map_view.py:536`
- **根因层**:引擎渲染策略
- **严重度**:**严重**(玩家出戏)

#### 症状 3 — choice affordance 标签密度严重不均 + 标签语义贫乏 🔴
- **症状描述**:抽样测试:`n_landmark_picker` 10 选项中**只有 1 个**显示了 affordance 标签;`n_s1_arrive` 5 选项中 4 个显示"巡点"(与文案语义重复 — 视觉噪音)。**整树 450 个 choices,0 个有作者手写 `intent`/`archetype` 字段** — 全部 affordance 都是 effects 派生(Pass 11 路线)
- **代码位置**:`src/ghost_story_factory/v5/player.py:481-552 choice_affordance_tags()`
- **根因层**:派生策略 + 文案密度(只有 ~9 种 tag 词汇)
- **严重度**:**严重**(选项变盲选)

#### 症状 4 — picker 顶部 20+ 行视觉装饰推下 narrative 🔴
- **症状描述**:进入 picker 节点的 TUI 渲染顺序(`tui_player.py:397-432`):红色 `═══` 横幅 4 行 → 拓扑图 15 行(大量空白和 `[?]` 占位)→ 图例 + footer 2 行 → 线索/NPC/进度/工具栏 8-15 行 → 行为画像。玩家第一眼看到 **20+ 行视觉装饰**,真正的 24 个 narrative_variants 反应文本**被推到下一屏**
- **代码位置**:`src/ghost_story_factory/v7/tui_player.py:380-432`;`v7/map_view.py:_render_topology` 硬编码 15 行布局
- **根因层**:TUI 渲染顺序 + 视觉权重失衡
- **严重度**:**严重**(Pass 19-26 反应 clause 投入被装饰挡住)

#### 症状 5 — 拓扑图早期 `[?]` 占位居多,看起来像加载失败 🟡
- **症状描述**:开局 `known_landmarks` 只有 `S1`,6/7 地标显示为 `[?] ?? ??? ??:??` — **像 ASCII art 渲染 bug 或加载失败**,不像"探索式渐进揭示"
- **代码位置**:`src/ghost_story_factory/v7/map_view.py:124-126, 130-131`
- **根因层**:引擎渲染(渐进揭示视觉表达失败)
- **严重度**:**一般**(首次印象差)

#### 症状 6 — 三个 picker 节点中两个 narrative 是占位符 `(占位)` 🔴 ⛔
- **症状描述**(已实测确认):
  - `n_landmark_picker`(G-273):narrative 有内容(254 chars)+ 24 variants
  - `n_l1985_landmark_picker`(linmou):narrative = `"(占位)"`
  - `n_lore_index`(传闻):narrative = `"(占位 — 此节点应该总是命中某个 narrative_variant)"`
- 如果任何 narrative_variant 的 `if` 条件没命中,**玩家真的会看到"(占位)"调试字符串**
- **代码位置**:`stories/hangzhou_yebanbaoan/tree.json` 中的两个节点
- **根因层**:剧本数据(默认文案为调试字符串,无 fallback)
- **严重度**:**严重**(linmou 周目 / 传闻首次访问可能可见 — UX 灾难现场)

#### 症状 7 — tools 9 个 emoji 图标在 Textual 渲染下宽度不稳 🟡
- **症状描述**:`tree.tools` 全部用 emoji 当 icon:📻📁☎💬🐛🏚🔔⚰🦚。`map_view.py:409` `f"  [{icon}] {label:<10} {status_text}"`,`label:<10` 对中文宽度对齐已有问题,加 emoji 后**对齐肯定崩**
- **代码位置**:`src/ghost_story_factory/v7/map_view.py:404-410`
- **根因层**:TUI 框架限制(Textual/Rich CJK + emoji 宽度计算)
- **严重度**:**一般**

#### 症状 8 — 过门反馈与本节点 narrative 黏在一起,因果链断裂 🟡
- **症状描述**:玩家选了选项后,过门反馈(`_pending_transition_lines`)在**下一节点的顶部**显示。**galgame 范式期望"选择→即时反馈→新场景",不是"新场景里塞旧反馈"**
- **代码位置**:`src/ghost_story_factory/v7/tui_player.py:544-565`
- **根因层**:引擎渲染顺序
- **严重度**:**一般**

### Pass 13-18 UX backlog 复盘

| Backlog 项 | 当前状态 | 是否用户痛点 |
|---|---|---|
| #1 主角身份文案一致性 | Pass 19 已做 | 否 |
| #2 行为画像"克制度"复盘 | 待做 | 可能是(症状 4 同谋) |
| #3 多周目"已见过"信息呈现 | 嵌入 Pass 20 候选 | 否 |
| #4 **首次进入→第一结局心流计时** | **待做** | **极可能** — UX 测量工具,本次评审建议立 Pass 32 |
| #5 **选择意图标签信息密度二次校准** | **待做** | **是** — 症状 3 直接对应,纳入 Pass 29 |

### 与 Chief 前一稿 Pass A/B/C 整合

Chief 在事实包到达前提出 Pass A(`n_first_pick` 开局选起点)、Pass B(中阶 variants 补完)、Pass C(lore_index 沙盒化)。UX 主笔评估后:

- **Chief Pass A**(首次玩家只能去 S1)→ 问题真实但**优先级低于症状 1/4/6**。玩家走完 S1 后自然解锁,损耗 5 分钟可消解;症状 1/4/6 是**每一次进 picker 都在加深损耗**。重新归类为 **Pass 31(可挂账)**
- **Chief Pass B**(首周目 24 variants 仅 3 个可达)→ 部分有效,但**真问题是 picker 装饰挡住了 variants 显示**(症状 4)。先做 Pass 28(渲染顺序重排)后再评估是否需要补 variants
- **Chief Pass C**(`n_lore_index` 沙盒化)→ **与症状 6 重合**(`n_lore_index.narrative` 是"(占位)")。**并入 Pass 27 的"补默认 narrative"子项**,不单独立 Pass

### UX 推荐 3 项主 Pass(本轮主战场)

#### Pass 27 候选 ★ — picker 双轨清理 + 文案重生(对应症状 1/2/6,含 Chief Pass C 子项)
- **内容**:
  - 把 `n_landmark_picker.choices[]` 作者写的叙事文案**接回 TUI 渲染**:`picker_choices()` 改为「读 tree.json 静态 choices 的 text 作为基础,landmark_map 的 short/place/time 作为标签」,而不是反过来
  - 删除 / 不渲染 `picker_choices` 自己拼的 `"→ S1 湖滨 · 湖滨第三把绿色长椅 (20:27)"` 格式
  - 给 `n_l1985_landmark_picker` 和 `n_lore_index` 补默认 narrative(消灭 `(占位)` 调试字符串)
- **工时**:3-4 小时
- **风险**:动态选项 require 过滤逻辑要保留;linmou Act 1 sandbox debt 不在本 Pass 解决根本
- **可量化改善**:picker 文字质感从"RPG 菜单"恢复到"夜班巡更员视角";0 个调试占位泄漏
- **对应症状**:1、2、6

#### Pass 28 候选 ★ — picker TUI 渲染顺序重排 + 拓扑图减负(对应症状 4/5)
- **内容**:
  - 把 narrative_variants 文本提到拓扑图**之前**显示(进入 picker 玩家首先读反应 clause)
  - 拓扑图压缩:开局只显示 S1 周围 +1 跳邻居,其他用「└─ 4 个未知地标 ─┘」一行折叠
  - 行为画像移到选项**下方**或左侧边栏,不挤 narrative
- **工时**:4-5 小时
- **风险**:破坏现有 TUI 测试(`tests/test_tui_presenter.py`);需重做截图基线
- **可量化改善**:进入 picker 首屏看到 narrative 概率从 ~30% → 90%+;首次进入认知负担减半
- **对应症状**:4、5

#### Pass 29 候选 ★ — affordance 标签精细化:增加作者手写 hint 通道(对应症状 3)
- **内容**:
  - 在 choice schema 加可选 `_hint: "短词"` 字段(作者手写,1-3 字)
  - `choice_affordance_tags()` 优先读 `_hint`,无则走 effects 派生
  - 给主路径关键 ~30-50 个选项手补 `_hint`:"先观察"/"直接冲"/"绕路"/"记录"
  - 增加 audit 工具检查"标签语义重复率"
- **工时**:6-8 小时
- **风险**:与 Pass 11 affordance 路线兼容性需保证;作者文案需评审
- **可量化改善**:选项有效区分度从抽样 ~20% → 80%+
- **对应症状**:3;backlog #5

#### Pass 30 候选(低优先)— 过门反馈渲染位置修复(对应症状 8)
- 把 `_pending_transition` 移到选择**触发时**就在原节点尾部显示。工时 ~2 小时

### UX 推荐落地顺序

**Pass 27 → Pass 28 → Pass 29(→ Pass 30 / Pass 31 / Pass 32 挂账)**

理由:
1. Pass 27 不动渲染顺序,只修数据通路,**先把作者最 hurts 的"作者文案被丢弃"解决**
2. Pass 28 在数据通路修复后再调整视觉,避免改两次
3. Pass 29 是文案密度增强,放最后

### 不推荐做的(防止再被拖偏)

- ❌ 加新装饰组件(用户已经说过"不要 TUI 美化")
- ❌ 改 emoji icon 系统(症状 7,治本要改 Textual 框架,投入产出比差)
- ❌ 重写整个 v7 TUI(Pass 16 已经做了 presenter 边界,够了)

### 产出

- **TUI/CLI 草图(Pass 27 + 28 整合示意)**:

```
更衣室外,墙上挂着一张杭州地铁夜班巡逻图。
7 个打卡点,用红圈标着。你低头看着自己的手 —
食指已经虚搭在 B3 档案室那个圈上。            ← narrative_variant 顶部显示

  [01] 湖滨长椅 — 把手电调低,先去最近的水边。  [先观察]    ← 作者文案 + hint
  [02] 柳浪闻莺 307 阶 — 沿湖走到台阶尽头。       [绕路]
  ...

──────────────────────────────────
S1 湖滨 ● 现在     └─ 4 个未知地标 ─┘            ← 拓扑减负 + S1 +1 跳邻居
──────────────────────────────────
```

- **排版规范变更**:picker 节点首屏必须可见 narrative_variant 完整段落 + 至少 3 个选项
- **玩家旅程节点变化**:无新增节点(Pass 31 才加 n_first_pick,本轮挂账)

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与(Pass A 起点文案 + Pass C lore_index 沙盒化文案)

**意见**:

Lore 主要关切两件:

### Pass A — "今晚先去哪打第一个点" 的 lore 锚点

不能让 4 个起点听起来像选择题。**每个起点必须有 lore-grade 的具体诱因**:
- S1 湖滨 — "靠单位最近,前任在交接表上画了 ★"(单位制纪律暗示)
- S4 羊血弄 — "广播喇叭最近一直放某条新闻,'⺶记屠铺'昨天关了门"(EXPOSED 反咬伏笔)
- S5 留下小学旧楼 — "203 琴房灯还亮着,值班记录上没标"(REGRET 反咬伏笔)
- S7 平海路 — "调度说今晚特别交代'最远的点先打',字条没署名"(隐藏起点暗示)

每个起点的选择对**之后的 narrative 走向有微妙影响**(蝴蝶效应在文案密度,不在 state)。

### Pass C — lore_index 不能是"百度百科条目"

5 个传闻必须保持:
- **杭州本地质感**:松木场 / 浙大老校区 / 武林广场 / 孔雀大厦 / 雷峰塔,Lore 已审核合格,不动
- **NPC 关联**:每条传闻必须能挂到某个 NPC 的 `related_foreshadows`(目前没挂)— Pass C 实施时补
- **行为画像反映**:玩家**已拣 shard 的传闻在最上面**,未拣的在下面,符合"夜班保安先看自己关心的"心理

### Lore 红线

- ❌ **不要把 5 项传闻改成"按点击量排序"现代化呈现**
- ❌ **不要加 emoji 标签**(🏠 寺庙 / 👻 鬼 / 💀 死亡)
- ✅ 用纯字符标记(◐ 已拣 / ✓ 已解 / · 未触)

### 产出

- 新增元素考据清单:**无新增**(本轮不新增 lore 元素)
- lore 不一致警告:**Pass A 4 起点文案必须杭州本地化,不能"任选一个"扁平化**
- 命名建议:Pass A 新节点用 `n_first_pick` 或 `n_shift_start_choice`

**Lore 推荐**:Pass A/B/C 全部放行,但起点 lore 锚点 + 传闻索引文案密度必须由 Lore 主笔

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:🔥 **深度主导(本轮主笔)**

**意见**:

Topology Designer 在本轮**完整提交 7 症状清单**(主笔产出),诊断 **picker 节点作为沙盒契约项 5 "反应 clause" 承载者** — 实测发现 1 个 P0 阻断同时是 UX Designer 症状 1 的姊妹根因。

### 🎯 P0 重大发现:Pass 27' 已被并行实施(评审进行时)

**症状 1 当时诊断**:`tui_player.py:380-432` 的 `_is_map_picker` 分支**只调用 `format_map_lines`,不调用 `resolve_narrative`** — `n_landmark_picker` 的 24 个 narrative_variants(Pass 9 / Pass 24 / Pass 26 反咬,行为画像反喂,theme/foreshadow/deduction/ending_seen 多维分化)**全部运行时不显示**。

**这是 Topology Designer 与 UX Designer 互相印证的同一根因**:作者写的 picker 内容(无论 narrative_variants 还是 choices.text)都被引擎跳过。

**评审进行时事实变化**:实测 `tui_player.py:383-392` 与 `v5/player.py:1164-1167` **已包含 `Pass 27' 修复(2026-05-14 评审决议)` 注释 + `resolve_narrative` 调用 + `(占位` 前缀过滤**。`git diff` 确认两处约 30 行修改尚未 commit。**修复方案 = Topology 候选 A 原文**,主助手或并行 worker 已在评审过程中实施。

**当前状态**:**P0 已修复(代码层)**,但:
- 修改未 commit,需评审后 commit + 测试 + snapshot 锁
- 这只解决症状 1(picker variants 不渲染),症状 2-7 全部待做

### Topology 完整 7 症状清单(主笔产出)

#### 症状 1 【P0 阻断 — 已修复未提交】picker 24 档 narrative_variants 运行时被 map_view 渲染完全替代
- **代码位置**:`v7/tui_player.py:380-432` + `v5/player.py:1160-1178`
- **数据位置**:`n_landmark_picker.narrative_variants` 共 24 条
- **沙盒契约视角**:触发 **ADR-010 黑名单 4** 孪生反模式 — "picker 反复访问 narrative_variants 不展示"
- **严重度**:**P0 阻断** ✅ **已修复(评审进行时,~ 30 行,见 git diff)**

#### 症状 2 【P1 严重】picker.choices 静态 10 选项全部 `cond=None` — 决策密度为零的菜单分发器
- **数据位置**:`n_landmark_picker.choices[0..9]`,全部无 `if` / `condition`
- **裂痕**:作者编辑剧本时看到的 10 选项是装饰;运行时被 `map_view.picker_choices()` 完全替换(connections 邻接过滤 / 回访标记 / S7 终局标记 / 锁定提示)— **作者审查盲区**
- **沙盒契约视角**:擦边 ADR-010 黑名单 2(connections 真实生效),但**静态声明 vs 运行时实现的双层 picker 是审稿/审计鬼影**
- **严重度**:**P1 严重**。与 UX Designer 症状 1 是同一裂痕的不同侧面

#### 症状 3 【P1 严重】picker_choices() 动态横跳选项缺乏"为什么去"的信息
- **代码位置**:`map_view.py:520-542`
- **实际行为**:选项 text 是机械模板 `f"→ {sid} {short} · {place} ({time}){ending_tag} {revisit_tag}"`
- **缺什么**:
  - 没"线索召唤"(`_landmarks_with_clue_hint` 已计算但未注入选项 text)
  - 没"NPC 在场"(`npc_locations` 已计算,只地图视图显示)
  - 没"风险 hint"(高 PR / 低共鸣地标动态浮现)
  - 没"成就 hint"(差一个 visit_count 触发某 variant)
- **沙盒契约视角**:违背"沙盒玩法"内核 — 玩家应"看着地图衡量代价做选择",现在只是"7 个景点选一个"
- **严重度**:**P1 严重**

#### 症状 4 【P1 严重】地标 _arrive 节点 narrative_variants 偏斜:S1=7 / S6=2 / S2=3 / 平均 4.0
- **数据位置**:实测 `n_s1_arrive..n_s7_arrive` 各 narrative_variants
- **沙盒契约视角**:触发 **ADR-010 黑名单 4**(地标反复访问无分化),S6 / S2 软违规
- **严重度**:**P1 严重**。补 variants 即可,无拓扑改动

#### 症状 5 【P2 严重】`n_scene_evaluator_room` in_degree=5 但 14 variants — 内容沉没
- **数据位置**:`in_degree=5`,`narrative_variants=14`
- **实际行为**:90% 玩家走主线不会点 `[回访]` → 14 variants 沉没
- **严重度**:**P2 一般**。在 picker variants 动态推荐引导发现

#### 症状 6 【P2 严重】`n_lore_index` (传闻入口) 只有 2 个 narrative_variants
- **数据位置**:`narrative_variants` = 2
- **严重度**:**P2 一般**。补 variants 即可

#### 症状 7 【P2 钝化】picker.choices[8] "[结束] 至少 4 个点" 静态文案无 cond,实际靠 `picker_choices()` 过滤
- **代码 vs 数据裂痕**:tree.json 写死提示但 TUI 完全被覆盖
- **严重度**:**P2 钝化**

### 与上一轮 linmou 误判的自我修正

**Topology 在 `2026-05-14-next-wave-direction.md` § 7 关切 linmou `landmark_map: {}` 接合点未审清**。本次实测**自我修正**:
- tree 顶层 `landmark_map` 数组包含 11 entry(7 G-273 + 4 linmou)
- linmou 4 地标 connections 完整(L1 连 L2/L3/L4,L3 连 L1/L2/L4),**网状度高于 G-273**
- `picker_choices()` 按 connections 真实横跳

**linmou 数据层无 debt**。上一份 Pass 28 "connections 节点层显式化"子项**已自动完成**,无需做。

### 沙盒契约核查(ADR-010 5 项原语)

| 原语 | G-273 | linmou | n_lore_index |
|---|---|---|---|
| picker hub | ✅ n_landmark_picker | ✅ n_l1985_landmark_picker | ⚠️ `_is_map_picker:True` 但无 connections,**契约破损** |
| landmark connections | ✅ 11 边 | ✅ 8 边(全网) | ❌ 0 边 |
| `_is_tool` 节点 | ✅ 12 工具 | ✅ 2 工具 | ✅ 共享主线工具 |
| `stay: true` | ✅ 12 处 | ✅ 2 处 | N/A |
| 反应 clause variants | ✅ 24 个(P0 修复后渲染) | ✅ 6 个 | ⚠️ 仅 2 个 |

**`n_lore_index` 是隐性破损**:它假装自己是 picker hub(`_is_map_picker:True`),实质退化为静态菜单。`audit_sandbox` 没扫到。

### Topology 候选 Pass 推荐(主笔产出)

#### Pass 候选 A 【P0】picker narrative_variants 渲染修复
- ✅ **已实施(评审进行时,git diff 显示 ~ 30 行未 commit)**
- 在 `_is_map_picker` 分支前调 `resolve_narrative` + 过滤 `"(占位"` 前缀 + 渲染
- **沙盒契约影响**:0 破坏,修复 ADR-010 项 5 "反应 clause" 运行时兑现
- **下一步**:commit + 加 snapshot test 锁基线 + audit_state 加 Rule "节点 narrative 不许包含 `(占位)`"

#### Pass 候选 B 【P1】picker 选项 hint 注入 — 线索/NPC/风险三路
- 改 `map_view.picker_choices()` 让 travel choice text 注入:
  1. `_landmarks_with_clue_hint` 关联伏笔 slot 数 → `→ S4 羊血 ❗ 2 处未看完`
  2. `npc_locations` 在场 NPC → `→ S2 柳浪 👤 红衣女孩`
  3. high-PR 警告(state.PR >= 70 且 visited >= 1)→ `→ S6 联庄 ⚠ 高耗`
- **工时**:2-3 小时,~ 80 行
- **沙盒契约影响**:0 破坏,加强项 5 入口可见性
- **风险**:hint 过多导致 picker 视觉嘈杂,需 UX 把控密度

#### Pass 候选 C 【P1】narrative_variants 偏斜补完(S6 / S2 / lore_index)
- 针对 ≤ 2 的节点(S6=2 / lore_index=2 / S2=3)按 visit_count_min / ending_seen / theme_resolved 三档补
- **工时**:1-2 小时,0 代码,~ 60 行 tree.json
- **沙盒契约影响**:0 破坏,修复 ADR-010 项 4 软违规

### Topology 优先级排序

**A(已实施) → B → C**

若只做一个新 Pass:**B 优先**(picker 从"7 景点菜单"变为"7 决策点"是 UX 决策密度最大提升)。

### 沙盒契约红线检查

| 候选 Pass | 是否违反 ADR-010 |
|---|---|
| A picker variants 渲染 | ❌ 不违反,反而修复项 5 |
| B picker 选项 hint 注入 | ❌ 不违反 |
| C 地标 variants 补完 | ❌ 不违反 |
| UX 主笔 Pass 28/29 | ❌ 不违反 |
| Chief 前一稿 Pass A 开局选起点 | ❌ 不违反 |

**无 ADR-010 一票否决**。

### 产出

- 节点结构变更:无(Pass A 是引擎层 + 数据兜底)
- 状态维度调整:无
- 可达性证明:Pass A 已实施未破坏现有 ending(snapshot test 待补)
- **拓扑红线**:
  1. **新增 `audit_state` Rule**:节点 `narrative` 字段不许包含 `"(占位)"` 字符串(防症状 1 类回归)
  2. **新增 `audit_sandbox` Rule**:`_is_map_picker:True` 节点必须 ① 有 connections ≥ 1 或 ② 显式 `_is_archive:True`(解决 `n_lore_index` 隐性破损)
  3. **picker.choices 静态字段标记**:作者维护陷阱(症状 2),需 schema 加 `"_runtime_replaced_by": "map_view.picker_choices"` 注释字段

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与(本轮 3 个 P0 改动需要回归)

**意见**:

QA 在 2026-05-13 立场:`audit_cross_run_continuity` + golden file pytest 回归是最高优先级。本轮 Pass A/B/C 涉及玩家路径关键节点,**必须 snapshot 锁现状再改**。

### QA 测试矩阵(本轮)

| 改造项 | 工时 | 新审计 / 测试 | 关键断言 |
|---|---|---|---|
| Pass A 开局选起点 | 1d | `tests/test_first_pick.py`(新建)+ `audit_paths` 加起点分歧检测 | 4 起点路径都能到所有 main ending;known_landmarks 初始 ≥ 1 + 邻接;`n_intro → n_first_pick → 任一起点`路径覆盖 |
| Pass B 中阶 variants 补完 | 0.5d | `audit_variant_trigger` 验证新 variants 首周目触发率 | 第 4-8 次进 picker 都能匹配中阶 variant;variants 分布基尼系数 ≤ 0.6 |
| Pass C lore_index 沙盒化 | 1d | `tests/test_lore_index_picker.py`(新建)+ `audit_sandbox` 新 Rule | C1:`n_lore_index` 有 ≥ 5 边 connections;C2:无 `_is_map_picker:True` 标志且有 narrative_variants ≥ 3 |
| Pass D node.choices 死字段清理 | 0.2d | grep 验证 | 所有 `_is_map_picker:True` 节点的 `.choices` 字段为空或带 `_dead_` 前缀 |

### QA 红线断言

- **新红线**:`audit_sandbox` 加 Rule "`_is_map_picker:True` 必须有 connections 或 `_is_archive:True`"
- **新红线**:首次玩家(visit_count=0 + endings_seen=0)进 picker 必须看到 ≥ 3 个 travel choice(Pass A 落地后)
- **维持红线**:Pass 26 `audit_profile_inheritance` 阻断模式不变

### QA 立场

- **Pass A / B / C 都必须 snapshot 锁现状再改** — 否则会丢失玩家熟悉感
- **Pass A 必须先做**,因为它改变 `n_intro` 出口,所有下游路径都受影响
- 建议:Pass A 与 Pass C 同 PR(都是节点级改动,审计同步覆盖);Pass B 单独 PR(纯 variants 增量)

### 产出

- 测试路径序列:
  - Pass A:`n_intro → n_first_pick → S1/S4/S5/S7 → ... → 各 ending`(4 条主路径,每条都要走到 ending)
  - Pass B:`n_landmark_picker × 8 次访问`,断言 8 次显示的 narrative_variant id 不重复(至少 5 个不同)
  - Pass C:`[传闻] → n_lore_index → 各传闻条目`(C2 模式断言 narrative_variants 切档)
- Bug 清单(分等级):
  - **阻断**:首次玩家只能去 S1(P0 — Pass A 解决)
  - **阻断**:首周目第 4+ 次进 picker 80% variants 不可达(P0 — Pass B 解决)
  - **阻断**:`n_lore_index` 退化为 6 项静态菜单(P0 — Pass C 解决)
  - **严重**:`audit_sandbox` 不检查 picker hub connections 完整性
  - **一般**:`n_landmark_picker.choices` 10 项死字段(Pass D)
  - **中长期**:`_render_topology` 硬编码 7 地标(前一份 Pass 30)
- 回归测试入口:`pytest tests/test_first_pick.py tests/test_lore_index_picker.py` + `bash tools/audit_all.sh`

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行 — Pass 27' P0 修复已在评审进行时并行实施(待 commit + 测试),Pass 28/29 主战场继续 + 3 项挂账**

### 🎯 评审进行时事实变化(Pass 27' 已实施)

Topology Designer 与 UX Designer **两线主笔互相印证**发现 P0 根因:**`_is_map_picker` 分支不调 `resolve_narrative`,作者写的 24 个 narrative_variants + 10 个 picker.choices 文案全部运行时丢失**。

**评审过程中,主助手(或并行 worker)已实施修复**:
- `git diff src/ghost_story_factory/v7/tui_player.py`:line 380-396 加 `resolve_narrative` + 过滤 `(占位` + 渲染(~ 20 行)
- `git diff src/ghost_story_factory/v5/player.py`:line 1164-1167 同形修复(~ 10 行)
- 注释明确:`# Pass 27' 修复(2026-05-14 评审决议):picker variants 死渲染`

**这相当于 Topology Pass 候选 A 已先于评审报告完成**。修复未 commit,本评审决议要求:
1. **commit 这 30 行修改**(Pass 27' 正式完成)
2. **加 pytest snapshot test** 锁住 G-273 picker 三档典型 variants(visit_count_min / ending_seen.last / theme_resolved)的渲染基线
3. **新增 `audit_state` Rule**:节点 narrative 不许含 `"(占位)"` 字符串(防回归)

---

### § 9.0 v2 修订日志(2026-05-14 报告产出后,Pass 27 部分实施)

用户对本报告 Pass 27/28/29 推荐**口头放行**,并要求"先 A 然后 B":A = 立即开 Pass 27 修复 picker variants 死渲染 / B = 把新发现追加报告。

**Pass 27a 已落地** ✅ — 主助手实施了 Pass 27 中**最便宜的子项**(< 30 分钟):

- **改动**:
  - `src/ghost_story_factory/v7/tui_player.py:380` 添加 `resolve_narrative(node, self.state)` 调用,picker 分支现在先渲染 narrative_variant 再叠加地图视图
  - `src/ghost_story_factory/v5/player.py:1162` 同步修复
  - 加 `(占位` 前缀 guard,防止玩家看到 `n_l1985_landmark_picker.narrative = "(占位)"` 这种调试字符串
- **效果**:Pass 9/23/24/26 写的 picker `narrative_variants` 资产(24 条 G-273 反咬 + 6 条 linmou + 2 条 lore_index)立即复活,玩家终于能看到"指尖虚搭在 B3 圈上"等多周目残影
- **验证**:
  - ✅ `bash tools/audit_all.sh` 13/13 全绿
  - ✅ imports clean(v5 + v7)
  - ✅ patches 在两个文件都生效
  - ⚠️ 2 个 pytest pre-existing failures(Issue #15 跨 character ending_seen + 2 个 linmou_sandbox endshift)与本补丁**无关**,stash 验证

**Pass 27 剩余子项**(本次未做,挂账继续):
- ⏳ **picker `node.choices[]` 静态作者文案接回**(UX Designer P0,见 §9 下文 Pass 27 详述)— 作者写的 `[01] 湖滨长椅 — 把手电调低,先去最近的水边。` 等 10 条文案目前仍被 `picker_choices()` 动态生成的 GPS 格式覆盖,需要 `picker_choices()` 改造为读取静态文案 + landmark_map 标签合成
- ⏳ Pass 28(渲染顺序重排 + 拓扑减负)、Pass 29(choice `_hint` affordance 精细化)— 未启动

**Pass 27a 与原 Pass 27 的关系**:Pass 27a 是 Pass 27 的"最便宜子项",落地后让 24 picker variants 立即可见,**消除了报告中症状 6 的"占位字符串泄漏"**;但**症状 1 的"choices 文案静默丢弃"仍未修**,需要继续完成 Pass 27 全量。

下文 §9 推荐 3 项主 Pass 仍然有效,只是 Pass 27 的子项 27a 已 done。

---

### 用户原话再校准

> "地图功能,我觉得没有深度契合玩法,并且 UX 方面极其差劲"

经过 UX Designer 主笔的 8 症状清单实测 + Chief 前一稿 3 根因合并,评审团**最终诊断**:

**核心结论**:用户感知的"差劲"主要由 **3 个引擎/数据层 bug + 5 个 UX 细节** 累积造成,**不是地图功能缺失**:

| 严重度 | 症状 | 位置 |
|---|---|---|
| ⛔ 阻断 | 症状 1:作者写的 picker 文案被 `picker_choices()` 静默丢弃 | `tui_player.py:380-396` |
| ⛔ 阻断 | 症状 6:`n_l1985_landmark_picker` / `n_lore_index` narrative 是 `"(占位)"` 调试字符串 | `tree.json` 两节点 |
| 🔴 严重 | 症状 2:动态选项是 GPS 菜单格式,失去夜班质感 | `map_view.py:536` |
| 🔴 严重 | 症状 3:450 个 choices 全无作者手写 hint,affordance 标签贫乏 | `player.py:481-552` |
| 🔴 严重 | 症状 4:picker 顶部 20+ 行装饰挡住 24 个 variants | `tui_player.py:397-432` |
| 🟡 一般 | 症状 5:`[?]` 占位看起来像渲染 bug | `map_view.py:124-131` |
| 🟡 一般 | 症状 7:emoji icon 宽度对齐崩溃 | `map_view.py:409` |
| 🟡 一般 | 症状 8:过门反馈黏在下一节点 narrative | `tui_player.py:544-565` |

**Chief 前一稿的"首次开局只能去 S1 / 24 variants 80% 不可达"3 根因诊断**仍然成立,但 UX 主笔评估认为**优先级低于上述 3 个阻断/严重项** — 因为它们是"5 分钟内自然消解"的一次性问题,而 UX 8 症状是"每次进 picker 都在加深损耗"的持续性问题。

### 共振轴

**共振轴一(7 票一致)**:**用户投诉真根因是"作者文案被引擎绕过 + 装饰挡住 narrative + 标签贫乏"**
- Chief / State / Topology / QA / UX / Lore / Meta 全部确认

**共振轴二(6 票:Chief / UX / State / Topology / QA / Lore)**:**Pass 27 双轨清理 P0**
- 解决症状 1+2+6,**直击"作者最 hurts 的'文案被丢弃'"**

**共振轴三(5 票:Chief / UX / QA / Topology / Lore)**:**Pass 28 渲染顺序重排 P0**
- 解决症状 4+5,让 24 variants 真正被玩家看到

**共振轴四(4 票:Chief / UX / QA / State)**:**Pass 29 affordance 精细化 P1**
- 解决症状 3,选项区分度从 ~20% → 80%+

### 推荐 3 项主 Pass(本轮主战场,UX Designer 主笔)

#### Pass 27 候选 🔥 —— picker 双轨清理 + 文案重生(P0,对应症状 1/2/6)

- **内容**:
  1. 把 `n_landmark_picker.choices[]` 作者写的叙事文案**接回 TUI 渲染**:`picker_choices()` 改为「读 tree.json 静态 choices 的 text 作为基础,landmark_map 的 short/place/time 作为标签」
  2. 删除 / 不渲染 `picker_choices` 自己拼的 `"→ S1 湖滨 · 湖滨第三把绿色长椅 (20:27)"` 格式
  3. 给 `n_l1985_landmark_picker` 和 `n_lore_index` 补默认 narrative(消灭 `"(占位)"` 调试字符串)
- **范围**:动 `map_view.py:picker_choices` 1 处 + 数据补 2 处 + 测试
- **验收**:
  - 玩家看到的 picker 选项是作者原文案,而非 GPS 模板
  - 任何 picker 节点 narrative_variant 全 miss 时不暴露调试字符串
  - `audit_state` 加 Rule:无节点 narrative 包含 "(占位)" 字符串
- **工时**:3-4 小时
- **为什么先做**:6 票共振 / 0 新字段 / 直击作者文案被丢弃 / 顺手修 `n_lore_index` + `n_l1985_landmark_picker` 的占位 narrative bug

#### Pass 28 候选 🔥 —— picker TUI 渲染顺序重排 + 拓扑图减负(P0,对应症状 4/5)

- **内容**:
  1. 把 narrative_variants 文本提到拓扑图**之前**显示(进入 picker 时玩家首先读反应 clause)
  2. 拓扑图压缩:开局只显示 S1 周围 +1 跳邻居,其他用「└─ 4 个未知地标 ─┘」一行折叠
  3. 行为画像移到选项**下方**或左侧边栏,不挤 narrative
- **范围**:`tui_player.py:_render_node` + `map_view.py:_render_topology` 渲染序调整
- **验收**:
  - 进入 picker 首屏看到完整 narrative_variant 概率 ≥ 90%
  - 拓扑图行数从 15 → ≤ 5 行(开局阶段)
  - 现有 TUI snapshot 测试更新基线(QA 责任)
- **工时**:4-5 小时
- **为什么次做**:5 票共振 / 让 Pass 19-26 投入的 24 variants 真正被玩家看到

#### Pass 29 候选 🔥 —— affordance 标签精细化:作者手写 hint 通道(P1,对应症状 3)

- **内容**:
  1. 在 choice schema 加可选 `_hint: "短词"` 字段(作者手写,1-3 字)
  2. `choice_affordance_tags()` 优先读 `_hint`,无则走 effects 派生
  3. 给主路径关键 ~30-50 个选项手补 `_hint`:"先观察"/"直接冲"/"绕路"/"记录"
  4. 增加 audit 工具检查"标签语义重复率"
- **范围**:`player.py:choice_affordance_tags` + Lore 出词 ~30-50 处 + audit 工具
- **验收**:
  - 选项有效区分度(同节点不同 tag 比例)≥ 80%
  - audit 工具检测同节点 ≥ 3 个选项共用同 tag 时报警
- **工时**:6-8 小时
- **为什么 P1**:4 票共振 / backlog #5 直接对应 / 但工时长,放在 Pass 27/28 落地后

### 挂账(本轮不立 Pass,但记录在案)

#### Pass 30(挂账)—— 过门反馈渲染位置修复(对应症状 8)
- 把 `_pending_transition` 移到选择**触发时**就在原节点尾部显示,工时 ~2 小时

#### Pass 31(挂账,原 Chief Pass A)—— 开局选起点(`n_first_pick` 节点)
- Chief 前一稿提的"首次玩家只能去 S1"问题。UX 评估**优先级低于 Pass 27/28** — 因为玩家 5 分钟后自然解锁。但如果 Pass 27 已重构 `picker_choices`,顺手做 Pass 31 成本低,可同 PR
- 实施按 State A3 方案(`effects.add_known`,0 新字段)

#### Pass 32(挂账)—— 首次进入→第一结局心流计时(对应 UX backlog #4)
- 引入 `tools/measure_player_path.py`,自动跑路径输出 timing / 文本密度 / 选项数直方图
- **为后续 UX 优化提供客观断点测量**,避免"UX 差劲"再次成为主观争论

### 与前一份报告 Pass 27/28/29 的关系(命名冲突解决)

**重要**:前一份报告 `2026-05-14-next-wave-direction.md` 的 Pass 27/28/29 与本轮 Pass 27/28/29 是**不同含义**。建议:

| 编号 | 旧含义(前一份) | 新含义(本份,UX 主笔) | 处置 |
|---|---|---|---|
| Pass 27 | Issue #15 + golden file + CLAUDE.md | picker 双轨清理 + 文案重生 | **本份优先**,旧 Pass 27 重命名为 **Pass 33**(合规债,并行做) |
| Pass 28 | linmou 肌理补完 | TUI 渲染顺序重排 + 拓扑减负 | **本份优先**,旧 Pass 28 **缩 scope 后挂账**(linmou connections 已落地) |
| Pass 29 | Pass 25 缺席 debt ADR 入档 | affordance 标签精细化 | **本份优先**,旧 Pass 29 重命名为 **Pass 34**(纯文档清账) |

**用户确认决议后**,由助手统一更新 INDEX 行的 Pass 编号,避免文档持续冲突。

### 推荐执行顺序

**Pass 27 → Pass 28 → Pass 29 → 挂账(Pass 30/31/32)+ 并行清账(旧 Pass 33/34)**

理由(UX 主笔):
1. Pass 27 不动渲染顺序,只修数据通路 — **先把作者文案接回玩家眼前**
2. Pass 28 在数据通路修复后再调整视觉序,避免改两次
3. Pass 29 文案密度增强放最后

### 不推荐(明确放行 = 本次不做)

- **加新装饰组件**(用户已说"不要 TUI 美化")
- **改 emoji icon 系统**(症状 7,治本要改 Textual 框架,投入产出比差)
- **重写整个 v7 TUI**(Pass 16 已经做了 presenter 边界,够了)
- **加新地标 / 新角色**:本轮焦点是已有数据的呈现
- **加新 state 字段**:0 新字段路线严守
- **图鉴 / True Ending 门槛**:Meta Pass 35+ 候选

### 关键风险(决议为"修改后放行",必填)

1. **State 红线**:Pass 27 重构 `picker_choices` 不许引入新 state 字段;Pass 31 实施时严守 A3 方案(`effects.add_known`)
2. **UX 红线**:Pass 28 渲染顺序重排必须**先 snapshot 锁现状**,字符级 diff 给作者审查后再合入
3. **Lore 红线**:Pass 29 作者 hint 文案 + Pass 27 占位 narrative 补完 + Pass 31 起点诱因文案,**Lore 必须主笔**(不允许助手代写)
4. **Topology 红线**:Pass 27 重构 picker_choices 不许破坏 connections 自由移动逻辑;`audit_sandbox` 加 Rule "`_is_map_picker:True` 节点 narrative 不许包含 `(占位)` 字符串"
5. **QA 红线**:
   - Pass 27/28 必须 snapshot 锁住主线 5 ending + linmou 4 ending 关键路径
   - 新增 audit:`tools/audit_state.py` 检测 `(占位)` 调试字符串泄漏
6. **沙盒契约**:Pass 27 处理 `n_lore_index` 的方式必须遵守 ADR-010 — 要么补 connections 让 `_is_map_picker` 名副其实,要么删除 `_is_map_picker` 标志改为内容节点

### 后续动作

- 用户决策:
  - 确认推荐短名单 → 助手用 writing-plans skill 把 Pass 27 拆任务
  - **解决 Pass 编号冲突**:本份 Pass 27/28/29 与前一份 Pass 27/28/29 命名重复,需用户决定哪个保留 27-29 编号(建议:本份 UX 主笔优先,旧的重编号为 33-34)
  - **如果用户原话实际指"添加迷你地图 / 导航箭头 / 图形 UI"**,方向需调整 — 但评审团从代码实测倾向于上述诊断
- 推荐执行顺序:**Pass 27 → Pass 28 → Pass 29 → 挂账与清账并行**

### 不同意见记录

- **UX vs Chief**:本轮 Chief 前一稿提出"首次玩家只能去 S1"是 P0,UX 主笔评估降为 P2 挂账(Pass 31)— **理由**:UX 8 症状是持续损耗,Chief Pass A 是 5 分钟内自然消解的一次性问题。Chief 接受 UX 主笔评估
- **State**:坚决反对 Pass 27 实施时引入新 state 字段或新 schema 字段(`_hint` 已在 Pass 29,合规) — 采纳
- **Topology**:上一份报告 "linmou `landmark_map: {}`" 判断**自我修正**,实测发现 connections 已落地;本轮关切 `audit_sandbox` 加 Rule 检测 `_is_map_picker:True` 但 connections 空的节点
- **Lore**:Pass 27 补 2 处占位 narrative + Pass 29 ~30-50 处作者 hint + Pass 31 4 起点诱因文案,**Lore 必须主笔**
- **Meta**:本轮不深度介入,放行;但提醒 Pass 31 是 Memory Echo 雏形,Pass 35+ 候选可衔接

---

### Linus 一句话总结

**"用户骂 UX 差劲,不是因为缺组件 — 是因为作者写好的 10 段文案被引擎换成了 GPS 菜单、玩家进 picker 先看到 20 行装饰再看到 narrative、450 个选项的 affordance 标签只有 9 种词汇能选。先把这三件事修了,再去管首次玩家只能去 S1 的事 — 因为前者是每次进 picker 都在恶化,后者只痛 5 分钟。"**
