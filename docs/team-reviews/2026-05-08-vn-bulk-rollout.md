# 2026-05-08 Pass 6 / VN 化大批量铺开

> 评审团:script-review-team
> 任务 slug:vn-bulk-rollout
> 报告生成时间:2026-05-08

---

## § 1. 任务描述

用户原话:**"你剧情先对剧本动刀子,大量改动先"**

背景链:
- Pass 5 单节点试水: `n_scene_lake_underwater` 165 → 2386 字 + 5 stay 互动 + `_is_tool: true`(commit b62d6c4)
- 用户反馈链: "内容太空洞,达不到视觉小说" → "多增加互动点" → 试玩触发 visit_count_min schema bug 修(4c7a855) → 英文净化(5b119c0) → 现在: "对剧本动刀子,大量改动先"
- 任务实质: 把 Pass 5 单节点 VN 化做法,推到所有 P0/P1 沙盒热门节点(8 节点,lake 已完,7 节点待做)

**任务影响范围**: **多层** = 剧本(主) + 引擎(次,_is_tool / stay schema) + UX(次,VN 互动密度)

**评审范围确定**(直接采纳 spec):
- P0(4): `n_landmark_picker` / `n_scene_lake_underwater`(已完) / `n_scene_lost_archive` / `n_npc_predecessor_voice`
- P1(4): `n_l1985_landmark_picker` / `n_npc_eight_self` / `n_s1_arrive` / `n_npc_red_dress_girl`
- 实际待做: **7 节点**

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与

**层级判定**:多层(剧本主 + 引擎/UX 次)

**意见**:

VN 化是"翻译层" 不是"设计层"。整个 Pass 6 的剧情连续性风险只有一类: **写作团队为填字数偷塞新设定 / 新 flag / 新 lore 锚点 / 新 reaction**。这必须由各专家 audit 死守边界。除此之外,Pass 5 lake_underwater 已证明 VN 化纯文本扩写不破契约。

伏笔-兑现链完整性: 8 节点中 6 个有现成 reaction_contracts variants(deduction/foreshadow/theme/ending_seen),VN 化时必须保证这些 reaction variants 的 if 子句**纹丝不动**——可以扩写文本,不能动 if 子句。

**产出**:

- **VN 化六不准** (Chief Editor 综合 6 角色意见后的硬约束):
  1. 不动 reaction variants 的 `if` 子句结构(只能扩写 `text`)
  2. 不加新 `effects.flags` key(75 上限不动,采纳 state_architect)
  3. 不加新 lore 锚点(只挖深现有白名单)
  4. 不动 picker hub 结构(`_is_map_picker` + `landmark_map` + `connections` 不变)
  5. 不破坏沙盒 5 项最小骨架(ADR-010)
  6. 不引入英文/AI 八股文/promotional language
- **变更顺序契约**: 剧本(narrative + variants 文本)优先 → UX(stay 互动 + _is_tool 标注)其次 → 不动 picker / connections / state_template

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与

**意见**:

VN 化扩字数 = 大量新增 narrative_variants 分支,极易借机偷塞 effects.flags(开发者写 if 子句缺覆盖时,本能反应是"加个 flag 区分一下"),直接撞 ADR-007 红线。当前 73 / 75 flag,余 2 席。lake_underwater 已 VN 化样板良好(0 新 flag,纯靠 visit_count + 现有 namespace),作为黄金标准。

**判定原则**: VN 化 = 翻译层,不是设计层。需要新维度区分,先回炉走设计评审,不在 VN 化 PR 内夹带。

**产出**:

- **VN 化 effects 字段白名单**(硬红线 SOP):
  - ✅ 文本字段(narrative / variants[].text / choices[].text)字数变化
  - ✅ `visit_count_min` 阈值微调
  - ✅ 已存在的 reaction(theme/deduction/foreshadow_resolved / ending_seen / inv_has)+ 已存在 oneshot.* arc.* know.* 引用
  - ❌ 新增任何 `effects.flags` key
  - ❌ 新增 `effects.PR / GR / inv_add / inv_remove / puzzle_add`
  - ❌ if 子句引用 ADR-007 namespace 之外的 key
  - ❌ if 引用尚未在任何 effects 里 set 的 flag(orphan)

