# TASK: 下一阶段目标 - 剧本深挖与 VN 沙盒可玩闭环

版本: v0.1
状态: Active
关联:
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS1.md`
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS2.md`
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS3.md`
- `docs/tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md`
- `docs/tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md`
- `docs/tasks/TASK_SCRIPT_BEHAVIOR_FEEDBACK_PASS6.md`
- `docs/tasks/TASK_SCRIPT_DEPTH_BREADTH_PASS9.md`
- `docs/tasks/TASK_SCRIPT_ROOT_CAUSE_PASS17.md`
- `docs/tasks/TASK_SCRIPT_THIN_NODES_PASS18.md`
- `docs/tasks/TASK_SCRIPT_PROTAGONIST_LEAK_PASS19.md`
- `docs/tasks/TASK_VN_PRESENTATION_RUNTIME_PASS10.md`
- `docs/tasks/TASK_CHOICE_AFFORDANCE_PASS11.md`
- `docs/tasks/TASK_VN_SANDBOX_IMPROVEMENT_PLAN_PASS12.md`
- `docs/tasks/TASK_BEHAVIOR_PROFILE_PASS13.md`
- `docs/tasks/TASK_TUI_EXPERIENCE_PASS14.md`
- `docs/tasks/TASK_TUI_SCENE_VIEW_PASS15.md`
- `docs/tasks/TASK_TUI_PRESENTER_BOUNDARY_PASS16.md`
- `docs/tasks/TASK_V7_AUDIT_DEBT_CLEANUP.md`
- `docs/tasks/TASK_GAMETREE_V1.md`
- GitHub Issue: `#22`
- GitHub Milestone: `v7 剧本深度与广度补强`

---

## 0. 当前判断

正式杭州剧本已经从“不可玩散点”推进到“可审计、可抵达、可重访有差异”的状态。

但它还没有达到目标里的 galgame / 视觉小说厚度。真正的问题不是再加几个吓人名词,而是三件事:

1. 玩家选择对角色关系的影响还不够可见;
2. 清洁工、论坛围观者、评价室已经完成第一轮人格化,Pass 8 已把三者推进为“曝光 / 删除 / 审判”的同一张 NPC 账本;
3. VN 演出字段已经覆盖正式节点,关键节点已补 `camera / cg_intent / transition_intent`,并被 `audit_playability` 关键节点 warning 锁住。

本任务记录下一阶段的目标,避免后续继续凭感觉修文本。

---

## 1. 当前问题记录

### 1.1 阻塞级问题

- 无。`bash tools/audit_all.sh` 已通过;
- 正式树当前节点可达率为 145/145;
- 当前结局节点为 21;
- `audit_variants` 未发现 `undifferentiated_revisit_nodes`。

### 1.2 非阻塞技术债

- `database/ghost_stories_test.db` 会被测试改动,当前是本地脏文件,不应提交;
- `audit_tree` 的 9 个 `inv_descriptions` 孤儿道具已在 Issue `#27` 第一批处理中收敛为 0;
- `audit_state` 已新增 `severity.errors / warnings / info` 分级输出,剩余 warning/info 可按后续任务继续压缩;
- `TASK_GAMETREE_V1.md` 和 GitHub Issue `#19` 仍处于 Active,需要单独收尾或拆出剩余项;
- `docs/specs/ISSUE_*` 与 `SPEC_TODO.md` 存在大量历史 TODO,不能作为下一阶段唯一真相源。

---

## 2. 下一阶段目标

### M1: 剧本 Pass 3 - 叶某与巡夜员群像

状态: Done,见 `docs/tasks/TASK_SCRIPT_SANDBOX_PASS3.md`。

目标:

- 让叶某从“203 琴房事件”升级为能影响林晓燕、赵某、True/Truth/Data 三类结局的角色;
- 让 7 名巡夜员不只是安全帽数字,而是在 S6/B3/结局中体现不同失败方式;
- 让清洁工、论坛围观者、评价室不再只承担功能判断,而是反馈玩家之前的选择姿态;
- 继续保持开放沙盒,不锁死固定地标顺序。

验收:

- 至少 3 个旧 NPC 在重访时出现新的关系型 variant;
- 至少 2 个结局根据叶某或巡夜员群像状态出现差异文本;
- `audit_variants` 仍保持 `undifferentiated_revisit_nodes: []`。

### M2: 互动反馈 - 玩家不是摄像机

状态: Done。Pass 4 已完成入口、地图、晨湖和核心结局的赵某身份回收;Pass 5 已完成论坛 / 清洁工 / 评价室对曝光、注销、审判姿态的回收;Pass 6 已把行为画像前移到地图 hub、工具回访、B3 与晨湖。见 `docs/tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md`、`docs/tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md` 与 `docs/tasks/TASK_SCRIPT_BEHAVIOR_FEEDBACK_PASS6.md`。

目标:

- 建立“玩家行为画像”的最小规则,例如:救人优先、取证优先、替班逃避、曝光冲动;
- 把行为画像写进 B3、评价室、晨湖、Data/Truth/True End 的文本回收;
- 不新增复杂好感度系统,优先复用现有 flag / deduction / theme。

验收:

- 玩家至少能在终局前看到自己玩法被系统或 NPC 反咬一次;
- 至少 3 类选择姿态能在不同节点产生可读差异;
- 不新增 DB schema。

### M3: VN 演出契约 - 素材未到,结构先到

状态: Done for current baseline。Pass 4 已给入口 / 简报 / 地图 / 晨湖补关键 `presentation`;Pass 5 已在论坛 / 清洁工 / 评价室 / Data / Broadcast / Hidden 结局补 `camera / cg_intent / transition_intent`;Pass 7 已补遗失档案、红色电话亭、B3、红衣女孩、8 棺自己、True / Truth / Bad / Neutral 等关键节点,并在 `audit_playability` 中锁定关键节点演出意图 warning。正式树仍保持 145/145 演出字段覆盖。

目标:

- 明确 `presentation` 字段的最小契约:背景、角色位、音效、镜头、CG fallback;
- 对关键节点标记“未来应替换为 CG / 立绘 / 音效”的素材槽;
- 增加审计,保证正式节点不会缺少基础演出字段。

验收:

- 关键 NPC 和结局节点有稳定的 `presentation` 语义;
- 审计能报告缺失素材槽,但不要求真实图片音频立刻存在;
- CLI 仍能用 text fallback 正常运行。

### M4: 工具债收敛

状态: Done for current baseline。Issue `#27` 已完成 audit_tree 孤儿道具口径修正与 audit_state 分级输出;Issue `#19` 已关闭并把 v4 生成器对齐拆到 `#23`;已完成的 `#31` / `#33` 也已关闭,当前 milestone 只剩 roadmap `#22` 与 v4 生成器对齐 `#23`。

目标:

- 处理 9 个孤儿道具描述:要么接入节点,要么删除注册;
- 给 `audit_state` 增加分级输出,把历史噪音从真正错误里拆开;
- 收尾 `TASK_GAMETREE_V1.md` 与 Issue `#19`,把已完成项勾掉,剩余项拆新任务。

验收:

- `audit_tree` 不再报告无意义孤儿道具;
- `audit_state` 的输出能分出 error / warning / info;
- Issue `#19` 状态与 Task 文档一致。

### M5: 剧本 Pass 8 - NPC 关系账本与终局前回咬

状态: Done,见 `docs/tasks/TASK_SCRIPT_NPC_ACCOUNTABILITY_PASS8.md` 与 GitHub Issue `#36`。

目标:

- 让论坛、清洁工、评价室不再只是功能节点,而是共同读取玩家取证、曝光、删痕、审判和命名行为;
- 用既有 `arc.named_the_dead / oneshot.live_streaming / oneshot.s6_no_fingerprint / arc.got_judge_seal / route.behavior_self_audit` 建立终局前回咬;
- 保持开放沙盒和 DB schema 不变。

验收:

- `n_npc_forum_lurkers` 写入命名死者状态;
- `n_npc_cleaner_null`、`n_scene_b3_corridor`、`n_scene_evaluator_room`、`n_scene_morning_lakeside` 读取 NPC 账本状态;
- 新增 `tests/test_npc_accountability_pass8.py`;
- `audit_all` 与统一测试通过。

