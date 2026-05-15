# 2026-05-15 Pass 35-B1 tool 占位清扫(3 节点)

> 评审团:script-review-team
> 任务 slug:pass-35b1-tools-fill
> 报告生成时间:2026-05-15 现场会议
> 前置任务:Pass 35-A(lore_voice_matrix + songmuchang/wulinmen/zheda 三 lore 节点的 G-273 character variant 差异化)
> 后续任务:Pass 35-B2(UX 状态行 `[lore · 第 N 次查阅 · 已收录]`,引擎/UX 层独立 Pass)

---

## § 1. 任务描述

**用户原话(转述)**:Pass 35-A 沉淀出"高频 NPC/lore 节点 character=default variant 一字不差 = 系统性反模式"的治理范式。本 Pass 接续清扫剩余 3 个高频 tool 节点(`n_scene_lost_archive` 13 入边 / `n_npc_predecessor_voice` 13 入边 / `n_scene_red_telephone` 7 入边),它们都是主文为 `(占位)`、character=default variant 字数 1001 / 897 / 1317、视角不分化的同模式实例。本 Pass 仅做"占位回填 default 主文 + 新增/补完 G-273 character variant",**不动** 6+5 条 ending_seen / theme_resolved / deduction_resolved / foreshadow_resolved / inv_has 触发分支。

**任务影响范围**:**剧本**(单层 — tree.json node body + character variant,引擎/UX 状态行已拆出 35-B2 独立 Pass)

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与

**层级判定**:**剧本**(单层 — 拆包后 B1 不再跨层)

**意见**:

35-A 治理模板可直接复用,但有 **3 个本质差异**必须在 B1 起手就压住:

1. **体量差异**:35-A 的 songmuchang/wulinmen 主文字数 265/253,本 B1 三节点 1001/897/1317 是 **4 倍体量**。G-273 character variant 不能用"局部替换 1-2 句"的轻改,需要**语气贯穿性重写**。但 UX 决议把 G-273 短路线压到 **200-260 字**(与 1000+ 字 default 形成体量对比作为辨识度),让"长 default / 短 variant"的反差本身成为玩家信号。

2. **节点性质差异**:35-A 三节点是 lore 类(玩家主动查阅型),本 B1 是 tool 类(玩家主动使用型)。tool 节点周期性返场频次更高(13/13/7 入边),character 字段失能等于**整个工具家族对 G-273 没有视角**。State Architect 的"26 入边实质失能"定性成立。

3. **跨周目契约负担**:35-A 沉淀的"主文不能动"原则在 B1 受到考据硬伤反推力——Lore Keeper 发现 GP-300/GP-328 对讲机型号、湖滨菩萨弄地名两处 lore 硬伤。这不是"占位回填"任务能消化的负担。Chief Editor 决议:**B1 范围内的考据修正必须做(否则新写的 default 一上线就是错的)**,但 35-A 已落地 lore_voice_matrix 的 GP-328 同型错误**单独开 Pass 35-A-fix-walkie-talkie**,不在 B1 范围。

**关键冲突点裁决**:

| 冲突点 | Chief Editor 决议 |
|---|---|
| 35-A lore_voice_matrix 是否一并修对讲机型号 | **不在 B1**,开 Pass 35-A-fix-walkie-talkie(P1 优先级,但独立 Pass) |
| predecessor_voice [2] 死代码 | **删除**,与 [0] `last:E_DATA` 合并(QA 强需求) |
| lost_archive 平海街地址改名 + B3 货梯井 | **纳入 B1**,因新写 default 必须用一个具体地名,Lore Keeper 给的"平海街老百货大楼地下室"满足 800-1300 字 default 的具体性要求,不算范围扩张 |
| QA 发现的 character 顺序 bug | **必修(B1 阻断)**,35-A 同型 bug 在新节点复发说明这是结构性问题,B1 不修等于明知失能 |

**伏笔影响**:

