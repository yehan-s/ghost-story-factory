"""
Depth Orchestrator（无人值守巡航器）

功能：
- 监控 checkpoints/tree_incremental.jsonl 的增长与主线深度
- 检测平台期或未达标时，自动以更激进参数调用 depth_booster 继续扩展

用法：
    python -m ghost_story_factory.pregenerator.depth_orchestrator \
        --city 上海 --character 夜班地铁维保员 --title 静安寺地下电梯 \
        --target-depth 30 --max-depth 60 --poll-interval 60 --patience 3
"""

import os
import time
import json
import argparse
import subprocess
from pathlib import Path
from typing import Tuple


def _tail_metrics(jsonl_path: Path) -> Tuple[int, int, str]:
    if not jsonl_path.exists():
        return 0, 0, ""
    max_depth = 0
    nodes = 0
    last_ts = ""
    try:
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                last_ts = obj.get("ts") or last_ts
                node = obj.get("node") or {}
                d = node.get("depth")
                if isinstance(d, int) and d > max_depth:
                    max_depth = d
                nodes += 1
    except Exception:
        pass
    return max_depth, nodes, last_ts


def main(argv=None):
    ap = argparse.ArgumentParser(description="无人值守深度巡航器")
    ap.add_argument("--city", required=True)
    ap.add_argument("--character", required=True)
    ap.add_argument("--title")
    ap.add_argument("--target-depth", type=int, default=int(os.getenv("MIN_MAIN_PATH_DEPTH", "30")))
    ap.add_argument("--max-depth", type=int, default=int(os.getenv("MAX_DEPTH", "60")))
    ap.add_argument("--poll-interval", type=int, default=60, help="轮询秒数")
    ap.add_argument("--patience", type=int, default=3, help="连续平台轮数后触发增强")
    args = ap.parse_args(argv)

    os.environ.setdefault("NON_INTERACTIVE", "1")

    jsonl = Path("checkpoints/tree_incremental.jsonl")
    plateau = 0
    last_depth = -1
    last_nodes = -1

    print("🛰️  Orchestrator 启动")
    while True:
        depth, nodes, ts = _tail_metrics(jsonl)
        print(f"[orchestrator] depth={depth}, nodes={nodes}, ts={ts}")

        if depth >= args.target_depth:
            print("✅ 达到目标主线深度，巡航结束")
            return

        if depth <= last_depth and nodes <= last_nodes:
            plateau += 1
            print(f"ℹ️ 平台轮次 +1 → {plateau}/{args.patience}")
        else:
            plateau = 0
        last_depth, last_nodes = depth, nodes

        if plateau >= args.patience:
            print("⏩ 触发自动增强：调用 depth_booster")
            plateau = 0
            cmd = [
                "python", "-m", "ghost_story_factory.pregenerator.depth_booster",
                "--city", args.city,
                "--character", args.character,
                "--title", args.title or "",
                "--target-depth", str(args.target_depth),
                "--max-depth", str(args.max_depth),
                "--extend", os.getenv("EXTEND_ON_FAIL_ATTEMPTS", "8"),
                "--force-critical", os.getenv("FORCE_CRITICAL_INTERVAL", "1"),
                "--max-nodes", os.getenv("MAX_TOTAL_NODES", "1200"),
                "--plateau", os.getenv("PROGRESS_PLATEAU_LIMIT", "4"),
                "--seconds-per-choice", os.getenv("SECONDS_PER_CHOICE", "90"),
                "--concurrency", os.getenv("TREE_BUILDER_CONCURRENCY", "6"),
            ]
            subprocess.run(cmd, check=False)

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()


