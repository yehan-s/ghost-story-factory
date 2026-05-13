# 评审团报告: Pass 24 linmou 终局反咬 + Pass 25 跨周目人格惯性

日期: 2026-05-13
任务:
- 挂账项 1: linmou ending 跨周目反咬补完(Pass 24 候选)
- 挂账项 2: Meta「人格惯性」演出(Pass 25 候选)
Issue: 待创建
决议:
- Pass 24:**放行**
- Pass 25:**修改后放行**(State Architect A 方案 + MRU + 限定主线结局 + 引擎 `.last` 取值器)

> 出席:Chief Editor / State Architect / Meta-Game Designer / Lore Keeper / QA(5/7)
> **缺席**:Topology Designer / UX Designer(两次催场仅 idle 无正文,按缺席记录)

---

## 1. Chief Editor

结论:Pass 24 放行;Pass 25 修改后放行。

**挂账项 1**:E_LINMOU_RELEASE / E_LINMOU_EXPOSED 没反咬就是 sandbox debt,Pass 23 已立模板,机械复刻即可。0 新字段,0 拓扑改动,1 PR ≤ 80 行。

**挂账项 2**:Meta 原方案 `profile_history[]` 新字段 🔴 否决——违反 ADR-007/008 单一真相源,画像是 in-memory 派生量不许落地。但"上周目最终画像 = ending_id"这件事是真的,**ending 就是画像的冷冻态**。`endings_seen[story_id]` 已经存了,直接派生即可,**零新字段、同一字段两种语义(反咬 + 画像惯性),完全合规 ADR-010**。

---

## 2. State Architect

结论:Pass 24 放行;Pass 25 修改后放行,**A 方案**。

**关键裁定**:

- **方案 A(endings_seen 派生,推荐)**:`endings_seen[story_id].last` 取 MRU(最后一次通关的 ending),作为上周目主导画像的唯一信源。`ending_id → 画像语义` 对照表写在 ADR / 剧本 README,**不进引擎**,引擎只补一个 `.last` 取值器,**约 5 行代码**。
- **方案 B(持久化画像快照)**:🔴 **否决**。新字段违反 ADR-007/008,且 behavior_profile 本就是派生量,落地之后会和 endings_seen 互相打架,出现"两份真相"。
- **方案 C(Meta 折衷)**:实质是 A 的实现细节,本身没错,但 Meta 把它讲成新方案,容易混淆。**并入 A**,不另立。

**红线**:

1. 取值规则用 **MRU(last seen)**,不要均值化或多 ending 投票——画像应当稳定可预测,投票会让玩家感到 NPC 反应"飘"。
2. **不给 BAD 结局写 cross_run variant**。BAD 结局是死局,不应该让玩家在下一轮听到 NPC 暗示"我记得你那次失败了",会扭曲画像语义。
3. `ending_id → 画像` 映射只许写在文档,**不允许引擎硬编码**——明天加新 ending 不能改代码。

---

## 3. Meta-Game Designer

意见(Chief 备注):**对挂账项 1 投不值得做,理由失效**;对挂账项 2 推荐方案 C。

**Meta 反对理由原文**:"linmou 是 sandbox debt,不值得本轮再补。"

**⚠️ 信息过时**:Pass 21 已偿 linmou sandbox debt:

- 2 个 `_is_tool` 节点已建
- 1 处 `stay: true` 工具自循环已建
- 1 处 reaction variant 已建
- landmark `connections` 网状关系已 manifest 层落地
- `audit_sandbox` **12/12 全绿**

Meta 的反对建立在 linmou 仍是 27 节点单向辐射的旧状态上,事实已不成立。**Chief Editor 推翻 Meta 反对,挂账项 1 进 Pass 24**。

挂账项 2 上 Meta 推荐的方案 C 与 State A 实为同事,并入 A 执行。

---

## 4. UX Designer

**缺席**。两次催场仅 idle 无正文,按缺席记录。

