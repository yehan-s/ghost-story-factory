# 2026-05-07 伏笔/推论/母题"戏剧化反应"机制

> 评审团:script-review-team
> 任务 slug:dramatic-reaction
> 报告生成时间:2026-05-07 03:30

---

## § 1. 任务描述

扩展 `narrative_variants[].if` 评估器(`src/ghost_story_factory/v5/player.py::_meets_clause()` 199-252 行),新增 3 个条件判断:

- **`deduction_resolved`** — 某推论已合并 → 节点叙述变化
- **`foreshadow_resolved`** — 某伏笔已解 → NPC 说不同的话
- **`theme_resolved`** — 某母题"通透"(所有 manifestations 解开) → 全图氛围切档

给 5-8 个关键节点(picker / 对讲机 / 老人 / 红衣 NPC 等)加"反应式" variant;choice 也享受同套条件;(可选)on_resolve 注入。

**为什么做**:当前元数据(14 伏笔 / 4 推论 / 6 母题 / 10 成就 / 3 路线)只对档案视图(`s` 键)开放,主流程毫无回响。**架构是死的成绩单**,玩家在主流程感觉不到这套架构存在 — 这是最大的浪费。

**任务影响范围**:**多层**(引擎 + 剧本 + 部分 UX/Lore)

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与
**层级判定**:引擎 + 剧本(多层)

**意见**:
原则上支持,但有三处必须卡死。**一、覆盖优先级**:variants 的 require 是"加分项"而非"独占项",匹配命中后必须保留 fallback 到原 narrative 的路径,否则首次未解开的玩家永远拿不到原版铺垫,伏笔链会从源头断裂。**二、立场漂移**:推论解开后回访,人物语气变化必须受"关系 flag"和"当前场景情绪基调"双重约束(老人在『地下室真相暴露』后仍称玩家为"小同志"就是出戏)。**三、时序**:on_resolve 写入 flags 必须带时间戳(`resolved_at_node`),防止"还没走到该节点就因连锁推理提前解锁"导致的因果倒错。

**产出**:
1. **反应式节点白名单**(必须保留默认 narrative):储物间初见 picker / 对讲机异响 / 老人讲述往事 / 红衣女子二次照面 / 监控回放 / 钥匙串细节 / 食堂留字 — 共 7 节点
2. variant schema 扩展提议:`{require, voice_constraint, priority(int), fallback_to_default(bool=true)}`
3. 引擎层 picker 改为按 priority desc 稳定排序,命中即返回;无命中走默认
4. `audit_variants.py` 新增红线:任何节点若所有 variants 都带 require 且无默认版,CI 失败
5. 立场约束矩阵(character × resolved_state → allowed_voice)由 Lore Keeper 出表

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与

**意见**(Linus 风格):
B 是垃圾——参数瘟疫。C 看起来很聪明实际是制造两个真相源(save_manager 有 resolved 集合,flags 又有 `_resolved_<id>` 镜像,任何一处忘了同步就是隐藏 bug)。**A 才是唯一正确解**:State 在构造时就该知道自己属于哪个 story_id、绑定哪个 save_manager。"坏程序员担心代码,好程序员担心数据结构"——save_manager 是 State 的合法依赖,不是外人。**坚决反对 on_resolve_inject**:解开伏笔的唯一真相在 save_manager,谁要查就调查询方法,别搞两套账本。

**产出**:
- **方案选择**:**A** — `State.__init__(..., save_manager=None, story_id=None)`,save_manager 为 None 时三个新条件一律返回 False(向后兼容,不破坏现有测试)
- **拒绝 on_resolve_inject**:不写 `_resolved_<id>` 镜像到 flags,单一真相源 = save_manager,职责分离铁律
- **条件统一**:beat 级 require 和 choice 级 require 共用同一套 `_meets_clause`,不分开
- **命名规范**:
  - `deduction_resolved: "D-001"` → 单条 = `["D-001"]`
  - `deduction_resolved: ["D-001", "D-002"]` → **ANY 语义**(任一解开即满足)
  - 需要 ALL 语义请显式 `all_of: [{deduction_resolved: "..."}, {...}]`
- **theme_resolved 检查**:`themes[id].manifestations ⊆ save_manager.get_resolved_foreshadows(story_id)`
- **SaveManager 需暴露**:`is_deduction_resolved` / `is_foreshadow_resolved` / `get_resolved_foreshadows(story_id) -> set` 三个查询方法

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:深度参与

