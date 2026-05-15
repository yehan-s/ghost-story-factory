# 2026-05-15 Pass 35-A — lore 占位清扫(5 节点 + 主文)

> 评审团:script-review-team
> 任务 slug:pass-35a-lore-fill
> 报告生成时间:2026-05-15 当日

---

## § 1. 任务描述

用户原话:**"为 5 个 n_lore_* 节点 + n_lore_index 主文撰写真实 narrative,替换 (占位) 文本。范围:雷峰塔(1924) / 孔雀塌楼(2007) / 松木场(1987) / 浙大钟楼(1991) / 武林门刑场(1947),周目 hangzhou_yebanbaoan,纯 narrative 字段写作,不动数据契约/拓扑/引擎。"**

实测现状(`stories/hangzhou_yebanbaoan/tree.json`):

| 节点 ID | 入边 | `narrative` 主文 | `narrative_variants` 数 | 是 _is_tool |
|---|---|---|---|---|
| n_lore_index | 1 | 36 字「(占位)」 | 2(visit2 + default 363 字) | 否 |
| n_lore_kongque_collapse | 5 | 4 字 | 3(visit2 / G-273 / default,差异化) | 是 |
| n_lore_leifeng_worm | 5 | 36 字 | 3(visit2 184 / G-273 322 / default 322) | 是 |
| n_lore_songmuchang_inn | 5 | 4 字 | 3(visit2 148 / G-273 = default 265 字字相同) | 是 |
| n_lore_wulinmen_execution | 5 | 4 字 | 3(visit2 230 / G-273 = default 253 字字相同) | 是 |
| n_lore_zheda_clock_girl | 5 | 4 字 | 3(visit2 193 / G-273 = default 268 字字相同) | 是 |

**任务影响范围**:**lore**(纯叙事文本层 + 一个 variant 顺序 bug 修)

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与

**层级判定**:lore

**意见**:

连续性审查三问回答:

1. **variants 一致性**:songmuchang / wulinmen / zheda 三节点 G-273 与 default 文本字字相同,违背 `narrative_variants` 反应切档原语(ADR-010)— if 分支输出同一段文字 = 在数据契约里说谎,**好品味的反面**。
2. **伏笔/兑现链**:6 个 lore 节点是 `_is_tool: true` + `stay: true` 工具节点(除 n_lore_index),不在主推论链,不触发 `deduction_resolved` / `foreshadow_resolved`。改 narrative 文本不污染伏笔单一真相源(ADR-007/008)。安全。
3. **真问题不是"占位"四个字**:default variant 已写得不错(250-320 字),引擎大概率走 variant 兜底,**玩家实际不会裸看到"(占位)"**。真问题 = G-273 与 default 冗余(Option B 设计债)+ n_lore_index 主文 36 字裸奔(Option A 兜底风险)。

**产出**:
- **悖论清单**:零(本任务不动 connections / if / flags)
- **伏笔变更**:零
- **一致性规范**:G-273 variant 必须与 default 拉开 50%+ 字符级差异,否则 if 分支等于谎言

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与

**意见**:

- G-273 = default 字字相同(songmuchang/wulinmen/zheda 三节点)是 **死剧本反模式**(占了 if 槽却无差异),B 这三节点是 **P0 不是 P1**
- A 方案主文写真实兜底**不引入隐性 state**,前提:**禁止"写完主文就删 default variant"**(一票否决)。两者并存是 ADR-010 沙盒合约
- if 矩阵**不扩展**,沿用现有三元组(`visit_count_min` + `character` + 默认),禁止新加 `player_class` / `time_of_day` / `has_flashlight` 维度
- 新增 flags:**零**(明确否决)
- 引擎扩展:**零**

**产出**:
- **新增 flags**:零
- **新增 variants 条件**:零(沿用现有三元组,只重写文本)
- **引擎扩展需求**:零(narrative 字段已被 `resolve_narrative` 读取,Pass 27a 已修死渲染 bug)
- **B 方案差异化硬指标(必检)**:G-273 vs default **字符级差异 ≥ 50%**,含 ≥ 2 个保安职业锚点(时间戳 + 工具 + 空间盲区任选其二)

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:放行

