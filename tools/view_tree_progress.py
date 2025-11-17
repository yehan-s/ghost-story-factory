#!/usr/bin/env python3
"""
对话树生成进度可视化工具

用途：
- 基于 TreeBuilder 的检查点或增量 JSONL 日志，生成一份结构快照；
- 支持：
  - 终端模式：Rich 表格展示；
  - HTML 模式：生成静态报告页面，方便在浏览器中查看。

典型用法：
    venv/bin/python tools/view_tree_progress.py \\
        --checkpoint checkpoints/上海_深夜电台主播_tree.json

    venv/bin/python tools/view_tree_progress.py \\
        --checkpoint checkpoints/上海_深夜电台主播_tree.json \\
        --log-jsonl checkpoints/tree_incremental.jsonl \\
        --output-html checkpoints/tree_progress.html
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table


@dataclass
class NodeInfo:
    """内部使用的节点信息结构"""

    node_id: str
    depth: int
    scene: str
    is_ending: bool
    narrative: str
    parent_id: Optional[str]
    # 当前节点中“在全局出现次数 >1 的选项文本”数量，用于标记重复度高的节点
    repeated_choice_count: int = 0
    ts: Optional[datetime] = None


def _load_tree_from_checkpoint(path: Path) -> Dict[str, Any]:
    """从 checkpoint 或纯树 JSON 中加载对话树结构"""
    if not path.exists():
        raise FileNotFoundError(f"未找到 checkpoint/tree 文件: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    # 如果是 full checkpoint，则包含 tree 字段；否则直接视为树
    if isinstance(data, dict) and "tree" in data and isinstance(data["tree"], dict):
        return data["tree"]
    if isinstance(data, dict):
        return data
    raise ValueError(f"不支持的 checkpoint 格式: {type(data)}")


def _load_incremental_events(path: Path) -> List[Dict[str, Any]]:
    """加载增量 JSONL 日志（每行一个 JSON 事件）"""
    events: List[Dict[str, Any]] = []
    if not path.exists():
        return events
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
                if isinstance(evt, dict):
                    events.append(evt)
            except Exception:
                continue
    return events


def _build_node_index(tree: Dict[str, Any]) -> Dict[str, NodeInfo]:
    """从对话树构建节点索引"""
    index: Dict[str, NodeInfo] = {}
    for nid, node in tree.items():
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("node_id", nid))
        depth = int(node.get("depth", 0) or 0)
        scene = str(node.get("scene", "") or "")
        is_ending = bool(node.get("is_ending", False))
        narrative = str(node.get("narrative", "") or "")
        parent_id = node.get("parent_id")
        if parent_id is not None:
            parent_id = str(parent_id)
        index[node_id] = NodeInfo(
            node_id=node_id,
            depth=depth,
            scene=scene,
            is_ending=is_ending,
            narrative=narrative,
            parent_id=parent_id,
        )
    return index


def _attach_timestamps_from_events(
    index: Dict[str, NodeInfo], events: List[Dict[str, Any]]
) -> None:
    """根据 JSONL 事件为节点附加 ts 字段（若存在）"""
    for evt in events:
        if evt.get("event") != "add_node":
            continue
        node = evt.get("node") or {}
        nid = str(node.get("node_id") or node.get("id") or "")
        if not nid:
            continue
        ts_raw = evt.get("ts")
        if not ts_raw:
            continue
        try:
            ts = datetime.fromisoformat(ts_raw)
        except Exception:
            continue
        info = index.get(nid)
        if info:
            info.ts = ts


def summarize_tree(
    tree: Dict[str, Any], events: Optional[List[Dict[str, Any]]] = None, recent_limit: int = 15
) -> Dict[str, Any]:
    """从对话树与可选事件中生成结构摘要"""
    index = _build_node_index(tree)
    if events:
        _attach_timestamps_from_events(index, events)

    if not index:
        return {
            "summary": {
                "total_nodes": 0,
                "max_depth": 0,
                "ending_count": 0,
            },
            "depth_stats": {},
            "main_path": [],
            "recent_nodes": [],
        }

    # 选择点重复度统计：按全局出现次数标记“高重复”选项
    # 统计每个节点的选项文本，以及全局每个文本出现的次数
    choice_texts_per_node: Dict[str, List[str]] = {}
    global_choice_counts: Dict[str, int] = {}
    try:
        for nid, node in tree.items():
            if not isinstance(node, dict):
                continue
            choices = node.get("choices") or []
            if not isinstance(choices, list):
                continue
            texts_for_node: List[str] = []
            for ch in choices:
                if not isinstance(ch, dict):
                    continue
                text = str(ch.get("choice_text", "")).strip()
                if not text:
                    continue
                texts_for_node.append(text)
                global_choice_counts[text] = global_choice_counts.get(text, 0) + 1
            if texts_for_node:
                choice_texts_per_node[str(node.get("node_id", nid))] = texts_for_node
    except Exception:
        choice_texts_per_node = {}
        global_choice_counts = {}

    # 为每个节点打上 repeated_choice_count 标记
    if global_choice_counts:
        for nid, info in index.items():
            texts = choice_texts_per_node.get(nid) or []
            repeated = sum(1 for t in texts if global_choice_counts.get(t, 0) > 1)
            info.repeated_choice_count = repeated

    # 总体统计
    depths: Dict[int, List[NodeInfo]] = {}
    endings: List[NodeInfo] = []
    for info in index.values():
        depths.setdefault(info.depth, []).append(info)
        if info.is_ending:
            endings.append(info)

    max_depth = max(depths.keys()) if depths else 0

    # 选取一条“主线路径”：沿 children 自 root 出发找到最长路径
    def _find_longest_path_ids(tree_dict: Dict[str, Any]) -> List[str]:
        if not tree_dict or "root" not in tree_dict:
            return []
        longest: List[str] = []

        def dfs(nid: str, cur: List[str]) -> None:
            nonlocal longest
            cur = cur + [nid]
            if len(cur) > len(longest):
                longest = cur.copy()
            node = tree_dict.get(nid) or {}
            for child_id in (node.get("children") or []):
                if child_id in tree_dict:
                    dfs(child_id, cur)

        dfs("root", [])
        return longest

    main_ids = _find_longest_path_ids(tree)
    main_path: List[NodeInfo] = [index[nid] for nid in main_ids if nid in index]

    # recent nodes：按 ts 降序（若无 ts，则按 depth 降序）
    nodes_with_ts: List[NodeInfo] = list(index.values())
    nodes_with_ts.sort(
        key=lambda n: (
            n.ts if n.ts is not None else datetime.min,
            n.depth,
        ),
        reverse=True,
    )
    recent_nodes = nodes_with_ts[:recent_limit]

    # depth-level stats
    depth_stats: Dict[int, Dict[str, Any]] = {}
    for depth, nodes in depths.items():
        depth_stats[depth] = {
            "nodes": len(nodes),
            "endings": sum(1 for n in nodes if n.is_ending),
        }

    summary = {
        "total_nodes": len(index),
        "max_depth": max_depth,
        "ending_count": len(endings),
    }

    return {
        "summary": summary,
        "depth_stats": depth_stats,
        "main_path": [n.__dict__ for n in main_path],
        "recent_nodes": [n.__dict__ for n in recent_nodes],
    }


def render_terminal(report: Dict[str, Any]) -> None:
    """终端模式输出"""
    console = Console()
    summary = report["summary"]
    depth_stats = report["depth_stats"]
    main_path = report["main_path"]
    recent_nodes = report["recent_nodes"]

    console.print("\n[bold cyan]对话树生成进度快照[/bold cyan]\n")

    # 总体统计
    table_sum = Table(show_header=True, header_style="bold magenta")
    table_sum.add_column("指标")
    table_sum.add_column("值")
    table_sum.add_row("总节点数", str(summary.get("total_nodes", 0)))
    table_sum.add_row("最大深度", str(summary.get("max_depth", 0)))
    table_sum.add_row("结局数量", str(summary.get("ending_count", 0)))
    console.print(table_sum)
    console.print()

    # depth 分布
    table_depth = Table(show_header=True, header_style="bold magenta")
    table_depth.add_column("深度")
    table_depth.add_column("节点数")
    table_depth.add_column("结局数")
    for depth in sorted(depth_stats.keys()):
        ds = depth_stats[depth]
        table_depth.add_row(
            str(depth),
            str(ds.get("nodes", 0)),
            str(ds.get("endings", 0)),
        )
    console.print("[bold]各层分布：[/bold]")
    console.print(table_depth)
    console.print()

    # 主线路径
    table_main = Table(show_header=True, header_style="bold magenta")
    table_main.add_column("深度")
    table_main.add_column("节点 ID")
    table_main.add_column("场景")
    table_main.add_column("是否结局")
    table_main.add_column("重复选项数")
    table_main.add_column("叙事摘要", overflow="fold", max_width=60)
    for n in main_path:
        nar = (n.get("narrative") or "").strip()
        if len(nar) > 80:
            nar = nar[:77] + "..."
        table_main.add_row(
            str(n.get("depth", 0)),
            n.get("node_id", ""),
            n.get("scene", ""),
            "是" if n.get("is_ending") else "",
            str(n.get("repeated_choice_count", 0)),
            nar,
        )
    console.print("[bold]一条主线路径（基于最长 parent 链）：[/bold]")
    console.print(table_main)
    console.print()

    # 最近节点
    table_recent = Table(show_header=True, header_style="bold magenta")
    table_recent.add_column("时间")
    table_recent.add_column("深度")
    table_recent.add_column("节点 ID")
    table_recent.add_column("场景")
    table_recent.add_column("是否结局")
    table_recent.add_column("重复选项数")
    table_recent.add_column("叙事摘要", overflow="fold", max_width=60)
    for n in recent_nodes:
        ts = n.get("ts")
        if isinstance(ts, str):
            ts_str = ts
        elif isinstance(ts, datetime):
            ts_str = ts.isoformat(timespec="seconds")
        else:
            ts_str = ""
        nar = (n.get("narrative") or "").strip()
        if len(nar) > 80:
            nar = nar[:77] + "..."
        table_recent.add_row(
            ts_str,
            str(n.get("depth", 0)),
            n.get("node_id", ""),
            n.get("scene", ""),
            "是" if n.get("is_ending") else "",
            str(n.get("repeated_choice_count", 0)),
            nar,
        )
    console.print("[bold]最近生成的节点（按时间/深度）：[/bold]")
    console.print(table_recent)
    console.print()


def render_html(report: Dict[str, Any], output_path: Path) -> None:
    """生成静态 HTML 报告"""
    summary = report["summary"]
    depth_stats = report["depth_stats"]
    main_path = report["main_path"]
    recent_nodes = report["recent_nodes"]

    def esc(s: Any) -> str:
        import html

        return html.escape(str(s) if s is not None else "")

    rows_depth = []
    for depth in sorted(depth_stats.keys()):
        ds = depth_stats[depth]
        rows_depth.append(
            f"<tr><td>{depth}</td><td>{ds.get('nodes', 0)}</td><td>{ds.get('endings', 0)}</td></tr>"
        )

    rows_main = []
    for n in main_path:
        nar = (n.get("narrative") or "").strip()
        if len(nar) > 120:
            nar = nar[:117] + "..."
        rows_main.append(
            "<tr>"
            f"<td>{n.get('depth', 0)}</td>"
            f"<td>{esc(n.get('node_id', ''))}</td>"
            f"<td>{esc(n.get('scene', ''))}</td>"
            f"<td>{'是' if n.get('is_ending') else ''}</td>"
            f"<td>{n.get('repeated_choice_count', 0)}</td>"
            f"<td>{esc(nar)}</td>"
            "</tr>"
        )

    rows_recent = []
    for n in recent_nodes:
        ts = n.get("ts")
        if isinstance(ts, datetime):
            ts_str = ts.isoformat(timespec="seconds")
        else:
            ts_str = esc(ts) if ts else ""
        nar = (n.get("narrative") or "").strip()
        if len(nar) > 120:
            nar = nar[:117] + "..."
        rows_recent.append(
            "<tr>"
            f"<td>{ts_str}</td>"
            f"<td>{n.get('depth', 0)}</td>"
            f"<td>{esc(n.get('node_id', ''))}</td>"
            f"<td>{esc(n.get('scene', ''))}</td>"
            f"<td>{'是' if n.get('is_ending') else ''}</td>"
            f"<td>{n.get('repeated_choice_count', 0)}</td>"
            f"<td>{esc(nar)}</td>"
            "</tr>"
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>对话树生成进度快照</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 20px; }}
    h1, h2, h3 {{ color: #333; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 24px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; font-size: 13px; vertical-align: top; }}
    th {{ background-color: #f5f5f5; text-align: left; }}
    tr:nth-child(even) {{ background-color: #fafafa; }}
    .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; }}
    .badge-ok {{ background-color: #e0f7e9; color: #1b5e20; }}
    .badge-warn {{ background-color: #fff3e0; color: #e65100; }}
  </style>
</head>
<body>
  <h1>对话树生成进度快照</h1>
  <h2>总体统计</h2>
  <table>
    <tr><th>指标</th><th>值</th></tr>
    <tr><td>总节点数</td><td>{summary.get('total_nodes', 0)}</td></tr>
    <tr><td>最大深度</td><td>{summary.get('max_depth', 0)}</td></tr>
    <tr><td>结局数量</td><td>{summary.get('ending_count', 0)}</td></tr>
  </table>

  <h2>各层分布</h2>
  <table>
    <tr><th>深度</th><th>节点数</th><th>结局数</th></tr>
    {''.join(rows_depth)}
  </table>

  <h2>一条主线路径（基于最长 parent 链）</h2>
  <table>
    <tr><th>深度</th><th>节点 ID</th><th>场景</th><th>是否结局</th><th>重复选项数</th><th>叙事摘要</th></tr>
    {''.join(rows_main)}
  </table>

  <h2>最近生成的节点</h2>
  <table>
    <tr><th>时间</th><th>深度</th><th>节点 ID</th><th>场景</th><th>是否结局</th><th>重复选项数</th><th>叙事摘要</th></tr>
    {''.join(rows_recent)}
  </table>
</body>
</html>
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="对话树生成进度可视化工具")
    parser.add_argument(
        "--checkpoint",
        type=str,
        help="TreeBuilder 检查点或纯对话树 JSON 路径（必选，或与 --log-jsonl 一起使用）",
    )
    parser.add_argument(
        "--log-jsonl",
        type=str,
        help="增量日志 JSONL 路径（可选，用于补充最近节点时间信息）",
    )
    parser.add_argument(
        "--output-html",
        type=str,
        help="输出 HTML 报告路径（可选）",
    )

    args = parser.parse_args(argv)

    if not args.checkpoint:
        parser.error("必须提供 --checkpoint 路径（目前不支持仅基于 JSONL 的视图）")

    checkpoint_path = Path(args.checkpoint)
    tree = _load_tree_from_checkpoint(checkpoint_path)

    events: List[Dict[str, Any]] = []
    if args.log_jsonl:
        events = _load_incremental_events(Path(args.log_jsonl))

    report = summarize_tree(tree, events)

    # 终端输出
    render_terminal(report)

    # 可选 HTML 报告
    if args.output_html:
        output_path = Path(args.output_html)
        render_html(report, output_path)
        Console().print(f"\n[green]✅ HTML 报告已生成：{output_path}[/green]\n")


if __name__ == "__main__":
    main()
