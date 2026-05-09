# Ghost Story Factory · 项目状态快照 & 伏笔注册表

**日期**: 2026-05-07
**状态**: v7 内容完工 + 主菜单/解锁系统实施中
**用途**: **未来失去上下文的 Claude session 读完这份就能接上,继续推进 v8。**

**关系说明**:本文件是 v7 当前事实快照;拓扑原则看 `2026-05-07-v7-maze-master-spec.md`,运行方式看项目根 `V7_PLAY_NOW.md`。

---

## 0. 阅读次序(读这份文档前)

1. 这份文档(完整状态快照)
2. `CLAUDE.md`(项目根)— 工程规则
3. `V7_PLAY_NOW.md` — 怎么跑
4. `2026-05-07-v7-maze-master-spec.md` — v7 拓扑设计
5. `2026-05-07-v7-maze-completion-and-template-spec.md` — 完善 plan
6. `2026-05-07-v8-character-roster-spec.md` — 8 棺角色 roster 草案
7. `docs/templates/v7_maze/` — 模板,用来开新故事

---

## 1. 当前完成度(v7)

### 1.1 数据快照

| 指标 | 值 |
|---|---|
| 故事 | 杭州·断桥残雪·夜班保安 (v7 真迷宫) |
| 主角 | 赵某 G-273 |
| 节点总数 | 145 |
| 结局节点 | 21(8 主 + 13 mini/支线) |
| 节点覆盖率 | 100% |
| tree.json 大小 | ~500 KB |
| 总字数 | ~50,000 字 |
| 平均 narrative | 212 字/节点 |
| 共享 NPC | 13(全部有 narrative_variants) |
| 共享场景 | 7(全部有 narrative_variants) |
| 道具总数 | 30 件(15 件被 require 引用,15 件 flag-driven) |
| 主结局 narrative_variants | 32 种(平均每结局 4 种) |

### 1.2 核心文件

```
play.py                          # CLI 入口
play_tui.py                      # TUI 入口(textual 全屏)
src/ghost_story_factory/
├── v5/player.py                 # 状态 + 渲染逻辑(CLI 主循环)
└── v7/tui_player.py             # TUI(复用 v5 的 State)

stories/hangzhou_yebanbaoan/
├── tree.json                    # 合并产物(玩这个)
├── README.md                    # 玩法说明
├── _fragment_v7_shared.json     # 共享头部 + NPC + 场景 + 结局
└── _fragment_v7_landmark_s1.json ~ s6.json  # 6 个地标

tools/
├── merge_fragments.py           # fragment 合并 + 引用完整性
└── path_explorer.py             # BFS 全路径分析

docs/
├── superpowers/specs/           # ADR / spec 文档
└── templates/v7_maze/           # 复用模板(给新故事用)
```

### 1.3 玩法

```bash
python play.py                                 # CLI 主菜单
.venv/bin/python play_tui.py                   # TUI 主菜单
GHOST_FAST=1 python play.py                    # 关闭逐字打印
python play.py stories/.../tree.json           # 跳过菜单直接玩(开发用)
```

---

## 2. 当前已实现的系统

### 2.1 State schema(`v5/player.py`)

```python
class State:
    PR: int = 0                # 个人共鸣(0-100,玩家不可见,s 键可查)
    GR: int = 0                # 全局共鸣(同上)
    shifts_completed: int      # 完成的地标数
    shifts_skipped: int        # 跳过的地标数(漏卡)
    inv: List[str]             # 随身物品
    flags: Dict[str, bool]     # 200+ 个剧情 flag
    route: Optional[str]       # v6 遗留(v7 不再使用)
    skipped_landmarks: List
    visited_landmarks: List
    puzzle_pieces: List        # 拼图碎片(0-5)
    character: str = "G-273"   # v7 多角色伏笔接口
    meta_flags: Dict[str, bool] # 跨周目持久化(v8)
```

### 2.2 选项可见性分类(`get_choice_status`)

每个选项的 `require` 被分类为:

| 状态 | 触发条件 | 显示效果 |
|---|---|---|
| `visible` | require 满足 / 没 require | 可点击,有编号 |
| `locked` | 仅 inv_has / inv_lacks / puzzle_pieces_min 不满足 | 🔒 显示 + "需要「X」" |
| `hidden` | 包含 spoiler 条件(flags / PR / GR / not / shifts) | 完全不渲染 |

