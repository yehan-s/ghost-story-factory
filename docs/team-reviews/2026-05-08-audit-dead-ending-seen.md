# 2026-05-08 audit_reactions DEAD_ENDING_SEEN 红线加固 + Pass 2 docs commit

> 评审团:script-review-team
> 任务 slug:audit-dead-ending-seen
> 报告生成时间:2026-05-08 01:25

---

## § 1. 任务描述

推进 option B — 补完 audit_reactions DEAD_ENDING_SEEN 红线修复 WIP,并提交 Pass 2 流程 docs。

**当前 unstaged**:
1. `tools/audit_reactions.py` 改动:新增 `_walk_ending_seen()` 递归(any_of/all_of/not 全覆盖)+ `DEAD_ENDING_SEEN` 检测(narrative_variants[].if.ending_seen 引用的 ending_id 必须存在为节点;`*` 通配跳过)
2. `tests/test_audit_reactions.py`:新增 3 个用例(dead / passes / wildcard)
3. 4 个 untracked docs:`docs/superpowers/plans/{2026-05-07-dramatic-reaction.md, 2026-05-08-pass2-effects-learn-and-npc-drowned-pilot.md}` + `docs/team-reviews/{2026-05-07-dramatic-reaction.md, 2026-05-07-pass2-effects-learn-and-npc-drowned-pilot.md}`

**待补步骤**:
- 主 tree.json audit 跑一次(预期 1 条红线 — commit aa71047 linmou Act 1)
- 决定是否就地修数据(_fragment_v7_*.json)
- ADR-009 cross-character ending_seen 契约文档化
- commit message + 拆分

**任务影响范围**:多层(引擎工具 + 剧本契约 + 测试 + 数据 + 文档)

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与

**层级判定**:多层(确认助手预判)。引擎工具(audit_reactions.py)+ 剧本契约(ADR-009 cross-character clause)+ 测试(3 用例)+ 数据修(linmou fragment)+ 文档,五条线一齐动,典型多层。

**意见**:

1. **DEAD_ENDING_SEEN 检测覆盖完整,无漏路径**。`_walk_ending_seen()` 走了 `any_of / all_of / not` 三条递归,与现有 `_walk_reaction_keys` 同构。`*` 通配跳过的语义和 ADR-009 第 47 行明文一致。3 个测试覆盖 dead / passes / wildcard 够。**唯一边角**:嵌套 `not.any_of` 这种深结构没有显式 case,但因为递归正交,不需要单独测(*注:QA 给出反对意见,见 § 8*)。

2. **主 tree 红线确认是真 bug,不是误报**。`n_l1985_landmark_picker` variant 引用 `ending_id: "E_TRUTH"`,但主 tree 节点表里只有 `n_end_truth`。`E_TRUTH` 是 `ending_type` 字段值,**不是 node_id** —— commit aa71047 写 linmou Act 1 时把 ending_type 当节点 ID 写了。**剧情后果**:linmou 周目玩家若先通 G-273 真相结局再回 1985,本应触发"过道煤油灯不像 1985"的 meta-诡异 variant,**现在永远触发不了**——伏笔兑现链断了,体验回退到默认 variant。必修。

3. **就地修数据**,改 `_fragment_v7_linmou_1985.json:27` 把 `"E_TRUTH"` 改成 `"n_end_truth"`,然后重跑 stitch/build 生成 tree.json。**严禁直接编辑 tree.json**(违反 ADR / build 链单一真相源)。修后再跑一次 audit 确认全绿。

4. **ADR-009 cross-character ending_seen 契约需要追加显式条款**。当前 ADR-009 第 38-71 行讲了 clause 形式与 audit 检查项,但**没有明文规定** "`ending_id` 字面量 = 目标节点 ID,不是 ending_type 字符串"——这次 bug 就是契约语义未明文导致的。建议加 §跨角色引用规范:`ending_seen.ending_id` 必须是节点表中存在的 ending 节点 id(snake_case `n_end_*`),不是 ending_type 枚举值;通配 `*` 是唯一例外。

