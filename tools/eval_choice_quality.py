#!/usr/bin/env python3
"""
选择点 BMAD 评估 CLI 工具

用途：
- 从对话树 JSON / checkpoint 中选取某个节点；
- 调用 ChoiceQualityEvaluator 对该节点的一组选项做多维离线打分；
- 结果仅用于开发者调参与诊断，不影响运行时逻辑。

典型用法：
    venv/bin/python tools/eval_choice_quality.py \\
        --tree-json checkpoints/story_7_夜班外卖骑手_tree_export.json \\
        --node-id node_0001
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.table import Table

from ghost_story_factory.engine.choice_evaluator import ChoiceQualityEvaluator
from ghost_story_factory.engine.state import GameState


console = Console()


def _load_tree(path: Path) -> Dict[str, Any]:
    """从 JSON / checkpoint 中加载对话树结构"""
    if not path.exists():
        raise FileNotFoundError(f"未找到对话树文件: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "tree" in data and isinstance(data["tree"], dict):
        return data["tree"]
    if isinstance(data, dict):
        return data
    raise ValueError(f"不支持的树结构格式: {type(data)}")


def _find_node(tree: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    """在树中查找指定节点（优先按 key，其次按 node_id 字段）"""
    if node_id in tree and isinstance(tree[node_id], dict):
        return tree[node_id]

    for _, node in tree.items():
        if not isinstance(node, dict):
            continue
        if str(node.get("node_id")) == node_id:
            return node

    raise KeyError(f"在对话树中未找到节点: {node_id}")


def _build_game_state(raw: Dict[str, Any] | None) -> GameState:
    """从树节点中的 game_state 字段构造 GameState（尽量兼容）"""
    data: Dict[str, Any] = dict(raw or {})

    # 旧树结构中使用 time 字段，这里归一化为 timestamp
    if "time" in data and "timestamp" not in data:
        data["timestamp"] = data.pop("time")

    # 只保留 GameState 支持的字段，避免多余键报错
    allowed_keys = set(GameState.__dataclass_fields__.keys())
    cleaned = {k: v for k, v in data.items() if k in allowed_keys}

    return GameState(**cleaned)


def _extract_beat_info(node: Dict[str, Any]) -> Dict[str, Any]:
    """从节点元数据中提取节拍信息"""
    meta = node.get("metadata") or {}
    if not isinstance(meta, dict):
        return {}
    beat_info: Dict[str, Any] = {}
    for key in ("beat_type", "tension_level", "act_index", "leads_to_ending"):
        if key in meta:
            beat_info[key] = meta[key]
    return beat_info


def _render_result(node_id: str, scene: str, result: Dict[str, Any]) -> None:
    """在终端中以表格形式展示评估结果"""
    console.print("\n[bold cyan]选择点 BMAD 评估结果[/bold cyan]\n")
    console.print(f"[dim]节点: {node_id}  场景: {scene}[/dim]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("维度", style="cyan", width=16)
    table.add_column("得分", width=8)
    table.add_column("说明", width=80)

    for dim in result.get("dimensions", []):
        name = str(dim.get("name", "未知"))
        score = f"{float(dim.get('score', 0.0)):.1f}"
        comment = str(dim.get("comment", ""))
        table.add_row(name, score, comment)

    console.print(table)

    overall = float(result.get("overall_score", 0.0))
    console.print(f"\n[bold]总体评分：[/bold]{overall:.1f} / 10.0\n")

    suggestions = result.get("suggestions") or []
    if suggestions:
        console.print("[bold]改进建议：[/bold]")
        for idx, s in enumerate(suggestions, 1):
            console.print(f"  {idx}. {s}")
        console.print()


def main() -> int:
    parser = argparse.ArgumentParser(description="对单个节点的选择集合进行 BMAD 风格离线评估")
    parser.add_argument(
        "--tree-json",
        required=True,
        help="对话树 JSON 或 checkpoint 路径",
    )
    parser.add_argument(
        "--node-id",
        required=True,
        help="要评估的节点 ID（如 root / node_0001）",
    )
    args = parser.parse_args()

    tree_path = Path(args.tree_json)
    tree = _load_tree(tree_path)
    node = _find_node(tree, args.node_id)

    choices = node.get("choices") or []
    if not isinstance(choices, list) or not choices:
        console.print(f"[red]节点 {args.node_id} 不包含 choices，无法评估。[/red]")
        return 1

    game_state_raw = node.get("game_state") or {}
    game_state = _build_game_state(game_state_raw)
    beat_info = _extract_beat_info(node)

    scene = str(node.get("scene", "")) or "未知场景"
    evaluator = ChoiceQualityEvaluator()
    result = evaluator.evaluate(
        scene_id=scene,
        choices=choices,  # 直接传入 dict，评估器内部可兼容
        game_state=game_state,
        beat_info=beat_info,
    )

    _render_result(str(node.get("node_id", args.node_id)), scene, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

