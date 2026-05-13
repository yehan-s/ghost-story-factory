# 2026-05-13 项目下一步深入方向调研

> 评审团:script-review-team
> 任务 slug:next-direction-survey
> 报告生成时间:2026-05-13 (路线调研型,非实现任务)

---

## § 1. 任务描述

用户原话:**"启动团队,帮我调研一下现在是什么情况,可以列出接下来可以深入的地方"**。

这是路线调研型任务,不是"实现 X 功能"。目标:Pass 1-18 全部 Done、Pass 19 进行中的当前节点,产出"项目下一步可深入方向"的多视角短名单,作为后续 Pass 20 / Pass 21 切片依据。

**项目当前快照**:正式剧本 145/145 可达、21 结局、薄节点 31(Pass 18 刚从 50 压下);G-273 周目(56 入边 + 7 地标 + 9 工具)是 ADR-010 沙盒契约参考实现;linmou_1985 副线可达但 Act 1 是已挂账 sandbox debt(ADR-009,27 节点/0 工具/单向辐射);8 项 audit 守门工具锁定;8 个 open Issues 多为 audit 工具增强(p1-p3)。

**任务影响范围**:**多层**(剧本主导 + lore 配合 + 引擎守门,**非纯 UX**)。

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与

**层级判定**:**多层**

**意见**:
用户原话"剧本深度广度不达标""主角剧本不行"诉求落在剧本,但 Pass 17-19 已证明剧本病根经常需要 lore(角色弧线/伏笔账本)+ 引擎(audit_*)+ 拓扑(沙盒契约)联合修。UX/TUI 本轮不该是主战场——用户已明确说"不要被 TUI 拖住"。从连续性、伏笔兑现、复访分化、跨周目一致性角度,有 5 处值得深入。

**产出**:
- 方向 1 — **linmou Act 1 沙盒债清算(ADR-009)**:第二可玩角色走死剧本反模式是连续性丑闻,主角 G-273 立标杆 linmou 没跟上。开 M17 对标 ADR-010 沙盒最小骨架移植。
- 方向 2 — **伏笔-兑现链审计工具化(audit_foreshadow_chain)**:8 个守门工具无专项审"伏笔埋了没人捡 / 捡了没回响"。Pass 19 narrative_variants 承担兑现职责却无工具守,下次重写会塌。加入 audit_all.sh 第 9 项。
- 方向 3 — **跨周目联动实质内容补强(endings_seen 复用)**:CLAUDE.md 第一公理列了 `endings_seen[story_id]` 作 0 新字段联动方案,但两角色间几乎没有跨周目 reaction clause。纯 narrative_variants 工作。
- 方向 4 — **正式剧本"非主角群像"复访分化补完**:Pass 9 节点 ≥160、Pass 18 薄节点压到 31,但"薄节点"和"复访分化"是两件事。按"高频访问 NPC"维度跑一次 audit_variants 报告,挑 top 5-10 补 variants。
- 方向 5(长线低优先)— 第三可玩角色提案,linmou Act 1 沙盒债没还前不开新角色。

**Chief 优先级**:1 > 2 > 4 > 3 > 5。

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与