**意见**:

- 本任务对元游戏层**零结构性影响**(`foreshadows_seen` / `endings_seen` / `deductions_resolved` 全不动)
- 跨周目 lore 重访无分化(visit_count 跨周目重置)是 **ADR-010 已知 sandbox debt**,**不在本 Pass 处理**(违反"手术式精准")
- 留底建议:未来开 ADR 讨论 `lore_seen[story_id]: list[node_id]` 字段(对齐 `endings_seen` 模式),**禁止用 flags 镜像**

**产出**:无(放行,无元游戏机制变更)

---

## § 5. UX Designer — 文字体验设计师

**相关度**:深度参与

**意见**:

- 250-320 字是 lore 应有体量(picker 98 字扫读 / lore 30-45s 驻足 / 水下 ~5 分钟沉浸),**不要再加**
- **风险**:6 节点连读 = 1800 字"博物馆疲劳",picker 应灰显已读(挂账 Pass 后续)
- **铁律**:**重访辨识不该污染 lore 正文**,禁止"你又一次想起..."廉价补丁(违反 ADR-007 单一真相源)
- **方案**:lore 节点入口固定渲染状态行 `[lore · 第 N 次查阅 · 已收录]`,N 从 `foreshadows_seen` / 节点 visit_count 派生,**0 schema 改动**
- B 方案保安视角元素是叙事正文,但门禁/打卡钟用 **`>` 引用块**(类日志格式):`> 03:47 · 西门门禁:无异常`,限 1 处/节点
- 转场**不要**"你回到了 picker 大厅"RPG 桥段,直接黑屏 → picker

**产出**:
- **TUI 草图**(lore 节点入口固定状态行):
  ```
  ─────────────────────────────────────
  [lore · 第 2 次查阅 · 已收录]
  ─────────────────────────────────────
  <narrative 正文>
  ```
- **排版规范变更**:每节点 3 段结构:**首段环境 ~80 字 → 中段事件 ~120 字 → 末段保安主观感受 ~80 字**
- **玩家旅程节点变化**:picker → lore 入口状态行 → 三段 narrative → `stay: true` 自循环 → picker(直接黑屏,无 RPG 桥段)

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与

**意见**:

5 条传闻考据结果:

| 传闻 | 考据 | 风险 | 决议 |
|---|---|---|---|
| 雷峰塔 1924 | ✅ 历史/民俗准 | ⚠️ 地点错 — 九溪十八涧理安寺远离雷峰塔,"夜班保安顺路看裂钟"逻辑不通 | **必改地点为净慈寺后山 / 夕照山下** |
| 孔雀塌楼 2007 | ❌ 杭州无"孔雀大厦";2007 真实塌方是萧山西兴大桥引桥;"乌龙王"是闽粤民间信仰,杭州主要是钱塘龙君 | 🔴 通用化风险高(可移植到任何城市) | **必改:延安路商住楼工地挖出镇水石犴**(钱塘江镇水兽,本地传说基础);年份保留 2007 或挪到 2003(地铁 1 号线庆春广场段地质事故) |
| 松木场 1987 | ✅ 全准(80 年代温州商人来杭,217 房编号合理) | 🟢 杭州专属 | 直接采用 |
| 浙大钟楼 1991 | ⚠️ 需明示"玉泉老校区钟楼"(避免与之江校区混淆);1991 跳绳女生纯虚构 | 🟡 任何高校都有钟楼传说,需加细节锚 | 加锚"那年浙大女生宿舍刚换防盗窗" |
| 武林门刑场 1947 | ✅ 全准 | 🟢 杭州专属 | 需在 narrative 中明示 **2-3 个年代锚**(长衫/中山装/工装裤/列宁装/喇叭裤,横跨 1900-2000) |

**B 方案保安道具优先级**:
- 🥇 **机械打卡钟**(80 年代信号棒插孔)— G-273 一代核心物件,**强烈建议作为 lore 入口道具**
- 🥈 摩托罗拉 GP-300 对讲机静电
- 🥉 门禁时间戳(注意 80 年代是纸质签到簿,90 年代末才有 IC 卡门禁,**年代分层警告**)