### 2.3 narrative_variants

按顺序匹配,第一个 `if` 条件满足的 `text` 显示。都不满足则 fallback 到 `narrative`。

---

## 3. 共享 NPC 注册表(13 个)

**所有 NPC 都已有 narrative_variants(每个 3-4 个变体)。**

| ID | 标签 | 主入口地标 | 跨地标可达 | 已埋伏笔 |
|---|---|---|---|---|
| `n_npc_faceless_coat` | 空风衣实体(无脸) | S1 | S3 跨流, S7 终局 | 风衣 = 1985 林某穿过的 |
| `n_npc_predecessor_voice` | 前任 G-273 对讲机声 | S1 / S2 / S5 | 任何拍照行为后 | G-272 在 27F,记 11 年 |
| `n_npc_drowned_official` | 1985 投湖林副科长 | S1 / S3 | 共享水下 | 27 笔贪污只 13 笔是他做的,26 笔另一人 |
| `n_npc_red_dress_girl` | 1996 红衣电视女孩 | S2 / S5 / S7 | 跨流 | 真名 何小燕,1996-08-23 货梯失踪 |
| `n_npc_yang_butcher` | 1933 无头黑山羊 | S4 | S6 跨流 | 1933 开山首刀的人,被烧死 |
| `n_npc_helmet_workers` | 1986 沉船 7 工人 | S6 | S3 水下 | 第 8 个买票没上船的是 1985 林某的鬼 |
| `n_npc_piano_ghost` | 1991 自缢叶某 | S5 / S2 跨流 | 共享 | 外婆 1959 也死在同一琴房 |
| `n_npc_corrosion_face` | 裂钟铜锈侧脸 | S3 | S7 | 9 个候选编号,玩家是第 1 个『说不』的 |
| `n_npc_forum_lurkers` | 夜班论坛匿名观众 | 任何拍照后 | — | G-272 在评论区,1985_ghostfile 是林某儿子 |
| `n_npc_evaluator_chair` | 夜班评议会 | 任何关键选择后 | — | G-001 1959 撕过同款小票,被授『革命党人』 |
| `n_npc_eight_self` | 8 棺残片(另一个你) | S7 / 共享 | 多入口 | **8 棺 = 8 个未来角色 roster** |
| `n_npc_cleaner_null` | 不存在的清洁工 | 摄像头死角累积触发 | — | 三处扬声器同步广播 |
| `n_npc_ghost_guard` | 上一任 G-273(已数据化) | S7 / 共享 | — | 11 年前接的红印,12 任叠在同位置 |

### 3.1 NPC 跨周目槽(`_foreshadow_slot` 已埋)

- `n_npc_eight_self`: `["8_self_roster", "1985_linmou_other26", "1986_lin_coin", "1991_yeh_classmate", "1996_red_girl_truth"]`
- `n_npc_ghost_guard`: `["G272_predecessor_identity"]`
- `n_npc_red_dress_girl`: `["1996_red_girl_truth"]`
- `n_scene_lost_archive`: `["all_archive_truths"]`

---

## 4. 共享场景注册表(7 个)

| ID | 场景 | 入口来源 | 关键作用 |
|---|---|---|---|
| `n_scene_lake_underwater` | 西湖水下 | S1 进湖, S3 水下回声, S6 沉船备份池 | 跨地标 hub,8 棺 + 林某 + 钟 |
| `n_scene_27th_floor_corridor` | 不存在的 27 楼走廊 | S2 红衣女孩, S6 b3_unlocked, S7 | 12 任 G-273 工牌墙 |
| `n_scene_b3_corridor` | 平海街 B3 走廊 | S7 入口, S2 跨流深层 | 27 台电视,雪花 |
| `n_scene_evaluator_room` | 夜班评议会档案室 | 拿到候补判官章后任意地标解锁 | E_HIDDEN 入口 |
| `n_scene_lost_archive` | 遗失档案室 | S3 / S5 / 共享 | 5 张拼图 = E_TRUTH 入口 |
| `n_scene_red_telephone` | 红色公用电话亭 | S1 / S5 / 求救后 | 拨 1987 接前任 |
| `n_scene_morning_lakeside` | 6:03 湖滨日出 | 多结局共享前置 | **8 主结局枢纽** |

---

## 5. 道具注册表(30 件)

