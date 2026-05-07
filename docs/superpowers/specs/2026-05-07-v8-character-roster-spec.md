# v8 多角色 Roster · 8 棺角色规划

**日期**: 2026-05-07
**状态**: Draft(预留接口,内容由 v8 阶段写)
**前置**: `2026-05-07-v7-maze-completion-and-template-spec.md` Phase C
**依赖**: v7 已完成 Phase A/B/C(变体覆盖、payoff 节点、player schema 扩展)

---

## 0. 设计目的

v7 的 `n_npc_eight_self` 节点已经埋下 8 棺架构 — 8 个不同年份的「另一个你」。
v8 的目标:**让玩家可以选择不同棺,从那个年份的视角重玩故事,发现 v7 时无法理解的真相**。

每个角色:
- 起点节点不同(不再统一从 `n_intro`)
- 初始 inv / flags 不同(反映他们已经掌握的信息)
- 在共享 NPC / 场景节点看到不同的 narrative_variants
- **解锁 v7 主角无法看到的伏笔槽** — 这是核心价值

---

## 1. Roster 总表

| 棺# | 年份 | 角色 ID | 真名 | 死法 | 解锁伏笔槽 |
|---|---|---|---|---|---|
| 主 | 2024 | `G-273` | 赵某 | (主角,本夜班) | (主线) |
| 1 | 1980 | `worker_1980` | 待定 | 待定 | (待开放) |
| 2 | 1985 | `linmou_1985` | 林副科长 | 投湖 | `1985_linmou_other26` / `1986_lin_coin` / `1985_account_full` |
| 3 | 1986 | `worker_1986` | 钱塘江 7 工之一 | 沉船 | `1986_lin_coin` / `1986_no_eighth` / `seven_worker_truth` |
| 4 | 1987 | `red_victim_13` | (待定) | 百货大楼踩踏 第 13 名 | `1987_red_dress_truth` / `1987_actual_count` |
| 5 | 1991 | `yeh_1991` | 叶某 | 自缢 | `1991_yeh_classmate` / `1991_grandma_link` |
| 6 | 1996 | `red_girl_1996` | 何小燕 | 货梯门关 | `1996_red_girl_truth` / `red_girl_shoe_origin` |
| 7 | 1998 | `predecessor_1998` | (待定) | 待定 | (待开放) |
| 8 | 2009 | `predecessor_2009` | (待定) | 待定 | (待开放) |

---

## 2. 详细角色卡(高优先级 4 个)

### 2.1 林副科长 1985 (`linmou_1985`)

```json
{
  "label": "林某 · 1985-10-18 投湖前夜",
  "start_node": "n_linmou_office",
  "initial_inv": ["林副科长账本完整版", "钢笔(1985 年款)", "西湖牌 14 寸黑白电视小票"],
  "initial_flags": {
    "is_linmou": true,
    "year": 1985,
    "knows_27_accounts": true,
    "knows_actual_culprit": true
  }
}
```

**起点新增节点**(v8 必写):
- `n_linmou_office` — 1985-10-18 18:00,办公室,审计组将到。林某发现账本上 27 笔贪污只有 13 笔是自己的。
- `n_linmou_decision` — 是否带账本去找『另一个人』对峙 / 投湖前留遗书 / 销毁账本
- `n_linmou_lakeside` — 来到湖滨第三把长椅(就是 v7 主角看到风衣的位置)

**解锁的 v7 节点 narrative_variants**(v7 已埋槽):
- `n_npc_faceless_coat` — 主角 A 玩时风衣是谜;林某 B 玩时风衣**就是自己穿过的**
- `n_npc_drowned_official` — A 玩时是「另一个人」;B 玩时是镜子,B 看见自己 41 年后浮上岸
- `n_npc_eight_self` — A 看 8 棺;B 看的是「我躺进哪一台?」的选择
- `n_scene_lake_underwater` — A 是探索;B 是回忆死亡那刻

**结局映射**:
- E_LINMOU_TRUE:把账本完整版交给『另一个人』面前的法庭(V8 新结局)
- E_LINMOU_TRUTH:写完整遗书,交给湖底的下一任 G-273(穿越 39 年到达 2024 主角手里)
- E_LINMOU_DATA:不投湖,但被 26 笔的真凶发现,被灭口
- E_LINMOU_NEUTRAL:还是投湖。账本随他沉。1985-2024 一切重演

### 2.2 叶某 1991 (`yeh_1991`)

```json
{
  "label": "叶某 · 留下小学 1991-04-23 11:47",
  "start_node": "n_yeh_classroom",
  "initial_inv": ["1991 数学卷子(87 分)", "红头绳", "大白兔糖", "小学毕业班合照"],
  "initial_flags": {
    "is_yeh": true,
    "year": 1991,
    "knows_grandma_1959": true
  }
}
```

**起点新增节点**(v8 必写):
- `n_yeh_classroom` — 11:47 班级解散,叶某拿到 87 分卷子
- `n_yeh_corridor` — 走出教室。203 琴房在哪?
- `n_yeh_grandma_visit` — 在 203 琴房遇到外婆 1959 的钢琴幽灵(grandma_link 槽解锁)

**解锁的 v7 节点**:
- `n_npc_piano_ghost` — A 玩时是叶某幽灵;B 玩时叶某是**自己**,看到的是**外婆 1959 的幽灵**
- `n_s5_chalk_name` — A 看 1988 个「叶某」黑板字;B 看到的是**未来 G-273 来认领自己的过程**
- 3 排 2 个班级合照里那个 11 岁赵某 — A 看是谜;B 看是**真同学**

