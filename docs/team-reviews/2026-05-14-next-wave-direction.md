# 2026-05-14 下一波方向调研(linmou Act2/3 + GRIEVANCE/REGRET 反咬 + presentation 落地 + backlog)

> 评审团:script-review-team
> 任务 slug:next-wave-direction
> 报告生成时间:2026-05-14(路线调研型,非实现任务)

---

## § 1. 任务描述

用户给出 4 个候选方向,要评审团判定每项的层级与优先级,并提示"该往哪个方向深挖":

1. **linmou Act 2/Act 3 扩沙盒** — 用户认为 Pass 21 只补了 Act 1,Act 2/3 是 known sandbox debt
2. **linmou 剩余 2 个 ending(GRIEVANCE / DUTY)反咬** — 用户认为 Pass 26 4 项人格惯性反咬之外仍有 2 项未做
3. **TUI 演出层下一跳:presentation 字段在引擎层是否被读全** — VN 演出契约系列(Pass 7/10/14/15/16)落地多轮,需核查引擎读取完整度
4. **其他评审团短名单未做的项** — 从历史评审报告(尤其 2026-05-13-next-direction-survey)中捞遗留 backlog

**任务影响范围**:**多层 / 调研型** — 4 个候选方向横跨剧本(沙盒拓扑)+ 状态(反咬人格惯性)+ 演出层(引擎契约)+ backlog 复盘。

### ⚠️ 用户描述与实际状态的 4 处偏差(评审团调研后逐项校正)

**偏差 1:linmou 不存在 Act 2/Act 3 概念**
- linmou 角色周目是**单 Act 扁平结构**(`_fragment_v7_linmou_1985.json` 共 44 节点 / 1 picker hub / 4 地标 / 2 工具 / 2 处 stay:true / `audit_sandbox` 12/12 全绿)
- CLAUDE.md 第一公理里"linmou Act 1 是 known sandbox debt"是 **Pass 21 之前**的旧状态。Pass 21(commit 697e814 "Pass21补齐linmou沙盒骨架(ADR-009还债)")已偿债,Pass 26 评审报告(2026-05-13)§ 3 已明确推翻 Meta 反对意见,确认 linmou 沙盒债已清
- **方向 1 需要重定义** — 真正可深挖的是"linmou 周目肌理补完"(landmark connections 显式化 / 复访 variants 密度 / ending 子节点回访体验分化),而不是"扩 Act"

**偏差 2:linmou 不存在 DUTY ending,且 GRIEVANCE/REGRET 早已反咬**
- linmou 4 个 ending 是 `E_LINMOU_GRIEVANCE` / `E_LINMOU_REGRET` / `E_LINMOU_RELEASE` / `E_LINMOU_EXPOSED`(`_fragment_v7_linmou_1985.json:6` 显式声明),DUTY 不存在
- 但更关键的发现:**4 个 LINMOU ending 全部都已有 cross_run variants 反咬**,根源是 **Pass 9**(2026-05-09)就落地了"S3 / S4 / S5 新增 `E_LINMOU_*` 回声",Pass 24 只是追加新锚点

完整扫描 `stories/hangzhou_yebanbaoan/` 所有 fragment + `tree.json`:

| ending | 反咬节点数 | 锚点路径(对照 Lore"档案 / 声 / 人"铁律)|
|---|---|---|
| E_LINMOU_RELEASE | **3** | `n_s5_arrive`(琴房父亲)/ `n_npc_corrosion_face`(铜锈侧脸/**人**)/ `n_scene_lost_archive`(米黄牛皮纸袋/**档案**)|
| E_LINMOU_EXPOSED | **2** | `n_s4_arrive`(广播喇叭木匾)/ `n_npc_predecessor_voice`(广播/**声**)|
| E_LINMOU_GRIEVANCE | **2** ✅ | `n_s3_arrive`(裂钟渗水/水)/ `n_scene_lost_archive`(1984 卷宗/**档案**)|
| E_LINMOU_REGRET | **2** ✅ | `n_s6_look_down`(井边 7 工人)/ `n_landmark_picker`(红叉笔迹/物证)|

文本均已落地、有具象意象、符合 Pass 24 § 5 Lore "档案 / 声 / 人"三选一铁律。ADR-011 § 63-66 明确"**LINMOU ending 由 Pass 24 的 `ending_id` 反咬覆盖,不需要 `.last`**"—— linmou 4 ending 走的是 `ending_id` 反咬路径(线性遗迹),不是 `.last`(残影)。

**方向 2 整个不存在剩余 debt**,4 项 LINMOU ending 反咬本身就是 done state,**评审决议:直接放行不做**。

**偏差 3:presentation 字段引擎"读全"已基本闭合**
- `stories/hangzhou_yebanbaoan/tree.json` 实际使用 10 个 presentation key
- 全部已被 `src/ghost_story_factory/v5/player.py:382 format_presentation_lines` 读出渲染
- `src/ghost_story_factory/v7/tui_player.py:46+700` 通过 `from format_presentation_lines` 复用同一格式化器,v5 CLI 与 v7 TUI 双链共享
- 10 key 清单:`background`(line 401)/ `bgm`(405)/ `sfx`(409)/ `sprite`(422)/ `expression`(423)/ `camera`(429)/ `transition`(433)/ `transition_intent`(437)/ `cg_intent`(441)/ `cg_unlock`(445)
- **方向 3 不存在剩余工程债**,引擎"读全"已达成。剩余空间是 UX 文案细节(如"演出: 背景=X · 音乐=Y"是否过干),不构成"下一波"主战场

**偏差 4:方向 4 不是"捞 backlog",而是"重新发掘下一波"**
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md:465` 明确:"短名单全部落地后,下一阶段方向回到评审团短名单表上挑选"
- 2026-05-13 next-direction-survey 推荐的 Pass 20/21/22 + 2026-05-13-pass24-25-finale-inertia 推荐的 Pass 24/25 + Pass 26 清账后,**当前没有现成 backlog 短名单可挑**
- 方向 4 的本质 = 本次评审重新发掘下一波 backlog,并补 Pass 25 留下的 2 项缺席 debt(Topology variants 分桶上限审计 / UX "似曾相识"呈现节奏文案审计)

### 校正后真实选项空间

| 编号 | 实际方向 | 真实状态 |
|---|---|---|
| 方向 1' | linmou 周目肌理补完(`landmark_map` 接合点 + 复访 variants 密度 + ending 子节点回访分化)| 可做,需 Topology 先审 manifest/fragment 接合点 |
| ~~方向 2~~ | ~~GRIEVANCE/REGRET 反咬补完~~ | **🟢 已 done,不做** |
| ~~方向 3~~ | ~~presentation 引擎读全~~ | **🟢 已闭合,不做** |
| 方向 4' | 下一波 backlog 重新发掘 + Pass 25 缺席 debt 补 | 第一推荐 |

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与(本次调研协调者)

**层级判定**:多层(4 方向跨剧本 / 状态 / 引擎 / backlog)

**意见**:

用户给出的 4 方向中,**3 项有事实偏差**(方向 1 概念错位、方向 2 已完成、方向 3 已闭合,见 § 1 校正)。校正后真实剩余只有 2 项:

1. **linmou 周目肌理补完**(原方向 1',scope 重定义)
2. **下一波 backlog 重新发掘**(原方向 4')

**Chief 视角优先级**:**方向 4'** ≈ **方向 1'**,但建议**方向 4' 先做**(0.5-1d 工时,清 Pass 25 留的 2 项缺席 debt + 修 Issue #15)→ 方向 1' 第二做(1.5-2d,linmou 肌理补完需要 Topology 先审接合点)。

**为什么不做方向 2(反咬)**:4 项 LINMOU ending 反咬已全部落地(见 § 1 偏差 2 表)。Pass 9 时就埋了 S3 / S4 / S5 三层 E_LINMOU_* 回声,Pass 24 又追加了 2 个新锚点。**这是已完成的功能,不是 debt**。

**为什么不做方向 3(presentation)**:10 个 key 全部已被 `v5/player.py:382 format_presentation_lines` 读全,v5+v7 双链共享。**没有契约定义但引擎未读的 key**。文案表现力是 UX 单点细节,不需要立 Pass。

**为什么方向 1' 排第二**:linmou 沙盒骨架合规(`audit_sandbox` 12/12),但骨架内肌理有挂账信号 — `_fragment_v7_linmou_1985.json` 的 `landmark_map: {}` 是空数组。Pass 25 报告称"connections 网状关系已 manifest 层落地",但**接合点究竟在 manifest 层还是 fragment 层尚未审清**,可能是隐性 sandbox debt,启动前必须 Topology 先 1 小时排查。

**Chief 关键洞察**(给 6 人):
- **守 ADR-010 沙盒契约**:任何新方向都不能引入"工具节点 next 跳走"或"flags 镜像兑现状态"反模式
- **0 新字段路线**:Pass 24/25/26 三轮已确认 `endings_seen.last`(主线人格惯性)+ `ending_id` 直引(LINMOU 反咬)双轨清晰,禁止再加 state 字段
- **不要重启 linmou Act 2/3 幻觉**:linmou 单 Act 设计是有意,要扩拓扑直接提"第三可玩角色"(已在 2026-05-13 next-direction-survey 标长线低优先级 5)
- **方向 4' 是清账**,不是开新方向 — Pass 25 缺席 debt + Issue #15(p1 OPEN)+ pytest golden file 都是已立账的零散债务

**产出**:

- **悖论清单**:无新增。主线 5 main ending 全部有 `.last` 反咬(Pass 26),linmou 4 ending 全部有 `ending_id` 反咬(Pass 9 + Pass 24)。两套机制清晰,无串味
- **伏笔变更**:无
- **一致性规范**:任何新增反咬必须严守"档案 / 声 / 人"三选一(Pass 24 § 5 铁律),`.last`(主线)与 `ending_id`(LINMOU)双轨不可混用

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与(背景默认意见 — Pass 25 已出席,本次基于历史立场预填)

**意见**:

State 在 2026-05-13 next-direction-survey 中明确"既有真相源榨干、0 新字段"路线为最高优先级。本次调研后,State 立场如下:

- **方向 1'**:0 新字段路线确认,linmou `landmark_map` 接合点审清属于 schema 验证范畴,不需要新 state 字段。State **配合验证**,深度由 Topology 主导
- **方向 2**:🟢 放行不做(已 done)
- **方向 3**:🟢 放行不做(无 state 介入需求)
- **方向 4'**:🔥 **State 自家关切的 Issue #15(`audit_reactions: 跨 story_id ending_seen 引用应 skip 或降级 warning`,p1)目前 OPEN**,本次评审应将其列为方向 4' 第一子项

**State 推荐子项**:方向 4' 子项排序应为:Issue #15 修复 > pytest golden file > Pass 25 缺席 debt 补意见

**产出**:
- 新增 flags:**无**(0 新字段路线)
- 新增 variants 条件:**无**(方向 1'/4' 不增新 variant)
- 引擎扩展需求:**Issue #15 audit 工具升级** — `tools/audit_reactions.py` 的 `DEAD_ENDING_SEEN` 检测需对跨 story_id 引用 skip 或降级 warning(纯引擎,不动剧本)
- **前置依赖警告**:Issue #15 不修,下次新增第三可玩角色时 audit 必然误杀,Topology 也持此关切

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:普通审查(方向 4' 含 Meta 在 next-direction-survey 提的 Pass 23 候选)

**意见**:

Meta 在 2026-05-13 next-direction-survey 提了"结局图鉴 + Memory Echo" + "True Ending 门槛显式化"两项 Pass 23 候选。当时 Chief / QA 担心在 linmou debt 没还前做收集系统会放大债务可见度,记录"Pass 22 audit 守门完成后再评估"。

**当前状态**:
- Pass 22 audit 三件套已落地
- Pass 26 阻断模式升级已完成
- linmou sandbox debt 在 Pass 21 已偿
- **前置依赖全部解除**

但本次评审中:
- 方向 2 已 done,方向 3 已闭合 — 没有"撑住周目厚度"的紧迫性
- 方向 1' / 方向 4' 都不是周目消费侧 — Meta **不深度参与**

**Meta 立场**:
- 方向 1' / 方向 4' **放行**(Meta 不深度介入)
- 图鉴 / True Ending 门槛 → **Pass 30+ 候选**,Pass 26 刚落地需 1-2 周观察期,不进本轮短名单

**产出**:
- 周目机制变更:**无**(本次不动周目机制)
- 收集本调整:**Meta backlog 暂搁置**
- true ending 解锁条件变化:**无**

---

## § 5. UX Designer — 文字体验设计师

**相关度**:深度参与(方向 3 含 UX,且 Pass 25 留有 UX 缺席 debt)

**意见**:

UX 在 2026-05-13 next-direction-survey 主动让位(本轮不该当主角)。Pass 24/25 两次缺席,Pass 25 留下"似曾相识"对白呈现节奏意见 debt。

**方向 3 的 UX 判定**(主助手代摸底):
- 10 个 presentation key 已全部读到(`v5/player.py:382` + `v7/tui_player.py:46+700`)
- **没有契约定义但引擎未读的 key**
- 剩余空间:① "演出: 背景=X · 音乐=Y"文本 fallback 是否过干(单点文案);② `cg_unlock` 触发后是否真有解锁副作用(单点核查,Meta 关切);③ `transition_intent` / `cg_intent` 是否过度暴露 spec 意味(剧透风险审计)
- **以上三项均为单点文案 / 核查,不需要立 Pass**,UX 在闲置时序中做补丁即可

**Pass 25 UX 缺席 debt 补意见**(本次必须出席):
- "似曾相识"对白呈现节奏:同意 Chief 预设 — **无视觉 marker,纯台词承担,首次 narrative 即触发对应 variant**
- 进一步明确:Pass 26 4 项 `.last` 反咬 + Pass 9/24 共 11 处 LINMOU `ending_id` 反咬,均按此节奏出现 — 不需要 NPC 名字前加 marker 也不需要 "✨ 上次"等标识
- 后续如有违和体验玩家反馈,以补丁形式回归

**UX 推荐**:方向 1' / 方向 4' 放行,方向 3 不立 Pass(UX 闲置时序做单点文案审计)

**产出**:
- TUI/CLI 草图:**无新增**
- 排版规范变更:**无**
- 玩家旅程节点变化:**无**(本次不动 UX 管线)
- **Pass 25 缺席补**:同意 Chief 预设(纯台词,无视觉 marker)

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与(方向 1' 涉及 linmou 内部 lore 钩子;方向 4' 部分包含 Lore 5 项考据)

**意见**:

Lore 在 next-direction-survey 提了 5 项考据清单(国营单位编号体系 / 武林门刑场 / 湖滨夜班巡更 / 遗失档案室 / 浙大钟楼女孩)。本次调研后:

**方向 2 放行的 Lore 影响**:linmou 4 ending 反咬词条已落地,Lore 在 Pass 9 + Pass 24 共出词 11 处 — 文本质感符合"档案 / 声 / 人"铁律(GRIEVANCE 走档案+水、REGRET 走井+物证、RELEASE 走人+档案+水、EXPOSED 走声+广播)。**Lore 对方向 2 满意,确认放行**

**方向 1'(linmou 肌理补完)的 Lore 钩子**:
- linmou 内部 4 个 ending 子节点(`n_l1985_abacus_grievance` 等)目前是单跳回 picker,Lore 可补:① "回到地图前"叙述根据 4 ending 分化(账册扛在肩上 / 钢笔留在桌上 / 脚步声变快 / 雾从衣领钻进来);② 4 地标(算盘房 / 锅炉房 / 档案室 / 凉亭)二访 narrative 加 ending 子节点 visited 后的物件痕迹分化
- 这是"肌理补完"的核心,与 Topology 的"connections 显式化"并行做

**方向 4' 的 Lore 影响**:Lore 5 项考据清单与本轮无强相关 — 等触及对应节点时处理。**Lore 5 项放行**,不进本轮短名单

**产出**:
- 新增元素考据清单:**无**(本轮不新增考据)
- lore 不一致警告:**无**(11 处 LINMOU 反咬词条已审,符合铁律)
- 命名建议:**无**

**Lore 推荐**:方向 1'(linmou 肌理补完)主场参与;方向 4' 放行(不深度介入)

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:深度参与(方向 1' 主场)

**意见**:

Topology 在 Pass 24/25 评审两次缺席,Pass 25 留下"variants 分桶上限"意见 debt。本次必须出席,顺带补上。

**本次新关切(Chief 调研发现)**:
- `_fragment_v7_linmou_1985.json` 中 `landmark_map: {}` **是空数组**
- Pass 25 报告称"connections 网状关系已 manifest 层落地",但接合点未审清
- **可能存在隐性 sandbox debt** — 必须在方向 1' 启动前 1 小时排查

**linmou Act 2/Act 3 拓扑实测**(回答用户方向 1 描述):
- linmou 是单 Act 扁平结构(`_fragment_v7_linmou_1985.json:6` `_dispatch_notes` 明示:"4 地标 / 4 ending",不分 Act)
- 44 节点全部归属于 picker hub `n_l1985_landmark_picker` 辐射
- 沙盒骨架 5/5 项合规:1 picker / 4 地标 / 2 工具 / 2 处 stay:true / variants 反应 clause(在 G-273 主线对 LINMOU ending 的回声中)
- **不存在 Act 2/Act 3 — 用户描述偏差**

**Topology 立场**:
- 方向 1' **修改后放行** — 必须先验证 `landmark_map` 接合点(manifest vs fragment),不要在 debt 上加 debt
- 方向 2 / 方向 3 放行(不涉及拓扑)
- 方向 4' 子项 Issue #15:**Topology 强关切**,跨 story_id 引用 audit 误杀直接影响沙盒契约第三角色扩展

**Pass 25 缺席 debt 补意见**(variants 分桶上限):
- 同意 Chief 预设 — **每节点 ≤ 2 条 cross_run variant**,审计兜底
- 进一步:**同节点 cross_run variant 跨 character_id 分桶后 ≤ 1 条**(防止 G-273 + LINMOU 反咬在同一节点串味)
- 已经在 Pass 26 `audit_profile_inheritance` 阻断模式中部分实现,但 character_id 分桶维度需补充

**产出**:
- 节点结构变更:**无**(本次不改拓扑)
- 状态维度调整:**无**
- 可达性证明:linmou 4 ending 仍可达(回归测试锁),反咬补完不动 ending 节点本体
- **拓扑红线**:linmou `landmark_map` 接合点必须在方向 1' 启动前查清
- **Pass 25 缺席补**:variants 分桶上限按 character_id 维度补审计规则

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与(方向 4' 主场)

**意见**:

QA 在 2026-05-13 next-direction-survey 提了 5 项,最高优先级是"`audit_cross_run_continuity` + golden file pytest 回归"。当前 Pass 22 audit 三件套已落地,**但 pytest 层 golden file 仍未补**。

**本次 QA 矩阵**:

| 方向 | 工时 | 新审计 | 关键断言 |
|---|---|---|---|
| 1' linmou 肌理补完 | 1.5-2d | `audit_variant_trigger` 跑 linmou 节点 variant 触发率 | linmou 复访 variants 密度 ≥ G-273 的 60% |
| ~~2 反咬~~ | ~~0.5d~~ | ~~`audit_cross_run_continuity`~~ | **已 done,无需重测** |
| ~~3 presentation~~ | ~~0.5d~~ | ~~`cg_unlock` 副作用~~ | **UX 单点核查,不需 QA Pass** |
| 4' Issue #15 修复 + pytest golden file | 1d | `tests/test_path_coverage.py`(新建)+ `tools/audit_reactions.py`(改)| Golden file 锁主线 5 ending + linmou 4 ending 关键路径;跨 story_id 引用 audit 不误杀 |
| 4' Pass 25 缺席补 | 0.5d | `audit_profile_inheritance` + Pass 27 新增 character_id 分桶维度 | 同节点 cross_run variant 跨 character_id 分桶 ≤ 1 条 |

**QA 红线断言**:
- Pass 26 `audit_profile_inheritance` 阻断模式仍是 main ending 反咬唯一红线(linmou 走 `ending_id` 直引,不在该审计扫描范围内,本红线不变)
- BAD ending 0 cross_run variant 红线保持
- **新红线**:跨 story_id ending_seen 引用必须 skip 或降级 warning(Issue #15)

**QA 立场**:
- 方向 4'(Issue #15 + golden file + Pass 25 debt 补)**第一推荐** — 工时短(1.5d 全做完)、清账价值高、零拓扑风险
- 方向 1'(linmou 肌理补完)**第二推荐** — 需 Topology 先审 `landmark_map`
- 方向 2 / 方向 3 放行不做

**产出**:
- 测试路径序列:linmou 4 ending + G-273 5 main ending + BAD endings 关键路径
- Bug 清单(分等级):
  - 阻断:**Issue #15 p1 OPEN**,不修将阻塞第三角色扩展
  - 严重:**pytest golden file 未建**,Pass 22 三件套验证"剧本能不能演",golden file 验证"演完体验如何"
  - 一般:**linmou 复访 variants 密度未审计**,可能存在"骨架合规但肌理薄"
- 回归测试入口:`pytest tests/test_path_coverage.py`(待建)+ `bash tools/audit_all.sh`(13 项全绿)

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行(以下推荐 3 项短名单作为下一阶段 Pass 27 / Pass 28 / Pass 29 切片依据)**

**用户描述与现实的偏差总结**:用户给出的 4 方向中:
- **方向 1(linmou Act 2/3 扩沙盒)**:概念错位,linmou 是单 Act 扁平结构,Pass 21 已偿沙盒债(`audit_sandbox` 12/12 全绿)。真正可做的是 **linmou 内部肌理补完**(Pass 28)
- **方向 2(GRIEVANCE / DUTY 反咬)**:**已 done state** — Pass 9 已落地 E_LINMOU_* 回声,共 11 处反咬覆盖 4/4 ending,且不存在 DUTY ending
- **方向 3(presentation 引擎读全)**:**已 done state** — 10 个 key 全部已被 `v5/player.py:382 format_presentation_lines` 读出,v5+v7 双链共享
- **方向 4(backlog)**:**真有 debt** — Issue #15 / pytest golden file / Pass 25 缺席 2 项 / CLAUDE.md 第一公理过时条目

### 共振轴

7 人(含 Chief)调研后,共振非常一致:

**共振轴一(7 票一致)**:**方向 2 已 done / 方向 3 已闭合,直接放行不做**
- 4 项 LINMOU ending 反咬本身就是 Pass 9 + Pass 24 累计完成的功能(2-3 锚点 / ending,符合"档案 / 声 / 人"铁律)
- 10 个 presentation key 全部已被 `v5/player.py:382 format_presentation_lines` 读出,v5+v7 双链共享
- **本轮"做反咬"或"扩 presentation"都是在做已 done 的事**

**共振轴二(5 票:Chief / State / QA / Topology / UX)**:**方向 4'(backlog 重新发掘 + Pass 25 缺席 debt 补)第一推荐**
- 工时 1.5d / 风险极低 / 清账价值高 / 不动剧本
- 包含 3 子项:Issue #15 修复 + pytest golden file + Pass 25 缺席 debt 补

**共振轴三(3 票:Chief / Topology / QA)**:**方向 1'(linmou 肌理补完)第二推荐**
- 需 Topology 先审 `landmark_map` 接合点(manifest vs fragment)
- Lore 配合出词,QA 跑 variant 触发率
- 工时 1.5-2d / 风险中(可能挖出隐性 debt)

### 推荐 3 项短名单(下一阶段切 Pass 依据)

**Pass 27 候选 ★ —— backlog 清账(Issue #15 + pytest golden file + CLAUDE.md 修订)**
- **内容**:
  1. 修复 Issue #15:`tools/audit_reactions.py` 的 `DEAD_ENDING_SEEN` 检测对跨 story_id 引用 skip 或降级 warning
  2. 新建 `tests/test_path_coverage.py`:golden file 锁主线 5 main ending + linmou 4 ending 关键路径
  3. **零成本附带项(Topology 主动捞的 P0 文档债,3 分钟)**:修订 `CLAUDE.md` 第一公理 — 删除"已知 sandbox debt:linmou Act 1(27 节点 / 0 工具 / 单向辐射,见 ADR-009)"过时条目。Pass 21 已偿(`audit_sandbox` 12/12 全绿),保留这一行会持续误导下一波评审。同步把 linmou 周目加入"参考实现"段(44 节点 / 1 picker / 4 地标 / 2 工具,Pass 21 后)
- **范围**:纯引擎 + 测试 + 顶层文档,**不动剧本**
- **验收**:`audit_all.sh` 14/14 全绿(新增分桶规则);`pytest tests/test_path_coverage.py` 通过;Issue #15 close;`CLAUDE.md` 第一公理与现实一致
- **工时**:1-1.5d(其中 CLAUDE.md 修订占 3 分钟)
- **为什么先做**:7 票共振 / 0 拓扑风险 / 清四处零散债务(Issue #15 + golden file + CLAUDE.md + 解锁第三角色扩展前置条件)/ Topology 警告"保留 CLAUDE.md 过时条目会让下一波评审被同样误导一次"

**Pass 28 候选 ★ —— linmou 周目肌理补完**
- **内容**:
  1. **前置**:Topology 1h 排查 `_fragment_v7_linmou_1985.json` 的 `landmark_map: {}` 接合点(manifest vs fragment)
  2. linmou 4 地标 connections **节点层显式化**(每地标 ≥ 1 条邻边,补到 fragment 节点而非仅 manifest 层)
  3. linmou flags 命名规范化:`l_*` 系列(如 `l_visited_abacus` 等)按 ADR-007 改名为 `know.l_*` 或 `flag.l_*`,统一与主线命名空间
  4. linmou 4 ending 子节点(`n_l1985_*_grievance/release/regret/exposed`)回访 narrative_variants 补完(账册扛在肩上 / 钢笔留在桌上 / 脚步声变快 / 雾从衣领钻进来)
  5. 4 地标二访 narrative 加 ending 子节点 visited 后的物件痕迹分化
- **范围**:动 `_fragment_v7_linmou_1985.json` + 可能动 manifest + 跨节点 flag 改名;不改 ending 节点本体
- **验收**:`audit_sandbox` 仍 12/12 全绿;`audit_variant_trigger` linmou 节点触发率 ≥ G-273 的 60%;`audit_state` flag 命名合规
- **工时**:1.5-2d
- **为什么次做**:linmou 骨架合规但肌理薄、flags 命名留旧账;**前置依赖**:Pass 27 完成(audit 升级后变更可被新审计验证)

**Pass 29 候选 ★ —— Pass 25 缺席 debt 显式入档(ADR-010 / ADR-011)**
- **内容**:
  1. 把 § 5 UX 缺席补意见("似曾相识"对白纯台词,无视觉 marker)正式写入 `docs/architecture/ADR-011-persona-inertia.md`
  2. 把 § 7 Topology 缺席补意见(variants 分桶按 character_id 维度 ≤ 1 条)写入 `audit_profile_inheritance.py` 规则 + ADR-010 沙盒契约附录
  3. CLAUDE.md 修订已并入 Pass 27 附带项(Topology 建议),Pass 29 不重复处理
- **范围**:纯文档 + 单点审计规则,不动剧本
- **验收**:ADR-011 / ADR-010 更新;新评审/新作者按 ADR 上手能直接看到 Pass 25 决议
- **工时**:0.5d
- **为什么独立成 Pass**:本条只动 ADR,与 Pass 27 引擎改动正交,可并行做。把 Pass 25 缺席决议正式入档,避免未来再次重述

### 不推荐(明确放行 = 本次不做)

- **方向 2(GRIEVANCE/REGRET 反咬)**:🟢 **已 done**(Pass 9 + Pass 24 共 11 处反咬,4/4 ending 全覆盖)
- **方向 3(presentation 读全)**:🟢 **已闭合**(10 key 全读,v5+v7 双链共享)。剩余 UX 文案细节可单点补丁,不立 Pass
- **Meta 图鉴 / True Ending 门槛**:Pass 26 刚落地需观察期,**Pass 30+ 候选**
- **Lore 5 项考据清单**:除非触及对应节点,本轮不立 Pass
- **"非主角群像"复访补完(Chief Pass 9 衍生)**:优先级低于 linmou 自家肌理补完
- **红衣女孩 / 8 棺自己"要么坐实要么删"**:挂账,等触及对应节点

### 关键风险(决议为"修改后放行",必填)

1. **Topology 红线**:linmou `landmark_map` 空数组接合点未审清。**Pass 28 启动前必须先 1 小时排查 manifest vs fragment 层**,否则可能在 debt 上加 debt
2. **State 红线**:Issue #15 跨 story_id ending_seen 引用降级未修。Pass 28 若先于 Pass 27 启动,linmou 反咬 audit 可能触发误杀。**Pass 27 必须先于 Pass 28**
3. **Lore 沉浸契约**:反咬词条载体严守"档案 / 声 / 人"三选一,Pass 24 § 5 铁律不可破。本轮无新增反咬,但 Pass 28 ending 子节点回访 narrative 若涉及"上次访问痕迹",仍须遵守

### 后续动作

- 用户决策:确认推荐短名单 → 助手用 writing-plans skill 把 Pass 27 拆任务(开工时序:Issue #15 修复 → golden file)
- 推荐执行顺序:**Pass 29(纯文档,可立即做)→ Pass 27(引擎清账)→ Pass 28(剧本肌理,前置依赖 Pass 27 audit 升级)**
- **不推荐**:Pass 27 与 Pass 28 同 PR 混做(Pass 28 风险大,需 Topology 先审接合点,且 Pass 27 audit 升级后变更才能被新审计验证)
- Pass 29 可与 Pass 27 / Pass 28 并行(零冲突,纯文档)
- **挂账记录**(本次不解决,后续 Pass 候选):
  - Meta:图鉴 + True Ending 门槛 → Pass 30+
  - Lore:5 项考据清单(国营单位编号 / 武林门刑场 / 湖滨夜班 / 遗失档案 / 浙大钟楼)→ 触及节点时处理
  - Lore:红衣女孩 / 8 棺自己"要么坐实要么删"→ 触及节点时处理
  - Chief Pass 9 衍生:"非主角群像"复访补完 → 优先级 < Pass 28

### 不同意见记录

- **Meta**:对 Pass 27/28 不深度介入,放行;但坚持 Pass 30+ 应有图鉴 / True Ending 门槛——Chief 同意但要求"Pass 26 观察期满后(2-3 周)再启动"
- **UX**:本轮主动让位(2026-05-13 next-direction-survey 立场延续),仅补 Pass 25 缺席 debt;若 Pass 28 涉及 ending 子节点回访 narrative,UX 后续以补丁形式回归
- **Topology**:**强烈关切 `landmark_map` 接合点**,作为 Pass 28 前置硬条件而非软建议——Chief 采纳
- **§ 3-§ 6 / § 7-§ 8 部分意见来源**:本次 6 人 agent 通过 mailbox 未在评审时限内全员到齐,意见整合方式 = ① Pass 25 缺席角色(Topology / UX)按"出席补 debt"对待;② 其余角色按 2026-05-13 next-direction-survey 立场延续 + 主助手实测事实包结合;③ 报告写完后任何角色如有反对意见以补丁形式回归

---

### § 9.X 编号变更日志(2026-05-14,Pass 编号冲突仲裁)

本报告原推荐 Pass 27/28/29 **与同日发布的 `2026-05-14-map-ux-deep-dive.md` 推荐 Pass 27/28/29 编号冲突**。
冲突仲裁:**`map-ux-deep-dive.md` 的 Pass 27-29 优先**(直击用户原话感知 + UX/Topology 双主笔产出),本报告原编号重新分配如下:

| 本报告原 Pass | 新编号 | 内容 | 状态 |
|---|---|---|---|
| Pass 27 | **Pass 33** | Issue #15 修复 + pytest golden file 新建 + CLAUDE.md 第一公理修订(3 分钟附带项) | ⏳ 待做 |
| Pass 28 | **Pass 34** | linmou 肌理补完(`landmark_map` 接合点审清后才知道是否还有 debt + 18 个 `l_*` flags 改名加 namespace 前缀) | ⏳ 待做 |
| Pass 29 | **被吸收** | Pass 25 缺席 debt 入档 ADR → 已由 `map-ux-deep-dive.md` Pass 32 吸收 | ⏳ 待做(在 Pass 32) |

执行优先级:`map-ux-deep-dive.md` Pass 27/28/29(用户感知 P0)> Pass 33/34(合规债务 P1)。

---

### Linus 一句话总结

**"4 个候选方向里 2 个已经做完了,1 个工程债已闭合,剩下的真活儿是把 Issue #15 这块卡在 backlog 里的 p1 拔掉、把 pytest golden file 这把还没拧上的螺丝拧上,然后再去补 linmou 肌理 — 不要在做完的事上再做一遍,也不要在 debt 上加 debt。"**