### 5.1 真有用(15 件)— 被 `inv_has` require 引用

| 道具 | 用法 |
|---|---|
| 林副科长账本残页 | 档案室对照 26 笔真凶 / 风衣面对面 |
| 1986 林字硬币 | S6 井底扔下还林某债 |
| 铜锈片 | 烫腕认领或拒绝 H 编号 |
| 铜锈护符 | 随身让 NPC 反应不同 |
| ⺶ 符文 | E_TRUE 必要前置 |
| 27 楼通道钥匙 | 开 B3 走廊 27 楼通道 |
| 27F 铜钥匙 | 开 S7 终局区钢门 |
| G-272 工牌 | 挂回 27F 替前任下班(E_TRUTH) |
| 米色风衣 | 穿进 27F 黑门代林某『回家』(E_TRUTH) |
| 1991 请假条 | 直接交给叶某改命 |
| 1991 班级合照 | 揭你与叶某的同班同学之谜 |
| 1991 钢丝绳 | 带走触发班级合照剧情 |
| 1959-043 磁带 | 档案室旧录音机播放 |
| 1987 告示残页 | S5 琴房放报纸 |
| 7 工人速写 | 贴在 1986 沉船档案旁 |
| 前任电话号码 | 红色电话亭可拨 |

### 5.2 展示 / 档案物件

部分物件不是 `require.inv_has` 消耗品,而是 NPC 档案 `key_items` 或剧情展示物。
`audit_tree` 会把 `npcs[*].key_items` 纳入使用口径,避免把档案物件误报为孤儿道具。

```text
14 寸黑白电视 / 1959-043 粮票 / 7 顶柳条安全帽 /
十三号湿巾 / 商场总控钥匙 / 工牌 G-273 /
红衣女孩铜锈 / 血毛笔 / 铜锈片
```

### 5.3 inv_descriptions

`tree.json` 顶层 `inv_descriptions` 字典,玩家获得时显示用途说明。
当前为 27 条正式说明 + 1 条 `未注明物品` fallback。详见 `tools/merge_fragments.py STORY_META`。

---

## 6. 结局矩阵(17 个)

### 6.1 8 主结局(在 `n_scene_morning_lakeside` 根据 require 触发)

| ID | 名 | 触发 | narrative_variants 数 |
|---|---|---|---|
| `n_end_true` | E_TRUE 关闭杭州常数 | ⺶ 符文 + 7 归航 + 5 班 | 4 |
| `n_end_truth` | E_TRUTH 揭穿真相 | 拼图 ≥5 | 4 |
| `n_end_data` | E_DATA 数据化 | 工牌献祭 / 27F 挂工牌 | 5 |
| `n_end_broadcast` | E_BROADCAST 永生论坛 | posted_photo + PR ≥50 | 3 |
| `n_end_bad_1987` | E_BAD_1987 无尽 1987 | 漏卡 ≥3 / S2 死循环 / S4 多画一笔 | 4 |
| `n_end_bad_drown` | E_BAD_DROWN 沉船替死 | 7 帽 / S4 跪 3 / S5 自缢 | 5 |
| `n_end_neutral` | E_NEUTRAL 平安下班 | 默认 fallback | 4 |
| `n_end_hidden` | E_HIDDEN 重投胎 | 候补判官章 + 拼图 ≥3 | 3 |

### 6.2 9 mini-ending(地标内不可逆死亡)

| ID | 触发 | 类型 |
|---|---|---|
| `n_s2_endless_loop` | S2 数到 1987 阶 | E_BAD_1987 |
| `n_s3_temple_descend_h` | S3 接受 H=1987 | E_BAD_DROWN |
| `n_s3_eighth_strike` | S3 撞第 8 下钟 | E_BAD_1987 |
| `n_s4_kneel_three` | S4 跪三个 | E_BAD_DROWN |
| `n_s4_extra_stroke` | S4 多画一笔 | E_BAD_1987 |
| `n_s5_self_hang` | S5 自缢 | E_BAD_DROWN |
| `n_s5_wear_shoes` | S5 穿女孩鞋 | E_DATA |
| `n_s6_grab_seven` | S6 抢 7 帽 | E_BAD_DROWN |
| `n_s6_wear_seventh` | S6 戴第 7 帽 | E_DATA |

---

## 7. 8 棺角色解锁矩阵(v8 待实施)

