# v7 — 立即可玩(真迷宫图,环环相扣)

## 两种界面任选

```bash
# CLI 模式(行式打印,零依赖)
python play.py

# TUI 模式(全屏 textual,带状态栏 / 鼠标 / 方向键)
.venv/bin/python play_tui.py    # 需先 uv pip install textual
```

**TUI 操作**:↑↓ 选项 / Enter 确认 / 1-9 数字键快选 / s 状态 / q 退出 / 鼠标可点。
**CLI 操作**:输入数字 / s 状态 / q 退出。

终端窗口建议至少 100×30。

---

## v7 vs v6 区别(用户痛点修复)

v6 曾被诟病:**"3 条平行路线 95% 不交叉,只在 S6 才汇合,选择只是 PR 数值差。"**

v7 把这个问题彻底重做了:

| | v5(50 节点线性) | v6(94 节点 3 平行路线) | v7(109 节点 真迷宫图) |
|---|---|---|---|
| 拓扑 | 线性 | 3 路线 + S6 汇合 | **7 地标 × 共享 NPC/场景** |
| 路线 | 无 | A/B/C 锁定 | **不锁定,状态自然分化** |
| 选项后续 | 立刻汇合 | 立刻进路线主线 | **每选项后 2-4 层子选项** |
| 多入口 | 少 | s6_hub 等 3 个 | **landmark_picker 37 入边、scene_lake 13 入边** |
| 结局 | 5 | 8 | **8 主结局 + 9 mini = 17 种 narrative** |
| narrative_variants | 无 | s6_hub 等 | **几乎所有关键节点都有** |
| 环结构 | 无 | 少 | **每地标 ≥5 个真环** |
| 节点 | 50 | 94 | **109(每地标迷宫 16 节点)** |
| 字数 | ~1.8 万 | ~3.5 万 | **~5.6 万(173 KB)** |

---

## 关键技术不变量

每个地标都满足:
- 15-25 内部节点(平均 16 节点)
- ≥5 个真环(深处选项 → 回到地标入口节点,但 narrative_variants 反映状态变化)
- ≥3 个多入口汇合点
- ≥3 个跨地标出口(到共享 NPC / 共享场景)
- ≥3 个死胡同 / mini-ending(不可逆死亡分支)
- 至少 1 个 narrative_variants 节点反映"再次到达"

---

## 13 共享 NPC + 7 共享场景

**13 共享 NPC**(任何地标都可能到达):
- `n_npc_faceless_coat`(空风衣)
- `n_npc_predecessor_voice`(对讲机里前任)
- `n_npc_drowned_official`(投湖林副科长)
- `n_npc_red_dress_girl`(红衣电视女孩)
- `n_npc_yang_butcher`(黑山羊)
- `n_npc_helmet_workers`(7 工人)
- `n_npc_piano_ghost`(自缢叶某)
- `n_npc_corrosion_face`(铜锈侧脸)
- `n_npc_forum_lurkers`(夜班论坛观众)
- `n_npc_evaluator_chair`(评议会)
- `n_npc_eight_self`(8 棺另一个你)
- `n_npc_cleaner_null`(不存在的清洁工)
- `n_npc_ghost_guard`(上一任 G-273)

**7 共享场景**:
- `n_scene_lake_underwater`(西湖水下,3 入口)
- `n_scene_27th_floor_corridor`(不存在的 27 楼)
- `n_scene_b3_corridor`(B3 走廊)
- `n_scene_evaluator_room`(评议会档案室)
- `n_scene_lost_archive`(遗失档案室)
- `n_scene_red_telephone`(红色公用电话亭)
- `n_scene_morning_lakeside`(6 点湖滨日出 — 主结局枢纽)

---

## 8 主结局多样性(每个 ending 有 2-4 个 narrative_variants)