**意见**:
这是元游戏的核心命题:玩家"知道"和角色"知道"必须分离。跨周目继承应是"元层认知"而非"叙事 flag"——D1 在本周目解开,下周目同节点 narrative 可以切,但切的是"叙述者口吻 / 选项措辞 / 隐藏选项可见性",**不是角色对话事实**。否则角色失忆设定崩塌,Lore 自相矛盾。**反对**把"解开 N 推论"作为 true ending 硬门槛——会逼玩家刷周目,违背"一周目完整体验"原则;改为"额外结局变体"或"档案彩蛋",保留 true ending 在单周目可达。

**产出**:
- **ADR-008《跨周目认知继承与状态分桶契约》**(后续撰写)
- 三命名空间设计(放在文档而非变量前缀):
  - `meta.deduction_resolved:D1` 只读 SaveManager,只能驱动 narrative_variants 切换、不可写 run 状态
  - `run.foreshadow_seen:F3` 读 per-run 状态,可被 on_resolve 写入
  - `motif.echo:M2` 读 meta 计数(母题累计触达次数),驱动隐藏选项可见性
- 配套交付:`audit_state.py` 扩展校验(禁止 on_resolve 写 meta.*)、tree.json 跨周目反应矩阵示例(linmou_1985 节点的 meta-aware variants 模板 3 例)
- **明确反对**:把"解开 N 推论"作为 true ending 硬门槛 → 改为可选档案成就

---

## § 5. UX Designer — 文字体验设计师

**相关度**:深度参与

**意见**:
戏剧化反应是恐怖叙事的灵魂——它让世界"记得"玩家做过什么。但 UX 上最大的陷阱是"玩家不知道变了什么,以为是 bug"。**节点级 variant 静默切**(让玩家自己发现差异 = horror 体验的核心快感);**母题级是一次性大变化**,值得轻量环境提示(如灯光/气味描述变化的 narration beat);从未解开推论的玩家进同节点不应感到困惑,他们看到的是"默认 variant",本身自洽。**关键原则**:variant 必须独立可读,不能依赖玩家"记得上次说了什么"。

**产出**:
1. **切换策略**:节点级 variant 静默切(无动画无提示),母题级切换在首次触发节点插一段过渡 narration("空气里的味道变了"),**拒绝 glitch 动画/弹窗**(破坏恐怖氛围)
2. **variant 自洽原则**:每条 variant 必须独立成立,新玩家读不出"这是变化版"
3. **新选项无标记**:通过文本内嵌暗示("你忽然想起前任的话…")而非 UI 标签
4. **archive_view 增加"反向影响索引"**:每条已解锁伏笔/推论下显示"影响节点:N3, N7, N12...",通关后玩家可 trace 自己的发现路径
5. **节点元数据加 `variant_trigger_summary` 字段**,让 archive 能聚合"因 X 推论而变化的节点列表"

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与

**意见**:
推论解开后语气切档若无锚点,人物会从"1985 投湖的林副科长"漂成"通用悬疑 NPC"。必须用杭州本地夜班国营质感的具体词钉住。**禁区**:不许出现非杭州地标(外滩、长城)、非 80 年代物件(智能手机、扫码)、非国营夜班用语("打工人"、"内卷")、不许把红衣女子写成日式怨灵(贞子式),她是西湖溺亡叙事谱系。

**产出**:**《杭州夜班 Lore 切档锚点表 v1》**

| NPC | 解开前 | 解开后 |
|---|---|---|
| 林副科长 | 小同志/小鬼 | 小赵/小张(具名) |
| 老人 | 后生 | 后生家 + 方言尾词「伐」 |
| 红衣女子 | 不语 | 1985 年代词(的确良/搪瓷缸/广播体操) |
| 1986 工人 | 师傅 | 老法师 |

**6 母题 × 视/听/嗅 18 条锚点词库**:
- `hangzhou_constant` — 西湖水汽 / 桂花潮味 / 远处轮渡汽笛
- `scapegoat` — 樟脑丸味 / 旧棉袄 / 煤炉灰
- `time_loop` — 老式挂钟滴答 / 搪瓷盆碰撞 / 磁带倒带声
- `datafication` — G-273 工牌反光 / 打卡机咔哒 / 荧光灯频闪
- `thirteen_curse` — 13 路公交报站 / 平海街 13 号门牌 / 旧日历撕到 13
- `folklore` — 雷峰塔风铃 / 苏堤夜雾 / 灵隐钟声远闻