5. **WIP 补完顺序合理**:audit 工具落地→跑主 tree→修数据→重 build→audit 再跑→docs 落地→commit。**关键节点**:第二次 audit 必须全绿才能 commit,否则 `test_main_tree_currently_clean` 会红。

6. **拆 commit 三段式**(强烈建议,不合一):
   - C1 `feat(audit): DEAD_ENDING_SEEN 检测 + 跨角色 ending_seen 引用契约` — `tools/audit_reactions.py` + `tests/test_audit_reactions.py` 三新用例 + ADR-009 §跨角色引用规范追加
   - C2 `fix(linmou-1985): E_TRUTH 节点引用修正为 n_end_truth` — `_fragment_v7_linmou_1985.json` + 重 build 后的 `tree.json`(同 commit,机械产物)
   - C3 `docs(plans): pass2 dramatic-reaction + effects-learn 计划与评审报告` — 4 个 untracked docs

   **理由**:Linus 手术式精准——一个 commit 一件事,出问题能精确定位。

**产出**:
- **悖论清单**:1 条已识别(linmou Act 1 picker 的 E_TRUTH 反应永远不触发),修后清零
- **伏笔变更**:E_TRUTH→1985 反应链由"断"恢复"通",对应 ADR-009 第 84 行"跨角色反向影响"承诺生效
- **一致性规范**:ADR-009 追加"`ending_id` 必须是节点 id 字面量,不是 ending_type"硬契约

---

## § 3. State Architect — 状态系统建筑师

**相关度**:普通审查放行(audit-only,零字段增量,符合 ADR-007 冻结清单)。

**意见**:

- **状态层影响**:✅ 本次改动 0 新增 flag / state / 引擎字段。`tools/audit_reactions.py` 仅是**只读静态检查器**,`_walk_ending_seen()` + `DEAD_ENDING_SEEN` 全是验证器逻辑。`endings_seen[story_id]: list[ending_id]` 已在 ADR-007 11 字段冻结清单内,本次是**强化引用一致性**,不是新增。完全符合反加法者立场。

- **`_walk_ending_seen` 递归完备性**:✅ 覆盖 `any_of` / `all_of` / `not`,与现有 `_walk_reaction_keys` 同构。边界处理 `req["ending_seen"] or {}` + `spec.get("ending_id")` + `if not eid or eid == "*": continue` 一行同时覆盖了 None / 空串 / 通配三种 skip。

- **通配 `*` skip 语义正确**:✅ ADR-009 cross-character 契约里 `ending_id="*"` = 任意 ending。代码 `eid == "*"` 短路完全正确。

- **误杀风险**(⚠️ 轻度警告但非阻断):当前同 tree 内 ending_id 必须存在为节点 — 这意味着**跨周目引用其他角色尚未实现的 ending 会触发 DEAD_ENDING_SEEN**。但 ADR-009 ending_seen 是**跨 story** 的(story_id 字段就是路标),audit 只跑当前 tree.json,理应 skip 跨 story 引用。**当前代码用 `eid not in nodes` 判断,会把"杭州 A 角色引用 杭州 B 角色 ending"误判为 DEAD**。

**产出**(放行 + 1 个跟进 issue):
- 0 新增 flag / state(audit 工具,符合预期)
- 建议补:`spec.get("story_id") != current_story_id` 时 skip 或降级 warning(开 follow-up issue,本 PR 不阻断)
- 测试覆盖建议加 1 例:跨 story_id 引用应 skip(防止 Pass 2 误杀)

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:深度参与 — DEAD_ENDING_SEEN 直接守护周目继承契约,是元游戏机制的护栏。

**意见**:

1. **周目继承影响(强正面)**:`endings_seen[story_id]: list[ending_id]` 是 ADR-007 冻结的跨周目联动唯一真相源,也是收集本 / True Ending 解锁的底层依据。本次检查器加强等价于把"林副科长 variant 引用 G-273 ending"这类跨角色契约从隐性约定升级为编译期硬约束。