B1 范围严守"不碰 6+5 条触发 variants"。Meta-Game Designer 的锚点 lock 是底线:
- lost_archive 主文锚点 lock:**档案 / 纸张 / 编号**(default 1000+ 字主文不能写偏)
- predecessor_voice 主文锚点 lock:**录音 / 断点 / 前任称谓**
- red_telephone 保留 `oneshot.contacted_predecessor` 触发后的"已联系"余味(default 主文中性,不预设是否联系过)
- G-273 character variant 必须自洽于含 `g273_ending` 的 endings_seen 语境

**产出**:
- 悖论清单:无(B1 不触碰触发链)
- 伏笔变更:无(锚点词 lock,内容差异化在视角层)
- 一致性规范:character variant 顺序必须严于所有 visit_count_min 之前(B1 沉淀的新不变量,QA 写回归断言)

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与

**意见**:

lost_archive(13 入边)+ predecessor_voice(13 入边)= **26 入边的 `state.character` 字段实质失能**——比 35-A 严重 **4 倍**(35-A 是 7+5+3=15 入边,B1 是 26 入边)。这不是"个别占位",是 character 字段在高频 tool 节点上的**系统性反模式**。本质问题:**修 character 字段的失能**,占位只是表症。

red_telephone(7 入边)无 G-273 variant,语义上是工具/线索查询型,跨周目感由 default 文本承载即可,**放过**不强加 G-273 variant(避免内容稀释)。

**核心红线**(B1 强契约,违反则打回):

| 红线 | 数值 / 规则 |
|---|---|
| 零新增 flags | B1 不允许任何 flags 字段 |
| G-273 vs default 字符级差异度 | **≥ 60%**(比 35-A 50% 提高 10pp,因体量更大) |
| G-273 character variant 字数 | **200-260 字**(与 UX 短路线契约一致) |
| default 主文字数 | **800-1300 字**(三节点 1001 / 897 / 1317 保留量级,允许微调) |
| character variant 顺序 | **严于所有 visit_count_min 之前**(本 Pass 沉淀的新不变量) |
| red_telephone G-273 variant | **不加**(语义不需,跨周目感由 default 承载) |
| 零引擎扩展 | player.py / save_manager.py 零改动 |

**产出**:

- 新增 flags:**无**(0 新增)
- 新增 variants 条件:
  - `lost_archive[N]`(N = 把 [18] 移到 [12] 前的新位置):`{character: 'G-273'}` — 200-260 字 G-273 视角短路线
  - `predecessor_voice[N]`(N = 把 [13] 移到 [6] 前的新位置):`{character: 'G-273'}` — 200-260 字 G-273 视角短路线
  - `red_telephone`:**无新增**(不加 G-273 variant)
- 引擎扩展需求:**无**(player.py 零字段,save_manager.py 零字段,tui_player.py 零渲染逻辑)

**结构性沉淀(供后续 Pass 35-C+ 复用)**:

每当遇到 "high-frequency tool/lore node + (占位) body + character=default 字字相同 variant" 三特征同时出现的节点,默认套用本 Pass 模板:
1. 把 character variant 物理位置移到所有 visit_count_min 之前
2. default 主文字数保留 800-1300 量级
3. G-273 character variant 200-260 字 + ≥ 60% 差异度
4. 零 flags 零引擎扩展

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:深度参与

**意见**:

B1 的最大跨周目风险是 default 主文重写后**破坏现有 ending_seen / theme_resolved / deduction_resolved 触发 variants 的语义依赖**。这些反应文本是上一轮玩家"见过 X"的契约兑现,主文重写时如果把它们依赖的"锚点意象"洗掉,跨周目反咬会失语。

**锚点词 lock 清单**(B1 default 主文重写必须命中):

| 节点 | 锚点词(主文必须出现且语义清晰) |
|---|---|
| lost_archive | **档案 / 纸张 / 编号**(3 个 ending_seen variants 都依赖"档案室找到/没找到"的物理具体性) |
| predecessor_voice | **录音 / 断点 / 前任称谓**(3 个 ending_seen variants 都依赖"录音被掐断 / 前任说了一半"的悬置感) |
| red_telephone | **公用电话 / 投币 / 接通失败**("已联系前任"余味必须由 default 主文承载,不预设结果) |

**G-273 character variant 跨周目自洽要求**:

G-273 是 g273_ending 当事人——B1 写的 G-273 character variant 玩家**必然已见 g273_ending**(否则不会拿到 G-273 身份)。所以 G-273 视角文本可以**默认 endings_seen 含 g273_ending**,语气可以是"上一周目我已经死过一次"的余味,但**不能**直接剧透其他 ending(玩家可能只见过 g273_ending 一个 ending)。

**周目机制变更**:无(B1 零周目机制改动)

**收集本调整**:无(B1 零收集本字段)— `lore_seen[story_id]` 字段 **挂账 Pass 36+**

**true ending 解锁条件变化**:无

**产出**:

- 锚点词 lock 清单(见上表,B1 强契约)
- G-273 character variant 跨周目自洽规则:默认 endings_seen 含 g273_ending,但不剧透其他 ending
- 红色 telephone 不加 G-273 variant 的元游戏理由:工具节点跨周目感由 default 承载够,过度差异化反而稀释"普通保安使用公用电话"的日常质感

---

## § 5. UX Designer — 文字体验设计师

**相关度**:深度参与

**意见**:

**关键判断**:三节点 default 字数 1001 / 897 / 1317 **过长**——lore/tool 节点周期性返场,250-320 字适配 30-45 秒阅读窗口,1000+ 字会**强迫玩家跳读**,反过来削弱跨周目反咬的辨识度(玩家根本看不完)。

但 B1 拆包契约不动 default 字数(State Architect 决议 800-1300 字保留)。**问题转化为**:让 **G-273 character variant 走 200-260 字短路线**,**"长 default / 短 variant" 的体量反差**本身成为视角辨识度信号——玩家见到短文本立刻意识到"这是 G-273 周目专属"。

**G-273 视角差异化锚点候选**(避开 35-A 已用的"打卡钟 / 对讲机"):

| 锚点候选 | 适用节点 | 备注 |
|---|---|---|
| 巡更钥匙串(机械重量 + 某把钥匙齿痕磨损) | lost_archive | 物理触觉锚点,与"档案柜钥匙"自然衔接 |
| 值班日志最后一页笔迹断裂 | predecessor_voice | 笔迹断裂呼应"录音断点",跨媒介互文 |
| 监控墙雪花噪点节律 | lost_archive 或 predecessor_voice | 时间/技术老化感锚点 |
| 手电筒电池接触不良间歇熄灭 | red_telephone(若需) | 已被 State Architect 决议红色 telephone 不加 G-273 variant,**搁置** |
| 制服口袋汗浸应急电话卡 | predecessor_voice | "联系前任"的物理凭证,可与 oneshot.contacted_predecessor 形成余味 |

**选 2-3 个,不要全用**(避免与 35-A 的"打卡钟节律"同样的锚点堆砌反模式)。**推荐**:
- lost_archive G-273 variant:**巡更钥匙串 + 监控墙雪花噪点节律**
- predecessor_voice G-273 variant:**值班日志笔迹断裂 + 制服口袋应急电话卡**

**`>` 引用块用量**:仍限 **1 处/节点**(B1 字数体量更大不允许扩到 2 处,否则玩家阅读节奏崩塌)。1 处 `>` 用于 G-273 视角最强情感锚点,不用于物理描述。

**产出**:

- TUI/CLI 草图:无新增(渲染层 Pass 35-B2 处理)
- 排版规范变更:G-273 character variant 200-260 字 + 1 处 `>`,与 35-A 节奏一致
- 玩家旅程节点变化:
  - 入口:tool 节点首次访问 → 看 default 主文 800-1300 字(信息密度高)
  - 反咬触发:`endings_seen / theme_resolved / deduction_resolved` 命中时插入对应 variant(不动)
  - G-273 周目:首次访问即看到 200-260 字短路线(体量反差 = 信号),立刻知道"这是周目专属视角"

**与 35-B2 协同(挂账,不在本 Pass)**:

UX 状态行 `[lore · 第 N 次查阅 · 已收录]` 拆到 Pass 35-B2,B1 完成后再开。N 从 `foreshadows_seen[story_id]` 派生,picker(`tui_player.py:384`)和 regular(`:1196`)入口对称渲染,与 (占位 guard 的先后交互需要 writing-plans 评审。

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与(发现 3 处硬伤,2 处必修)

**意见**:

逐节点考据:

### 🟡 lost_archive — 凑合(地名建议改 + 80 年代档案室真实元素)

**硬伤等级**:🟡 凑合(可上线但建议改)

**问题**:
- 现 default 中"平海街 1 号 B1/B3"地址过具体——平海街是杭州真实街道(西湖区),门牌 1 号是绍兴饭店所在,与"老百货大楼地下室"语义冲突
- B1/B3 双层结构需要叙事支撑(为什么档案在 B3 而不是 B1?)

**建议改**:
- 把"平海街 1 号"改为 **"平海街老百货大楼地下室"**(去具体门牌,保留杭州本地地标感)
- B1 保留档案室(纸质卷宗),B3 改为 **"封死的废弃货梯井"**(呼应 1996 货梯红衣女孩传说,B1 lore 库已建立的元素)

**80 年代档案室真实元素清单**(20 个 variants 务必命中 3+ 项):
1. 牛皮纸卷宗袋 + 棉线缠绕(1985 年公文规范)
2. 铁皮档案柜(墨绿漆面剥落,统一制式)
3. 红蓝双色档案章(分密级)
4. 仿宋体手写卡片目录(电脑普及前的检索系统)
5. 白炽灯泡拉绳开关(节能荧光灯 1990s 才普及)

### 🔴 predecessor_voice — 必修硬伤(对讲机型号错)

**硬伤等级**:🔴 必修

**问题**:
- **GP-328 错**:摩托罗拉 GP-328 是 **2003 年后**机型,1985 年不存在
- **GP-300 也错**:摩托罗拉 GP-300 是 **1994 年后**产品,1985 年同样不存在
- 35-A 的 lore_voice_matrix 也用了 GP-328 同型错误 → **35-A consistency bug**

**建议改**:
- default 改 **"老式建伍 TK-308 对讲机"**(肯伍德 TK-308 是 1980 年代实际产品)
- 或泛称 **"八十年代镍镉电池手持台"**(去品牌,保留时代感,跨周目更安全)
- **35-A 的 lore_voice_matrix 单独开 Pass 35-A-fix-walkie-talkie 修正**(不在 B1 范围,Chief Editor 决议)

### 🔴 red_telephone — 必修硬伤(地名 + 电话亭型号)

**硬伤等级**:🔴 必修

**问题**:
- **"湖滨菩萨弄"不存在**——杭州湖滨真实老巷:学士路 / 仁和路 / 平海路 / 菩提寺路 / 佑圣观巷
- **1989 年款公用电话亭部分准**:1989 年杭州主流是绿色磁卡亭(1988 邮电部铺设);"红色 + 玻璃门上半截透明 + 下半截铁皮"符合 **1985-1988 投币款**

**建议改**:
- 地名改 **"菩提寺路"**(真实存在,紧邻湖滨,寺院遗址,氛围对位)
- 或 **"佑圣观巷"**(道观遗址,氛围更对,但需 Lore Keeper 二次确认)
- 电话亭改 **"1986 年款红色投币电话亭"**
- 1987 年拨号建议虚构 **"1987 平海街百货失踪案"**(与已建立的 1987 踩踏事故事件对应,跨节点 lore 联动)

### B1 G-273 视角推荐锚点(避开 35-A 已用元素)

避开 35-A 的"打卡钟 / 对讲机节律 / 出入登记本":
1. **纸质签到簿 + 蓝黑墨水钢笔**(80 年代值班标配,与 lost_archive 档案室质感衔接)
2. **永备 5 号电池铜帽手电筒**(永备是 80 年代国民品牌)
3. **巡更钥匙串(铜挂钩 + 编号铝牌)**(与 UX 推荐的"机械重量 + 齿痕磨损"形成双重锚点)

**通用化风险评估**:

| 节点 | 通用化风险 | 原因 |
|---|---|---|
| lost_archive | 🟢 低 | 80 年代档案室元素特色足,杭州本地化由"平海街老百货"承担 |
| predecessor_voice | 🔴 高 | 改对讲机型号后**强锚 "湖滨保安队 1985 年编制表"** 才能避免通用化(否则任何城市都能套) |
| red_telephone | 🟡 中 | 菩提寺路 + 1987 平海街百货失踪案 是双锚点,但需要 B1 主文真正把两者串起来 |

**产出**:

- 新增元素考据清单:
  - 平海街老百货大楼地下室 → 杭州西湖区平海街本地地标(去具体门牌,保留区域感)
  - 1996 货梯红衣女孩 → B1 lore 库已建立元素,B3 货梯井引用即可
  - 老式建伍 TK-308 对讲机 → 1980 年代肯伍德实际产品
  - 1986 年款红色投币电话亭 → 1985-1988 杭州街头实际型号
  - 1987 平海街百货失踪案 → 与 1987 踩踏事故对应的虚构事件(跨节点 lore 联动)
  - 永备 5 号电池铜帽手电筒 → 80 年代国民品牌
- lore 不一致警告:
  - **35-A lore_voice_matrix GP-328 同型错误** → 单独开 Pass 35-A-fix-walkie-talkie(P1)
  - 平海街 1 号现实是绍兴饭店,与"老百货大楼地下室"冲突(改地址消除)
- 命名建议:
  - 湖滨菩萨弄 → **菩提寺路** 或 **佑圣观巷**
  - GP-328 / GP-300 → **老式建伍 TK-308 对讲机** 或 **八十年代镍镉电池手持台**
  - 平海街 1 号 → **平海街老百货大楼地下室**

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:放行(35-A 决议适用)

**意见**:

B1 是 variants 内容差异化 + 节点 body 占位回填 = **纯内容层**改动,沙盒原语零触碰:
- `_is_map_picker: true` hub 不动
- `landmark_map` + `connections` 不动
- `_is_tool: true` + `effects.stay: true` 不动(red_telephone 的 stay 状态保留)
- `narrative_variants[].if` 触发分支不动
- `reaction_contracts` 不动
- `endings_seen[story_id]` 不动

**沙盒最小骨架 5 项全保留**:
1. ≥ 1 个 `_is_map_picker` hub ✅(`n_landmark_picker` 不动)
2. ≥ 4 地标 + connections 邻边 ✅(地标网不动)
3. ≥ 2 个 `_is_tool` 节点 ✅(3 节点都是 _is_tool: true)
4. ≥ 1 处 `stay: true` 工具自循环 ✅(red_telephone 保留)
5. ≥ 1 处反应 clause variants ✅(6+5 触发分支全保留)

**ADR-010 死剧本黑名单复核**:全 0 命中。

**遗留观察(不阻塞 B1,挂账 Pass B3+)**:

3 个 tool 节点的 `effects.stay: true` 字段未在 tree.json 明示标注。**Topology Designer 决议:留独立 Pass(B3+)统一扫描所有 `_is_tool: true` 节点补全 effects.stay 字段**,不混入 B1。理由:B1 范围是内容层占位回填,补 effects.stay 是 schema/结构层改动,合包会模糊 git diff 的"为什么改这里"——违反手术式精准。

**产出**:

- 节点结构变更:**无**(B1 零拓扑改动)
- 状态维度调整:**无**
- 可达性证明:B1 不改 connections / next / triggers,所有 endings / CG / 知识可达性等价于 B1 前状态(reaction 触发链未触及)

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与(发现严重 bug + 死代码)

**意见**:

实测 variants 顺序,发现 **35-A 同型 bug 在新节点复发**:

| 节点 | variants 总数 | character 位置 | visit_count_min 位置 | default 位置 | 35-A 规则(character 严于所有 visit_count_min 之前) |
|---|---|---|---|---|---|
| `n_scene_lost_archive` | 20 | [18] | [12, 15, 16, 17] | [19] ✅ | ❌ **违反**(character [18] 在 visit_count_min [12-17] 之后) |
| `n_npc_predecessor_voice` | 15 | [13] | [6, 10, 11, 12] | [14] ✅ | ❌ **违反**(character [13] 在 visit_count_min [6-12] 之后) |
| `n_scene_red_telephone` | 5 | — | — | [4] ✅ | N/A(无 character variant) |

**B1 阻断 bug**(必修,否则 G-273 重访被截胡):
1. `lost_archive` — character variant 从 [18] 上移到 [12] 之前(物理位置 < 12)
2. `predecessor_voice` — character variant 从 [13] 上移到 [6] 之前(物理位置 < 6)
3. red_telephone — 无 character variant,无需调整

**新发现死代码**(B1 严重 bug,应修):
- `predecessor_voice[0]` `last: E_DATA` 与 `[2]` `ending_id: E_DATA` 语义重叠
- 查找顺序 [0] 先命中 → [2] **永远不会被触发** = 死代码
- **建议 B1 删除 [2] 或合并到 [0]**(Chief Editor 决议:删除 [2])

**red_telephone 不对称**(留底,不修):
- 5 个 variants 全是行为门控(inv_has / oneshot / visit_count_min)
- 跨周目 ending_seen 反应缺失,与 lost_archive / predecessor_voice 不对称
- 与 State Architect 决议一致:**放过**(语义不需,跨周目感由 default 承载)

**3 条新回归断言**(写入 `tests/test_pass35a_lore_invariants.py`):

```python
# 断言 1:character 必须严于所有 visit_count_min 之前(35-A 同型 bug 防回归)
def test_character_variant_before_all_visit_count_min():
    for node in load_high_freq_nodes():
        variants = node.get('narrative_variants', [])
        char_idx = next((i for i, v in enumerate(variants) if v.get('if', {}).get('character')), None)
        vcm_indices = [i for i, v in enumerate(variants) if 'visit_count_min' in v.get('if', {})]
        if char_idx is not None and vcm_indices:
            assert char_idx < min(vcm_indices), \
                f"{node['id']}: character variant 必须在所有 visit_count_min 之前"

# 断言 2:同一 (story_id, ending_id) 的 ending_seen 不重复(防死代码)
def test_no_duplicate_ending_seen():
    for node in load_high_freq_nodes():
        seen = set()
        for v in node.get('narrative_variants', []):
            key = (
                v.get('if', {}).get('ending_seen', {}).get('story_id'),
                v.get('if', {}).get('ending_seen', {}).get('ending_id') or v.get('if', {}).get('last'),
            )
            if all(key) and key in seen:
                raise AssertionError(f"{node['id']}: ending_seen 重复 {key}")
            if all(key):
                seen.add(key)

# 断言 3:variants ≥ 8 的高频节点必须有 character 分支(避免 G-273 永远兜底 default)
def test_high_freq_nodes_have_character_variant():
    for node in load_high_freq_nodes():
        if len(node.get('narrative_variants', [])) >= 8:
            has_char = any(v.get('if', {}).get('character') for v in node['narrative_variants'])
            # red_telephone 例外:语义不需 G-273 视角(7 入边但工具/线索查询型)
            if node['id'] == 'n_scene_red_telephone':
                continue
            assert has_char, f"{node['id']}: 高频节点必须有 character variant"
```

**产出**:

- 测试路径序列:
  - 路径 A:G-273 周目首次进入 lost_archive → 应命中 character variant(改顺序后),不应被 visit_count_min 截胡
  - 路径 B:同上 predecessor_voice
  - 路径 C:删除 predecessor_voice [2] 后,E_DATA ending_seen 必须仍能通过 [0] `last: E_DATA` 触发(无回归)
  - 路径 D:red_telephone 7 入边全路径走通,不要求 G-273 variant
- Bug 清单:
  - **阻断**(B1 必修):
    1. lost_archive character variant 顺序错乱([18] → 移到 [12] 前)
    2. predecessor_voice character variant 顺序错乱([13] → 移到 [6] 前)
    3. predecessor_voice [2] 死代码(删除)
  - **严重**(B1 应修):
    4. 3 条新回归断言写入 `tests/test_pass35a_lore_invariants.py`
  - **一般**(可修):
    5. red_telephone 跨周目反应不对称(放过,留底)
- 回归测试入口:
  - `pytest tests/test_pass35a_lore_invariants.py -v`
  - 新增的 3 条断言对 hangzhou_yebanbaoan 故事全部高频节点(≥ 8 variants)运行

**QA 结论**:**B1 不能直接开干**,必须先完成 4 项前置:
1. lost_archive 把 [18] 上移到 [12] 前
2. predecessor_voice 把 [13] 上移到 [6] 前
3. 删 predecessor_voice [2] 死分支
4. 加 3 条新断言

完成上述 4 项后,才能进入"占位回填 default 主文 + 写 G-273 character variant"环节。

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行**

**理由**:

- Topology Designer 放行(沙盒原语零触碰)
- State Architect / Meta-Game Designer / UX Designer 给出明确数值红线契约
- Lore Keeper 发现 2 处必修硬伤(对讲机型号 + 湖滨地名)+ 1 处建议改(平海街地址)
- QA 发现 3 项 B1 阻断 bug(2 顺序 + 1 死代码),35-A 同型 bug 在新节点复发说明这是**结构性问题**,B1 不修等于明知失能

B1 范围实际比原定"占位清扫 + G-273 variant"扩大,包含:
1. **必做**:占位回填 default 主文(3 节点)+ G-273 character variant(2 节点,red_telephone 不加)
2. **必做**:QA 发现的 character 顺序修正(2 节点)
3. **必做**:predecessor_voice [2] 死代码删除
4. **必做**:Lore Keeper 发现的 2 处硬伤(对讲机型号 + 湖滨地名)+ 1 处建议改(平海街地址)
5. **必做**:3 条新回归断言写入测试

**关键风险**:

1. **35-A lore_voice_matrix GP-328 同型错误未修**(Lore Keeper 发现的 lore consistency bug)→ 单独开 **Pass 35-A-fix-walkie-talkie**(P1 优先级,B1 完成后立即接 — 否则 35-A 与 B1 lore_voice_matrix 不一致)
2. **default 主文 1000+ 字过长削弱跨周目反咬辨识度**(UX Designer 提出)→ B1 范围内不解决(契约不动 default 字数),靠 G-273 character variant 200-260 字短路线 + 体量反差作为辨识度信号缓解,长期问题挂账 Pass 36+ "高频节点 default 字数压缩"
3. **predecessor_voice 通用化风险高**(Lore Keeper 评估)→ B1 强锚 **"湖滨保安队 1985 年编制表"** 必须出现在 default 主文中,否则任何城市都能套用
4. **effects.stay: true 字段在 3 节点未明示**(Topology Designer 观察)→ 不混入 B1,挂账 Pass B3+ 统一扫描

**后续动作**:

- B1 开干顺序(严格按此):
  1. **先做 QA 前置 4 项**(顺序修正 + 死代码删除 + 3 条新断言)→ 跑 pytest 全绿后再进入内容回填
  2. **回填 default 主文**(3 节点,锚点词 lock 遵守 Meta-Game Designer 清单,lore 考据遵守 Lore Keeper 清单)
  3. **写 G-273 character variant**(2 节点,200-260 字 + ≥ 60% 差异度 + 1 处 `>` 引用块)
  4. **跑 audit_all**(确保 ADR-010 沙盒原语零触碰)
  5. **跑 pytest tests/test_pass35a_lore_invariants.py -v**(3 条新断言全绿)
- **直接开干**,**不需要 writing-plans**(35-A 已沉淀模板,本 Pass 是同模式延续,有数值红线 + 锚点词 lock + lore 考据清单 + QA 测试清单四重契约)
- B1 完成后立即开 **Pass 35-A-fix-walkie-talkie**(修 35-A lore_voice_matrix 的 GP-328 同型错误)
- B1 完成后另开 **Pass 35-B2**(UX 状态行 `[lore · 第 N 次查阅 · 已收录]`,引擎/UX 层,需要 writing-plans)

**不同意见记录**:

- **UX Designer**:default 1000+ 字过长建议未被采纳(B1 契约不动 default 字数,长期问题挂账 Pass 36+)— 不阻塞 B1,记录备查
- **Lore Keeper**:佑圣观巷 vs 菩提寺路 二选一未定(建议 B1 实施时由实施人选定其一,二者氛围权衡:菩提寺路更对位"红色电话亭"日常感,佑圣观巷更对位"道观遗址灵异感",B1 倾向 **菩提寺路**)