- **variants if 子句"扩字数不破契约"4 红线**:
  1. 互斥/优先级显式: 同一节点 ≥ 3 条 variants 时, if 必须形成偏序(theme > deduction > foreshadow > visit_count_min),引擎按数组顺序首匹配,不允许两条 if 同时为真依赖排序"运气"
  2. 子集吃掉检测: `visit_count_min: {X: 2}` 必须排在 `min: 1` 之前(更严格优先)。lake_underwater 已正确做到 → 参考实现
  3. default 兜底必备: 每个 ≥ 2 variants 节点最后必须无 if 或 base case
  4. if 嵌套 ≤ 2 层

- **Audit 工具加固提案(P0,与 VN 化首节点 PR 同 PR 提交)**:
  1. `flag_count_ceiling`: 全文唯一 namespaced flag ≤ 75,超过即 fail
  2. `vn_diff_no_new_flag`: PR 仅修改 narrative/variants[].text 但 git diff 含新 effects.flags key → fail
  3. `variant_if_uniqueness`: 同节点两条 variants if 完全相等 → fail
  4. `variant_if_orphan_namespace`: variants[].if 中 flag key 缺前缀 → fail
  5. `variant_count_per_node_warn`: 单节点 narrative_variants > 8 → 警告

- **量化红线**:
  - flag 总数 ≤ 75 (硬上限,撞顶 -1)
  - 单节点 variants ≤ 8 (品味红线,超过说明该拆设计)
  - if 嵌套深度 ≤ 2 (Linus 第 4 规)

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:深度参与

**裁决: ❌ 不可放行(阻断决议)**

**意见**:

Meta-Game Designer 提出**沙盒玩法承诺断裂风险**: 将 Pass 5 单节点 VN 化模式无差别推到 8 节点,会从"沙盒可探索"滑到"VN 阅读器"。沙盒契约(ADR-010)的核心是**节点 = 决策机** + **拓扑 = 探索图**,而 2000-5000 字 / 节点 + ≥3 stay 互动 / 节点的均匀铺开会让玩家"在每个节点都停 5+ 分钟读字",**主线推进感和地图探索冲动彻底崩盘**。这不是 lore / 文本 / 字数问题,是**玩法定位问题**。

**Meta 的具体反对理由**:

1. **均匀铺开毁玩法节奏**: VN 化对场景节点(lake / archive / s1_arrive)合理,因为玩家在场景里"停留观察"是玩法承诺。但 VN 化对 picker hub(landmark_picker / l1985_landmark_picker)= **导航节点变阅读节点 = 玩家拒绝换地标**。
2. **NPC 节点 VN 化与沙盒"反复访问有变化"承诺冲突**: NPC 节点回访价值在"NPC 反应玩家行动"(reaction variants 切档),不在"NPC 独白 5000 字"。强 VN 化 NPC = 第一次惊艳, 第二次开始跳读, 第三次玩家不再回访。
3. **stay 互动数过载**: ≥3 stay / 节点 × 8 节点 = 24+ stay 互动,玩家试玩疲劳,沙盒"地图探索"主张被"逐节点穷举互动"取代。
4. **Pass 5 试水样本数 = 1 不能推全部**: lake_underwater 是**结局前关键节点**(玩家已动机十足,愿意停留),不能代表 8 节点全集(landmark_picker 高频导航 / s1_arrive 入口快速通过 / NPC 节点轻量对话各有节奏)。

**Meta 的修改建议**(若坚持本任务则按此走):

- **分级 VN 化(不是均匀铺开)**:
  | 节点类型 | VN 字数 | stay 互动 | _is_tool |
  |---|---|---|---|
  | 场景节点(lake / archive / s1_arrive)| 2500-4000 | 5-7 | ✅ |
  | NPC 节点(predecessor / eight / red_dress)| 1500-2500(轻量化)| 2-3(轻量化)| ❌ 不强标 |
  | picker hub(landmark_picker / l1985_landmark_picker)| **800-1500(显著轻于场景)** | **0(picker 不加 stay)** | **❌ 严禁** |