2. **True Ending / 收集本影响(零)**:改动只新增 audit 检查,不改 runtime 解析路径,不改 `endings_seen` 存储 / 读写语义。`ending_id="*"` 通配豁免也保留了"任意 ending 见过"的跨周目语义弹性。

3. **未来角色扩展兼容性(需要"宽容模式")**:第三可玩角色 C 的 tree.json 在生成阶段会引用前两角色 ending_id,但 C 的 audit 是单 tree 内进行 —— 如果 C 的 variant 引用 A 的 ending_id,A 的 ending 节点不在 C 的 tree 里,**会被误杀为 DEAD_ENDING_SEEN**。

**产出**:
- 跨周目继承机制变化点:跨角色 ending 引用从"隐性约定"变成"audit 期硬契约",收集本不会再因 variant typo 静默失效
- 未来角色扩展兼容方案(follow-up issue,本次不阻断):
  - 方案 A(推荐):`story_id != 当前tree.story_id` 时跳过节点存在性检查
  - 方案 B:引入全局 `endings_registry.json`,audit 跨 tree 校验

---

## § 5. UX Designer — 文字体验设计师

**相关度**:放行

**意见**:
- 本次改动仅限 audit 工具 + 测试 + docs,零玩家可见 UI / CLI / TUI 路径,UX 无影响
- 隐含风险(理论):若 DEAD_ENDING_SEEN 红线被忽略,variant 条件永不满足 → NPC 反复访问 narrative 不切档,玩家会感到"这个角色像坏掉的录音机",沉浸感断裂;严重时让"跨周目联动"承诺(endings_seen 影响后续对白)落空,玩家失去探索动机。**加固 audit 等于守住"沙盒会记得你"的 UX 信任契约**。

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:普通审查 — 放行(但建议顺手补 ADR-009 一小段)

**意见**:
- **lore 一致性影响**:本次改动是 `audit_reactions.py` 的 DEAD_ENDING_SEEN 红线加固,纯工具层契约校验,**零新增 lore 元素** — 杭州本地性 / 国营单位夜班 / 羊符 / 铜锈侧脸 / G-273 编号 / 林副科长 / 6 点湖滨日出 / 7 工人 全部未触动。放行。
- **ADR-009 是否追加 cross-character 契约段**:**建议追加**。工具加强后,跨角色 `ending_seen` 引用从"约定俗成"升格为"红线契约",ADR-009 应在 lore 层把"林副科长跨周目记忆"表达为**单位档案制度**内的合理叙事,避免被误读为元叙事 / 打破第四面墙。

**产出**(ADR-009 追加段建议文字):

> **§ Cross-character ending_seen 契约(lore 锚点)**
>
> 林副科长作为 G-273 单位"夜班交接记录员"的鬼差化身,其跨周目记忆并非超自然全知,而是**单位档案制度的延续**:每位夜班保安离岗(ending)时,交接簿留痕;林副科长以鬼差视角调阅前任记录。
>
> 因此 `narrative_variants[].if.ending_seen: [story_id, ending_id]` 在 lore 上对应"林副科长翻看了你前一班的交接簿",台词应以**制度化口吻**呈现:
> - ✅ "上回那位小同志,选了把符烧了,档案里记着。"
> - ❌ "我看见你做了 X 选择。"(超验全知,破第四面墙)
>
> 引用的 `ending_id` 必须在对应 `story_id` 的 endings 闭包内真实存在 — 这既是 `audit_reactions.py` DEAD_ENDING_SEEN 红线,也是"档案里不会凭空出现条目"的 lore 自洽。工具校验失败 = 单位档案有伪造嫌疑 = lore 破裂。

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:深度参与

**意见**:

1. **沙盒契约影响**:零影响,放行。改动局限在 audit_reactions.py 工具层,不触碰任何 ADR-010 沙盒原语。属于守门人维度的契约执行加固,方向正确。建议红线消息里加一行 hint:"修复方向 = 补 ending 节点 / 改 ending_id 引用,不要删 variant"——否则开发者图省事删 variant,会丢跨周目 cross_run 反应,违背 ADR-010。

