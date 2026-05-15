"""Pass 35-A 沉淀的不变量回归断言。

来源:docs/team-reviews/2026-05-15-pass-35a-lore-fill.md
QA 路径测试官:variants if={} 必须最后一项,否则 default 截胡其他 variant
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest


TREE_PATH = Path("stories/hangzhou_yebanbaoan/tree.json")
LORE_NODE_IDS = (
    "n_lore_index",
    "n_lore_kongque_collapse",
    "n_lore_leifeng_worm",
    "n_lore_songmuchang_inn",
    "n_lore_wulinmen_execution",
    "n_lore_zheda_clock_girl",
)


@pytest.fixture(scope="module")
def tree():
    return json.loads(TREE_PATH.read_text(encoding="utf-8"))


def test_lore_nodes_have_no_placeholder_narrative(tree):
    """Pass 35-A 决议 A:6 个 lore_* 节点 narrative 主文不得含"(占位"。

    主文是引擎 variants 全失配时的兜底文本(player.py:799-806),
    生产路径下永不触发,但需作为引擎裸奔安全网 + 文档清洁性。
    """
    for nid in LORE_NODE_IDS:
        node = tree["nodes"].get(nid)
        assert node is not None, f"{nid} 节点不存在"
        narrative = node.get("narrative", "") or ""
        assert "(占位" not in narrative, (
            f"{nid} 主文仍含'(占位'。Pass 35-A 决议 A 要求消除占位裸奔。"
        )
        assert len(narrative) >= 150, (
            f"{nid} 主文 {len(narrative)} 字 < 150,主文应作为完整兜底文本。"
        )


def test_narrative_variants_default_is_last(tree):
    """QA 沉淀:所有节点的 narrative_variants 中 if={} 必须是最后一项。

    引擎实测(player.py:resolve_narrative):variants 按顺序匹配,
    首个匹配的 variant 立即返回。如果 if={} 不在末位,会截胡后续条件 variant。

    Pass 35-A 修复了 5 个 lore_* 节点的 character 提前问题,
    此断言防止未来回归。
    """
    violations = []
    for nid, node in tree["nodes"].items():
        variants = node.get("narrative_variants") or []
        if not variants:
            continue
        default_indices = [
            i for i, v in enumerate(variants) if v.get("if") == {}
        ]
        if not default_indices:
            # 没有 default variant 不强制要求(可能不需要兜底)
            continue
        # if={} 必须只有一个且在末位
        assert len(default_indices) == 1, (
            f"{nid} 有 {len(default_indices)} 个 if={{}} variant,应只有 1 个"
        )
        if default_indices[0] != len(variants) - 1:
            violations.append(
                f"{nid}: if={{}} 在 [{default_indices[0]}] 但应在 [{len(variants) - 1}](末位)"
            )

    assert not violations, (
        "以下节点违反 'if={} 必须末位' 不变量:\n  " + "\n  ".join(violations)
    )


def test_lore_g273_variants_differ_from_default(tree):
    """Pass 35-A 决议 B P0:G-273 variant 与 default 字符级差异 ≥ 50%。

    songmuchang / wulinmen / zheda 三节点 G-273 与 default 原本一字不差,
    属于死剧本反模式(占了 if 槽却无差异)。
    """
    import difflib

    B_P0_NODES = (
        "n_lore_songmuchang_inn",
        "n_lore_wulinmen_execution",
        "n_lore_zheda_clock_girl",
    )
    for nid in B_P0_NODES:
        node = tree["nodes"][nid]
        variants = node.get("narrative_variants", [])
        g273 = next(
            (v.get("text", "") for v in variants if v.get("if", {}).get("character") == "G-273"),
            "",
        )
        default = next(
            (v.get("text", "") for v in variants if v.get("if") == {}),
            "",
        )
        assert g273 and default, f"{nid} 缺 G-273 或 default variant"
        ratio = difflib.SequenceMatcher(None, g273, default).ratio()
        diff_pct = (1 - ratio) * 100
        assert diff_pct >= 50, (
            f"{nid} G-273 vs default 差异 {diff_pct:.0f}% < 50%,违反 B P0 死剧本反模式修复"
        )


def test_kongque_lore_uses_hangzhou_authentic_naming(tree):
    """Pass 35-A 决议(Lore Keeper 红线):孔雀大厦 / 乌龙王是地名+信仰错配。

    必须换为延安路商住楼 + 钱塘江镇水石犴。
    """
    tree_str = json.dumps(tree, ensure_ascii=False)
    forbidden = ["孔雀大厦", "乌龙王", "乌龙庙"]
    for kw in forbidden:
        assert kw not in tree_str, (
            f"'{kw}' 仍在 tree.json 中,违反 Lore Keeper 红线"
            f"(杭州无孔雀大厦 / 乌龙王是闽粤信仰)"
        )


def test_leifeng_lore_uses_jingci_location(tree):
    """Pass 35-A 决议(Lore Keeper):雷峰塔现场不能是九溪十八涧理安寺。"""
    leifeng = json.dumps(tree["nodes"]["n_lore_leifeng_worm"], ensure_ascii=False)
    assert "九溪十八涧理安寺" not in leifeng, (
        "雷峰塔节点不应再出现九溪十八涧理安寺(地理错位,夜班保安顺路逻辑不通)"
    )
    assert "净慈寺" in leifeng or "夕照山" in leifeng, (
        "雷峰塔节点应包含净慈寺 / 夕照山(就近的真实地点)"
    )


def test_zheda_lore_specifies_yuquan_campus(tree):
    """Pass 35-A 决议(Lore Keeper):浙大钟楼必须明示玉泉老校区。"""
    import re
    zheda_text = json.dumps(tree["nodes"]["n_lore_zheda_clock_girl"], ensure_ascii=False)
    # 凡是出现"老校区钟楼",前缀必须含"玉泉"
    hits = re.findall(r"([一-鿿]{2})老校区钟楼", zheda_text)
    non_yuquan = [h for h in hits if h != "玉泉"]
    assert not non_yuquan, (
        f"浙大老校区钟楼必有'玉泉'前缀,但发现 {non_yuquan}"
    )


# ─── Pass 35-B1 沉淀的不变量 ──────────────────────────────

def test_character_variant_before_visit_count_min(tree):
    """Pass 35-B1 沉淀(QA):character variant 必须在所有 visit_count_min variant 之前。

    引擎按顺序匹配(player.py:799-806),若 visit_count_min 在 character 之前,
    G-273 角色重访(visit≥2)时会被 visit_count_min 截胡,看不到 G-273 专属文本。
    Pass 35-A 修过 5 个 lore_* 节点,Pass 35-B1 修了 lost_archive / predecessor_voice。
    """
    violations = []
    for nid, node in tree["nodes"].items():
        variants = node.get("narrative_variants") or []
        char_idx = next(
            (i for i, v in enumerate(variants) if "character" in (v.get("if") or {})),
            None,
        )
        visit_idxs = [
            i for i, v in enumerate(variants) if "visit_count_min" in (v.get("if") or {})
        ]
        if char_idx is not None and visit_idxs:
            if char_idx >= min(visit_idxs):
                violations.append(
                    f"{nid}: character@[{char_idx}] ≥ visit_count_min 首位@[{min(visit_idxs)}]"
                )
    assert not violations, (
        "character variant 必须在所有 visit_count_min 之前(防 35-A 同型 bug 复发):\n  "
        + "\n  ".join(violations)
    )


def test_no_duplicate_ending_seen_variants(tree):
    """Pass 35-B1 沉淀(QA):同一节点的 narrative_variants 中,
    同一 (story_id, ending_id) 的 ending_seen 不得出现多次。

    QA 实测发现 predecessor_voice 曾有 [0] last:E_DATA + [2] ending_id:E_DATA,
    后者被前者截胡 → 死代码。Pass 35-B1 删除了 [2]。
    """
    violations = []
    for nid, node in tree["nodes"].items():
        seen = set()
        for i, v in enumerate(node.get("narrative_variants") or []):
            cond = v.get("if") or {}
            es = cond.get("ending_seen")
            if es and isinstance(es, dict) and "ending_id" in es and "story_id" in es:
                key = (es["story_id"], es["ending_id"])
                if key in seen:
                    violations.append(f"{nid}.variants[{i}]: 重复 ending_seen {key}")
                seen.add(key)
    assert not violations, (
        "同一 (story_id, ending_id) 的 ending_seen 不得重复(死代码防回归):\n  "
        + "\n  ".join(violations)
    )


def test_heavy_variant_tool_nodes_have_character_branch(tree):
    """Pass 35-B1 沉淀(QA):_is_tool 节点 variants ≥ 8 时必须有 character 分支。

    工具节点是玩家高频重访点,若 variants 丰富但无 character 分支,
    G-273 玩家专属代入感丢失。Pass 35-A 修了 5 个 lore_* tool,
    Pass 35-B1 修了 lost_archive / predecessor_voice。

    KNOWN_DEBT 是 Pass 35-B1 评审时暴露的历史 sandbox debt,
    挂账 Pass 36+ 处理(forum_lurkers 是 NPC 而非真工具,可能调整 _is_tool 标记;
    lake_underwater 是终局场景,character 是否必要待评)。
    """
    KNOWN_DEBT = {
        "n_npc_forum_lurkers",  # 10 variants,Pass 36+ 补 character 或下放 _is_tool
        "n_scene_lake_underwater",  # 8 variants,西湖水下终局场景
    }
    violations = []
    for nid, node in tree["nodes"].items():
        if nid in KNOWN_DEBT:
            continue
        if not node.get("_is_tool"):
            continue
        variants = node.get("narrative_variants") or []
        if len(variants) >= 8:
            has_char = any("character" in (v.get("if") or {}) for v in variants)
            if not has_char:
                violations.append(f"{nid}: {len(variants)} variants 无 character 分支")
    assert not violations, (
        "重 variants 工具节点(≥8)必须有 character 分支(G-273 重访身份代入感):\n  "
        + "\n  ".join(violations)
    )