`n_npc_eight_self` 节点列出 8 + 主角 = 9 个不同年份的『另一个你』:

| 棺# | 年份 | 角色 ID | 解锁条件(通关哪个 ending) | 状态 |
|---|---|---|---|---|
| 主 | 2024 | `G-273` | (起手默认) | ✅ 已实现 |
| 1 | 1980 | `worker_1980` | E_HIDDEN 通关 | ⏳ v8 待写 |
| 2 | 1985 | `linmou_1985` | E_TRUTH 通关 | ⏳ v8 待写,角色卡见 v8-character-roster-spec |
| 3 | 1986 | `worker_1986` | E_BAD_DROWN 通关(获 helmet_stuck) | ⏳ v8 待写 |
| 4 | 1987 | `red_victim_13` | E_BAD_1987 通关 | ⏳ v8 待写 |
| 5 | 1991 | `yeh_1991` | E_TRUE 通关(s5_freed_yeh)| ⏳ v8 待写 |
| 6 | 1996 | `red_girl_1996` | E_TRUTH 通关(s2/s5 with red girl flags)| ⏳ v8 待写 |
| 7 | 1998 | `predecessor_1998` | E_DATA 通关 | ⏳ v8 待写 |
| 8 | 2009 | `predecessor_2009` | E_BROADCAST 通关 | ⏳ v8 待写 |

---

## 8. 已实现的伏笔点(v7 中埋的"角色 A 不懂")

每条都有"v7 主角 G-273 玩时不解释,等未来角色玩时揭晓"的设计:

| 槽 ID | 谁不懂 | 谁能解释 | 在哪几个节点出现 |
|---|---|---|---|
| `1985_linmou_other26` | G-273 | linmou_1985 | n_npc_drowned_official, n_s1_pocket_book |
| `1986_lin_coin` | G-273 | linmou_1985 OR worker_1986 | n_s1_shoe_sole, n_s6_drop_coin, n_npc_helmet_workers |
| `1986_no_eighth` | G-273 | worker_1986 | n_s6_listen_engine, n_s6_operator_room |
| `1987_red_dress_truth` | G-273 | red_victim_13 OR red_girl_1996 | n_npc_red_dress_girl, n_s2_step_308 |
| `1991_yeh_classmate` | G-273(11 岁的我?) | yeh_1991 | n_s5_take_rope, n_s5_chalk_name |
| `1991_grandma_link` | G-273 | yeh_1991 | n_npc_piano_ghost(磁带 1959-043) |
| `1996_red_girl_truth` | G-273 | red_girl_1996 | n_npc_red_dress_girl, n_s2_inspect_shoes |
| `G272_predecessor_identity` | G-273 | predecessor_2009 | n_npc_ghost_guard |
| `8_self_roster` | G-273 | 任何角色通关 | n_npc_eight_self |

---

## 9. 主菜单流程(本次实施)

```
启动 play_tui.py
  ↓
[屏幕 1] 选城市
  ┌─────────────────────────────────────┐
  │ 杭州·断桥残雪·夜班外卖  [可玩]      │
  │ 上海·外滩夜班(待开发) [🔒]         │
  │ 北京·胡同夜班(待开发) [🔒]         │
  └─────────────────────────────────────┘
  ↓
[屏幕 2] 选剧情(本城市内)
  ┌─────────────────────────────────────┐
  │ 断桥残雪 · 夜班外卖 [可玩 · 8 结局] │
  │ (未来:晨断桥 / 灵隐午斋 ...)       │
  └─────────────────────────────────────┘
  ↓
[屏幕 3] 选角色
  ┌────────────────────────────────────────┐
  │ ▶ 赵某 G-273 · 现役夜班保安           │
  │ 🔒 林副科长 · 1985 投湖前夜            │
  │    解锁条件:E_TRUTH 通关 G-273 线     │
  │ 🔒 叶某 · 1991 自缢 11 岁              │
  │    解锁条件:E_TRUE 通关 + s5_freed_yeh│
  │ 🔒 ...                                 │
  └────────────────────────────────────────┘
  ↓
开始游戏
```

CLI 简化版:文本菜单,数字选择。

---

## 10. 存档系统(`~/.ghost_save.json`)