2. **可达性 / 拓扑结构**:DEAD_ENDING_SEEN 报红线不会自动改图,只是信号。本案修复(`E_TRUTH` → `n_end_truth`)是改字符串,不增删边、不改可达性矩阵。linmou picker 入边 / 7 地标 connections 网 / 工具 stay 自循环全部不动。

3. **path_explorer 盲点 — 单独 issue,不顺手修**(Linus "一个补丁只做一件事"):
   - (a) p2,识别 `picker_choices` 动态生成消除 5 孤儿误报
   - (b) p2,把 `is_ending=true` 节点(含 E_LINMOU_* schema)统一识别为结局,消除 5 死路误报
   - (c) p3,617 条 GR 上溢 warning 分级降噪

**产出**:

- **DEAD_ENDING_SEEN 主 tree 实跑红线清单**(1 条):
  - 节点:`n_l1985_landmark_picker`(linmou Act 1 地标 picker)
  - 引用 ending_id:`E_TRUTH`(主 tree nodes 表中不存在)
  - 源 fragment:`stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json` line 24-29,`narrative_variants[0].if.ending_seen.ending_id`

- **数据修复方案**:主 tree 实有 endings 含 `n_end_true` 和 `n_end_truth`。`E_TRUTH` 是历史命名遗留。建议改 `_fragment_v7_linmou_1985.json:27` `"ending_id": "E_TRUTH"` → `"ending_id": "n_end_truth"`(隐藏真相档,与 linmou Act 1 觉醒文案"过道走过几千次,你忽然知道这一夜走过很多次"语义对齐——重复周目的元觉醒,正是 hidden truth 触发,不是 main true)。`story_id: "杭州_v7"` 保留。

- **path_explorer 盲点**:本 commit **不顺手修**,开 3 个独立 issue 挂 v0.2.x。

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与

**意见**:

测试覆盖度:10 个用例全过(`test_audit_reactions.py` 10 passed in 0.01s)。3 个新增 cross_character 用例(dead / passes / wildcard)正向 / 反向 / 通配三角覆盖。`_walk_ending_seen` 的递归实现(any_of/all_of/not)逻辑正确,**但单元测试没显式覆盖嵌套场景**——只测了 top-level `if.ending_seen`,没测 `any_of: [{ending_seen: ...}]` / `all_of` / `not.ending_seen` 路径。**这是阻断级缺漏**:递归代码在 main tree 用不到(主 tree 当前没嵌套),回归会盲。

主 tree audit 实际状态:**1 条 DEAD_ENDING_SEEN** —— 节点 `n_l1985_landmark_picker`,variant 引用 `ending_id='E_TRUTH'` 不在节点表。`test_main_tree_currently_clean` 只 assert DEAD_REACTION/UNREACHABLE_REACTION,**故意不卡 DEAD_ENDING_SEEN**——这是正确选择(否则破回归),但需在评审报告写明白这条债的存在 + 处理时间表。

回归套件:基线 253 → 现 256,+3 一致(任务文档"256→259"基线写错)。其他模块 0 影响。

**产出**:

- **Bug 清单**:
  - 【阻断】缺嵌套递归测试:`_walk_ending_seen` 三个递归分支(any_of / all_of / not)0 单测覆盖
  - 【一般】`test_main_tree_currently_clean` 函数名误导(只测 DEAD_REACTION 系不测 ENDING_SEEN),建议改名 `test_main_tree_no_dead_resolver`
  - 【一般】edge case 未测:`{"ending_seen": null}` / `{"ending_seen": {}}` / 缺 `ending_id` 字段

- **缺漏的测试边界用例**(必补 3 条):
  1. `test_ending_seen_in_any_of_nested` — `if: {any_of: [{ending_seen: {ending_id: 'E_FAKE'}}]}` 应触发 DEAD
  2. `test_ending_seen_in_all_of_and_not` — 嵌套两层 + `not` 包裹
  3. `test_ending_seen_missing_ending_id_field` — `ending_seen: {story_id: 'x'}`(无 ending_id)应静默跳过

