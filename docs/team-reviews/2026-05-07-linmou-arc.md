# 2026-05-07 linmou_1985 角色周目(第二可玩角色)

> 评审团:script-review-team
> 任务 slug:linmou-arc
> 报告生成时间:2026-05-07 04:00

---

## § 1. 任务描述

新增 **linmou_1985**(林副科长,1985 投湖前夜的财务科副科长)作为第二可玩角色。原计划三幕剧 12000-15000 字:
- Act 1: 1985-10-18 投湖前 6 小时(20:00 → 02:00)
- Act 2: 1986-08-17 鬼身买第 8 张归航船票
- Act 3: 结局(4-6 个分支)

进入点:**主菜单选**(默认锁定,通关 G-273 E_TRUTH 解锁)。
跨角色联动:**linmou 选择 → 反向影响下次 G-273 看到不同详情**(复用刚做的反应机制 + 加 character_played meta flag)。

**任务影响范围**:**多层**(剧本 + 引擎 + UX + Lore + Meta)

---

## § 2. Chief Editor — 首席编辑

**相关度**:深度参与
**层级判定**:多层

**关键洞察**:**三幕悖论不是 bug,是 feature**。linmou 周目玩的不是"历史"而是"鬼魂在湖底的循环回放"(参考《聊斋·王六郎》代死结构)。Act 1 任何选择最终都必须收束到"投湖"这个事实节点(lore canon 红线,不可破),但**死法/心境/最后一念**可以分支。

**意见**:Act 3 的差异在于"鬼魂带着什么执念离开"——这个执念是反向影响 G-273 的真正变量。**反向影响 = 同节点不同 narrative 文本替换**,不新增分支。12000-15000 字必须拆,Act 1 单独可玩可发布,Act 2/3 标记锁定。

**产出**:
1. 《linmou 周目剧本契约 v0.1》— Act 1 收束铁律(必死)+ Act 3 三执念变量(冤/悔/释)+ canon 红线
2. 《反向影响映射表》— 3-5 个 G-273 节点 narrative 替换,用 character_played + linmou_ending 双键路由(注:State Architect 后续否决双字段方案)
3. 《拆分发布计划》— Act 1 ~5000 字 P0 → Act 2 ~4000 字 P1 → Act 3 ~3000-6000 字 P1
4. Act 1 发布时主菜单显示 linmou,标"前传·1/3"

---

## § 3. State Architect — 状态系统建筑师

**相关度**:深度参与(Linus 反加法者)

**意见(强硬)**:
> 你又要加两个字段。停。`character_played` 是冗余 — `endings_seen` 已经是 `dict[story_id, list[ending_id]]`,通关过 linmou 等价于查询。`linmou_ending` 同理,就是 `endings_seen[...][-1]`。**0 新字段, 1 新 clause, 3-4 新 ending_id**。

**产出**:

```python
# _meets_clause 唯一新条件:
# clause 形如 {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}
# 通配:{"ending_seen": {"story_id": "杭州_v7", "ending_id": "*"}}  → 任意该故事 ending
if "ending_seen" in clause:
    sid = clause["ending_seen"]["story_id"]
    eid = clause["ending_seen"]["ending_id"]
    seen = save.endings_seen.get(sid, [])
    if eid == "*":
        return len(seen) > 0
    return eid in seen
```

- **新 ending(canon)**:`E_LINMOU_GRIEVANCE`(冤)/ `REGRET`(悔)/ `RELEASE`(释)/ `EXPOSED`(曝光,Meta-Game 加的隐藏 ending)
- **同一 story_id `杭州_v7`** — linmou 是杭州故事的角色周目,不是新故事
- **拒绝** `character_played` / `linmou_ending` 字段
- ADR-008 写明:`endings_seen 是真相源`

---

## § 4. Meta-Game Designer — 元游戏设计师

**相关度**:深度参与

**意见**:角色解锁是"叙事承诺装置",菜单不是 UI 是 player journey 锚点。三铁律:
1. 锁定角色暴露"可窥见但不可玩"(诱饵 vs 空槽位)
2. Act 1 单发布**自带闭环 4 结局**,不要 WIP 占位(违反 Never break userspace)
3. 收集本必须分角色 Tab(母题异构,混排稀释叙事密度)

