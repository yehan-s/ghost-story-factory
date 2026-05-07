# ADR-009: linmou_1985 角色周目契约 + 跨周目联动

## Status
Accepted

## Date
2026-05-07

## Context

`linmou_1985`(林副科长)在 8 棺角色 roster 中已声明,通关 G-273 E_TRUTH 解锁,但**没有可玩内容** — 整个解锁系统是空架子。第二可玩角色是把"通关解锁"机制变现的最直接方式。

7 人评审团对 `linmou_1985` 角色周目设计给出意见,产出 `docs/team-reviews/2026-05-07-linmou-arc.md`,决议为"修改后放行"。本 ADR 固化关键决议。

## Decision

### 周目结构(Phase 拆分)
- **P0(本期)**:Act 1 — 1985-10-18 投湖前 6 小时,~5000 字 / 50 节点 / 4 ending 闭环
- **P1(后续)**:Act 2 — 1986-08-17 鬼身买第 8 张归航船票
- **P1(后续)**:Act 3 — 执念结局扩展(每 ending ~1000 字补充)

### 核心设计哲学
**三幕悖论是 feature 不是 bug**(Chief Editor)。linmou 周目玩的不是"历史"而是**鬼魂在湖底的循环回放**(参考《聊斋·王六郎》代死结构)。Act 1 任何选择最终都必须收束到"投湖"这个事实节点(lore canon 红线,**不可破**),但**死法 / 心境 / 最后一念**可以分支。

### 4 个 Ending Canon
| ID | 中文 | 核心情绪 | 锚点 |
|---|---|---|---|
| `E_LINMOU_GRIEVANCE` | 冤 | 拨款单被烧/被夺,带恨投湖 | 蓝布账册包空了一份 |
| `E_LINMOU_REGRET` | 悔 | 把账册塞进老李抽屉,牵连他 | 老李算盘上摆着搪瓷缸 |
| `E_LINMOU_RELEASE` | 释 | 接受集体信念已死,独自抵账 | 西湖夜雾中带账册包入水 |
| `E_LINMOU_EXPOSED` | 曝光(隐藏) | 被同事举报,湖面成公开行刑场 | 大院广播喇叭批斗声 |

### State 极简(Linus 反加法者)
**0 新字段, 1 新 clause, 4 新 ending_id**(State Architect):
- **拒绝** `character_played` / `linmou_ending` 字段(冗余 — `endings_seen` 已是真相源)
- 复用 `endings_seen[story_id]: list[ending_id]`,linmou 同 story_id `杭州_v7`
- `_meets_clause` 加唯一新条件 `ending_seen` (支持 `*` 通配)
- SaveManager 升级 v4 → v5:`endings_seen` `list` → `dict[story_id, list]`,旧版自动迁移

### `ending_seen` Clause 形式
```python
# 精确匹配
{"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}

# 通配:任意该 story 的 ending
{"ending_seen": {"story_id": "杭州_v7", "ending_id": "*"}}
```

### 双向联动(用户决议)
- **G-273 → linmou**:G-273 已通关 E_TRUTH → linmou Act 1 节点的叙述者口吻切档(玩家"已知答案的回响")
- **linmou → G-273**:linmou 通关 E_LINMOU_* → G-273 现有 3-5 个节点 narrative 切档

技术上**零额外开销** — 同一 `_meets_clause` + 同一 `ending_seen` clause 实现两个方向。

### 拓扑契约(Topology Designer)
- 新建 `_fragment_v7_linmou_1985.json`,**不嵌入 shared**(物理分片 ≠ 逻辑边界,linmou 是独立时空)
- 命名:`n_l1985_*` 前缀(年代锚点)
- **picker hub**:`n_l1985_landmark_picker`(复用 G-273 模式)
- 节点预算 50:picker 1 + 4 地标 × 10 + 收束 4 + endings 4 + entry 1
- 4 地标:**算盘房 / 锅炉房 / 档案室 / 湖边凉亭**

### 必死不变量(QA Path Tester)
`tools/audit_paths_linmou.py` 强制:
- **INV-1**:所有 linmou 周目终态(`choices=[]`)∈ 4 ending 白名单
- **INV-2**:无边从 linmou 子图通向 Act 2/3 节点(本期 trivial,P1 落地时立刻补)
- **INV-3**:投湖节点 `n_l1985_lake_jump` 后置必为 ending,无中间 narrative
- **INV-4**:4 ending 节点必须有 `_lore_canon.must_die: true`(canon 标记)