- **回归测试入口命令**:
  ```
  .venv/bin/pytest tests/test_audit_reactions.py -v
  .venv/bin/python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json
  ```

- **放行条件**:补 3 个嵌套递归测试 + 在 Pass 2 docs / ADR-009 sandbox debt 段登记 `n_l1985_landmark_picker → E_TRUTH` 这条债。

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行**

**关键风险**:
1. **【阻断】递归 `_walk_ending_seen` 三分支(any_of/all_of/not)0 单测覆盖**(QA)— 必须补 3 个嵌套测试,否则递归代码裸奔,未来嵌套引用红线漏报
2. **【必修】主 tree 实跑 1 条 DEAD_ENDING_SEEN**:`n_l1985_landmark_picker` → `E_TRUTH`(应为 `n_end_truth`)— 修 `_fragment_v7_linmou_1985.json:27` + 重 build tree.json,严禁直接编辑 tree.json
3. **【契约】ADR-009 缺 cross-character ending_seen 引用规范**(Chief Editor + Lore Keeper)— 追加 §跨角色引用规范 + § Cross-character lore 锚点

**后续动作**(按 Chief Editor 三段式 commit 拆分):

**C1** `feat(audit): DEAD_ENDING_SEEN 检测 + 跨角色 ending_seen 引用契约`
- `tools/audit_reactions.py`:已有改动 + 错误消息加 hint(Topology 建议:"修复方向 = 补 ending 节点 / 改 ending_id 引用,不要删 variant")
- `tests/test_audit_reactions.py`:已有 3 测试 + 补 3 个嵌套递归测试(QA 必补) + 改 `test_main_tree_currently_clean` → `test_main_tree_no_dead_resolver`
- `docs/architecture/ADR-009-linmou-arc-canon.md`:追加 §跨角色引用规范(Chief Editor 文字) + § Cross-character lore 锚点(Lore Keeper 文字) + § Sandbox Debt 登记 `n_l1985_landmark_picker → E_TRUTH`(QA 要求)

**C2** `fix(linmou-1985): E_TRUTH 节点引用修正为 n_end_truth`
- `stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json:27`:`E_TRUTH` → `n_end_truth`
- `stories/hangzhou_yebanbaoan/tree.json`:重 build 后的机械产物(同 commit)
- 验证:`audit_reactions.py` 全绿 + `audit_paths_linmou.py` INV-1~5 仍 0 问题

**C3** `docs(plans): pass2 dramatic-reaction + effects-learn 计划与评审报告`
- 4 个 untracked docs:`docs/superpowers/plans/{2026-05-07-dramatic-reaction.md, 2026-05-08-pass2-effects-learn-and-npc-drowned-pilot.md}` + `docs/team-reviews/{2026-05-07-dramatic-reaction.md, 2026-05-07-pass2-effects-learn-and-npc-drowned-pilot.md}`
- 同步 INDEX.md(已有 2 行可补?核对)

**Follow-up issues(本次不做,挂 v0.2.x)**:
- `[p1]` audit_reactions:跨 story_id ending_seen 引用 skip 或降级 warning(State + Meta + QA 一致建议)
- `[p2]` path_explorer:识别 picker_choices 动态生成,消除 5 孤儿误报
- `[p2]` path_explorer:把 is_ending=true 节点统一识别为结局,消除 5 死路误报
- `[p3]` path_explorer:617 条 GR 上溢 warning 分级降噪

**不同意见记录**:
- **Chief Editor vs QA**:Chief Editor 认为递归三分支因正交不需要单独测;QA 认为是阻断级缺口必须补。**采纳 QA 意见**(更严格,符合 Linus "测试是最后守门员"原则)。
- **State Architect / Meta-Game / QA 一致**:跨 story_id 引用误杀风险存在,但都同意作 follow-up issue 不阻断本 PR。