- **改动顺序(场景先,NPC 减量,picker 最轻)**:
  1. `n_scene_lost_archive`(P0,场景,首做,最稳)
  2. `n_npc_predecessor_voice`(P0,NPC,**轻量 VN 化** 1500-2500 字,不强标 _is_tool)
  3. `n_landmark_picker`(P0,picker,**只扩 narrative + vibe variants 文本到 800-1500 字,不加 stay/不加 _is_tool**)
  4. P1 决议推迟到 P0 完工 + 用户试玩反馈"密度足够"再讨论

- **边际效用临界点**(Meta 立场): **不做完 P0 的 3 个就推 P1 = 一票否决**。理由同 § 3 state_architect: 单 PR 单节点降险, batch 7 节点暴雷概率高。

- **量化红线**(违一项即打回该节点 PR):
  - picker hub 字数 > 1500 → 打回
  - picker hub 出现 _is_tool / stay 互动 → 打回
  - NPC 节点字数 > 2500 → 打回
  - 任何节点 stay 互动 > 7 → 打回
  - 用户试玩反馈"主线推进感丢了" → 立即停 batch, 回炉

---

## § 5. UX Designer — 文字体验设计师

**相关度**:深度参与

**意见**(综合 team-lead 转述: 选项分组 + 内心独白 dim + 分屏):

2000-5000 字 / 节点对照主流 VN 中位数: 命运石之门约 1500-3000 字 / 节, 白色相簿 2000-4000 字 / 节, Doki Doki 1000-2500 字 / 节。**我们 2000-5000 偏上限**,合理,但要求文本质量必须撑得住,否则会显冗余。lake_underwater 2386 字处于下限附近,是稳健起点。

**产出**:

- **节点类型 × 字数 / 比例配方**:
  | 节点类型 | 推荐字数 | 描写/对白/独白比 | 备注 |
  |---|---|---|---|
  | 场景节点(scene)| 2500-4000 | 70/10/20 | 描写主导,留白心理独白 |
  | NPC 节点(npc) | 2000-3500 | 30/55/15 | 对白主导,独白少 |
  | picker hub | 1500-2500 | 50/0/50 | 描写+独白(picker 没对白对象) |

- **stay 互动数(QA 校验依据)**:
  - 场景节点: **5-7 个**(lake_underwater 5 个为下限)
  - NPC 节点: **3-5 个**(对话分支非 stay,仅"问什么"是 stay)
  - picker hub: **0 个**(不加 stay,加了反而失推进)

- **vibe×VN 协同方案**(关键决议):
  - **default narrative**: VN 字数(2000-5000),60-30-10 比例
  - **vibe ABCD variants**: **保持 Pass 3 短切档(80-180 字)**
    - 理由: vibe 是"差异化补丁",玩家在 visit≥1 时 if 子句先匹配 vibe,跳过 default。如果每个 vibe 也 VN 字数 = 玩家回访每次读 2000+ 字 = 节奏崩溃
    - 实施: vibe variants 短(80-180 字), default fallback 长(VN 字数)
  - **reaction variants**: 中等字数(200-600 字),既要承接 default 的密度,又要因为是已解谜后的反应不必铺垫

- **过载风险与缓解**:
  - 单节点停留 >10 分钟 → 失推进感
  - **缓解**: stay 互动 UI 加"返回主路径"显眼按钮(team-lead 转述的"选项分组"对应)
  - 内心独白用 dim 灰色区分(team-lead 转述确认)
  - 长文本分屏: 屏幕高度 / 6 行为一屏,空格继续(team-lead 转述确认)

- **UX 达标可观测指标**:
  - 单节点 default 阅读时间: 2-4 分钟(2000-5000 字 / 600 wpm 中文)
  - 玩家试玩 stay 互动触发率 ≥ 60% (5-7 个 stay 至少摸 3-5 个)
  - 主观沉浸打分: 试玩后用户评 ≥ 4 / 5(主观但必须问)

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与

**意见**:

VN 化扩字 ~10 倍 = lore 增量 ~10 倍。最大风险: 写作团队为填字数引入白名单外新元素。当前白名单(羊符 / 铜锈 / 二轻物资 / G-273 / 1985-10-18)对 8 节点 × 2000-5000 字**够用,前提是挖深而非铺新**。