**产出**:
- 主菜单 `character_select` 三态:**locked**(灰剪影+解锁条件)/ **unlockable**(闪烁+"!"badge)/ **playable**(立绘+结局徽章+前传·X/3)
- Act 1 节点预算:**50 ± 10**,**4 ending**(冤/悔/释 + 隐藏曝光)
- **第三角色**:沈玉茹(厂长之女,1985 现场目击者),由 linmou "悔" 结局解锁 → 形成 G-273(现在)→ linmou(过去)→ 沈玉茹(目击)三段真相揭示
- 收集本三 Tab 架构:**G-273 档案 / linmou_1985 遗物 / 沈玉茹回忆**,跨 Tab 反向影响用 `↔` 图标
- 周目计数器 UI:右上角 `Loop 1/3`(派生,不存字段)

---

## § 5. UX Designer — 文字体验设计师

**相关度**:深度参与

**意见**:三态主菜单用色块+字符密度区分。linmou 用**暖琥珀 #C9A227 + 宋体节奏(80ms/字)**,比 G-273 冷青 + 等宽 60ms 慢 25%,营造国营年代沉重感。投湖必死用"三段式静默":对白渐隐→纯黑→水声 ASCII 涟漪→黑屏停顿→返回主菜单。**拒绝**任何文字解释,沉默本身是叙事。

**产出**:

### CLI 三态主菜单草图
```
┌─ 主菜单 character_select ─────────────────────────────────┐
│  [1] G-273 夜班保安            ★★★ 已通关 4/4 结局         │
│      冷青 #4A6B7C / 等宽 60ms                              │
│  [2] 林某 (1985)               ! 新解锁                    │
│      ◇◇◇ 闪烁边框 ◇◇◇                                     │
│      暖琥珀 #C9A227 / 宋体 80ms                            │
│      「他在 G-273 的录音里听过你的名字」                   │
│  [3] ???                       🔒 锁定                     │
│      通关林某「悔」结局解锁                                │
│  [s] 收集本   [q] 退出                                     │
└────────────────────────────────────────────────────────────┘
```

### 投湖三段式静默(linmou Act 1 必死)
```
T+0.0s  对白「我对不起她……」逐字打完
T+0.3s  文字渐隐(每行 fade 100ms)
T+1.5s  ━━━━━ 纯黑屏 ━━━━━
T+2.0s  水声 ASCII:    ～～～  ～    ～～
        涟漪扩散:    （ ○ ）  →  （ ◯ ）  →  （    ）
T+4.3s  仅一行琥珀色:  「1985 年 10 月 18 日 · 西湖」
T+5.3s  →  返回主菜单(unlockable 状态点亮)
```

### 色彩节奏对照
|  | G-273 | 林某 1985 |
|---|---|---|
| 主色 | #4A6B7C 冷青 | #C9A227 琥珀 |
| 字速 | 60ms/字 | 80ms/字 |
| 静默 | 0.5s | 1.2s |
| 节拍 | 现代·急促 | 年代·沉重 |

### 反向影响"环境异变"
linmou 通关后,G-273 周目里 1985 档案条目字体从灰转琥珀色——玩家不点击不会注意,**点击才显**「此处由林某周目解锁」。**奖励观察者,不打扰主线**。

### 收集本三 Tab 横向布局
顶部 `[ G-273 ] │ 林某 │ 沈玉茹`,每 Tab 内纵向滚动。

---

## § 6. Lore Keeper — 世界观考据师

**相关度**:深度参与

**意见**:1985-10-18 是杭州深秋,西湖夜雾重、桂花已谢、梧桐落叶。**林某选西湖,不是钱塘江**——钱塘江夜潮太响、太硬,不适合"安静地走"。1985 杭州关键背景:亚运会落选刺激、价格双轨制试点引发国营单位账目混乱、绍兴酒厂窝案余波——这些是 26 个签字人案件的合理土壤。

**产出**:

### 单位
**杭州市第二轻工业局物资供应公司**(简称"二轻物资")财务科。1985 年正经历采购权下放,签字链最容易出事,副科长是签字漏斗的关键岗。

### 投湖具体地点 + 时间
**西湖北山街锦带桥东侧水域**,**1985-10-18 23:40 前后**。雾气从孤山方向漫过来,水温约 15℃。当夜杭州**无月**(农历九月初五),气温 12-15℃,微风,**末班船 22:30**,之后 6 小时空窗(渔政小艇黎明才出动)。

### Act 1 必出现 lore 元素清单
- **物件**:搪瓷缸(白底红字"劳动光荣")、铝制饭盒、的确良衬衫、人造革黑包、蓝色中山装、煤油应急灯、手摇电话、《浙江日报》1985-10-17 期、二八式永久自行车、半导体收音机(中央人民广播电台对台广播)
- **声音**:更夫梆子(罕见但二轻仓库区还有)、远处 104 厂夜班汽笛、桂花落地前的最后蝉鸣残响、保温瓶塞拔出"噗"声
- **气味**:煤球炉余烬、来苏儿消毒水、隔夜冷饭、雾里的湖水腥味、廉价烟丝(大前门 / 利群)
- **文本锚**:二轻物资 1985 年第三季度采购清单、26 人联签拨款单复印件、"调拨"两字红章