**Chief 代述需要回答的问题**(留作 Pass 25 开工前补意见):

- 「似曾相识」对白的呈现节奏:第一句话就暗示,还是延迟到关键节点?
- 是否需要在 TUI 上有任何**视觉**提示(如 NPC 名字前的 marker),还是纯靠台词承担?

**预设默认**:无视觉 marker,纯台词承担,呈现节奏 = 该 NPC 首次出现的 narrative 即触发对应 variant。UX 后续如有反对意见以补丁形式回归。

---

## 5. Lore Keeper

结论:Pass 24 放行;Pass 25 修改后放行。

**挂账项 1 锚点选定**:

- `E_LINMOU_RELEASE` → **`n_scene_lost_archive`**(纸/档案路径):释放对应"还林某清白",最合理的痕迹是档案被人翻动过、夹层多一张纸条。
- `E_LINMOU_EXPOSED` → **`n_npc_predecessor_voice`**(声/口述路径):曝光对应公开化处理,最合理的痕迹是前任值班员口述里多一句"上头说这事不能再压了"。

**挂账项 2 ending → 画像派生映射表**(写入 ADR / 剧本 README,**不进引擎**):

| ending_id | 上周目主导画像 | NPC 暗示语气 |
|---|---|---|
| `E_DATA` | 删除/规避 | "你那种眼神,不是第一次想把东西抹掉的人才有的。" |
| `E_TRUTH` | 曝光/记录 | "你像是已经习惯了把事情翻出来。" |
| `E_TRUE` | 取证 + 救援(复合) | "上次见你的时候,你救了一个不该救的人——不是这里。" |
| `E_LINMOU_RELEASE` | 共情/释放 | "你身上有股……愿意放手的气。" |
| `E_LINMOU_EXPOSED` | 公义/曝光 | "你做过让人不痛快的对的事,我看得出来。" |

**铁律**:NPC 跨周目记忆**只走"档案 / 声 / 人"三选一**——任何"清洁工记得你"、"论坛账号识别你"都不合理,违反沉浸契约直接打回。

---

## 6. Topology Designer

**缺席**。两次催场仅 idle 无正文,按缺席记录。

**Chief 代评估**(留作 Pass 25 开工前补意见):

- 挂账项 1 不改拓扑,只在既有节点加 `narrative_variants`,无 variants 爆炸风险。
- 挂账项 2 涉及 5 个 main ending × 多个 NPC 节点,若每个 NPC 都全表覆盖会爆。**预设分桶策略**:每个 NPC **最多挂 1 条 cross_run variant**(优先匹配 MRU.last),不需要枚举全部 5 个 ending_id。审计层需补一条:同一节点 cross_run variant 数 ≤ 2,否则告警。

Topology 后续如有反对意见以补丁形式回归。

---

## 7. QA / Path Tester

结论:Pass 24 放行;Pass 25 修改后放行。

**测试矩阵**:

| 挂账项 | 工时 | 新审计 | 关键断言 |
|---|---|---|---|
| 1 linmou 反咬 | 0.5d | 复跑 `audit_cross_run_continuity`,按 `character_id` 分桶 | 每个 linmou main ending 至少 1 处反咬;按 character_id 分桶后,G-273 与 linmou 各自反咬不串味 |
| 2 人格惯性 A 方案 | 1.5d | 新建 `audit_profile_inheritance` | 每个 G-273 main ending(E_DATA / E_TRUTH / E_TRUE / E_LINMOU_RELEASE / E_LINMOU_EXPOSED)至少 1 处派生反应;BAD ending 0 派生反应(红线) |
| 2 方案 B(参考否决) | 3-4d | 需新建 schema 迁移测试、state 字段双写一致性测试 | 否决,不实施 |
| 2 方案 C(并入 A) | 1.5d | 同 A | 并入 A,不另测 |

**红线断言**:`audit_profile_inheritance` 必须扫到"BAD ending → 0 cross_run variant",否则评审一票否决合并。