**易写飞节点排序**:
1. `n_npc_eight_self`(跨周目第八自己)— **最危险**, 跨周目对话边界模糊,易引入未通关 ending lore
2. `n_l1985_landmark_picker`(linmou Act 1)— 时空在 1985,易引入当代杭州元素
3. `n_npc_red_dress_girl`(红衣女孩)— 都市传说桶 D vibe 易飞
4. `n_npc_predecessor_voice`(前任声音)— 相对安全,有 lore 锚点充足

**产出**:

- **lore 锚点白名单(主周目 G-273)**:
  - 物件: 羊符 / 铜牌(锈成铜绿) / 二轻物资财务科 1985 款工装 / 工号 G-273 / 半导体收音机 / 新闻联播片头曲
  - 时间: 1985-10-18 / 1987 年冷冻舱
  - 空间: 西湖底 / 二轻物资财务科 / 档案室
  - 师父台词: "西湖底下,锁着一个还没下班的人"

- **lore 锚点白名单(linmou Act 1 单独)**:
  - 时空: 1985 年杭州 / 二轻物资财务科夜班
  - 人物: 林某(前任) / 同事(待 Act 2 揭开)
  - 事件: 1985-10-18 加班(具体待 Act 2)
  - **禁忌**: 任何 G-273 编号 / 现代元素 / 西湖冷冻舱(那是主周目结局揭谜,linmou Act 1 不能预先泄底)

- **跨周目 lore 引用守门**:
  - `n_npc_eight_self` variants 中 ending_seen 引用必须 grep 确认对应 ending 节点 narrative 已包含该 lore
  - `n_l1985_landmark_picker` 触发跨周目 variant 时,只能引用 G-273 周目玩家**已通关**的 ending(查 endings_seen[G-273])
  - 红线检查: variants[].if 含 ending_seen 时,变体 text 中的 lore 必须 ⊆ 该 ending 的 narrative

- **NPC 对白红线识别 4 条**:
  1. NPC 不能"知道"玩家未达成的 deduction(if 子句没 deduction_resolved 就不能引用该 deduction 揭谜文本)
  2. NPC 不能引用未触发的 foreshadow(同上)
  3. NPC 不能"穿透"周目: predecessor / eight_self / red_dress 在主周目对话不能直接引 linmou Act 1 私密信息
  4. NPC 不能"自报家门"未揭谜身份(eight_self 在 deduction_eight_self_resolved 之前不能称"我们是同一个人")

- **白名单扩列红线**:
  - ❌ 不加新 lore 文档(`data/lore.json` / `data/linmou_act1_lore.json` 不动)
  - ❌ 不加新历史人物 / 新历史事件
  - ✅ 可挖深现有锚点(铜绿 → 1985 年款铜牌的具体浮雕图样;二轻物资 → 财务科办公区的具体陈设)
  - ✅ 可加感官细节(声音 / 气味 / 触感)只要符合时代质感

- **lore 守门 checklist**(每节点完工时):
  ```
  □ 1. 文本中所有专名(物 / 时 / 地 / 人)都在白名单内?
  □ 2. NPC 对白没透露玩家未解开的 deduction / foreshadow?
  □ 3. 跨周目 variants 引用的 lore 在已通关 ending 内?
  □ 4. linmou Act 1 节点没有现代/G-273 元素?
  □ 5. 感官细节符合 1985 / 2010s 时代质感?
  ```

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:深度参与(报告写作时迟到,内容已整合至本节)

**意见**:

VN 字数膨胀 = 节点结构变化的"伪装窗口期",最易被偷渡的反模式: stay 改 next、新加 flag 镜像、NPC 单次访问硬扛"线性节拍"。lake_underwater(2386 字 / 5 stay / 7 variants / `_is_tool`)是 🟢 满分模板。

**沙盒原语现状**: `_is_map_picker` 2 个 / `_is_tool` 10 个 / `stay: true` effect 14 个分布在 10 节点 / reaction-clause variants 34 个