### Cross-character Contract(QA)
`audit_reactions.py` 加 **DEAD_ENDING_SEEN** 检测:任何 variant 引用 `ending_seen.ending_id`,该 ending 必须存在为节点表中的 ending(通配 `*` 不检查)。

### Lore Canon(Lore Keeper)
- **单位**:杭州市第二轻工业局物资供应公司财务科("二轻物资")
- **投湖地点**:西湖北山街锦带桥东侧水域,1985-10-18 23:40 前后
- **当夜**:无月(农历九月初五)、12-15℃、末班船 22:30、6 小时空窗
- 12 红线词汇 + 价值观红线 + 物件红线(见 `data/linmou_act1_lore.json`)

### UX(UX Designer)
- **CLI 主菜单三态**:`locked`(灰剪影+解锁条件)/ `unlockable`(闪烁+"!"badge)/ `playable`(立绘+结局徽章+前传·X/3)
- **色彩节奏**:linmou 暖琥珀 #C9A227 + 宋体 80ms,vs G-273 冷青 + 等宽 60ms
- **投湖三段式静默**:对白渐隐 → 黑屏 → 水声 ASCII → 黑屏 → 主菜单
- **拒绝**:glitch 动画 / 弹窗 / 文字解释(沉默本身是叙事)
- **跨角色反向影响**:静默切 + 字体微变(琥珀色)— 奖励观察者,不打扰主线

### Phase 拆分回归安全(QA)
- Act 1 上线时 fragment 加 `schema_version: "1.0-act1-frozen"`
- Act 2 单独建 `_fragment_v7_linmou_1985_act2.json`
- 生成路径快照 `tests/snapshots/linmou_act1_paths.json`
- audit_reactions 加 `frozen_node_check`:Act 1 已发布节点不允许改 narrative/choices(只能新增出边)

## Alternatives Considered

### Option A: `endings_seen[story_id, list]` dict 化 [✅ 采纳]
- Pros: 跨周目区分清晰,反向联动自然实现
- Cons: schema 升级需要迁移脚本(已加,旧版自动转 dict[杭州_v7])

### Option B: 新增 `character_played` + `linmou_ending` 字段 [❌]
- Why rejected: State Architect 强烈反对 — 冗余,与 `endings_seen` 双份真相源,迟早不同步

### Option C: 不同 story_id `linmou_1985_v1` [❌]
- Why rejected: linmou 是杭州故事的角色周目,不是新故事。两个 story_id 会让 SaveManager 跨故事查询,破坏现有数据结构

### Option D: 三幕一次性发布 12000-15000 字 [❌]
- Why rejected: 工作量过大,Lore canon 一次性消耗过多;Act 1 自带闭环 4 ending 已是完整悲剧,Act 2/3 标"新章节"而非"未完待续"

### Option E: 第三角色身份(Meta-Game 提议沈玉茹 vs roster 的 yeh_1991) [搁置]
- 决议:本 ADR 不锁定第三角色,沈玉茹是 Meta 远期建议,Act 3 之后再议

### Option F: True ending = 解开 N 推论 [❌]
- Why rejected: 逼玩家刷周目违背单周目完整体验。改为档案彩蛋(沿用 ADR-008 决议)

## Consequences

### Positive
- 第二可玩角色变现"通关解锁角色"机制,8 棺 roster 不再是空架子
- `endings_seen` dict 化让跨周目反向联动自然实现
- 必死不变量 + cross-character contract 守门,P1 加内容时不破坏 P0
- Lore canon 文档 + 数据双层固化,内容创作可机械查表

### Negative & Mitigation
- 存档 schema 升级 v4 → v5,需要迁移
  - **Mitigation**:`load()` 自动检测旧版 list,迁移归入 `杭州_v7`,有测试覆盖
- 内容创作 ~5000 字,工作量大
  - **Mitigation**:每地标 1 commit,可中途暂停;Lore 锚点表 + 锚点物件清单降低创作随机性
- INV-2(无边逃出)在 P0 是 trivial(Act 2/3 不存在),P1 上线时要立刻补
  - **Mitigation**:Phase 拆分文档明示;Phase 4 完成立即把 INV-2 真实化

## 参考

- 评审报告: `docs/team-reviews/2026-05-07-linmou-arc.md`
- 实施 plan: `docs/superpowers/plans/2026-05-07-linmou-arc-act1.md`
- Lore 数据: `data/linmou_act1_lore.json`
- 守门工具: `tools/audit_paths_linmou.py` + `tools/audit_reactions.py`(DEAD_ENDING_SEEN)
- 关联 ADR: ADR-007(状态空间契约)、ADR-008(戏剧化反应机制)
