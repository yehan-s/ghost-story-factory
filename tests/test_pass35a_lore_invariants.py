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