### 林某投湖必带物件
**蓝布人造革账册包**(里面是 26 个签字复印件)— 不是遗书。死意确认靠**物证**,不是文字。

### 红线
- **词汇**:矿泉水/塑料瓶/私家车/手机/BP机/商品房/股票/外卖/快递/超市/微信/支付/打卡机/监控摄像头/电脑/U盘/打印机(用油印/复写纸/算盘)
- **价值观**:不能出现"下海""创业""先富起来"的正面叙事 — 林某要死在"集体主义信念被 26 个签字撕裂"的语境里,**不是**"看不开经济转型"
- **物件**:不锈钢保温杯(用搪瓷)、一次性筷子、彩色塑料(只有蓝灰绿黑白)、合成洗涤剂广告(用肥皂)

---

## § 7. Topology Designer — 拓扑设计师

**相关度**:深度参与

**意见**:
1. **必须新建** `_fragment_v7_linmou_1985.json` — 50 节点单独成档,不嵌入 shared(物理分片 ≠ 逻辑边界,linmou 是独立周目+独立时空,混入会让 merge 来源追踪失效,git diff 爆炸)
2. **必须 picker hub**,不要线性 6 小时(线性 = 单一通路 = 无 Meta 价值)
3. **`n_l1985_*` 前缀**(语义自带年代锚点,与未来 `n_l2010_*` 正交)
4. character 字段隔离会"分裂"节点表 — **是好品味**(分裂的是视图不是数据)
5. 167 节点对 merge/audit 无实质影响,真正要警惕的是 audit_variants 的 O(V²) 在 200+ 节点时

**产出**:

### 拓扑契约
- 新建 `_fragment_v7_linmou_1985.json`
- **节点预算 50**:picker 1 + 4 地标 × 10 + 收束 4 + endings 4 + entry/exit 1
- 4 地标:**算盘房 / 锅炉房 / 档案室 / 湖边凉亭**
- picker `n_l1985_landmark_picker`(复用 G-273 hub 模式)
- 命名:`n_l1985_<area>_<seq>`(如 `n_l1985_abacus_01`)
- 跨角色联动只在 G-273 既有节点的 narrative_variants **增量加** `ending_seen`,**不新增节点**
- `merge_fragments.py` 加一行 fragment 来源日志即可,无需重构

---

## § 8. QA / Path Tester — 路径测试官

**相关度**:深度参与

**意见**:50 节点新拓扑 + picker hub + 4 ending 必死收束 = 路径覆盖高危区。`ending_seen` 是新增的跨周目状态依赖,必须当一等公民写进契约,不是 flag。Act 1 必死是 lore 铁律,**必须在 audit 层固化为不变量**(invariant),不能依赖人工 review。Phase 拆分关键:Act 1 上线即冻结 fragment + 加 schema_version,Act 2 用独立 fragment 追加,避免 diff 污染 P0 快照测试。

**产出**:

### 1. `tests/test_ending_seen.py`(6 用例)
- exact_match / story_mismatch / ending_mismatch
- wildcard_ending(`*`)
- wildcard_story(xfail,留作未来)
- empty_save 全 FAIL

### 2. 必死不变量(`tools/audit_paths_linmou.py` 或扩 audit_tree)
- **INV-1**:所有 linmou_1985 周目终态 ∈ 4 ending 集合(白名单)
- **INV-2**:不存在从 linmou 子图通向 Act 2/3 节点的边(防止逃出生天)
- **INV-3**:投湖节点 `n_l1985_lake_jump` 后置必为 ending,无中间 narrative
- **INV-4**:4 ending 节点 type 必须是 ending 且包含 lore_canon `must_die: true`
- **CI hook**:加入 `audit_all.sh` 第 5 项,失败阻断合并

### 3. audit_reactions cross-character 扩展
- 引用 `ending_seen` 的 clause,其 `(story_id, ending_id)` 必须在某 fragment ending 节点定义中存在
- 反向:任何 ending 节点应在 `docs/cross_character_map.md` 登记其下游影响节点

### 4. Phase 拆分回归安全
- Act 1 上线时 fragment 加 `schema_version: "1.0-act1-frozen"`
- Act 2 单独建 `_fragment_v7_linmou_1985_act2.json`
- P0 上线生成快照:`tests/snapshots/linmou_act1_paths.json`(所有路径 hash)
- audit_reactions 加 `frozen_node_check`:Act 1 已发布节点 id 锁定,Act 2 不允许改其 narrative/choices(只能新增出边)