**🚨 遗留拓扑债登记**(不在 Pass 6 范围,Pass 7+ 单独立项):
- `n_landmark_picker` "辐射"模型 — 8 个 `next: n_sX_arrive` + 1 交班,各 landmark 第一节点没横向 `connections`
- 违反 ADR-010 骨架第 2 项(地标连成网,非辐射)
- **Pass 6 不要顺手"修"** — 会破坏现网

**产出**:

- **拓扑 4 红线**(VN 字数扩写绝对禁止):
  1. ❌ 不许移除 `_is_tool: true`
  2. ❌ 不许 `effects.stay: true` 改成 `next: 真节点`
  3. ❌ 不许 reaction variants `if` 子句换成 `flags.xxx_resolved` 镜像
  4. ❌ 不许 stay 自循环 choice 改成跳走

- **死循环红线**: 每个 `_is_tool` 节点 ≥1 个非-stay 出口 — 否则困住玩家

- **P0/P1 候选节点 · 沙盒契约符合度分级**:

  | 优先级 | 节点 | narr | chs | stay | vars | _tool | 评级 | 处理 |
  |---|---|---|---|---|---|---|---|---|
  | P0 模板 | `n_scene_lake_underwater` | 2386 | 9 | 5 | 7 | ✅ | 🟢 | 已完成 |
  | P0 工具 | `n_scene_lost_archive` | 226 | 10 | **1** | 11 | ✅ | 🟡 补 stay | VN 扩写 + 补 ≥2 stay |
  | P0 工具 | `n_scene_red_telephone` | 122 | 4 | **1** | 3 | ✅ | 🟡 补 stay | VN 扩写 + 补 stay + variants |
  | P0 NPC | `n_npc_corrosion_face` | 437 | 3 | **0** | 7 | ❌ | 🟡 改造 | 补 stay + 标 `_is_tool` |
  | P0 NPC | `n_npc_drowned_official` | 454 | 4 | **0** | 5 | ❌ | 🟡 改造 | 同上 |
  | P0 NPC | `n_npc_red_dress_girl` | 436 | 3 | **0** | 9 | ❌ | 🟡 改造 | 同上 |
  | P0 NPC | `n_npc_piano_ghost` | 463 | 5 | **0** | 4 | ❌ | 🟡 改造 | 同上 |
  | **P1 急迫** | `n_lore_*` 5 个 | **4-36** | 3 | 1 | 2 | ✅ | 🔴 急迫 | narrative 仅 4-36 字, 纯文本扩写 |
  | P1 入口 | `n_s1_arrive` ~ `n_s7_arrive` | 200-430 | 5-6 | **0** | 0-7 | ❌ | 🟢 不 VN 化 | 辐射图 hub-spoke,VN 化反强化死剧本 |
  | P1 picker | `n_landmark_picker` | 254 | 8 | 0 | 10 | ❌ | 🟢 不 VN 化 | picker 应轻量 |
  | P0 结算 | `n_scene_morning_lakeside` | 474 | 10 | 0 | 4 | ❌ | 🟢 不 VN 化 | 结局枢纽 |

- **改动顺序建议(Linus 实用主义,与 § 4 / § 9 顺序方案并存)**:
  1. **第 1 批 — 高 ROI / 0 拓扑风险**: 5 个 `n_lore_*`(`songmuchang_inn` / `zheda_clock_girl` / `wulinmen_execution` / `kongque_collapse` / `leifeng_worm`)— 纯文本扩写
  2. **第 2 批 — 中风险 / 需补 stay**: `n_scene_red_telephone` → `n_scene_lost_archive`
  3. **第 3 批 — 高风险 / 拓扑改造,延后 Pass 7**: 4 个 NPC 升级 `_is_tool`
  - **绝对不动批**: `n_landmark_picker` / `n_sX_arrive` / `n_scene_morning_lakeside`(拓扑骨架,VN 化 = 破坏)

- **picker / NPC `_is_tool` 决策**(与 § 4 一致):
  - picker hub: **不加 `_is_tool`**(导航 hub 保持轻量)
  - NPC 节点: 第 3 批改造时保留 stay 但**不强标 `_is_tool`**(语义偏物件)