---

## 8. 风险清单

- **画像映射漂移**:`ending_id → 画像` 表只在文档,如果文档与 NPC 台词语气脱节,玩家会读出违和。**缓解**:Lore Keeper 拥有该表唯一所有权,每次新 ending 加入必须同步更新。
- **MRU 取值过于稳定**:玩家如果先通 E_TRUTH 再通 E_DATA,第三周目只会感受到 E_DATA 画像。**缓解**:这是有意为之——画像应当稳定可预测,Pass 25 之后如有强需求再考虑加权,但目前不做。
- **Variants 爆炸**:5 ending × N NPC 节点 = 潜在数百 variants。**缓解**:每节点 ≤ 2 条 cross_run variant 上限,审计强制。
- **BAD ending 误挂**:实施时若复制粘贴误把 BAD ending 写进 variant condition,会产生"NPC 暗示玩家上轮死了"的违和体验。**缓解**:`audit_profile_inheritance` 红线扫描。
- **Meta 信息时效性**:Meta-Game Designer 的反对建立在 Pass 21 之前的 linmou 旧状态,后续评审应建立"反对意见基于哪轮 audit 报告"的引用规范,避免重复出现。

---

## 9. 综合建议(Chief Editor 拍板)

### 9.1 Pass 24:挂账项 1 直接进开发(放行)

1. 在 `n_scene_lost_archive` 增加 `narrative_variants[].if.ending_seen` 引用 `E_LINMOU_RELEASE`,Lore Keeper 出词。
2. 在 `n_npc_predecessor_voice` 增加同形 variant 引用 `E_LINMOU_EXPOSED`。
3. State Architect 校验 0 新字段。
4. QA 复跑 `audit_cross_run_continuity`,补 character_id 分桶断言。
5. 预算 ≤ 80 行 / 1 PR。

### 9.2 Pass 25:挂账项 2 修改后放行(A 方案实施清单)

1. **引擎补 `.last` 取值器**(约 5 行):`endings_seen[story_id].last` 读 MRU,无值返回 None。
2. **写 ADR(新建)**:`docs/architecture/ADR-011-cross-run-profile-inheritance.md`,内容包含:
   - 决策:画像从 `endings_seen.last` 派生,0 新字段
   - 拒绝方案 B 的理由(违反 ADR-007/008)
   - `ending_id → 画像` 完整映射表(从 §5 复制)
   - 红线:BAD ending 不挂 cross_run variant
3. **剧本侧**:挑选 G-273 中**至少 5 处 NPC narrative 节点**(每个 main ending 对应 ≥ 1 处),Lore Keeper 写词,挂 `narrative_variants[].if.ending_seen` 引用对应 main ending。
4. **审计层补 `audit_profile_inheritance`**:
   - 红线 A:每个 main ending 至少 1 处 cross_run variant 引用
   - 红线 B:BAD ending 0 cross_run variant 引用
   - 红线 C:同一节点 cross_run variant ≤ 2
5. **预算**:1.5d,引擎 5 行 + ADR 1 篇 + 剧本 variants ~5-10 处 + 审计 1 个新 audit。

### 9.3 缺席记录

- **Topology Designer**:Pass 25 开工前需补 variants 分桶上限意见(目前用 Chief 预设值:每节点 ≤ 2 条,审计兜底)。
- **UX Designer**:Pass 25 开工前需补"似曾相识"对白呈现节奏意见(目前用 Chief 预设值:无视觉 marker,纯台词承担,首次 narrative 即触发)。

两人如未在 Pass 25 开发前补意见,默认采纳 Chief 预设值。后续以补丁形式回归。

### 9.4 流程节点

- Pass 24 PR 合并后,在 INDEX 标记"已落地,验证通过"
- Pass 25 启动前需:① ADR-011 草稿 ② Topology / UX 补意见(或默认采纳)③ `.last` 取值器 PR
- 完成后 Pass 25 决议升级为"已落地,验证通过"