### M6: 剧本 Pass 9 - 深度与广度补强

状态: Active,见 `docs/tasks/TASK_SCRIPT_DEPTH_BREADTH_PASS9.md`。

目标:

- 把“剧本厚度”从主观评价变成审计指标:节点数、最短结局路径、薄节点比例、地标层数、工具复访、variant 密度、VN 演出意图覆盖;
- 让林某 1985 线成为正式可达内容,不再只是注册在 `characters` 里的孤立前传;
- 补强至少 3 个 G-273 地标的跨地标 / 跨角色因果回收;
- 保持开放沙盒,不新增 DB schema,不把玩法改成线性章节。

验收:

- `tools/audit_script_depth.py` 通过;
- 正式树节点数不得低于 160;
- 林某线在深度审计中单独计入并可从角色入口游玩;
- `camera / cg_intent / transition_intent` 覆盖的关键节点数量不得低于 30;
- `audit_all` 与统一测试通过。

### M7: VN 演出契约进入运行时

状态: Done,见 `docs/tasks/TASK_VN_PRESENTATION_RUNTIME_PASS10.md`。

目标:

- 把已经写入正式树的 `presentation` 从审计字段变成玩家可见的运行时体验;
- v5 CLI 与 v7 TUI 复用同一套演出格式化器;
- 用 `tree.assets` 显示中文资产 label,避免裸 id 破坏沉浸;
- 没有 `presentation` 的旧树保持静默,不破坏旧运行路径。

验收:

- CLI 在 narrative / map 前显示压缩后的演出提示;
- TUI 显示同一提示且 Rich markup 安全;
- 新增渲染层测试;
- `audit_all` 与统一测试通过。

### M8: 选择意图与风险提示

状态: Active,见 `docs/tasks/TASK_CHOICE_AFFORDANCE_PASS11.md`。

目标:

- 让玩家在做选择前看到非剧透的行动意图,例如观察、移动、取证、路线留痕、心理高压;
- CLI 与 TUI 复用同一套选择标签 formatter;
- 不暴露精确 PR / GR 数值,不把恐怖沙盒变成优化表格;
- 无 effects 的旧选择保持原样。

验收:

- 选择列表显示最多 2 个短标签;
- 可用 `GHOST_CHOICE_HINTS=0` 关闭;
- 新增选择标签测试;
- `audit_all` 与统一测试通过。

### M9: VN 沙盒体验改进总方案

状态: Planning,见 `docs/tasks/TASK_VN_SANDBOX_IMPROVEMENT_PLAN_PASS12.md`。

目标:

- 把下一阶段改进拆成可执行路线,避免继续凭感觉加节点;
- 明确优先级:基线清账 → 选择后反馈 → 角色关系账本 → 周目复盘 → 演出优先级 → 质量红线;
- 将“深度不够”转成可验收的玩家反馈链路。

验收:

- 方案文档落地;
- 团队评审留痕;
- 后续 Pass 13 可直接从方案切出 Task / Issue。

### M10: 选择后反馈闭环与本轮行为画像

状态: Done,见 `docs/tasks/TASK_BEHAVIOR_PROFILE_PASS13.md`。

目标:

- 选择后显示短反馈,让玩家知道路线账本记住了这一步;
- 在地图 hub、B3、评价室、晨湖和结局节点显示本轮行为画像;
- 至少覆盖取证、曝光、救援/命名、审判/删除、漏卡/绕开等倾向;
- 不新增 DB schema,不暴露 PR / GR 数字。

验收:

- CLI/TUI 都显示选择后反馈;
- 关键节点能显示最多 2 行行为画像;
- 新增行为画像测试;
- `audit_all` 与统一测试通过。

### M11: TUI 体验收束与停留选项去重

状态: Done,见 `docs/tasks/TASK_TUI_EXPERIENCE_PASS14.md`。

目标:

- 把 TUI 作为正式体验入口处理,本轮不再以 CLI 为主;
- 修复 `stay` / “看一眼”重复刷当前节点 narrative / map 的体验问题;
- TUI 状态页移除内部 flag key,改为路线账本、行为画像、档案进度;
- 增加顶部场景条和 TUI 专属选择 badge。