- **沙盒最小骨架复核(VN 化后仍满足 ADR-010)**: ≥1 picker hub / ≥4 地标 + connections / ≥2 `_is_tool` / ≥1 stay 自循环 / ≥1 反应 clause variants

- **状态空间维度复核(配 State Architect)**: VN 文本"玩家已知 X"判定**只能用 `narrative_variants[].if.foreshadow_resolved` / `deduction_resolved`**,不许新增 `flags.xxx_known`

- **拓扑审计 checklist**:
  ```bash
  .venv/bin/python tools/audit_paths_linmou.py stories/hangzhou_yebanbaoan/tree.json
  .venv/bin/python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json
  ```

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与

**意见**:

VN 化 = 大量 JSON 编辑 + 新结构(_is_tool / stay / vibe×VN 嵌套)。已有两次 bug 教训(visit_count_min schema 4c7a855 / 英文净化 5b119c0),回归风险高。每节点改动必须强制工作流。

**产出**:

- **必跑测试套件**(每节点完工后):
  ```bash
  # 1. 重 build tree.json
  .venv/bin/python tools/merge_fragments.py --story-dir stories/hangzhou_yebanbaoan

  # 2. 主 tree audit(预期 0 红线)
  .venv/bin/python tools/audit_reactions.py stories/hangzhou_yebanbaoan/tree.json

  # 3. linmou 路径 audit(预期 0 problems)
  .venv/bin/python tools/audit_paths_linmou.py stories/hangzhou_yebanbaoan/tree.json

  # 4. 路径可达性
  .venv/bin/python tools/path_explorer.py stories/hangzhou_yebanbaoan/tree.json
  # 期望: 8 主结局可达, 孤儿/死路 ≤ 基线

  # 5. 全套回归
  .venv/bin/pytest --ignore=tests/test_story_generator_modes.py \
    --ignore=tests/test_pregenerated_mode.py \
    --ignore=tests/test_response_llmclient.py \
    --ignore=tests/test_choices_llm_wrapper.py \
    --ignore=tests/test_skeleton_generator.py \
    --ignore=tests/test_tree_builder_guided.py -q
  # 期望: 全 passed(基线为 Pass 5 完工时的 passed 数,以实测为准)

  # 6. flag 上限(state_architect 新加,与首节点 PR 同 PR)
  .venv/bin/python tools/audit_state.py stories/hangzhou_yebanbaoan/tree.json
  # 期望: flag_count ≤ 75
  ```

- **JSON 编辑工作流**(每节点强制):
  ```
  1. 编辑 _fragment_v7_*.json(单节点改动)
  2. python -m json.tool < _fragment_v7_*.json > /dev/null  (语法快验)
  3. merge_fragments.py 重 build
  4. audit_reactions.py + audit_paths_linmou.py + path_explorer.py
  5. pytest -q + audit_state.py(flag 上限)
  6. 人工 smoke test(visit=0/1/2/3 各跑一次)
  7. git add + commit(单节点 1 commit,粒度细到可独立 revert)
  8. git tag pass6-vn-<节点 ID>(回滚锚点)
  ```

- **试玩验证(覆盖 ≥ 路径数)**:
  - 8 主结局路径(每个 ending 至少跑通 1 次)
  - linmou Act 1 周目: 通主周目 G-273 hidden truth ending → 跨入 linmou
  - picker 反复回访: `n_landmark_picker` 连进 4 次,vibe ABCD 切档
  - 短切档低入度: `n_s1_arrive` 进 2 次,visit=0/1 切档
  - 至少 12 条独立路径

- **vibe×VN 协同试玩脚本**(配合 UX § 5 决议):
  ```
  Test 1 (visit=0): 新进 → 应见 default VN 长(2000-5000 字)
  Test 2 (visit=1): 第二次进 → 应见 vibe B 短(80-120 字)
  Test 3 (visit=2): 第三次进 → 应见 vibe C 短(96-144 字)
  Test 4 (visit=3): 第四次进 → 应见 vibe D 短(120-180 字)
  Test 5 (反应触发): 解一个 deduction 后回访 → 应见 reaction variant 中等(200-600 字)
  ```