**Lore 红线 12 条**(地标/物件/语汇/谱系)— 供 variant 创作直接查表替换,**禁止自由发挥**。

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:深度参与

**意见**:
三个新条件类**不会**让 `_meets_clause` 变成上帝函数——它们与现有 13 类同构(都是 state 谓词查询),只是查询对象从 flags/inv 换成 resolved_set。**真正的风险在 variant 维度爆炸**:14 伏笔 × 4 推论 × 6 母题 = 24 个独立布尔维度,理论 state 空间 2^24 ≈ 1670 万。但实际只有 5-8 个节点反应,每节点 2-3 个 variant(default + 1-2 个 resolved 切档),总增量 ~15-20 variants,可控。**resolved_set 单调递增**,玩家"回不到原版"——这是**特性不是 bug**,反应式节点本就该体现认知升级。`theme_resolved` 的 ⊆ 检查在 N=6 时 O(N) **完全无需 cache**(微秒级)。

**产出**:
1. **维度声明**:resolved_set 是 monotonic-growing set,与 flags 同语义层,**不引入新拓扑维度**
2. **Variant 选择规则**:`_meets_clause` 返回**首个匹配 variant**(列表序=优先级序),编剧手工排序 specific→general
3. **可达性约束**:default variant **必须保留**,在所有 resolved 状态下若玩家选"我重新审视"可显式 reset 触发(向后兼容路径)
4. **性能基线**:不 cache,加 `assert len(theme.manifestations) <= 8`,超限再议
5. **测试**:变异测试覆盖单条件、双条件、三条件叠加共 8 种组合,断言选中 variant 唯一

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与

**意见**:
新增三条件后,**核心风险是反应式 variant 成为死代码**——玩家路径无法触发 resolve,variant 永远沉默。当前 `audit_variants` 只检测重复访问无分化,无法识别"可达但永不满足条件"的 variant。**必须把 resolve 事件纳入状态空间契约(ADR-007)**,让 audit 工具能反向回溯。Linus 原则:好代码没有特殊情况——reaction variant 不应是孤岛,而是状态机的正常分支,必须可达性可证明。

**产出**:

1. **测试套件 `tests/test_reaction_coverage.py`**:
```python
def test_all_reaction_variants_reachable(tree):
    reactions = collect_reaction_variants(tree)
    for variant in reactions:
        resolver_node = find_resolver(tree, variant.required_id)
        assert resolver_node, f"{variant.id} 引用了不存在的 resolve"
        path = bfs_path(tree, root='G-273', via=resolver_node, to=variant.host_node)
        assert path, f"{variant.id} 是死代码"
```

2. **G-273 测试路径示例**(D1 解开后回 picker 触发反应):
```
ROOT → S1.告示栏[picker] → S2.对比笔迹[on_resolve F1]
     → D1.推理:换班表伪造[on_resolve D1]
     → S1.返回告示栏[revisit, variant require deduction_resolved=D1 触发]
        → 新文本:"纸边的折痕方向不对——是有人撕下重贴。"
```

3. **新工具 `tools/audit_reactions.py`**(扩展 audit_state):
   - **DEAD_REACTION**:variant require X_resolved=Y,但全树无 resolver 节点能解开 Y
   - **UNREACHABLE_REACTION**:resolver 存在,但从 resolver 出发 BFS 到 variant 宿主节点不可达
   - **ORPHAN_RESOLVE**:resolver 解开了 Y,但无任何 variant 消费 Y(剧本浪费)
   - 加进 CI:`audit_tree && audit_state && audit_variants && audit_reactions` 全绿才放行

4. **剧本契约补丁(ADR-007 增量)**:
   - 每加一个 deduction/foreshadow/theme,必须同时声明:`resolver_node` + `consumer_nodes`
   - tree.json 顶部 `lore_canon` 同级新增 `reaction_contracts` 字段,audit 直接消费此契约
   - 没声明 = audit ERROR,不让进 main

**Bug 等级**(防止性):
- **阻断**:DEAD_REACTION / UNREACHABLE_REACTION
- **严重**:ORPHAN_RESOLVE(剧本浪费)
- **一般**:ANY/ALL 语义混淆(测试用例覆盖)

**判定**:本任务通过门槛 = `audit_reactions` 跑出 0 DEAD_REACTION + 0 UNREACHABLE_REACTION,且 `test_reaction_coverage` 全绿。

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行**