```json
{
  "version": 1,
  "meta_flags": {
    "cleared_g273_truth": true,
    "cleared_g273_true": false,
    "cleared_g273_data": false,
    "...": "..."
  },
  "unlocked_characters": ["G-273", "linmou_1985"],
  "endings_seen": ["E_TRUTH", "E_NEUTRAL"],
  "last_played": "2026-05-07T03:00:00",
  "playthroughs": 2
}
```

通关时(玩家到达 `is_ending: true` 节点),写入:
- `endings_seen.append(ending_type)`
- 根据 ending → 更新 `unlocked_characters`
- 更新 `meta_flags`

---

## 11. v8 升级路线(给将来 session 用)

按这个顺序做:

1. **完成本次主菜单 + 解锁基础设施**(本 session)
2. **挑 1 个角色先写**(推荐 `linmou_1985`,叙事重量最大)
3. 写 10 节点起点 + 给现有 13 NPC / 7 场景加 `if: {character: "linmou_1985"}` 的 narrative_variants(~30 处)
4. 跑 path_explorer 验证林某线 ≥3 ending 可达
5. 实跑测试:玩 G-273 通 E_TRUTH → 解锁林某 → 玩林某线 → meta_flags 反向影响 G-273 二周目
6. 重复:每完成 1 个角色 → 更新本文档

---

## 12. 已实现(2026-05-07 完成)

- [x] 主菜单 TUI(`v7/menu_tui.py`,Screen 栈三屏)
- [x] 主菜单 CLI(`v7/menu_cli.py`,文本三屏 + b 返回)
- [x] 存档加载/写入(`v7/save_manager.py`,SaveManager + ENDING_UNLOCKS + CHARACTER_ROSTER)
- [x] 通关时写 `endings_seen` + `unlocked_characters` + `meta_flags`(`cleared_g273_<ending>`)
- [x] 锁住角色显示解锁条件(分两种:未解锁→"解锁条件:..."  / 解锁但未实现→"状态:已解锁,但本剧本暂无该角色线")
- [x] E2E 测试:mock tree → 通关 E_TRUTH → 验证存档写入 + 显示新解锁

### 12.1 入口
- `python play.py` → CLI 主菜单(传 path 仍能跳过)
- `python play_tui.py` → TUI 主菜单(传 path 仍能跳过)
- `~/.ghost_save.json` → 存档文件(原子写入,容错降级)

### 12.2 待 v8 实施
- [ ] 实际写一个 v8 角色线(推荐 `linmou_1985`,叙事重量最大)
- [ ] 给现有 13 NPC / 7 场景加 `if: {character: "linmou_1985"}` 的 narrative_variants(~30 处)
- [ ] 跑 path_explorer 验证林某线 ≥3 ending 可达
- [ ] 反向影响 G-273 二周目(meta_flags 在 require 中起作用)

---

## 13. 风险 / 已知坑

- **textual `App` 内置 `tree` 属性** — 不要用 `self.tree`,用 `self._tree`
- **f-string JSON 模板** — 不要在 f-string 里写 `{"flag": true}` 字面量,Python 会把 `true` 当格式说明符
- **dispatch 的 in-process agent 不跨 session** — 长任务 lead 自己干,别 dispatch
- **`meets()` 嵌套 require** — `not / any_of / all_of` 已支持
- **`character` 字段缺省值** — 默认 `"G-273"`,不破坏 v7
- **State.inv_descriptions 是类级别属性** — `play()` 加载时 `State.inv_descriptions = ...` 注入,所有 instance 共享(OK,只读数据)

---

## 14. 风格指南(写新内容时遵守)

- 第二人称
- 时间戳开头(20:27 / 22:48 / etc)
- 感官细节:温度 / 湿气 / 味道 / 声源位置 / 视觉错位
- 留悬念,不直说
- 单节点 narrative 200-350 字
- 共享 NPC 至少 4 个 narrative_variants
- 关键剧情后必有 payoff 节点(不立刻汇合到 picker)
- 不写 spoiler hint 在选项里(让玩家选完才知道)

---

**END**

读完这份文档,你应该:
1. 知道现在有什么(145 节点 / 13 NPC / 7 场景 / 30 道具 / 21 ending)
2. 知道哪些已经埋了什么伏笔(角色 A 不懂的事,角色 B/C/D 玩时能解释)
3. 知道下一步要做什么(主菜单 → 1 个 v8 角色 → 反向影响 G-273 二周目)
4. 知道怎么不踩坑(textual / f-string / dispatch / character 缺省)
