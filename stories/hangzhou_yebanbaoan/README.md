# 断桥残雪

> 杭州·湖滨国际名品街·夜班保安 G-273 的一夜七班。
> 112 节点真迷宫,7 个地标 + 13 共享 NPC + 7 共享场景,8 主结局 + 9 mini 结局,共 17 种 ending narrative。

## 玩法

```bash
# CLI 模式(零依赖)
python play.py                  # 主菜单(选城市 → 剧本 → 角色)
GHOST_FAST=1 python play.py     # 关闭逐字打印

# TUI 模式(textual 全屏)
.venv/bin/python play_tui.py    # 主菜单(同上)
```

## 操作

**CLI**:数字选择 / `s` 状态 / `q` 退出 / `h` 帮助

**TUI**:↑↓ 选项 / Enter 确认 / 1-9 数字键快选 / `s` 状态 / `q` 退出 / 鼠标可点

## 7 地标迷宫(每地标 16 节点左右)

| 编号 | 地标 | 时间 | 主 NPC | mini-ending |
|---|---|---|---|---|
| S1 | 湖滨第三把绿色长椅 | 20:27 | 空风衣实体 | (lead 写,进入 morning_lakeside) |
| S2 | 柳浪闻莺 307 阶 | 21:47 | 红衣电视女孩 | n_s2_endless_loop (E_BAD_1987) |
| S3 | 九溪理安寺裂钟 | 22:48 | 铜锈侧脸 | n_s3_temple_descend_h / n_s3_eighth_strike |
| S4 | 中山中路羊血弄 2 号 | 00:11 | 无头黑山羊 | n_s4_kneel_three / n_s4_extra_stroke |
| S5 | 留下小学 203 琴房 | 01:08 | 钢琴幽灵叶某 | n_s5_self_hang / n_s5_wear_shoes |
| S6 | 联庄站 B4 盾构井 | 01:52 | 7 顶柳条安全帽 | n_s6_grab_seven / n_s6_wear_seventh |
| S7 | 平海街 1 号货梯井(B3) | 04:00+ | 8 棺残片 | (主结局区) |

## 13 共享 NPC + 7 共享场景

每个地标都可能从多个方向到达**同一个共享 NPC**。

**13 共享 NPC** (节点 ID `n_npc_*`):
faceless_coat, predecessor_voice, drowned_official, red_dress_girl, yang_butcher, helmet_workers, piano_ghost, corrosion_face, forum_lurkers, evaluator_chair, eight_self, cleaner_null, ghost_guard

**7 共享场景** (节点 ID `n_scene_*`):
lake_underwater, 27th_floor_corridor, b3_corridor, evaluator_room, lost_archive, red_telephone, morning_lakeside

## 状态变量

| 变量 | 含义 |
|---|---|
| **PR** | 个人共鸣度 (0-100) |
| **GR** | 全局共鸣度 (0-100) |
| **夜班** | 完成的地标数 (0-7) |
| **漏卡** | 跳过的地标 |
| **拼图** | 调查派揭真相用 |
| **随身** | 拾取的道具 / 钥匙 / 符文 |
| **flags** | 上百个具体标记(s4_kneeled_three_times、completed_yang、seven_returned 等) |

不再有 `route` 锁定。玩家通过状态组合自然分化。

## 8 主结局 + 9 mini-ending = 17 种 narrative

**8 主结局** (在 n_scene_morning_lakeside 根据状态选择):

| ID | 名 | 触发 |
|---|---|---|
| E_TRUE | 关闭杭州常数 | ⺶ 符文 + 7 人归航 + 5 班完成 |
| E_TRUTH | 揭穿真相 | 拼图碎片 ≥5 |
| E_DATA | 数据化雪花频道 | 任意献祭(工牌 / 自己挂入 27F / 戴 helmet_stuck) |
| E_BROADCAST | 永生于夜班论坛 | 论坛点赞 + PR ≥50 |
| E_BAD_1987 | 无尽 1987 | 漏卡 ≥3 / S2 数到死循环 / S4 多画一笔 |
| E_BAD_DROWN | 沉船替死鬼 | 拾 7 帽 / S4 跪三个 / S5 自缢 / S6 抢帽 |
| E_NEUTRAL | 平安下班(但什么都没改变) | 默认 fallback |
| E_HIDDEN | 幽灵保安重投胎 | 候补判官章 + 拼图 ≥3 |

**9 mini-ending** (地标内直接结束,根据特定不可逆动作):
- S2: 数到死循环 (E_BAD_1987)
- S3: 接受 H=1987 (E_BAD_DROWN) / 撞第 8 下钟 (E_BAD_1987)
- S4: 跪三个 (E_BAD_DROWN) / 多画一笔 (E_BAD_1987)
- S5: 自缢 (E_BAD_DROWN) / 穿女孩鞋 (E_DATA)
- S6: 抢 7 帽 (E_BAD_DROWN) / 戴第七帽 (E_DATA)

每个主结局还有 2-4 个 narrative_variants(根据具体 flag 切换),
**例如 E_BAD_DROWN 有 4 种 narrative**:S4 跪三个版 / S5 自缢版 / S6 抢帽版 / 通用版。

总计 ~30 种不同的最终 narrative。**你选的每一步,真的会影响最后看到什么。**

## 设计与开发说明

- 总设计:`docs/superpowers/specs/2026-05-07-v7-maze-master-spec.md`
- 项目状态 + 伏笔注册表:`docs/superpowers/specs/2026-05-07-PROJECT-STATE-AND-FORESHADOW-REGISTRY.md`

## 内容资产

- `tree.json` (~240 KB) — 112 节点真迷宫图,Claude Opus 4.7 + team `ghost-v7-maze` 协作手写
- `_fragment_v7_*.json` — 7 个写作 fragment(7 地标 + 共享),合并源文件

合并 + 验证工具:
- `tools/merge_fragments.py` — fragment 合并 + 引用完整性检查
- `tools/path_explorer.py` — BFS 全路径分析 + 状态边界验证