- **终验 8 项 checklist**(P0 4 节点完工后):
  ```
  □ 1. pytest -q 全 passed
  □ 2. audit_reactions.py 0 红线
  □ 3. audit_paths_linmou.py INV-1~5 全 0 problems
  □ 4. path_explorer.py 8 主结局可达,孤儿/死路 ≤ 基线
  □ 5. audit_state.py flag ≤ 75
  □ 6. 12+ 路径试玩通过(含 vibe 4 桶 + reaction)
  □ 7. 字数符合 § 5 配方表(场景 2500-4000 / NPC 2000-3500 / picker 1500-2500)
  □ 8. lore 守门 checklist § 6 全过
  ```

- **Bug 等级响应**:
  - 阻断: pytest fail / audit 红 → 回滚 commit, 重 PR
  - 严重: 试玩崩溃 / 路径不可达 → 同节点 PR 内修
  - 一般: 字数偏差 ≤ 10% / 文本拼写 → 单独 cleanup PR

---

## § 9. 综合建议(Chief Editor 汇总)

### 决议: **修改后放行**

(Meta-Game Designer 投"不可放行" → Chief Editor 综合 6/6 角色意见后采纳 **Topology 3 批分级 + Meta 分级 VN 化 + UX render 层 P0** 三方修改建议化解)

### 评审分裂呈现(6/6 立场)

- **Meta-Game Designer**: ❌ **不可放行**(原始) — 反对均匀铺开到 8 节点,理由: 沙盒玩法承诺断裂(详见 § 4)
- **Topology Designer**: ✅ 修改后放行 — 提出"3 批分级 + 绝对不动批"(详见 § 7),与 Meta 修改建议方向一致
- **State Architect**: ✅ 修改后放行 — 5 项 audit 加固为前置条件
- **UX Designer**: ✅ 修改后放行 — render 层 P0 (选项分组 / 独白 dim / 分屏) 必须先做
- **Lore Keeper**: ✅ 修改后放行 — 白名单守门 5 项 checklist
- **QA / Path Tester**: ✅ 修改后放行 — 8 步 JSON 工作流 + 终验 8 项 checklist
- **Chief Editor 综合裁决**: 范围**收窄到第 1+2 批 8 节点 + 引擎渲染层 P0**(完全采纳 Topology 分级方案,放弃原 Meta 单 NPC 节点 predecessor_voice 方案)

### 范围决议(本 Pass 6 实际执行)

**本次范围 = 第 1 批 5 节点 + 第 2 批 2 节点 + 引擎渲染层 P0**(共 7 节点 + 引擎工作)
+ lake_underwater 已完(满分模板) → **总计 8 节点 + 渲染层**

- **第 1 批(纯文本扩写,0 拓扑风险)**: `n_lore_songmuchang_inn` / `n_lore_zheda_clock_girl` / `n_lore_wulinmen_execution` / `n_lore_kongque_collapse` / `n_lore_leifeng_worm`
  - narrative 4-36 字 → VN 字数 2000-3500
  - 加 vibe variants
  - 不补 stay,不动 _is_tool

- **第 2 批(扩写 + 补 stay)**: `n_scene_red_telephone`(122 字+1 stay) → `n_scene_lost_archive`(226 字+1 stay)
  - 扩写到 2000-4000 字
  - 补 stay 互动到 4-5 个
  - 已有 _is_tool: true

- **引擎渲染层 P0**(UX 必须先于第 2 批完成):
  - 选项分组 UI(stay 互动 vs 主线推进 视觉区分)
  - 内心独白 dim 灰色渲染
  - 长文本分屏(屏幕高 / 6 行,空格继续)

### 不做(本 Pass 6 范围外)

- ❌ 第 3 批 4 NPC(corrosion_face / drowned_official / red_dress_girl / piano_ghost)升级 _is_tool → **延后 Pass 7**
- ❌ 绝对不动批: `n_landmark_picker` / `n_sX_arrive` / `n_scene_morning_lakeside`(Topology 一票否决)
- ❌ 不加新 flag / 新 lore 文档 / 新 reaction_contracts
- ❌ 不动 picker connections(Sandbox debt 留 Pass 7+ 立项)