### 2.3 红衣女孩 1996 (`red_girl_1996`)

```json
{
  "label": "何小燕 · 万象城货梯 1996-08-23",
  "start_node": "n_redgirl_rehearsal",
  "initial_inv": ["1996 六一彩排红色舞台粉", "白布鞋(单只)", "14 寸黑白电视(玩具)"],
  "initial_flags": {
    "is_red_girl": true,
    "year": 1996,
    "knows_1991_yeh_pre_death": true
  }
}
```

**起点新增节点**(v8 必写):
- `n_redgirl_rehearsal` — 1996-08-23 下午,六一彩排,何小燕鞋掉一只
- `n_redgirl_elevator` — 货梯,门关上的瞬间,谁按的关门键
- `n_redgirl_27th` — 何小燕死后,她**自己**就是「27 楼」的来源

**解锁的 v7 节点**:
- `n_npc_red_dress_girl` — A 看是 NPC;B 玩时她是**自己**
- `n_scene_27th_floor_corridor` — A 不知道为什么有 27 楼;B 知道:**因为她死时数 27 个台阶**
- 「叔叔,27 楼怎么走?」原来是 B 在**问主角 A**怎么帮她找回那遗失的鞋

### 2.4 钱塘江 7 工之一 (`worker_1986`)

```json
{
  "label": "钱某 · 1986-08-17 钱塘江轮渡",
  "start_node": "n_worker_morning",
  "initial_inv": ["柳条安全帽 (干净版)", "1986 林字硬币 (新)"],
  "initial_flags": {
    "is_worker": true,
    "year": 1986,
    "borrowed_coin_from_linmou": true
  }
}
```

**起点新增节点**(v8 必写):
- `n_worker_morning` — 1986-08-17 早 6:00,工地集合,7 个工人加他=8 人买票
- `n_worker_ticket` — 第 8 个工人临时不舒服,把票让给『一个穿米色风衣的人』(伏笔解锁:那是 1985 林某的鬼)
- `n_worker_capsize` — 船沉

**解锁的 v7 节点**:
- `n_npc_helmet_workers` — A 看是 NPC;B 玩时他**就是 7 个里的一个**
- `n_s6_operator_room` — A 看 1986 工号牌错位;B 知道为什么(他亲眼看见林某的鬼上船)
- `1986_no_eighth` 槽 — 解释「为什么是 7 个,不是 8 个」

---

## 3. 跨周目记忆(meta_flags)机制

v7 player.py 已经支持 `meta_flags` 字段。设计:

| meta_flag | 触发条件 | 对其他周目的影响 |
|---|---|---|
| `played_linmou` | 通关一次 linmou_1985 | A 周目玩时,`n_npc_faceless_coat` narrative_variants 增加「你 5 分钟前是他」的视角 |
| `played_yeh` | 通关一次 yeh_1991 | A 周目玩 S5 时,叶某不再是单纯 NPC,有"我们认识"的对话 |
| `played_redgirl` | 通关一次 red_girl_1996 | A 周目 27 楼走廊,**只有玩过 redgirl 的人**才能开门 |
| `played_worker` | 通关一次 worker_1986 | A 周目 S6 井底,7 个工人**比 v7 多说一句话**,告诉主角林某也是亲戚 |
| `cleared_all_8` | 全部 8 个角色通关 | A 周目解锁 E_OMEGA 隐藏结局:打开 9 棺,**结束杭州常数轨道** |

**实现**:存档文件 `~/.ghost_save.json`,内容 `{"meta_flags": {...}}`。Player 启动时加载,玩家通关时更新写入。

---

## 4. v7→v8 迁移检查清单

迁移到 v8 时,需要做的事:

- [ ] 写 4 个高优先级角色的起点节点(每个 ~10 节点 = 40 节点)
- [ ] 给现有 v7 共享 NPC / 场景节点添加 `narrative_variants` with `if: {character: "linmou_1985"}` etc.
- [ ] 实现 `~/.ghost_save.json` 持久化(player.py 加 `_save_meta_flags()` 辅助函数)
- [ ] 写 4-8 个新结局节点(每个角色 1-2 个独家结局)
- [ ] 跑 path_explorer 验证每个角色起点都能通到至少 3 个结局
- [ ] 实跑测试:玩 G-273 一遍 → 玩 linmou → 再玩 G-273,验证有新内容浮现

---

## 5. 时间预估

按一个高质量节点 ~300 字算:
- 4 高优先角色 × 10 起点节点 = 40 节点 = 1.2 万字
- 现有 25 个共享 NPC/场景 × 4 角色 variants × 200 字 = 2 万字
- 4-8 新结局 × 500 字 = ~3000 字
- **总写作工作量:~3.5 万字**

加上 player.py 改动 + 测试,大约一个完整 session(同 v7 工作量)。

---

## 6. 不在范围

- 4 低优先级角色(1980 / 1998 / 2009)— 后续阶段
- 实时多人 / 联机 — 永远不在范围
- v8 故事的杭州延伸(比如『下一夜班』『1933 那个开山首刀的人』)— 单独立项

---

## 7. 谁来写?

按 v7 经验,5 个 writer agent 并发可行,但要预先写好每个角色的核心 narrative motif 范例(类似 v7 的 S1 标杆),再 dispatch。