### 5. picker hub 测试
- 扩 `tools/path_explorer.py` 加 `--story-scope linmou_1985`
- 断言:100% 路径终结于 4 ending 之一
- 4 ending 各自可达路径数 ≥ 1
- 死路径检测:任何节点若 choices 为空且不是 ending,FAIL

---

## § 9. 综合建议(Chief Editor 汇总)

**决议**:**修改后放行**

### 关键决议矩阵

| 议题 | Chief 提议 | 决议 |
|---|---|---|
| `character_played` + `linmou_ending` 双字段 | ✅ 提了 | **❌ 拒绝**(State Architect 反对)。复用 `endings_seen[杭州_v7]: list[ending_id]` |
| 4 ending(冤/悔/释/曝光) | Chief 提 3 个,Meta 加 EXPOSED 隐藏 | **✅ 4 ending**:`E_LINMOU_GRIEVANCE/REGRET/RELEASE/EXPOSED` |
| 同 vs 不同 story_id | — | **同一 `杭州_v7`**(State 决议,linmou 是杭州故事的角色周目) |
| _meets_clause 加几条 | Chief 提 2 个 | **✅ 1 个 `ending_seen`**(支持 `*` 通配),State 极简 |
| Act 1 单发布 WIP 占位 | Chief 提 | **❌ 拒绝**(Meta 反对),Act 1 自带闭环 4 ending |
| 第三角色身份 | linmou 解锁 | Meta 提议**沈玉茹**;但已存 roster 是 yeh_1991。**保留 roster 不变**,沈玉茹是远期建议,不阻塞 Act 1 |
| 投湖时间 | UX 写 1985-7-19(笔误) | **以 Lore Keeper 为准:1985-10-18 23:40** |
| picker hub vs 线性 | Topology 力主 hub | **✅ picker hub** |
| 跨角色 audit 扩展 | QA 提 | **✅ 必扩** `audit_reactions` cross-character contract |

### 关键风险

1. **Act 1 必死不可破**(Lore Keeper + QA):必须 audit 层不变量(INV-1~4),不能人工 review
2. **跨周目 ending_seen 是新一等公民**(QA):必须先做 schema 测试再写内容,否则 G-273 反向影响验证不到
3. **Phase 拆分快照锁定**(QA):Act 1 fragment 冻结,Act 2 不能动 Act 1 内容
4. **Lore 红线不可越**(Lore Keeper):12 红线词汇 + 价值观红线 + 物件红线全锁

### Phase 拆分(本期 P0)

**P0(本期)** — Act 1 ~5000 字 / 50 节点 / 4 ending
- 引擎:`_meets_clause` 加 `ending_seen` clause + `endings_seen` 改 list per story_id(若现状不是)
- 工具:`audit_paths_linmou.py` 不变量 + `cross_character_contract` 扩展 audit_reactions
- 内容:`_fragment_v7_linmou_1985.json`(picker hub + 4 地标 × 10 + 4 ending)
- UX:CLI 主菜单 `character_select` 三态 + 投湖三段静默
- Lore:固化 1985-10-18 setting + 物件清单进 ADR
- 反向影响:G-273 现有 3-5 节点 narrative 替换(用 ending_seen)

**P1(后续)** — Act 2 鬼身补票 / Act 3 执念结局扩展

### 后续动作

用 `superpowers:writing-plans` 写 P0 实施 spec(Act 1 only),分 5 phase:
1. **引擎扩展**:`ending_seen` clause + 测试
2. **工具守门**:audit_paths_linmou + cross_character contract
3. **Lore + ADR**:1985 单位 / 地点 / 物件清单进 ADR-009
4. **内容创作**:linmou Act 1 fragment(50 节点 / 4 ending)
5. **集成**:主菜单 character_select + 反向影响 G-273 节点 narrative 替换

### 不同意见记录

- **第三角色身份冲突**:Meta 提议沈玉茹(厂长之女),roster 现存 yeh_1991。决议保留 roster,沈玉茹作为远期建议(Act 3 之后再议)
- **UX 投湖时间笔误**:UX 草图写 7-19,Lore Keeper 钦定 10-18(深秋)。以 Lore 为准

---

**评审用时**:~30 分钟(并行 7 agent + Chief 汇总)
**决议**:修改后放行(State 极简方案 + Lore 详尽 setting + QA 必死不变量 = 三柱)
**下一步**:用户批准后,助手用 `superpowers:writing-plans` 写 Act 1 实施 spec