### 关键风险(按严重度排序)

1. **沙盒玩法承诺断裂**(Meta 阻断风险, 最高)
   - 缓解: Topology 3 批分级 + 绝对不动批 + Meta 分级字数,picker / NPC / 入口节点 100% 不在 Pass 6 范围
   - 红线: 任何"绝对不动批"节点出现 narrative 字数变更 → 打回 PR

2. **flag 75 上限被偷塞**(state_architect)
   - 缓解: § 3 5 项 audit 加固 + 第 1 批首节点 PR 同时合入
   - 红线: PR effects.flags 净增 ≥ 1 → 自动 fail

3. **拓扑 4 红线被偷渡**(topology_designer)
   - 移除 _is_tool / stay→next / flag 镜像 / self-loop choice 跳走
   - 缓解: § 7 4 红线 + 死循环红线(_is_tool 节点 ≥1 非-stay 出口)
   - 红线: 任一红线触发 → 打回 PR

4. **lore 写飞 / 跨周目越界**(lore_keeper)
   - 缓解: § 6 守门 5 项 checklist
   - 红线: NPC 对白透露未达成 deduction → 一票否决(本 Pass 6 第 3 批已延后,风险大幅降低)

5. **vibe variants 误扩到 VN 字数**(ux_designer)
   - 缓解: § 5 协同方案(default 长 / vibe 短 / reaction 中)
   - 红线: 任何 vibe variant > 300 字 → 打回

6. **JSON 编辑触发回归 bug**(qa_path_tester)
   - 缓解: § 8 8 步工作流强制,每节点 1 commit + git tag

### 改动顺序(强制)

1. **引擎渲染层 P0** + state_architect 5 项 audit 加固(同一 PR 系列, Pass 6 起步前置)
2. **第 1 批 5 lore 节点**(逐个完工,每节点 1 commit + git tag)
3. **第 2 批**: `n_scene_red_telephone` → `n_scene_lost_archive`
4. **试玩验证**(qa § 8 终验 8 项 + 用户主观沉浸打分)
5. (Pass 7 决议)第 3 批 4 NPC 改造

### 量化达标 = "大量改动"完成判据

**全部 5 项满足才算 Pass 6 完成**:

1. 引擎渲染层 P0 上线(选项分组 / 独白 dim / 分屏)
2. state_architect 5 项 audit 加固落库 + flag ≤ 75
3. 第 1+2 批 7 节点(共 8 节点含 lake)全 VN 化
4. qa 终验 8 项 § 8 全过 + lore 守门 § 6 全过
5. 用户试玩反馈"沙盒探索感未丢 + 文本密度足够"

### 后续动作

- **助手立即可做**:
  1. 实现 `audit_state.py` 的 5 项 audit 加固(state_architect § 3 P0)
  2. 引擎渲染层 P0(UX § 5 选项分组 / 独白 dim / 分屏)
  3. 用 writing-plans 写第 1+2 批 7 节点实施计划
  4. 第一节点 `n_lore_songmuchang_inn`(第 1 批最低风险)开工

- **不做的事**:
  - 不动绝对不动批(picker / sX_arrive / morning_lakeside)
  - 不做第 3 批 NPC 改造(延后 Pass 7)
  - 不加新 flag / lore 文档 / reaction_contracts
  - 不一次性 batch 多节点(单节点 1 commit + git tag)

### 不同意见记录

- **Meta-Game Designer 投"不可放行"**: 反对均匀铺开。已通过 Topology 3 批分级 + 绝对不动批 + 引擎渲染层 P0 化解(Meta 关切的 picker / NPC / 入口节点 100% 不在 Pass 6 范围)。如执行中第 3 批 NPC 偷做 → 自动回退"不可放行"
- **Topology 5 lore 节点 vs Meta 单 NPC predecessor_voice 方案分歧**: Chief Editor 采纳 Topology 方案(5 lore 节点 narrative 仅 4-36 字最空洞,VN 化 ROI 最高 + 0 拓扑风险)。Meta 原方案的 predecessor_voice(NPC, 437 字)归入 Pass 7 第 3 批

---

**报告生成完成**。Chief Editor 签收。