验收:

- 观察细节不重复整屏正文;
- 选择列表更适合扫读;
- 状态页不再像调试面板;
- 新增 TUI helper / 行为回归测试;
- `audit_all` 与统一测试通过。

### M12: TUI 当前场景视图与过门反馈

状态: Done,见 `docs/tasks/TASK_TUI_SCENE_VIEW_PASS15.md`。

目标:

- 主阅读区从滚动日志改成当前场景视图;
- 新节点渲染前清屏;
- 上一选择与路线账本反馈作为过门显示在下一屏顶部;
- `stay` / detail 保持原地追加,不清屏。

验收:

- 切节点不会堆叠旧 narrative;
- 选择反馈不会丢,会进入下一屏顶部;
- stay/detail 不重复访问计数;
- 新增 TUI 回归测试;
- `audit_all` 与统一测试通过。

### M13: TUI 表达层边界拆分

状态: Done,见 `docs/tasks/TASK_TUI_PRESENTER_BOUNDARY_PASS16.md`。

目标:

- 找出 TUI 病根:App 类混合状态、存档、表达格式化和 widget 操作;
- 新增 TUI presenter 模块,集中 Rich 转义、选择 badge、状态页、复盘、过门等纯表达函数;
- `tui_player.py` 不再直接持有这些 formatter;
- 不改 CLI / 正式剧本 / DB schema。

验收:

- 新增 presenter 边界测试;
- TUI 既有行为测试继续通过;
- `audit_all` 与统一测试通过。

### M14: 正式剧本病根深改

状态: Done,见 `docs/tasks/TASK_SCRIPT_ROOT_CAUSE_PASS17.md`。

目标:

- 修掉终局入口像菜单的结构病;
- 给晨湖高阶结局增加 `require` 门槛;
- 补强赵某 / G-273 / 记录表 / 行为账本的终局压力;
- 新增审计和测试,防止 True / Truth / Data / Hidden 无门槛回退。
- 新增主角履历审计,防止 G-273 首访文本混入旧版中年老保安设定。

验收:

- 晨湖高阶结局不再无条件可选;
- `audit_script_depth` 能报告终局门槛缺失;
- `audit_script_depth` 能报告单行路回地图与 G-273 旧履历泄漏;
- fragments 合并后的正式树通过 `audit_all` 与统一测试。

### M15: 正式剧本薄节点压缩

状态: Done,见 `docs/tasks/TASK_SCRIPT_THIN_NODES_PASS18.md`。

目标:

- 将 `audit_script_depth` 的薄节点数从 50 压到 31;
- 补强林某证据链和 G-273 前半夜行动节点;
- 让关键选择不再像提纲跳转,而是有动作、感官、后果;
- 新增薄节点上限审计,防止回退。

验收:

- 正式树薄节点数不高于 31;
- `audit_script_depth` 能把薄节点超标作为错误;
- fragments 合并后的正式树通过 `audit_all` 与统一测试。

### M16: G-273 主角身份泄漏清扫

状态: Active,见 `docs/tasks/TASK_SCRIPT_PROTAGONIST_LEAK_PASS19.md`。

目标:

- 清理正式剧本中残留的旧版中年保安主角设定;
- 将主角履历审计从默认 narrative 扩展到所有 `narrative_variants`;
- 修正 TUI 地图首开硬编码文案,避免“媳妇合照”等旧设定逃过剧本审计;
- 保持赵某为 2024 新入职、缺钱、误接编号的当前主角。

验收:

- 正式树不再包含 G-273 旧履历泄漏;
- `audit_script_depth` 能抓到 variant 里的旧履历词;
- TUI 首开地图文案不再泄漏旧主角设定;
- fragments 合并后的正式树通过 `audit_all` 与统一测试。

### M17: Pass 20 - 跨周目联动与行为画像反喂 variants

状态: Done,见 `docs/tasks/TASK_SCRIPT_REACTION_PROFILE_PASS20.md`。
来源 `docs/team-reviews/2026-05-13-next-direction-survey.md`(7 人共振 5 票)。

目标:

- 把"既有真相源榨干"——0 新字段,只动 `narrative_variants` 与 `reaction_contracts`;
- 让行为画像 7 维(救人/取证/替班/曝光/命名/删痕/审判)从"打标签"变成"反向喂 variants",在 NPC 复访 / 终局回咬里直接读 dominant_tag;
- 修 `audit_reactions` 跨 story_id `endings_seen` 引用降级(close #15),让跨周目联动真正生效;
- 至少补强 verdict / 审判维度在二周目可见;
- 保持开放沙盒,不新增 DB schema,不在 player.py 加持久字段。

验收:

- `reaction_contracts` 出现 behavior_profile 派生条件,且 G-273 至少 3 个 NPC 节点读这一条件分化;
- `endings_seen[story_id]` 跨周目引用在 audit_reactions 全部 pass,无降级;
- 至少 2 个 hangzhou ending 在二周目展示"上周目你判了谁"的回咬文本;
- `audit_all` 与统一测试通过。

非目标:

- 不加新 flag 镜像兑现状态;
- 不在 player.py 加 noticed_* / seen_* / met_* 字段;
- 不重写行为画像引擎。

### M18: Pass 21 - linmou Act 1 沙盒化(ADR-009 还债)

状态: Done,见 `docs/tasks/TASK_LINMOU_SANDBOX_PASS21.md`。
来源 `docs/team-reviews/2026-05-13-next-direction-survey.md`(7 人共振 3 票)。

目标:

- 把 linmou_1985 Act 1 的 27 节点 / 0 工具 / 单向辐射重构为符合 ADR-010 五项骨架的沙盒;
- 复用 G-273 周目作为参考实现(picker hub + 网状 connections + stay:true 工具自循环 + reaction variants);
- 保留 linmou "必死" 不变量(ADR-009),改造前 freeze ending_seen 入口;
- 不引入新角色/新结局,只重构现有 27 节点的拓扑形状。

验收:

- linmou Act 1 至少 1 个 `_is_map_picker: true` hub 节点;
- ≥ 4 地标,每个 ≥ 1 条 `connections` 邻边;
- ≥ 2 个 `_is_tool: true` 节点;
- ≥ 1 处 `effects.stay: true` 自循环;
- ≥ 1 处 `narrative_variants[].if.{deduction_resolved | foreshadow_resolved | theme_resolved | ending_seen}` 反应 clause;
- `audit_sandbox` 在 linmou Act 1 通过(不再列入 sandbox debt);
- `audit_paths_linmou` 仍保持必死不变量绿;
- ADR-009 状态从 Active 改为 Resolved 或 Superseded;
- `audit_all` 与统一测试通过。

非目标:

- 不为 linmou 加新结局;
- 不打破必死不变量;
- 不动 G-273 周目。

### M19: Pass 22 - audit 语义化三件套

状态: Done,见 `docs/tasks/TASK_AUDIT_SEMANTIC_PASS22.md`。
来源 `docs/team-reviews/2026-05-13-next-direction-survey.md`(7 人共振 2 票),可与 M17 并行。

### M20: Pass 23 - 主结局跨周目反咬补完

状态: Done,见 `docs/tasks/TASK_SCRIPT_CROSS_RUN_FINALE_PASS23.md`。
本 Pass 由 M19 的 audit_cross_run_continuity 揭示的剧本债务衍生而来——
沿用 Pass 20 (M17) 反咬模式,给 4 处主结局补 ending_seen variant。

目标:

- 把 audit 从"结构合规"扩展到"语义运行时",填补"在测代码能跑,没测剧本能演"的盲区;
- 新增三件工具:
  1. `audit_foreshadow_chain`:守"伏笔埋了但没人捡 / 捡了没回响",与 audit_variants 配对;
  2. `audit_cross_run_continuity`:验证 `endings_seen[story_id]` 在二周目真能被某 variant clause 命中,而非空挂;
  3. `audit_variant_trigger`:模拟最短触发路径长度 + 必需前置 flag 数,超阈值标 warning;
- 全部纳入 `tools/audit_all.sh`(第 9-11 项);
- 纯引擎工具,不动剧本。

验收:

- 三件工具落地并跑通正式 tree.json;
- `tools/audit_all.sh` 升级到 11 项,全绿;
- 新增 `tests/test_audit_foreshadow_chain.py` / `test_audit_cross_run_continuity.py` / `test_audit_variant_trigger.py`;
- 保安线增加"主角行为画像不变量"审计(对称 audit_paths_linmou);
- `audit_all` 与统一测试通过。

非目标:

- 不改剧本本体;
- 不强求 TUI session 回放校验(中危盲区挂账到后续 Pass);
- 不重写既有 8 项 audit 内部逻辑,只扩展。

---

## 3. 推荐执行顺序

1. 已完成 M4 的 `TASK_GAMETREE_V1` 收尾,项目账本已清;
2. 已完成 M1-M5 的剧本、行为反馈、VN 契约和 NPC 账本;
3. 当前优先做 M6 Pass 9,把“可玩闭环”推进到“内容厚度达标”;
4. M7 已完成,演出字段已进入运行时;
5. M8 已完成,选择意图已进入运行时;
6. M9 已完成,下一阶段总方案已落地;
7. M10 已完成,选择前意图已经接上选择后反馈闭环;
8. M11 已完成,TUI 从“能玩”推进到“读起来不累”的第一层闭环;
9. M12 已完成,主阅读区已从滚动日志改成当前场景视图;
10. M13 已完成,拆出 TUI 表达层,处理反复长体验问题的病根;
11. M14 已完成,正式剧本终局入口、单行路和 G-273 履历一致性进入审计红线;
12. M15 已完成,薄节点从 50 降到 31,并进入审计红线。
13. M16 已完成,主角身份泄漏清扫已落地(Pass 19)。
14. M17 已完成(Pass 20),**已把已有数据榨干**——跨周目联动 + 行为画像反喂 variants 接入引擎,#15 闭环,0 新字段;
15. M18 已完成(Pass 21),**沙盒债已偿**——linmou 子图独立满足 ADR-010 五项骨架,账册包+搪瓷缸升级为 tool 节点;
16. M19 已完成(Pass 22),**守门工具已加**——audit 语义化四件套(foreshadow_chain / cross_run_continuity / variant_trigger / protagonist_behavior),audit_all 从 8 项升到 12 项。
17. M20 已完成(Pass 23),**主结局反咬已补**——E_TRUE / E_BROADCAST / E_NEUTRAL / E_HIDDEN 各 1 处反咬 variant,cross_run_continuity debt 清零。
18. M21 已完成(Pass 24),**linmou ending 反咬已补**——E_LINMOU_RELEASE(米黄牛皮纸袋)/ E_LINMOU_EXPOSED(广播喇叭三遍)2 处反咬 variant 接入 G-273 主线节点。
19. M22 已完成(Pass 25),**人格惯性协议已落地**——`ending_seen.last` 协议 + record_ending 末尾重排 + ADR-011 映射表 + audit_profile_inheritance,audit_all 升到 13 项;4 项 main ending .last 反咬留 debt。
20. M23 已完成(Pass 26),**人格惯性 debt 清零 + 阻断升级**——E_TRUTH / E_BROADCAST / E_DATA / E_HIDDEN 各补 1 条 `.last` 残影变体,audit_profile_inheritance 默认 strict、CI 一票否决。新增 main ending 缺 .last consumer 的 PR 现在直接被红线挡下。

理由很简单:先清账,再加戏。否则后面每一次剧本增强都会被旧告警和旧任务拖住。

**M17/M18/M19 顺序不可换**:换了等于先在没扎实的数据底座上扩沙盒,再用未及格的审计验证——给未来的自己挖坑。详见 `docs/team-reviews/2026-05-13-next-direction-survey.md`。

**短名单全部落地后**:audit_cross_run_continuity 揭示 4 处主结局(E_TRUE / E_BROADCAST / E_NEUTRAL / E_HIDDEN)跨周目无反咬,留 Pass 23+ 偿还。下一阶段方向回到评审团短名单表上挑选。

---

## 4. 非目标

- 不做 Web UI;
- 不做真实图片 / 音频资产生产;
- 不新增数据库 schema;
- 不把沙盒改成线性章节;
- 不引入复杂数值好感度系统。