| ID | narrative 数 | 关键变体 |
|---|---|---|
| E_TRUE | 4 | 集齐羊符文+7人归航+林某 / 替七人 + 豆腐脑 / 锁死 8 棺 / 通用 |
| E_TRUTH | 4 | 救叶某 / S3 拒绝 H / 全档案公开 / 通用 |
| E_DATA | 5 | 27F 挂工牌 / 替代叶某 / 接 11cm 红印 / 工牌献祭 / 通用 |
| E_BROADCAST | 3 | 全程直播 / 双爆款帖子 / 通用 |
| E_BAD_1987 | 4 | 漏卡 5 个 / S2 数到死循环 / S4 多画一笔 / 通用 |
| E_BAD_DROWN | 5 | S4 跪三个 / S5 自缢 / S6 抢 7 帽 / 戴帽+羊标记双失 / 通用 |
| E_NEUTRAL | 4 | 老婆婆豆腐脑福报 / 漏卡欠下一夜 / S2 跳门后果 / 通用 |
| E_HIDDEN | 3 | 集齐 4 件套审判 11 任 / 撕小票成革命党 / 通用 |

总计:**32 种最终 narrative**(8 ending × 平均 4 种 variant)

加上 **9 个 mini-ending**(每个地标内的不可逆死亡分支),
**总共 41 种结局体验**。

---

## 环结构示例(以 S1 长椅为例)

S1 内部节点的环回:
- `n_s1_close → n_s1_close_touch → n_s1_close`(摸了又摸)
- `n_s1_close → n_s1_pocket_book → n_s1_close`(翻账本又关上)
- `n_s1_eyes_attack → n_s1_arrive`(被脸贴贴后强制回入口,带 marked 标记)
- `n_s1_walk_past → n_s1_arrive`(假装走过又回头)
- `n_s1_lake_chase → n_s1_arrive`(跑了又回)

跨地标出口:
- `n_s1_close_touch → n_scene_lake_underwater`(扔风衣进湖)
- `n_s1_close_flashlight → n_npc_predecessor_voice`(对讲机)
- `n_s1_pocket_book → n_npc_faceless_coat`(账本)
- `n_s1_pocket_book → n_npc_drowned_official`(签林某名)
- `n_s1_photo → n_npc_forum_lurkers`(论坛)

---

## 这次怎么做的(team `ghost-v7-maze`)

5 个 writer 启动并发,但旧 session 死后只有 lead 完成了 S1 + 共享。
新 session 由 team-lead 一人补完 S2-S6,然后整合。

实际产出:
- ✅ 109 节点 100% 可达(path_explorer 静态分析)
- ✅ 8 主结局全部可达
- ✅ 9 mini-ending 全部可达
- ✅ 0 悬空引用,0 孤儿节点
- ✅ PR/GR clamp 正常
- ✅ player.py 启动正常,可玩

---

## 文件清单

新增/修改:
- `play.py` / `play_tui.py` — CLI / TUI 入口(默认进主菜单)
- `src/ghost_story_factory/v5/player.py` — 状态 + 渲染逻辑
- `src/ghost_story_factory/v7/` — TUI player + 主菜单 + 存档系统 + 伏笔
- `stories/hangzhou_yebanbaoan/tree.json` — **112 节点真迷宫图**
- `stories/hangzhou_yebanbaoan/_fragment_v7_*.json` — 7 个写作 fragment(共享 + 6 地标)
- `tools/merge_fragments.py` — fragment 合并工具
- `tools/path_explorer.py` — 全路径分析工具
- `docs/superpowers/specs/2026-05-07-v7-maze-master-spec.md` — 总设计
- `docs/superpowers/specs/2026-05-07-PROJECT-STATE-AND-FORESHADOW-REGISTRY.md` — 项目状态 + 伏笔注册表

---

## 玩法

```bash
python play.py                  # 主菜单(选城市 → 剧本 → 角色)
.venv/bin/python play_tui.py    # TUI 主菜单
GHOST_FAST=1 python play.py     # 关闭逐字打印
```

操作:输入数字选择 / `s` 看状态 / `q` 退出 / `h` 帮助。

---

## 想推第二个故事

把 `stories/hangzhou_yebanbaoan/` 整个复制一份,改名,重写 fragment + 跑 merge。引擎不需要动。

或者用本次的 team workflow:
1. 写一份 master spec(`docs/superpowers/specs/<date>-<topic>-master-spec.md`)
2. lead 写 1 个标杆地标 + 13 共享 NPC + 7 共享场景 + 8 结局
3. dispatch 6 个 content writer 并行写其他地标(注意:in-process agent 不会跨 session 持续,长任务建议 chunk)
4. merge + path_explorer 验证
5. 给 8 ending 加 narrative_variants 用 worker 埋的 flag
6. 实跑测试 + 完工