### 关键风险

1. **死代码风险(QA + Topology)**:反应式 variant 若无 resolver 节点 / resolver 后回不到宿主节点,就是写了不跑。**必须**先做 `audit_reactions.py` 上 CI,再写内容。
2. **真相源分裂(State Architect)**:`on_resolve_inject` 镜像 flags 制造两套账本 — **拒绝**。单一真相源 = `save_manager`,State 持引用查询。
3. **角色立场漂移(Chief Editor + Lore Keeper)**:推论解开后人物语气切换必须用 Lore 锚点表(已产出),编剧不许自由发挥。
4. **新玩家困惑(UX)**:default variant 必须独立可读,不能预设"玩家记得上次说了什么"。

### 决议矩阵(评审中的不同意见处理)

| 议题 | Chief 提议 | 反对方 | 决议 |
|---|---|---|---|
| `on_resolve_inject` + 时间戳 | ✅ 加 | State Architect ❌ | **采纳 State 方案**,拒绝镜像。时序在 `audit_reactions` 检测 resolver→consumer 顺序 |
| variant schema 扩展(`voice_constraint` / `priority` / `fallback_to_default`) | ✅ 加字段 | Topology(列表序=优先级序,够用)、State(过度设计) | **不加新字段**。优先级用列表序;立场约束用 Lore 锚点表 + 编剧纪律;default 由 `audit_reactions` 强制 |
| meta./run./motif. 三命名空间前缀 | Meta-Game 提议 | State Architect(变量名前缀污染) | **不上前缀**,只在 ADR-008 文档说明语义分桶。实现层 `_meets_clause` 自然分桶(查 save_manager = meta;查 self.flags = run) |
| true ending 解锁 = 解开 N 推论 | — | Meta-Game ❌ | **拒绝**作为硬门槛,改为档案彩蛋 |
| `archive_view` 反向影响索引 | UX 提议 | — | **采纳**,通关后 trace 价值大 |

### 后续动作

**实施分 4 Phase**(用 `superpowers:writing-plans` 写 spec):

1. **Phase 1 — 引擎扩展**(~50 行)
   - `State.__init__` 加 `save_manager` + `story_id` 可选参数,默认 None
   - `_meets_clause` 加 3 个新条件分支(save_manager None 时返回 False 安全降级)
   - `SaveManager` 暴露 `is_deduction_resolved` / `is_foreshadow_resolved` / `get_resolved_foreshadows`
   - 单元测试:`tests/test_meets_reaction.py`(8 种组合 + 向后兼容)

2. **Phase 2 — 工具先行**(QA 守门)
   - `tools/audit_reactions.py`:DEAD_REACTION / UNREACHABLE_REACTION / ORPHAN_RESOLVE 三红线
   - `tree.json` 顶部加 `reaction_contracts` 字段(剧本契约)
   - `tests/test_reaction_coverage.py`(可达性测试)
   - **CI 流水线接入**:audit_reactions 不绿不让进

3. **Phase 3 — Lore 锚点表落地**(Lore Keeper 守门)
   - `data/lore_voice_matrix.json`:4 NPC × 2 状态语气矩阵
   - `data/motif_anchors.json`:6 母题 × 视听嗅 18 条锚点
   - 写到 ADR-008 / 或合并入 ADR-007 增量

4. **Phase 4 — 内容填充**(7 节点 × 2-3 variants)
   - 7 个反应节点(Chief Editor 白名单)各加 variant
   - default variant 必须保留 + 独立可读
   - `archive_view.py` 加反向影响索引

### 不同意见记录

- **Chief Editor 不同意 State Architect 完全拒绝 `on_resolve_inject`**:认为时序约束(`resolved_at_node`)在审查复杂连锁推理时仍有价值。
  → **决议**:接受 State 单一真相源原则,但 `audit_reactions` **必须**检测"resolver 节点是否在 consumer 节点的所有可达路径之前"(等价时序约束)。
- **Meta-Game 想要三命名空间前缀,State 反对**:
  → **决议**:实现层不加前缀(避免污染 prompt),但在 ADR-008 / 评审报告本节固化"meta vs run vs motif"语义,编剧创作必须遵守。

---

**评审用时**:~15 分钟(并行 7 agent + Chief 汇总)
**报告产出**:本文件
**下一步**:用户批准后,助手用 `superpowers:writing-plans` 写实施 spec