**产出**:
- **新增元素考据清单**:
  - 净慈寺夕照山(雷峰塔锚定)→ 1924 雷峰塔倒塌真实事件
  - 延安路商住楼工地 → 2003 地铁 1 号线庆春广场地质事故
  - 钱塘江镇水石犴 → 钱塘龙君信仰本地依据
  - 玉泉老校区钟楼 → 区别于之江校区
  - 武林门刑场 7 个时代衣着(长衫/中山装/列宁装/工装裤/喇叭裤/西装/休闲)
- **lore 不一致警告**:孔雀塌楼无本地依据,通用化风险高,**本 Pass 必须换名**
- **命名建议**:`n_lore_kongque_collapse` → 节点 ID 保留(不动数据契约),narrative 内容改为延安路 / 镇水石犴

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:放行

**意见**:

- 沙盒原语**零触碰**:picker / connections / _is_tool / effects.stay / variants[].if 全保留
- B 方案 variant 内容差异化 = **内容层非拓扑层**,沙盒契约不关心
- 沙盒最小骨架(G-273 周目)5 项全满足,本任务后依然满足
- **建议沉淀决议**:"variants 内容差异化(同 if clause 内改 narrative 文本)= 内容层,后续类似 lore 文本回填可绕过 Topology 评审,交 Lore Keeper + State Architect 即可"

**产出**:无(放行,无拓扑变更),但留一条**流程沉淀**:lore 文本回填类任务后续可豁免 Topology 评审。

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与(实测引擎代码)

**意见**:

**关键发现 1 — A 方案主文永不可达**:
- 引擎实测(`src/ghost_story_factory/v5/player.py:799-806`):variants 按顺序匹配,**首个 `if={}` 即兜底命中**,主文 `narrative` 只在 variants 为空或全不匹配时才走到
- 所有 6 节点 default variant `if={}` 已兜全 → **Pass 35-A "A 方案主文兜底"在生产代码下永不触发**
- A 价值降级为:**"占位文本看着扎眼的清洁性"+ 极端边界(variants 数组被误删时)的引擎裸奔安全网**

**关键发现 2 — 严重 bug(早就存在,非本 Pass 引入)**:
- variants 顺序问题:v[0] `visit_count_min: 2` 排在 v[1] `character: G-273` 前 → **G-273 玩家重访被 v[0] 截胡,看不到 G-273 专属重访文本**
- **建议 Pass 35-A 重写 G-273 variant 时同步调整顺序**:把 character 分支提到 visit2 前,或 v[0] 的 if 增加 `character != G-273` 排除条件

**产出**:
- **测试路径序列**:
  ```
  entry → n_landmark_picker → n_lore_index → n_landmark_picker → n_lore_leifeng_worm
  → n_landmark_picker → n_lore_songmuchang_inn → n_landmark_picker → n_lore_zheda_clock_girl
  → n_landmark_picker → n_lore_wulinmen_execution → n_landmark_picker → n_lore_kongque_collapse
  ```
- **Bug 清单(分等级)**:
  - **阻断**:无
  - **严重**:variants 顺序 bug — G-273 重访被 v[0] 截胡(早就存在)→ **本 Pass 顺手修(纳入 Pass 35-A 范围)**
  - **一般**:n_lore_index 主文 36 字裸奔(Option A,生产路径下永不触发但仍需清洁)
- **回归测试入口**:
  ```bash
  pytest tests/ -k "lore or variant"
  python3 -c "import json; t=json.load(open('stories/hangzhou_yebanbaoan/tree.json')); assert not any('占位' in (n.get('narrative') or '') for n in t.get('nodes',t).values()), '仍有占位'"
  ```
- **建议新增断言**:"所有 narrative_variants 中 `if={}` 必须是最后一项"

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行**(B 升 P0 + 孔雀换名必做 + variants 顺序 bug 顺手修)

**关键风险**:

1. **G-273 = default 字字相同是死剧本反模式**(songmuchang / wulinmen / zheda 三节点)— 沿用 if 槽却无差异,违背 ADR-010 反应切档契约。**B 升 P0**,**字符级差异 ≥ 50%**,含 ≥ 2 个保安职业锚点(时间戳 + 工具 + 空间盲区任二)
2. **孔雀塌楼无本地依据 + 通用化风险高**(Lore Keeper 一票必改)— narrative 内容必须换为**延安路商住楼 / 钱塘江镇水石犴**,节点 ID 保留不动
3. **variants 顺序 bug**(G-273 重访被 v[0] 截胡)— 早就存在,**本 Pass 一并修**(违反"一个补丁只做一件事"的边界,但属同一文件同范围,合并修复减少 PR 数,符合"手术式精准"精神)

**新冲突点最终决议**:

| 冲突点 | 决议 | 理由 |
|---|---|---|
| **A 方案是否做** | ✅ **做,但降级为"清洁性 + 边界安全网"** | QA 证实生产路径永不触发,但 (a) 36 字"(占位)"在 dump/tree.json grep 时扎眼;(b) 万一未来 variants 被误删,主文是兜底安全网。写 200-260 字普适视角文本,**禁止删 default variant** |
| **孔雀塌楼是否换** | ✅ **本 Pass 必换** | Lore Keeper 红线;无本地依据 = 与"杭州夜班保安"周目主题相悖;通用化风险一票否决 |
| **机械打卡钟优先级** | ✅ **B 方案选 机械打卡钟 + 对讲机静电 两个职业锚点** | Lore Keeper 优先级排序 + UX `> 03:47 · 西门门禁:无异常` 日志引用块限 1 处/节点(用于打卡钟)+ 对讲机静电作为环境锚 |
| **variants 顺序 bug** | ✅ **纳入 Pass 35-A** | 同文件同范围,合并修复;修复方式 = 把 `character` 分支提到 `visit_count_min` 前 |
| **UX `[第 N 次查阅]` 状态行** | ❌ **不纳入 Pass 35-A,挂账 Pass 35-B** | 0 schema 改动但属 UI 渲染层,需改 `tui_player.py` / `v5/player.py`,超出 lore 文本写作范围。违反"一个补丁只做一件事"则拆出 |

**后续动作**:

1. 用户/助手按本报告决议直接动手实施 Pass 35-A:
   - **(a)** 6 节点 `narrative` 主文写 200-260 字普适视角兜底文本(替换"(占位)")
   - **(b)** songmuchang / wulinmen / zheda 三节点 G-273 variant 重写为保安职业视角(机械打卡钟 + 对讲机静电锚点,字符级差异 ≥ 50%)
   - **(c)** 孔雀塌楼 narrative 内容换为延安路商住楼 / 钱塘江镇水石犴(年份 2003 或保留 2007),节点 ID 保留
   - **(d)** 雷峰塔地点改为净慈寺夕照山;浙大钟楼明示玉泉老校区;武林门刑场补 2-3 个年代衣着锚
   - **(e)** 调整 variants 顺序:`character` 分支提到 `visit_count_min` 分支前
2. 验证:
   - `python3 -c "import json; ..."` 占位 grep 断言
   - 新增断言:`if={}` 必须是 variants 数组最后一项
   - `pytest tests/ -k "lore or variant"`
3. **挂账后续 Pass**:
   - Pass 35-B:UX `[lore · 第 N 次查阅 · 已收录]` 状态行(需改 player.py)
   - Pass 35-C(可选):picker 已读 lore 灰显
   - 远期 ADR:`lore_seen[story_id]: list[node_id]` 跨周目联动字段

**不同意见记录**:无(6 角色一致同意 B 升 P0 + 孔雀换名 + 顺序 bug 顺手修)

---

## 附录:相关 ADR / 文档

- ADR-010 沙盒拓扑契约:`docs/architecture/ADR-010-sandbox-topology-contract.md`
- ADR-007/008 单一真相源:伏笔/推论
- 引擎代码:`src/ghost_story_factory/v5/player.py:799-806`(variants 匹配顺序)
- 数据文件:`stories/hangzhou_yebanbaoan/tree.json`
- 前序 Pass:`docs/team-reviews/2026-05-14-map-ux-deep-dive.md`(Pass 27a 修复 picker variants 死渲染 bug)