**意见**:
三大真相源已稳(endings_seen / foreshadows_seen / deductions_resolved / themes_resolved + reaction_contracts trigger_type)。**问题不在"少字段",在"既有字段没榨干"**——行为画像 7 维只打标签未反向喂 variants;reaction_contracts 跨 story_id 引用降级(#15)没修。

**产出**(全部 0 新字段路线):
- 新增 variants 条件思路:`{behavior_profile.<dim>: <threshold>}` — 让行为画像直接驱动反应 clause
- 引擎扩展需求:reaction_contracts 加 behavior_profile 派生条件支持(不加 player.py 持久字段)
- 5 方向:(1) 行为画像 → variants 闭环 (2) 跨 story_id ending 引用修复 + 联动扩面(close #15) (3) 薄节点反应化(接 variants + stay:true) (4) linmou Act 1 沙盒化(ADR-009 debt) (5) Verdict/审判维度跨周目可见
- **反加法警告**:不要为"玩家是否注意 NPC X"加 `noticed_npc` 类 flag;不要给行为画像在 `player.py` 加持久字段
- **推荐组合**:1 + 2 + 4

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:深度参与

**意见**:
数据底座完备(endings_seen + 行为画像 + 反应 clause),**但消费侧极薄**。21 结局无图鉴,True Ending 门槛黑盒,行为画像沉淀只在当周目用——玩家"周目厚度"感知不到。

**产出**(全部 0~1 新字段):
- 周目机制变更:(1) **结局图鉴 + Memory Echo**(对标 999 Flow Chart),hub picker 加 `_is_archive: true`,纯消费 `endings_seen` (2) **True Ending 门槛显式化**(对标 Steins;Gate 世界线变动率),hub 加"调查进度条"工具
- 收集本调整:(3) **「人格惯性」跨周目演出**(对标沙耶之歌),上周目主导画像影响本周目 NPC 对白 (4) **「死者命名」墓碑墙**(对标 Type-Moon 档案),`named_dead[story_id]` 同构 `endings_seen` (5) **跨剧本双向联动 linmou ↔ hangzhou**(对标 999/VLR 双主角)
- True ending 解锁条件变化:从黑盒变成显式调查进度,玩家可看到"还差 X 条线索"
- **优先**:#1 + #2 一周内可见,玩家周目厚度感知翻倍

---

## § 5. UX Designer — 文字体验设计师

**相关度**:**普通审查**(本轮不该当主角)

**意见**:
Pass 7-16 已把 VN 演出 + 选择意图 + 行为画像 + 过门反馈 + presenter 边界一整条管线打通。**机械层面就位,剩下不是缺组件,是组件传达的内容够不够撑住剧本质感**。本轮 UX 不加组件,审计现有文案。

**产出**(克制版):
- 玩家旅程节点变化:无新增,审计现有
- 5 方向:(1) 主角身份在文案层一致性审计(UX 必要) (2) 行为画像"克制度"复盘(基于真实周目录像) (3) 多周目"已见过"信息在正文里的呈现(与 Lore/State 协作) (4) 首次进入 → 第一结局心流计时(可用性观察) (5) 选择意图标签信息密度二次校准(回测剧透风险)
- **看似 UX 实非的警告**:玩家分不清线索 → Lore/State 的事;玩家不知下一步去哪 → 沙盒 connections 已经是答案;结局突兀 → Chief/Meta 的事;TUI 还能再美化 → 用户已明确说停

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与

**意见**:
**G-273 周目骨架搭好但肌理未填**。5 个民俗工具节点(雷峰塔虫/松木场客栈/浙大钟楼女孩/武林门刑场/孔雀坍塌)目前是"博物馆陈列柜"。北高峰缆车、红色电话亭、遗失档案室、红衣女孩、8 棺自己是"提到了但没用"重灾区——通用化换皮风险已经在门口。

**产出**:
- 新增元素考据清单(5 方向):
  1. **国营单位编号体系 lore 化**(G-273 / linmou 1985 工号绑成"编号继承链",反向解 linmou Act 1 sandbox debt 入口)
  2. **武林门刑场 → 单位大院选址叙事**(从孤立工具升级为"为什么这单位夜班邪"的根因)
  3. **湖滨夜班巡更路线**(雷峰塔虫 + 西湖夜雾):7 巡夜员绑真实地标,数字变可推理拓扑
  4. **遗失档案室 = 单位制记忆载体**(G-273 与 linmou 唯一物理交汇点)
  5. **浙大钟楼女孩 → 高校与单位夹缝**(挂钩叶某琴房背景)
- **通用化警告**:红衣女孩若只是"出现-惊吓-消失"就是换皮,必须绑保俶塔/1959 等具体坐标;8 棺自己若无半山公墓/南山陵园/单位制丧葬补贴根基就是廉价 jump scare,**要么坐实要么删**

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:深度参与

**意见**:
G-273 是 ADR-010 参考实现(拓扑健康度满分);linmou Act 1 是 sandbox debt(违反 5 项骨架中 4 项);其他周目/角色拓扑画像未审计——**盲区比已知 debt 更危险**。

**产出**:
- 节点结构变更:linmou Act 1 改造 picker hub + 地标网(保留"必死"不变量,即在沙盒拓扑里实现宿命)
- 状态维度调整:无新增全局维度,跨周目联动复用既有 `endings_seen` 局部读
- 可达性证明思路:改造后所有 linmou 既有结局必须仍可达(回归测试锁)
- 5 方向:(1) linmou Act 1 沙盒化改造(picker hub + 地标网,保留必死不变量) (2) **跨周目拓扑审计扩面**(零风险高 ROI,13 NPC × 7 场景跑合规度) (3) 反应 clause 跨周目联动深化(强化骨架第 5 项) (4) 工具节点 stay:true 自循环密度审计(识别"假工具") (5) picker hub connections 网状度评分(识别"伪 hub")
- **死剧本反模式警告**:新角色周目若不先签 5 项骨架直接打回;不要为"见过 X / 解开 Y"加 flags 镜像字段
- **推荐**:方向 2(审计扩面)→ 方向 5(网状度评分)→ 方向 1(linmou 改造,需审计数据先行)

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与

**意见**:
**"测试覆盖率虚高、语义覆盖率不足"**。8 项 audit 全绿但偏结构合规,对语义运行时(variant 实际触发率、跨周目继承、玩家路径分布)零覆盖。**现在测代码能跑,没测剧本能演**。

**产出**:
- Bug 清单(分等级):
  - **阻断**:保安线缺"主角行为画像不变量"审计(对称于 linmou 必死不变量)
  - **严重**:所有审计基于静态 JSON,无 TUI session 回放校验
- 5 方向:(1) audit_variants 增加触发率模拟(最短触发路径长度 + 必需前置 flag 数) (2) audit_script_depth 增加 variant 密度梯度检查(分桶基尼系数 >0.6 报警) (3) **新增 audit_cross_run_continuity**(最高优先级,验证 endings_seen 实际能被 variant 命中) (4) audit_sandbox 增加"工具节点实际可玩性"检查(工具裸奔标 warning) (5) 新增 test_path_coverage_regression(pytest golden file 锁关键路径)
- 回归测试入口:`pytest tests/test_path_coverage.py`(待实现)
- **QA 优先级**:#3 > #1 > #2 > #5 > #4

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**放行(以推荐 3 方向短名单作为下一阶段 Pass 20 / Pass 21 切片依据)**

本轮是**路线调研非实现**任务,不存在"风险清单",只存在"优先级共振"。7 人意见已显示三股清晰共振:

### 共振轴一(5 票):**既有真相源榨干,0 新字段路线**
Chief / State / Topology / QA / Meta **五人共指**——不再加字段,把 `endings_seen` / `foreshadows_seen` / `behavior_profile` 这些已经在的真相源,通过 narrative_variants + reaction_contracts 反向喂回剧本。这是 ADR-007/008/010 三个契约的合并红利,不动引擎就能让"周目厚度"翻倍。

### 共振轴二(3 票):**linmou Act 1 沙盒化(ADR-009 还债)**
Chief / State / Topology **三人共指**——第二可玩角色走死剧本反模式是已挂账的连续性丑闻。主角 G-273 立了 ADR-010 标杆,linmou 不跟上就是双重标准。

### 共振轴三(2 票):**audit 工具语义化扩展**
Chief / QA **两人共指**——8 项 audit 偏结构,缺 `audit_foreshadow_chain` / `audit_cross_run_continuity` / `audit_variant_trigger` 三项语义守门。Pass 19 已经在用 narrative_variants 兜底身份泄漏,无工具守等于把下一次塌陷的时间提前。

---

### **推荐 3 方向短名单**(下一阶段切 Pass 依据)

**Pass 20 候选 ★ —— 跨周目联动+行为画像反喂(共振轴一)**
- 内容:`endings_seen[story_id]` 反应 clause 扩面 + 行为画像 7 维派生 variants 条件
- 范围:0 新字段;改 narrative_variants + reaction_contracts
- 验收:audit_reactions 报告跨 story_id 引用 ≥ 5 条;高频复访 NPC 至少 60% 有行为画像分化 clause
- **为什么先做**:5 票共振、0 引擎风险、玩家可感知

**Pass 21 候选 ★ —— linmou Act 1 沙盒化还债(共振轴二)**
- 内容:对照 ADR-010 五项骨架,把 27 节点 / 0 工具 / 单向辐射改造为 picker hub + 4 地标 + 2 工具 + stay 自循环 + variants
- 范围:仅动 linmou Act 1 JSON;保留"必死"不变量
- 验收:`audit_sandbox` 对 linmou 输出健康 ≥ 0.7(对标 G-273)
- **为什么先做**:已挂账债务,Topology 警告"新角色不签骨架直接打回"——先把旧账还了再说新角色

**Pass 22 候选 ★ —— audit 工具语义化扩展(共振轴三)**
- 内容:新增三个 audit(`audit_foreshadow_chain` / `audit_cross_run_continuity` / `audit_variant_trigger`)并入 audit_all.sh
- 范围:纯引擎工具,不动剧本
- 验收:audit_all.sh 输出 11 项全绿;Pass 19 narrative_variants 兜底逻辑被工具锁住
- **为什么先做**:守门工具到位再做 Pass 20/21 的成果就能锁住,顺序上其实可与 Pass 20 并行

---

### 后续动作

- 用户决策:确认推荐短名单 → 助手用 writing-plans skill 把 Pass 20 拆任务(M2-M5),走 docs/tasks/TASK_NEXT_*.md 流程
- **不推荐**:第三可玩角色(Chief 方向 5)、UX 组件新增(UX 全员克制)、TUI 美化(用户已停)
- **挂账记录**:Lore Keeper 红衣女孩 / 8 棺自己"要么坐实要么删"决议,等触及对应节点时执行,不单独立 Pass

---

### 不同意见记录

- UX Designer:本轮不参加主战场,**主动让位**——本身就是共识,不构成阻塞
- Meta-Game Designer:推荐"结局图鉴 + Memory Echo"一周内见效,但 Chief/QA 担心在 linmou debt 没还前做收集系统会放大债务可见度。**记录备查**:Pass 22(audit 扩展)落地后再评估是否插入 Meta 的图鉴方向作 Pass 23

---

**Linus 一句话总结**:**"先把已有数据榨干,再还沙盒债,再加守门工具——三件事顺序不能换,换了就是给未来的自己挖坑。"**
