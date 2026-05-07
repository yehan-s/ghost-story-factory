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
    "title": "断桥残雪 · 夜班外卖 (v7 真迷宫图)",
    "display_name": "断桥残雪 · 夜班外卖",
    "display_subtitle": "完整版 · 8 主结局 · 13 NPC · 7 共享场景",
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
        "未注明物品": "(待说明)"
    },
    # 夜班路线图 — 7 地标的元数据,player 用来渲染地图屏 + picker 视图
    "landmark_map": [
        {"id": "S1", "node_id": "n_s1_arrive", "time": "20:27",
         "place": "湖滨第三把绿色长椅", "unlock": None},
        {"id": "S2", "node_id": "n_s2_arrive", "time": "21:47",
         "place": "柳浪闻莺 307 阶", "unlock": None},
        {"id": "S3", "node_id": "n_s3_arrive", "time": "22:48",
         "place": "九溪理安寺裂钟", "unlock": None},
        {"id": "S4", "node_id": "n_s4_arrive", "time": "00:11",
         "place": "中山中路羊血弄 2 号", "unlock": None},
        {"id": "S5", "node_id": "n_s5_arrive", "time": "01:08",
         "place": "留下小学 203 琴房", "unlock": None},
        {"id": "S6", "node_id": "n_s6_arrive", "time": "01:52",
         "place": "联庄站 B4 盾构井",
         "unlock": {"shifts_completed_min": 3},
         "unlock_hint": "夜班 ≥3 班"},
        {"id": "S7", "node_id": "n_s7_arrive", "time": "04:17",
         "place": "平海街 1 号 · B3 货梯井",
         "unlock": {"shifts_completed_min": 5},
         "unlock_hint": "夜班 ≥5 班(终局)"},
    ],
    # 工具栏 — 可重访的"开关"节点,在地图屏作为状态 toggle 显示
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
            "summary_locked": "档案显示 27 笔贪污,只 13 笔指向林某。剩下 14 笔的另一签字人是谁?为何从未被追责?",
            "summary_resolved": "另一签字人是杭州常数当年的『内部人』。林某是替罪羊。",
            "explained_by_character": "linmou_1985",
            "explained_by_ending": None,
        },
        "1986_lin_coin": {
            "title": "1986 林字硬币的来源",
            "summary_locked": "钱塘江沉船 7 工人之一手里捏着一枚『林』字硬币 — 林某 1985 年才投湖,这枚硬币怎么会到 1986 年的工人手上?",
            "summary_resolved": "硬币是林某死后『欠下的债』,杭州常数允许他以鬼身归还。",
            "explained_by_character": "linmou_1985",
            "explained_by_ending": None,
        },
        "1986_no_eighth": {
            "title": "为何只有 7 顶帽子",
            "summary_locked": "联庄站盾构井明明卖了 8 张归航船票,沉船时只 7 个工人。第 8 个买票没上船的人去哪了?",
            "summary_resolved": "第 8 个是林某的鬼,他在 1986 年用鬼身买了票。",
            "explained_by_character": "worker_1986",
            "explained_by_ending": None,
        },
        "1987_red_dress_truth": {
            "title": "308 阶上的红衣是谁",
            "summary_locked": "柳浪闻莺 308 阶台阶上有个数到 1987 就消失的红衣女人。她不是 1996 年的红衣女孩。",
            "summary_resolved": "她是 1987 年最后的『13 号替死鬼』,数到 1987 是她死亡的那一年。",
            "explained_by_character": "red_victim_13",
            "explained_by_ending": "E_BAD_1987",
        },
        "1991_yeh_classmate": {
            "title": "11 岁的你与叶某",
            "summary_locked": "1991 班级合照第三排第二个孩子和你长得一模一样。你 11 岁那年并没有上过留下小学。",
            "summary_resolved": "11 岁的『你』是叶某的同桌 — 杭州常数让多个时间线的你都在场。",
            "explained_by_character": "yeh_1991",
            "explained_by_ending": "E_TRUE",
        },
        "1991_grandma_link": {
            "title": "外婆与 1959-043 磁带",
            "summary_locked": "叶某的童谣磁带编号 1959-043 — 1959 年同一间琴房有过一次自缢,编号档案室收着。",
            "summary_resolved": "外婆 1959 年也死在那间琴房,叶某的死是『循环回归』。",
            "explained_by_character": "yeh_1991",
            "explained_by_ending": None,
        },
        "1996_red_girl_truth": {
            "title": "红衣女孩到底是谁",
            "summary_locked": "她抱着 14 寸黑白电视,屏幕里是她自己。1996-08-23,万象城货梯,有个孩子失踪。",
            "summary_resolved": "她叫何小燕。被她的『继父』在货梯里推下,杭州常数把她数据化保留。",
            "explained_by_character": "red_girl_1996",
            "explained_by_ending": "E_TRUTH",
        },
        "G272_predecessor_identity": {
            "title": "前任 G-273 的真身",
            "summary_locked": "对讲机里那个声音,自称记了 11 年班。但夜班保安岗位每 2 年换一次,11 年应是 5-6 任前。",
            "summary_resolved": "他是 12 任 G-273 的最后一任,数据化以后留在了对讲频段。",
            "explained_by_character": "predecessor_2009",
            "explained_by_ending": "E_DATA",
        },
        "8_self_roster": {
            "title": "8 棺里的『另一个你』",
            "summary_locked": "S7 终局区有 8 口棺材,每口里都有一个不同年份的『你』。他们是谁?",
            "summary_resolved": "8 个棺材是 8 个时间线分支的你,每个对应一个能成为夜班保安的『候补』。",
            "explained_by_character": None,
            "explained_by_ending": "E_TRUE",  # 通关 E_TRUE 才知全貌
        },
    },
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

    # 写出 tree.json
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
