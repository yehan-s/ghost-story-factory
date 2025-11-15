"""
view_tree_progress 工具测试

目标：
- 验证 summarize_tree 能正确统计：
  - 总节点数 / 最大深度 / 结局数；
  - 各 depth 分布；
  - 主线路径长度；
  - 最近节点列表。
"""

from pathlib import Path
from typing import Dict, Any

from tools.view_tree_progress import summarize_tree


def _build_small_tree() -> Dict[str, Any]:
    """构造一个小型对话树用于测试"""
    return {
        "root": {
            "node_id": "root",
            "scene": "S1",
            "depth": 0,
            "children": ["node_0001"],
            "is_ending": False,
        },
        "node_0001": {
            "node_id": "node_0001",
            "scene": "S1",
            "depth": 1,
            "children": ["node_0002", "node_0003"],
            "is_ending": False,
        },
        "node_0002": {
            "node_id": "node_0002",
            "scene": "S1",
            "depth": 2,
            "children": [],
            "is_ending": True,
            "parent_id": "node_0001",
            "narrative": "结局 A",
        },
        "node_0003": {
            "node_id": "node_0003",
            "scene": "S1",
            "depth": 2,
            "children": [],
            "is_ending": True,
            "parent_id": "node_0001",
            "narrative": "结局 B",
        },
    }


def test_summarize_tree_basic_stats(tmp_path: Path):
    """验证 summarize_tree 统计信息是否正确"""
    tree = _build_small_tree()

    # 构造一个简单的增量 JSONL，附加 ts 信息
    log_path = tmp_path / "tree_incremental.jsonl"
    lines = [
        '{"ts": "2025-11-15T12:00:00", "event": "add_node", "node": {"node_id": "node_0002"}}\n',
        '{"ts": "2025-11-15T12:00:10", "event": "add_node", "node": {"node_id": "node_0003"}}\n',
    ]
    log_path.write_text("".join(lines), encoding="utf-8")

    import json

    events = [json.loads(l) for l in lines]

    report = summarize_tree(tree, events)

    summary = report["summary"]
    depth_stats = report["depth_stats"]
    main_path = report["main_path"]
    recent_nodes = report["recent_nodes"]

    assert summary["total_nodes"] == 4
    assert summary["max_depth"] == 2
    assert summary["ending_count"] == 2

    # depth 分布：0 -> 1 节点，1 -> 1 节点，2 -> 2 节点
    assert depth_stats[0]["nodes"] == 1
    assert depth_stats[1]["nodes"] == 1
    assert depth_stats[2]["nodes"] == 2
    assert depth_stats[2]["endings"] == 2

    # 主线路径应该是 root -> node_0001 -> node_0002 或 node_0003
    assert len(main_path) == 3
    assert main_path[0]["node_id"] == "root"
    assert main_path[1]["node_id"] == "node_0001"
    assert main_path[-1]["depth"] == 2

    # 最近节点列表至少包含两个结局节点
    ids = {n["node_id"] for n in recent_nodes}
    assert "node_0002" in ids and "node_0003" in ids

