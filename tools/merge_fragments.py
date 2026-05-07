#!/usr/bin/env python3
"""合并 stories/hangzhou_yebanbaoan/_fragment_*.json 到 tree.json。

用法:
    python tools/merge_fragments.py [--check]
    python tools/merge_fragments.py --output stories/hangzhou_yebanbaoan/tree.json

每个 fragment 必须是 {"nodes": {...}, ...}。本工具只取 nodes 字段合并。
其余 fragment 字段(_comment / fragment_owner / _dispatch_notes)会被忽略。

冲突检测:同一 node ID 出现在多个 fragment → 报错并显示冲突来源。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


STORY_META = {
    "story_id": "hangzhou_yebanbaoan",
    "title": "断桥残雪",
    "display_name": "断桥残雪",
    "display_subtitle": "杭州夜班 · 8 主结局 · 13 NPC · 7 共享场景",
    "protagonist": "赵某 (G-273) · 湖滨国际名品街夜班保安",
    "version": "7.0",
    "author": "Claude Opus 4.7 + team ghost-v7-maze (handcrafted maze)",
    "start_node": "n_intro",
    "initial_state": {
        "PR": 0,
        "GR": 0,
        "shifts_completed": 0,
        "shifts_skipped": 0,
        "inv": [],
        "flags": {},
        "route": None,
        "skipped_landmarks": [],
        "visited_landmarks": [],
        "puzzle_pieces": [],
        "character": "G-273",
        "meta_flags": {},
        # NPC 初始位置 — 由 STORY_META.npcs[i].initial_location 自动注入(merge 时填充)
        "npc_locations": {},
        # 节点访问计数 — 给 NPC 重访对话用
        "visit_counts": {},
        "last_landmark_id": None,
        # 玩家"知道"的地标(地图能看到名字 + 路);开局只知道 S1
        # 踏入新地标 → 自动展开 X.connections 进 known
        # narrative effect.reveal_landmarks 也能显式揭示
        "known_landmarks": ["S1"],
    },
    # v7 多角色伏笔基础设施(schema 接口,等 v8 写入)
    # 当前只有 G-273 主角。将来可扩展 linmou_1985 / yeh_1991 / redgirl_1996 等。
    "characters": {
        "G-273": {
            "label": "赵某 G-273 · 现役夜班保安(主角)",
            "start_node": "n_intro",
            "initial_inv": [],
            "initial_flags": {},
            "_description": "2024 年新入职的夜班保安。本届主角。"
        }
        # 未来可扩展(v8):
        # "linmou_1985": {"label": "林副科长 · 1985-10-18 投湖前夜", ...},
        # "yeh_1991": {"label": "叶某 · 留下小学 1991-04-23", ...},
        # "redgirl_1996": {"label": "何小燕 · 万象城货梯 1996-08-23", ...},
        # "worker_1986": {"label": "钱塘江 7 工人之一 · 1986-08-17", ...},
    },
    # 道具说明 — 玩家拿到时显示"这是什么 / 可能用来做什么"
    # 每条 ≤ 60 字。模糊提示而非确切引导,保留惊喜。
    "inv_descriptions": {
        "商场总控钥匙": "总控柜 / B3 货梯 / 部分巡逻点门锁。你的工作钥匙。",
        "工牌 G-273": "你的身份证明。某些 NPC 会盯着工牌看。失去它,你就『不存在』了。",
        "前任电话号码": "上一任 G-273 的对讲频段 / 红色电话亭可拨。",
        "林副科长账本残页": "1985 年贪污账本。能解锁档案室 / 林某真相对话。",
        "1986 林字硬币": "钱塘江沉船工人借林某的硬币。能影响 S6 井底剧情。",
        "铜锈片": "S3 钟里的铜锈。可烫在手腕铜印上,认领或拒绝 H 编号。",
        "铜锈护符": "S3 钟身碎片。带在身上,某些 NPC 反应不同。",
        "⺶ 符文": "S4 羊血弄归位的符文。E_TRUE 真结局必要前置之一。",
        "羊公会欠条": "你欠羊公会一刀债。会带来夜班评议会注意。",
        "羊公会名册": "你被列入羊公会第 18 任。E_HIDDEN 路径加分。",
        "1991 请假条": "叶某 1991-04-23 没批准的请假条。能交给她改命。",
        "1991 钢丝绳": "203 琴房琴凳里的钢丝绳。带走会触发班级合照剧情。",
        "1991 班级合照": "第三排第二个『11 岁的你』。揭开你与叶某的隐藏关联。",
        "倒带背书声": "为叶某弹过琴的回响。S5 / 共享场景能听到。",
        "1959-043 磁带": "叶某外婆 1959 年的童谣录音。遗失档案室入口之一。",
        "1959-043 粮票": "S4 老婆婆塞给你的纪念品。",
        "1987 告示残页": "S2 红木门上的『请勿打扰 1987』告示。能影响 NPC 反应。",
        "1987 录像带": "1996 红衣女孩抢电视时拿到。",
        "27 楼通道钥匙": "红衣女孩给的。开 B3 走廊的 27 楼通道。",
        "27F 铜钥匙": "上一任 G-273 给的。开 S7 终局区钢门。",
        "G-272 工牌": "上一任 G-273 的工牌。挂回 27F 墙上能影响某些走向。",
        "米色风衣": "你穿上了林某的风衣。NPC 会以为你是他。",
        "14 寸黑白电视": "1996 红衣女孩抱过的玩具电视。屏幕里有她。",
        "7 顶柳条安全帽": "你薅光了归航帽。E_BAD_DROWN 已锁定。",
        "柳条安全帽 (粘住)": "粘在你头上摘不掉。S6 工人认你是第 8 个。",
        "7 工人速写": "你画下的归航工人 7 张脸。可去档案室核对工号册。",
        "十三号湿巾": "S2 擦出血的湿巾。第 13 号 — 前面 12 个 G-273 也擦过。",
        "铁锈湖泥湿巾": "S1 沾血泥的湿巾。能交给档案室。",
        "血毛笔": "S4 弄堂的笔杆是人骨做的。",
        "红衣女孩铜锈": "S3 钟另一面的红衣女孩侧脸铜锈。",
        "三柱香": "孔雀大厦楼下点的香 — 用来祭乌龙王。",
        "武林门 7 人录音": "通道里 7 个冤魂的工号 — S7 终局区可比对。",
        "浙大钟楼跳绳照片": "钟楼跳绳女生照片。带回 S5 琴房可发现关联。",
        "未注明物品": "(待说明)"
    },
    # 夜班路线图 — 7 地标的元数据,player 用来渲染地图屏 + picker 视图
    # short:在拓扑地图里显示的中文短名(2 字,等宽对齐)
    # connections:可直接走到的相邻地标 ID(用于"自由移动"机制)
    # 现实地理参考(西湖周边):
    #   S5(留下) ── S1(湖滨) ── S7(平海·武林门)
    #     │              │
    #   S6(联庄)     S4(羊血弄)
    #                    │
    #                  S2(柳浪) ── S3(九溪)
    "landmark_map": [
        {"id": "S1", "node_id": "n_s1_arrive", "time": "20:27",
         "place": "湖滨第三把绿色长椅", "short": "湖滨", "unlock": None,
         "connections": ["S4", "S5", "S7"]},
        {"id": "S2", "node_id": "n_s2_arrive", "time": "21:47",
         "place": "柳浪闻莺 307 阶", "short": "柳浪", "unlock": None,
         "connections": ["S3", "S4"]},
        {"id": "S3", "node_id": "n_s3_arrive", "time": "22:48",
         "place": "九溪理安寺裂钟", "short": "九溪", "unlock": None,
         "connections": ["S2"]},
        {"id": "S4", "node_id": "n_s4_arrive", "time": "00:11",
         "place": "中山中路羊血弄 2 号", "short": "羊血", "unlock": None,
         "connections": ["S1", "S2"]},
        {"id": "S5", "node_id": "n_s5_arrive", "time": "01:08",
         "place": "留下小学 203 琴房", "short": "留下", "unlock": None,
         "connections": ["S1", "S6"]},
        {"id": "S6", "node_id": "n_s6_arrive", "time": "01:52",
         "place": "联庄站 B4 盾构井", "short": "联庄",
         "unlock": {"shifts_completed_min": 3},
         "unlock_hint": "夜班 ≥3 班",
         "connections": ["S5"]},
        {"id": "S7", "node_id": "n_s7_arrive", "time": "04:17",
         "place": "平海街 1 号 · B3 货梯井", "short": "平海",
         "unlock": {"shifts_completed_min": 5},
         "unlock_hint": "夜班 ≥5 班(终局)",
         "connections": ["S1"]},
    ],
    # NPC 元数据 — 可在地图上"出没"的角色。每个 NPC 有 label/初始位置。
    # state.npc_locations 跟踪当前位置(运行时改变),地图屏会列出"今夜在场"。
    # initial_location 为 None 表示开局不在任何地标(如对讲机的前任只在频段里)。
    "npcs": {
        "linmou_coat": {
            "label": "无头风衣 · 林某",
            "real_name": "林副科长(1985 投湖)",
            "death_year": 1985,
            "initial_location": "S1",
            "related_foreshadows": ["1985_linmou_other26", "1986_lin_coin", "1986_no_eighth"],
            "key_items": ["林副科长账本残页", "1986 林字硬币", "米色风衣"],
            "dialog_topics": ["27 笔账", "另一签字人", "钱塘江第 8 工人"],
            "relations": {
                "seven_workers": "债主(欠 1 顶帽子)",
                "predecessor_g272": "同班(都是 G-273 候补)",
            },
            "_description": "湖滨第三把绿色长椅旁。穿米色风衣,无头。"
        },
        "old_grandma": {
            "label": "老婆婆 · 1959 粮票",
            "real_name": "叶某外婆(1959 自缢)",
            "death_year": 1959,
            "initial_location": "S4",
            "related_foreshadows": ["1991_grandma_link"],
            "key_items": ["1959-043 粮票"],
            "dialog_topics": ["留下小学", "203 琴房", "童谣"],
            "relations": {
                "yeh_1991": "外孙女(三十二年后同琴房自缢)",
            },
            "_description": "羊血弄 2 号门口的吊膀婆婆。"
        },
        "yeh_1991": {
            "label": "叶某 · 1991-04-23",
            "real_name": "叶某(11 岁,1991 琴房自缢)",
            "death_year": 1991,
            "initial_location": "S5",
            "related_foreshadows": ["1991_yeh_classmate", "1991_grandma_link"],
            "key_items": ["1991 请假条", "1991 钢丝绳", "1991 班级合照"],
            "dialog_topics": ["同桌赵某", "外婆", "童谣 1959-043"],
            "relations": {
                "old_grandma": "外婆(1959 同琴房)",
            },
            "_description": "留下小学 203 琴房,坐在最后一排弹童谣。"
        },
        "redgirl_1996": {
            "label": "红衣女孩 · 何小燕",
            "real_name": "何小燕(9 岁,1996-08-23 货梯失踪)",
            "death_year": 1996,
            "initial_location": "S2",
            "related_foreshadows": ["1996_red_girl_truth"],
            "key_items": ["14 寸黑白电视", "27 楼通道钥匙"],
            "dialog_topics": ["万象城货梯", "继父", "1996 录像带"],
            "relations": {
                "lake_red_dress_13": "前任替死鬼(1987 → 1996 编号承袭)",
            },
            "_description": "柳浪闻莺 308 阶,抱 14 寸黑白电视。"
        },
        "predecessor_g272": {
            "label": "前任 G-272(频段)",
            "real_name": "12 任 G-273 最后一任(2013 数据化)",
            "death_year": 2013,
            "initial_location": None,
            "related_foreshadows": ["G272_predecessor_identity"],
            "key_items": ["G-272 工牌", "27F 铜钥匙"],
            "dialog_topics": ["27 楼", "11 年班", "数据化"],
            "relations": {
                "linmou_coat": "前辈(同 G-273 候补线)",
                "broadcast_voice": "数据化以后留在论坛的残响",
            },
            "_description": "只在对讲机里。但你听够 3 次,他可能会出现。"
        },
        "seven_workers": {
            "label": "7 工人(钱塘江)",
            "real_name": "1986-08-17 归航沉船死者",
            "death_year": 1986,
            "initial_location": None,
            "related_foreshadows": ["1986_no_eighth", "1986_lin_coin"],
            "key_items": ["7 顶柳条安全帽", "1986 林字硬币"],
            "dialog_topics": ["第 8 张船票", "归航帽", "林某的债"],
            "relations": {
                "linmou_coat": "债务关系(林某买了第 8 张票没上船)",
            },
            "_description": "1986 年沉船。只有夜班 ≥4 才看得见 S6 井底。"
        },
        "lake_red_dress_13": {
            "label": "13 号红衣替死鬼",
            "real_name": "1987 最后的 13 号替死鬼",
            "death_year": 1987,
            "initial_location": "S2",
            "related_foreshadows": ["1987_red_dress_truth", "1987_songmuchang_inn"],
            "key_items": [],
            "dialog_topics": ["数到 1987", "请勿打扰", "13 的诅咒"],
            "relations": {
                "redgirl_1996": "下一任替死鬼(1987→1996)",
            },
            "_description": "柳浪闻莺 308 阶上,数到 1987 就消失。"
        },
        "stone_grandpa": {
            "label": "九溪石碑老人",
            "real_name": "(待说明 · 1924 雷峰塔倒下时的目击者)",
            "death_year": None,
            "initial_location": "S3",
            "related_foreshadows": ["1924_leifeng_worm"],
            "key_items": ["铜锈片", "铜锈护符"],
            "dialog_topics": ["裂钟", "敲钟 7 下", "1924 塔砖"],
            "relations": {},
            "_description": "理安寺裂钟旁拐杖老人 — 只夜里出现。"
        },
        "broadcast_voice": {
            "label": "夜班论坛 · 匿名楼层",
            "real_name": "(数据化的多任 G-273 残响)",
            "death_year": None,
            "initial_location": None,
            "related_foreshadows": ["G272_predecessor_identity", "2009_zheda_clock_99"],
            "key_items": [],
            "dialog_topics": ["雪花频道", "数据化", "下一任"],
            "relations": {
                "predecessor_g272": "同源(都是数据化残响)",
            },
            "_description": "夜班论坛的水楼,只在你发帖后回应。"
        },
        "archive_keeper": {
            "label": "档案守门人",
            "real_name": "(待说明 · 第 12 任档案管理员)",
            "death_year": None,
            "initial_location": None,
            "related_foreshadows": ["8_self_roster", "1985_linmou_other26",
                                    "1947_wulinmen_seven", "2007_kongque_collapse"],
            "key_items": [],
            "dialog_topics": ["合卷", "G-273 档案", "签字人"],
            "relations": {},
            "_description": "遗失档案室的看守者。访问 ≥2 次才出现。"
        }
    },
    # 工具栏 — 可重访的"开关"节点,在地图屏作为状态 toggle 显示
    # unlock 字段(可选):同 require 语义。tools 在 picker 里默认全显示,
    # 但被 picker_choices 过滤 — 仅 unlock 满足才出现。
    "tools": [
        {"id": "radio", "label": "对讲机", "icon": "📻",
         "node_id": "n_npc_predecessor_voice",
         "state_flag": "radio_listened",
         "on_text": "已开", "off_text": "未开"},
        {"id": "archive", "label": "遗失档案", "icon": "📁",
         "node_id": "n_scene_lost_archive",
         "state_flag": "archive_visited",
         "on_text": "已访问", "off_text": "未访问"},
        {"id": "phone", "label": "红色电话亭", "icon": "☎",
         "node_id": "n_scene_red_telephone",
         "state_flag": "phone_called_1987",
         "on_text": "已拨", "off_text": "未拨"},
        {"id": "forum", "label": "夜班论坛", "icon": "💬",
         "node_id": "n_npc_forum_lurkers",
         "state_flag": "forum_posted",
         "on_text": "已发帖", "off_text": "未发帖"},
        # 民间传闻线索组 — shifts ≥2 后浮现。每个都有 unlock 隐藏,
        # 玩家在地标里碰到对应触发点后才显示。
        {"id": "lore_leifeng", "label": "雷峰塔白虫", "icon": "🐛",
         "node_id": "n_lore_leifeng_worm",
         "state_flag": "recorded_white_worm",
         "on_text": "已记录", "off_text": "未记录",
         "unlock": {"shifts_completed_min": 2}},
        {"id": "lore_songmuchang", "label": "松木场酒店 217", "icon": "🏚",
         "node_id": "n_lore_songmuchang_inn",
         "state_flag": "asked_room_217",
         "on_text": "已问", "off_text": "未问",
         "unlock": {"shifts_completed_min": 2}},
        {"id": "lore_zheda", "label": "浙大钟楼 99", "icon": "🔔",
         "node_id": "n_lore_zheda_clock_girl",
         "state_flag": "counted_99",
         "on_text": "已数", "off_text": "未数",
         "unlock": {"shifts_completed_min": 3}},
        {"id": "lore_wulinmen", "label": "武林门刑场 7", "icon": "⚰",
         "node_id": "n_lore_wulinmen_execution",
         "state_flag": "avoided_wulinmen",
         "on_text": "已避开", "off_text": "未到",
         "unlock": {"shifts_completed_min": 3}},
        {"id": "lore_kongque", "label": "孔雀大厦乌龙王", "icon": "🦚",
         "node_id": "n_lore_kongque_collapse",
         "state_flag": "burned_incense_kongque",
         "on_text": "已祭", "off_text": "未祭",
         "unlock": {"shifts_completed_min": 4}},
    ],
    "endings": {
        "E_TRUE": "关闭杭州常数 (True · 调查派完整)",
        "E_TRUTH": "揭穿真相 (Truth · 调查派 + 拒绝献祭)",
        "E_DATA": "数据化 雪花频道 (任意路线 + 献祭)",
        "E_BROADCAST": "永生于夜班论坛 (围观派 + 论坛点赞 + 掠夺)",
        "E_BAD_1987": "无尽 1987 (漏卡 ≥3)",
        "E_BAD_DROWN": "沉船替死鬼 (拾满 7 帽)",
        "E_NEUTRAL": "平安下班 (但什么都没改变)",
        "E_HIDDEN": "幽灵保安重投胎 (三路并行隐藏)",
    },
    # 伏笔档案 — 玩家在游戏内会遇到的"未解之谜"。
    # 每条伏笔有两种解开方式:某个角色视角通关(explained_by_character)
    # 或某个 ending 通关(explained_by_ending)。两者满足其一即 resolved。
    # SaveManager 跟踪 seen / resolved 状态,主菜单显示进度 X/Y。
    "foreshadows": {
        "1985_linmou_other26": {
            "title": "26 笔贪污的另一签字人",
            "year": 1985,
            "theme": "杭州常数",
            "summary_locked": "档案显示 27 笔贪污,只 13 笔指向林某。剩下 14 笔的另一签字人是谁?为何从未被追责?",
            "summary_resolved": "另一签字人是杭州常数当年的『内部人』。林某是替罪羊。",
            "explained_by_character": "linmou_1985",
            "explained_by_ending": None,
            "shards": [
                {"id": "account_book", "label": "林某账本残页",
                 "text": "残页上写着「**第 13 笔 · 林**」 —— 但 14-27 笔全是另一种笔迹。"},
                {"id": "archive_signature", "label": "档案室签字对比",
                 "text": "档案室藏着 1985 年原始审计单。**第二个签字人**的签名被人涂掉。涂痕**新于** 2024 年。"},
                {"id": "predecessor_hint", "label": "前任的暗示",
                 "text": "对讲机里前任说:「林某只是**第 13 笔**。其余 14 笔的人,**还在编制内**。」"},
            ],
        },
        "1986_lin_coin": {
            "title": "1986 林字硬币的来源",
            "year": 1986,
            "theme": "替死鬼",
            "summary_locked": "钱塘江沉船 7 工人之一手里捏着一枚『林』字硬币 — 林某 1985 年才投湖,这枚硬币怎么会到 1986 年的工人手上?",
            "summary_resolved": "硬币是林某死后『欠下的债』,杭州常数允许他以鬼身归还。",
            "explained_by_character": "linmou_1985",
            "explained_by_ending": None,
            "shards": [
                {"id": "coin_obtained", "label": "工人手里的硬币",
                 "text": "S6 工人之一把硬币塞给你,温度异常 —— 像是**刚从活人手里拿出来**。"},
                {"id": "coin_inscription", "label": "硬币背面",
                 "text": "硬币背面刻着「**1986·林**」—— 但这种『年份+姓』组合,1986 年还没流通。"},
                {"id": "radio_explanation", "label": "对讲机的解释",
                 "text": "前任在对讲机里说:「林某用鬼身**还过债**。1986 年那枚硬币,是他给的『信物』。」"},
            ],
        },
        "1986_no_eighth": {
            "title": "为何只有 7 顶帽子",
            "year": 1986,
            "theme": "替死鬼",
            "summary_locked": "联庄站盾构井明明卖了 8 张归航船票,沉船时只 7 个工人。第 8 个买票没上船的人去哪了?",
            "summary_resolved": "第 8 个是林某的鬼,他在 1986 年用鬼身买了票。",
            "explained_by_character": "worker_1986",
            "explained_by_ending": None,
            "shards": [
                {"id": "ticket_stub", "label": "归航船票票根",
                 "text": "S6 井底有 8 张票根碎片。第 8 张的存根**没有签名**,只有指纹 —— 比对像**死人的**。"},
                {"id": "seven_helmets", "label": "7 顶柳条安全帽",
                 "text": "工人魂魄共 7 顶帽子,**没有第 8 顶**。但 8 张票卖出了。"},
                {"id": "worker_testimony", "label": "工人证词",
                 "text": "工人说:「我们 7 个上船,**第 8 个站岸边**没动。后来听说,他**早就死了**。」"},
            ],
        },
        "1987_red_dress_truth": {
            "title": "308 阶上的红衣是谁",
            "year": 1987,
            "theme": "13 的诅咒",
            "summary_locked": "柳浪闻莺 308 阶台阶上有个数到 1987 就消失的红衣女人。她不是 1996 年的红衣女孩。",
            "summary_resolved": "她是 1987 年最后的『13 号替死鬼』,数到 1987 是她死亡的那一年。",
            "explained_by_character": "red_victim_13",
            "explained_by_ending": "E_BAD_1987",
            "shards": [
                {"id": "stair_count", "label": "台阶尽头",
                 "text": "数到 308,你身后有声音说「**1987**」 —— 不是你的声音。"},
                {"id": "newspaper_1987", "label": "1987 旧报纸",
                 "text": "S1 报亭贴的 1987 年报纸 —— 同一天,有个**红衣 13 号**死于柳浪闻莺。"},
                {"id": "do_not_disturb", "label": "请勿打扰告示",
                 "text": "S2 灯柱旁的「**请勿打扰 · 1987**」告示 —— 是给**她**的,提醒**别再数**了。"},
            ],
        },
        "1991_yeh_classmate": {
            "title": "11 岁的你与叶某",
            "year": 1991,
            "theme": "时间循环",
            "summary_locked": "1991 班级合照第三排第二个孩子和你长得一模一样。你 11 岁那年并没有上过留下小学。",
            "summary_resolved": "11 岁的『你』是叶某的同桌 — 杭州常数让多个时间线的你都在场。",
            "explained_by_character": "yeh_1991",
            "explained_by_ending": "E_TRUE",
            "shards": [
                {"id": "class_photo", "label": "1991 班级合照",
                 "text": "S5 琴凳里的合照。**第三排第二个孩子**,和 11 岁的你**完全一样**。"},
                {"id": "school_record", "label": "学籍记录对比",
                 "text": "档案室翻 1991 年学籍 —— 那个孩子叫『**赵某**』,出生年月**和你完全一致**,但籍贯写的是**杭州**(你籍贯是别处)。"},
                {"id": "yeh_diary", "label": "叶某日记",
                 "text": "「同桌赵某今天没来。听说他**搬走了**。可我看见他**还在**走廊里看我。」"},
            ],
        },
        "1991_grandma_link": {
            "title": "外婆与 1959-043 磁带",
            "year": 1991,
            "theme": "时间循环",
            "summary_locked": "叶某的童谣磁带编号 1959-043 — 1959 年同一间琴房有过一次自缢,编号档案室收着。",
            "summary_resolved": "外婆 1959 年也死在那间琴房,叶某的死是『循环回归』。",
            "explained_by_character": "yeh_1991",
            "explained_by_ending": None,
            "shards": [
                {"id": "tape_label", "label": "磁带编号 1959-043",
                 "text": "磁带上贴着「**1959-043**」编号 —— 1959 年的事,1991 年磁带上为何有?"},
                {"id": "archive_1959", "label": "档案室 1959 卷宗",
                 "text": "档案室 1959 年卷宗:**留下小学 203 琴房自缢一例**,死者是叶某外婆。"},
                {"id": "song_reprise", "label": "童谣回响",
                 "text": "叶某弹的童谣,**和 1959 年磁带录音一字不差** —— 但叶某 1991 年才学会。"},
            ],
        },
        "1996_red_girl_truth": {
            "title": "红衣女孩到底是谁",
            "year": 1996,
            "theme": "数据化",
            "summary_locked": "她抱着 14 寸黑白电视,屏幕里是她自己。1996-08-23,万象城货梯,有个孩子失踪。",
            "summary_resolved": "她叫何小燕。被她的『继父』在货梯里推下,杭州常数把她数据化保留。",
            "explained_by_character": "red_girl_1996",
            "explained_by_ending": "E_TRUTH",
            "shards": [
                {"id": "tv_screen", "label": "14 寸电视屏",
                 "text": "电视屏里**是她自己** —— 在万象城货梯里被一个戴帽子的男人**推下去**。"},
                {"id": "missing_report", "label": "1996-08-23 失踪通报",
                 "text": "档案室 1996 年报案记录:**何小燕**, 9 岁,母再婚,**继父**报警,最终结案『**离家出走**』。"},
                {"id": "freight_lift_key", "label": "27 楼通道钥匙",
                 "text": "她给你的钥匙 —— 钥匙柄上刻着「**B3 · 货梯**」,1996 年款。"},
            ],
        },
        "G272_predecessor_identity": {
            "title": "前任 G-273 的真身",
            "year": 2024,
            "theme": "数据化",
            "summary_locked": "对讲机里那个声音,自称记了 11 年班。但夜班保安岗位每 2 年换一次,11 年应是 5-6 任前。",
            "summary_resolved": "他是 12 任 G-273 的最后一任,数据化以后留在了对讲频段。",
            "explained_by_character": "predecessor_2009",
            "explained_by_ending": "E_DATA",
            "shards": [
                {"id": "first_call", "label": "对讲机第一次接通",
                 "text": "声音说:「这里是 **G-272**。我接班 **11 年**了。」 —— 但岗位 2 年一换。"},
                {"id": "self_voice", "label": "对讲机第 5 次接通",
                 "text": "对讲机里传来**你自己的声音** —— 一字不差,但**没人录过**。"},
                {"id": "g272_badge", "label": "G-272 工牌",
                 "text": "S7 区墙上挂着 **G-272 工牌**。工牌照片**和你长得一模一样**。"},
            ],
        },
        "8_self_roster": {
            "title": "8 棺里的『另一个你』",
            "year": 2024,
            "theme": "杭州常数",
            "summary_locked": "S7 终局区有 8 口棺材,每口里都有一个不同年份的『你』。他们是谁?",
            "summary_resolved": "8 个棺材是 8 个时间线分支的你,每个对应一个能成为夜班保安的『候补』。",
            "explained_by_character": None,
            "explained_by_ending": "E_TRUE",
            "shards": [
                {"id": "coffin_count", "label": "8 口冰棺",
                 "text": "S7 走廊尽头,8 口冰棺并排。每口刻着年份:**1929 / 1959 / 1985 / 1986 / 1987 / 1991 / 1996 / 2024**。"},
                {"id": "coffin_face", "label": "冰棺里的脸",
                 "text": "你揭开 2024 那口的盖 —— **是你自己**。但你**还活着**站在棺前。"},
                {"id": "constant_hum", "label": "常数嗡鸣",
                 "text": "8 口棺同时**轻微震动**,像有 8 个心跳**同步**。这是『杭州常数』的频率。"},
            ],
        },
        # === 民间传闻升格(5 条 · theme="民间传闻") ===
        "1924_leifeng_worm": {
            "title": "雷峰塔下的白虫",
            "year": 1924,
            "theme": "民间传闻",
            "summary_locked": "1924 年雷峰塔倒,塔砖里钻出『没有眼睛』的白虫。捡塔砖的人家,夜夜看见白蛇。",
            "summary_resolved": "白虫是杭州常数最早的『**显形物**』 —— 它选了塔砖作宿主。九溪理安寺的裂钟下面,埋的就是 1924 那批塔砖。",
            "explained_by_character": None,
            "explained_by_ending": "E_TRUE",
            "shards": [
                {"id": "tower_brick", "label": "1924 塔砖",
                 "text": "S3 裂钟底座,有一块**裸露的砖** —— 比其他石材老,边缘啃过的形状像虫嘴。"},
                {"id": "white_worm", "label": "白虫现身",
                 "text": "你蹲下看裂钟铜锈面孔的眼睛位置 —— **两只白虫**正在爬出来。它们没眼睛,但**朝你的方向移动**。"},
                {"id": "scroll_record", "label": "地方志扫描页",
                 "text": "手机翻出 1924-09-25 杭州地方志:塔倒后 27 户人家瓦上『**结白霜**』 —— 当年 9 月还没冷到结霜。"},
            ],
        },
        "1987_songmuchang_inn": {
            "title": "松木场酒店 217 房",
            "year": 1987,
            "theme": "民间传闻",
            "summary_locked": "松木场某老酒店 3 楼 217 房,夜里敲门声不停 —— 1987 年有个温州女人在这间房上吊。",
            "summary_resolved": "她是『**1987 年最后的红衣**』 —— 同一个 13 号替死鬼,在 308 阶之外的另一个化身。217 = 13 × 16 + 9,杭州常数对她的编号是 **13-9**。",
            "explained_by_character": "red_victim_13",
            "explained_by_ending": "E_BAD_1987",
            "shards": [
                {"id": "room_217_key", "label": "217 房钥匙不在了",
                 "text": "门厅服务台钥匙板上,**217 的钩是空的**。前台说『今晚没人住 217』。"},
                {"id": "knock_pattern", "label": "敲门节奏",
                 "text": "你在楼下听见 217 的敲门 —— **3 短 4 长 6 短**。**1+3+4+6 = 14**。但**13 + 1 = 14** —— 第 14 个,就是**听她敲门的人**。"},
                {"id": "newspaper_1987_inn", "label": "1987 年报纸内页",
                 "text": "S1 报亭那张 1987 年报纸,第三版小字:『松木场某酒店 217 房,温州籍女子,**因情自缢**』 —— 但报告里**没有死者姓名**。"},
            ],
        },
        "2009_zheda_clock_99": {
            "title": "浙大钟楼跳绳女生",
            "year": 2009,
            "theme": "民间传闻",
            "summary_locked": "浙大老校区钟楼夜里 11 点一刻,4 楼有女生跳绳。她数到 99 —— 跟着数到 100 你就死,不数她就站到你身后。",
            "summary_resolved": "她是 2009 年浙大学生 **王某** —— SLH 论坛热帖原型。死因是宿舍楼顶跳楼,但**绳子是从钟楼飘到她身上**的。常数的『**13-12**』号。",
            "explained_by_character": None,
            "explained_by_ending": None,
            "shards": [
                {"id": "rope_in_window", "label": "钟楼 4 楼窗内的绳",
                 "text": "你抬头 —— 4 楼窗户**关着**。但**绳子打地的声音**清清楚楚,**和你的脚步同频**。"},
                {"id": "count_99_aborted", "label": "数到 99 中断",
                 "text": "你数到 99 时**强行停下**,**摀住耳朵**。回头她**没在身后** —— 但**钢笔写下**『**100**』在你的《异常事件记录表》上。**笔迹不是你的**。"},
                {"id": "slh_archive", "label": "SLH 论坛 2009 年原帖",
                 "text": "你在夜班论坛搜『**钟楼 99**』 —— 跳出 2009-04-23 原帖。最后一楼回复时间是**今晚**。"},
            ],
        },
        "1947_wulinmen_seven": {
            "title": "武林门 7 个冤魂",
            "year": 1947,
            "theme": "民间传闻",
            "summary_locked": "武林门是清代刑场,民国 36 年最后一次行刑枪决了 7 人。地脉冷气从地下渗上来。",
            "summary_resolved": "民国 36 年的 7 个死刑犯,**全是替罪羊** —— 真凶是当年的杭州市长。常数把这 7 人的『冤气』作为**S7 钢门的封印钥匙**储存。武林门 7 + S6 工人 7 + S7 8 棺,**就是 22 = 13 + 9**。",
            "explained_by_character": None,
            "explained_by_ending": "E_TRUE",
            "shards": [
                {"id": "seven_squat", "label": "通道里蹲着的 7 人",
                 "text": "武林门地下通道,**地面上蹲着 7 个穿不同年代衣服的人**。1947/1958/1965/1970/1979/1983/1995。他们都低头看自己的手 —— **手腕都有铜印**。"},
                {"id": "iron_smell", "label": "1947 铁锈味",
                 "text": "你蹲下 —— 通道里有股**陈年铁锈味**。不是地铁铁皮的,是**1947 年枪管的**。"},
                {"id": "ledger_match", "label": "档案室核对",
                 "text": "档案室翻 1947 年的杭州地方法院记录:**民国 36 年最后批 7 名死刑犯**,案由全部是『**附逆**』 —— 但当年的杭州市长**也姓林**。"},
            ],
        },
        "2007_kongque_collapse": {
            "title": "孔雀大厦塌楼真因",
            "year": 2007,
            "theme": "民间传闻",
            "summary_locked": "2007 年孔雀大厦第 9 层临街塌一段。官方说『施工质量』,坊间说施工队挖出乌龙王石像砸了。",
            "summary_resolved": "塌的不是 2007 年那栋楼 —— 是**1957 年被拆的乌龙庙**的『**回响**』。常数把乌龙庙作为『**反献祭**』装置(对抗常数的唯一民间力量)封存,2007 年挖出来等于**重启它**。所以孔雀大厦塌了。",
            "explained_by_character": None,
            "explained_by_ending": "E_HIDDEN",
            "shards": [
                {"id": "fence_blood", "label": "围栏后的渗血",
                 "text": "你翻过孔雀大厦围栏,**水泥地渗出红水**。**血是从水泥下渗上来的** —— 1957 年的。"},
                {"id": "shrine_stone", "label": "乌龙王石像残片",
                 "text": "水泥地下你挖出**一块碎石** —— 是乌龙王石像的**眼睛部分**。眼睛**还在看你**。"},
                {"id": "1957_demolition", "label": "1957 年拆庙记录",
                 "text": "档案室藏着 1957-07-20 杭州市政厅令:『**乌龙庙拆除**,原址改建办公楼』。批准人**也姓林**。"},
            ],
        },
    },
    # 主题(themes) — 元元数据:把所有 foreshadow / NPC / timeline 按母题聚合
    # 玩家发现一个伏笔 → 主题进度 +1。集齐主题下所有伏笔 → 主题"通透"
    # 用于:archive 视图分组 + 颜色染色 + 主菜单宏观进度
    "themes": {
        "hangzhou_constant": {
            "name": "杭州常数",
            "color": "magenta",
            "icon": "⊕",
            "description": "一个把杭州的『非自然死亡』当成数据存档的存在。它不杀人,只是把死亡『纳入档案』。",
            "manifestations": ["1985_linmou_other26", "8_self_roster",
                               "G272_predecessor_identity"],
        },
        "scapegoat": {
            "name": "替死鬼",
            "color": "red",
            "icon": "✗",
            "description": "杭州常数选定的『替身』 — 林某 1985、1986 工人、1987 红衣女、1996 红衣女孩、12 任 G-273…… 每一代都有人替。",
            "manifestations": ["1986_lin_coin", "1986_no_eighth",
                               "1987_red_dress_truth"],
        },
        "time_loop": {
            "name": "时间循环",
            "color": "cyan",
            "icon": "⟲",
            "description": "1959 → 1991 → 2024,同一间琴房,同一种死法,同一个『你』。",
            "manifestations": ["1991_yeh_classmate", "1991_grandma_link"],
        },
        "datafication": {
            "name": "数据化",
            "color": "blue",
            "icon": "▣",
            "description": "杭州常数不让你死透 —— 它把你『压缩』成对讲频段、电视雪花、夜班论坛水楼。",
            "manifestations": ["G272_predecessor_identity",
                               "1996_red_girl_truth"],
        },
        "thirteen_curse": {
            "name": "13 的诅咒",
            "color": "yellow",
            "icon": "⒔",
            "description": "13 是杭州常数固定使用的『献祭编号』 —— 第 13 笔贪污、第 13 号替死鬼、第 13 任 G-273……",
            "manifestations": ["1985_linmou_other26", "1987_red_dress_truth"],
        },
        "folklore": {
            "name": "民间传闻",
            "color": "green",
            "icon": "⌘",
            "description": "杭州本地的鬼故事 —— 雷峰塔白虫、松木场吊死女、浙大钟楼跳绳女生、武林门刑场冤气、孔雀大厦乌龙王。它们也都是常数的边缘案例。",
            "manifestations": ["1924_leifeng_worm", "1987_songmuchang_inn",
                               "2009_zheda_clock_99",
                               "1947_wulinmen_seven", "2007_kongque_collapse"],
        },
    },
    # 路线评分(routes) — formalize "调查派/围观派/幸存派"
    # 选项可挂 route_score: {investigator: +2, witness: -1, ...}
    # State.route 由累计分数最高的路线决定(回合结束时计算)
    "routes": {
        "investigator": {
            "name": "调查派",
            "icon": "🔍",
            "description": "查档案、追线索、问真相 —— 死了也要把杭州常数挖出来。",
            "color": "cyan",
            "endings": ["E_TRUTH", "E_TRUE"],
        },
        "witness": {
            "name": "围观派",
            "icon": "👁",
            "description": "拍照、发帖、看戏 —— 被网络数据流冲走,变成下一个雪花频道。",
            "color": "magenta",
            "endings": ["E_BROADCAST", "E_DATA"],
        },
        "survivor": {
            "name": "幸存派",
            "icon": "🚪",
            "description": "不问、不看、不还。打卡 → 交班 → 回家。但**什么都没改变**。",
            "color": "green",
            "endings": ["E_NEUTRAL", "E_HIDDEN"],
        },
    },
    # 成就(achievements) — 伏笔向之外的"小目标",跨周目持久化
    # 每条有触发条件(条件式),完成后存到 SaveManager.achievements
    "achievements": {
        "no_card_skipped": {
            "name": "完美打卡",
            "description": "整局通关,shifts_skipped=0",
            "icon": "🏆",
            "trigger": {"on_ending": True, "shifts_skipped_max": 0},
        },
        "all_shards": {
            "name": "档案全卷",
            "description": "收齐 27 块伏笔碎片",
            "icon": "📚",
            "trigger": {"shards_collected_min": 27},
        },
        "all_deductions": {
            "name": "推论合成师",
            "description": "触发全部 4 条推论",
            "icon": "⟁",
            "trigger": {"deductions_resolved_min": 4},
        },
        "radio_5_calls": {
            "name": "对讲第 5 次",
            "description": "听够 5 次前任的对讲机 — 你听到了你自己",
            "icon": "📻",
            "trigger": {"visit_count_min": {"n_npc_predecessor_voice": 5}},
        },
        "all_landmarks": {
            "name": "夜班全勤",
            "description": "踏入全部 7 个地标",
            "icon": "🗺",
            "trigger": {"visited_landmarks_count": 7},
        },
        "no_resonance": {
            "name": "心如止水",
            "description": "通关时 PR ≤ 5",
            "icon": "❄",
            "trigger": {"on_ending": True, "PR_max": 5},
        },
        "max_resonance": {
            "name": "完全共鸣",
            "description": "PR 一度达到 80+",
            "icon": "🔥",
            "trigger": {"PR_peak_min": 80},
        },
        "found_8_self": {
            "name": "8 棺识己",
            "description": "看见 S7 终局区 8 棺",
            "icon": "⚰",
            "trigger": {"foreshadow_seen": "8_self_roster"},
        },
        "all_endings": {
            "name": "结局全鉴",
            "description": "通关全部 8 主结局",
            "icon": "🏁",
            "trigger": {"endings_seen_min": 8},
        },
        "folklore_master": {
            "name": "怪谈通",
            "description": "解开全部 5 个民间传闻",
            "icon": "👻",
            "trigger": {"theme_resolved": "folklore"},
        },
    },
    # 推论(deductions) — 当多条 foreshadow 都 resolved 后,自动触发的『复合伏笔』
    "deductions": {
        "1986_eighth_passenger": {
            "title": "第 8 张归航船票的主人",
            "requires_resolved": ["1986_no_eighth", "1986_lin_coin"],
            "summary": "林某 1985 年投湖,1986 年用鬼身买了第 8 张归航船票 —— 但他**没上船**。所以只有 7 顶帽子。第 8 个『工人』,是站在岸边的他自己。"
        },
        "loop_constant_truth": {
            "title": "杭州常数的真面目",
            "requires_resolved": ["1991_grandma_link", "1996_red_girl_truth", "8_self_roster"],
            "summary": "1959 / 1991 / 1996 三起儿童死亡都被『杭州常数』纳入数据档案。8 棺里的另一个你,是被常数储备的下一任 G-273 —— 你也在循环里。"
        },
        "predecessor_loop": {
            "title": "前任就是你",
            "requires_resolved": ["G272_predecessor_identity", "8_self_roster"],
            "summary": "对讲机里那个声音,是**上一个时间线的你**。你**正在变成**下一个对讲机里的声音。"
        },
        "13_curse_chain": {
            "title": "13 号替死鬼的循环",
            "requires_resolved": ["1985_linmou_other26", "1987_red_dress_truth"],
            "summary": "林某是『**第 13 笔**』替罪羊,1987 红衣女人是『**13 号**』替死鬼。**13** 是杭州常数固定使用的『**献祭编号**』。下一个 13 是谁?"
        },
    },
    # 时间年表(timeline) — 杭州常数的关键事件,按年份索引
    # year: 真实年份;related_foreshadows / related_npcs 用于交叉引用
    "timeline": [
        {"year": 1924, "date": "1924-09-25", "event": "雷峰塔倒。砖中钻出白虫,民间称『白蛇骨』",
         "related_foreshadows": ["1924_leifeng_worm"], "related_npcs": ["stone_grandpa"],
         "tags": ["塔砖辟邪", "民间传闻"]},
        {"year": 1929, "event": "断桥残雪重修。捐资人名单中的『林』被人故意凿掉",
         "related_foreshadows": [], "tags": ["林某"]},
        {"year": 1947, "event": "民国 36 年武林门最后一次行刑,枪决 7 名『附逆』犯。当年杭州市长姓林",
         "related_foreshadows": ["1947_wulinmen_seven"], "tags": ["武林门", "刑场", "7"]},
        {"year": 1957, "date": "1957-07-20", "event": "杭州市政厅令拆乌龙庙,改建办公楼。批准人姓林",
         "related_foreshadows": ["2007_kongque_collapse"], "tags": ["乌龙庙", "拆"]},
        {"year": 1959, "event": "留下小学 203 琴房,叶某外婆自缢。档案 1959-043",
         "related_foreshadows": ["1991_grandma_link"],
         "related_npcs": ["old_grandma"],
         "tags": ["留下小学", "203 琴房"]},
        {"year": 1985, "date": "1985-10-18", "event": "林副科长投湖。账本 27 笔贪污,只 13 笔确认",
         "related_foreshadows": ["1985_linmou_other26"],
         "related_npcs": ["linmou_coat"],
         "tags": ["林某", "13"]},
        {"year": 1986, "date": "1986-08-17", "event": "钱塘江归航沉船。卖出 8 票,死 7 工人。1 顶『林』字硬币",
         "related_foreshadows": ["1986_lin_coin", "1986_no_eighth"],
         "related_npcs": ["seven_workers"],
         "tags": ["7 工人", "替死鬼"]},
        {"year": 1987, "event": "柳浪闻莺 308 阶,红衣 13 号替死鬼最后一次出现。同年松木场酒店 217 房有温州女子上吊",
         "related_foreshadows": ["1987_red_dress_truth", "1987_songmuchang_inn"],
         "related_npcs": ["lake_red_dress_13"],
         "tags": ["13", "替死鬼", "民间传闻"]},
        {"year": 1991, "date": "1991-04-23", "event": "留下小学 203 琴房,叶某自缢。同桌『赵某』缺席",
         "related_foreshadows": ["1991_yeh_classmate", "1991_grandma_link"],
         "related_npcs": ["yeh_1991"],
         "tags": ["叶某", "留下小学", "11 岁的你"]},
        {"year": 1996, "date": "1996-08-23", "event": "万象城 B3 货梯,何小燕(9 岁)失踪。继父报案",
         "related_foreshadows": ["1996_red_girl_truth"],
         "related_npcs": ["redgirl_1996"],
         "tags": ["红衣女孩", "货梯"]},
        {"year": 2007, "event": "孔雀大厦塌一层。地基挖出乌龙王石像,被砸 — 1957 拆庙的回响",
         "related_foreshadows": ["2007_kongque_collapse"],
         "tags": ["孔雀大厦", "乌龙王", "民间传闻"]},
        {"year": 2009, "date": "2009-04-23", "event": "浙大老校区钟楼,王某跳楼。SLH 论坛『钟楼 99 数』热帖原型",
         "related_foreshadows": ["2009_zheda_clock_99"],
         "tags": ["浙大钟楼", "民间传闻"]},
        {"year": 2013, "event": "12 任 G-273 中最后一任『数据化』,留在对讲机频段",
         "related_foreshadows": ["G272_predecessor_identity"],
         "related_npcs": ["predecessor_g272"],
         "tags": ["G-273", "对讲机"]},
        {"year": 2024, "event": "你(赵某)入职。第 13 任 G-273",
         "related_foreshadows": ["8_self_roster"],
         "tags": ["G-273", "13", "主角"]},
    ],
}


def find_fragments(story_dir: Path) -> List[Path]:
    return sorted(story_dir.glob("_fragment_*.json"))


def load_fragment(path: Path) -> Tuple[Dict[str, Any], List[str]]:
    """加载 fragment,返回 (nodes_dict, warnings)。"""
    warnings: List[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return {}, [f"❌ {path.name}: JSON 解析失败 — {e}"]

    nodes = data.get("nodes")
    if not isinstance(nodes, dict):
        return {}, [f"❌ {path.name}: 缺少 'nodes' 字典字段"]

    return nodes, warnings


def merge(story_dir: Path, output_path: Path, check_only: bool = False) -> int:
    fragments = find_fragments(story_dir)
    if not fragments:
        print(f"❌ 在 {story_dir} 找不到任何 _fragment_*.json")
        return 1

    print(f"找到 {len(fragments)} 个 fragment:")
    for f in fragments:
        print(f"  · {f.name}")
    print()

    merged_nodes: Dict[str, Dict[str, Any]] = {}
    node_origin: Dict[str, str] = {}
    all_warnings: List[str] = []
    fatal = False

    for path in fragments:
        nodes, warnings = load_fragment(path)
        all_warnings.extend(warnings)
        if warnings and any(w.startswith("❌") for w in warnings):
            fatal = True
            continue

        for node_id, node_data in nodes.items():
            if node_id in merged_nodes:
                msg = (
                    f"❌ 节点 ID 冲突: '{node_id}' 同时出现在 "
                    f"{node_origin[node_id]} 和 {path.name}"
                )
                all_warnings.append(msg)
                fatal = True
            else:
                merged_nodes[node_id] = node_data
                node_origin[node_id] = path.name

    for w in all_warnings:
        print(w)

    if fatal:
        print("\n❌ 合并失败,请修复冲突后重试。")
        return 1

    # 引用完整性检查
    refs: set = set()
    for node in merged_nodes.values():
        for choice in node.get("choices", []) or []:
            if choice.get("next"):
                refs.add(choice["next"])
            for v in choice.get("next_variants", []) or []:
                if v.get("next"):
                    refs.add(v["next"])

    missing = refs - set(merged_nodes.keys())
    if missing:
        print(f"\n⚠️  引用了未定义的节点(共 {len(missing)} 个):")
        for nid in sorted(missing):
            # 找出谁引用了它
            users = []
            for src_id, node in merged_nodes.items():
                for choice in node.get("choices", []) or []:
                    if choice.get("next") == nid or any(
                        v.get("next") == nid
                        for v in choice.get("next_variants", []) or []
                    ):
                        users.append(src_id)
            print(f"  · {nid}  ← 被 {users} 引用")
        print()

    orphans = set(merged_nodes.keys()) - refs - {STORY_META["start_node"]}
    if orphans:
        print(f"\n⚠️  孤儿节点(未被任何选项指向,共 {len(orphans)} 个):")
        for nid in sorted(orphans):
            print(f"  · {nid}  (来自 {node_origin[nid]})")
        print()

    # 统计
    print(f"\n📊 节点统计:")
    print(f"   总节点数: {len(merged_nodes)}")
    print(f"   结局节点: {sum(1 for n in merged_nodes.values() if n.get('is_ending'))}")
    print(f"   悬空引用: {len(missing)}")
    print(f"   孤儿节点: {len(orphans)}")

    if check_only:
        print("\n[--check 模式] 不写入输出文件。")
        return 0 if not (missing or orphans) else 1

    # 写出 tree.json — 先把 npcs[i].initial_location 注入 initial_state.npc_locations
    npc_meta = STORY_META.get("npcs") or {}
    for npc_id, info in npc_meta.items():
        loc = info.get("initial_location")
        if loc:
            STORY_META["initial_state"]["npc_locations"][npc_id] = loc
    tree = {**STORY_META, "nodes": merged_nodes}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已写入 {output_path}")
    print(f"   大小: {output_path.stat().st_size:,} 字节")
    return 0 if not missing else 1


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="合并 v6 fragment 到 tree.json")
    p.add_argument(
        "--story-dir",
        type=Path,
        default=Path("stories/hangzhou_yebanbaoan"),
        help="story 目录(包含 _fragment_*.json)",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="输出 tree.json 路径(默认:--story-dir/tree.json)",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="只检查,不写文件",
    )
    args = p.parse_args(argv)

    output = args.output or (args.story_dir / "tree.json")
    return merge(args.story_dir, output, check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
