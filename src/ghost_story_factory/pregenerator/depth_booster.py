"""
深度增强工具（Depth Booster）

用途：
- 从角色级检查点继续生成，强制拉深主线深度/时长/结局数量
- 通过环境变量调节引擎参数，而不重头跑

用法示例：
    python -m ghost_story_factory.pregenerator.depth_booster \
        --city 上海 \
        --character 夜班地铁维保员 \
        --target-depth 30 \
        --max-depth 60 \
        --extend 8 \
        --force-critical 1 \
        --max-nodes 1200 \
        --seconds-per-choice 90

可选：
- 如提供 --title，将尝试在 deliverables/程序-<city>/<title>/ 下加载 GDD/Lore/主线；
- 也可用 --gdd/--lore/--story 指定文件路径；均未提供将以空文本启动（允许离线默认分支/响应）。
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Tuple

from .tree_builder import DialogueTreeBuilder
from .time_validator import TimeValidator


def _read_text_or_empty(path: Optional[str]) -> str:
    if not path:
        return ""
    p = Path(path)
    if p.exists():
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


def _safe_title_dir(city: str, title: str) -> Path:
    from re import sub as _re_sub
    base = Path(f"deliverables/程序-{city}")
    safe = _re_sub(r"[^\w\u4e00-\u9fff]+", "_", title)
    return base / safe


def _maybe_load_docs(city: str, title: Optional[str], gdd: Optional[str], lore: Optional[str], story: Optional[str]) -> Tuple[str, str, str]:
    # 1) 明确文件路径优先
    gdd_txt = _read_text_or_empty(gdd)
    lore_txt = _read_text_or_empty(lore)
    story_txt = _read_text_or_empty(story)

    if title and (not gdd_txt or not lore_txt or not story_txt):
        # 2) 尝试从 deliverables 自动命中
        base_dir = Path(f"deliverables/程序-{city}")
        title_dir = _safe_title_dir(city, title)

        def _read_if_missing(cur: str, p: Path) -> str:
            if cur:
                return cur
            return p.read_text(encoding="utf-8") if p.exists() else cur

        gdd_txt = _read_if_missing(gdd_txt, title_dir / f"{city}_{title_dir.name}_gdd.md")
        lore_txt = _read_if_missing(lore_txt, title_dir / f"{city}_{title_dir.name}_lore_v2.md")
        story_txt = _read_if_missing(story_txt, title_dir / f"{city}_{title_dir.name}_story.md")

        # 再尝试城市级缓存
        gdd_txt = _read_if_missing(gdd_txt, base_dir / f"{city}_gdd.md")
        lore_txt = _read_if_missing(lore_txt, base_dir / f"{city}_lore_v2.md")
        story_txt = _read_if_missing(story_txt, base_dir / f"{city}_story.md")

    # 3) 仍缺失则返回空文本（允许离线默认逻辑继续推进）
    return gdd_txt or "", lore_txt or "", story_txt or ""


def run_boost(
    city: str,
    character: str,
    title: Optional[str],
    gdd_path: Optional[str],
    lore_path: Optional[str],
    story_path: Optional[str],
    target_depth: int,
    max_depth: int,
    extend_attempts: int,
    force_critical_interval: int,
    max_total_nodes: int,
    plateau_limit: int,
    seconds_per_choice: int,
    concurrency: int,
):
    # 设置环境（仅对当前进程及其子流程有效）
    os.environ.setdefault("NON_INTERACTIVE", "1")
    os.environ.setdefault("SKELETON_MODE", "1")
    os.environ.setdefault("MAX_BRANCHES_PER_NODE", "2")
    os.environ["MIN_MAIN_PATH_DEPTH"] = str(target_depth)
    os.environ["MAX_DEPTH"] = str(max_depth)
    os.environ["EXTEND_ON_FAIL_ATTEMPTS"] = str(extend_attempts)
    os.environ["FORCE_CRITICAL_INTERVAL"] = str(force_critical_interval)
    os.environ["MAX_TOTAL_NODES"] = str(max_total_nodes)
    os.environ["PROGRESS_PLATEAU_LIMIT"] = str(plateau_limit)
    os.environ["SECONDS_PER_CHOICE"] = str(seconds_per_choice)
    os.environ["TREE_BUILDER_CONCURRENCY"] = str(concurrency)

    checkpoint_path = f"checkpoints/{city}_{character}_tree.json"
    if not Path(checkpoint_path).exists():
        print(f"❌ 找不到角色检查点：{checkpoint_path}")
        sys.exit(2)

    # 尝试读取文档（优先用户传入/标题推断；缺失则空文本）
    gdd_txt, lore_txt, story_txt = _maybe_load_docs(city, title, gdd_path, lore_path, story_path)

    # 构建器（synopsis 仅用于新建根节点，本工具从检查点恢复，不依赖）
    builder = DialogueTreeBuilder(
        city=city,
        synopsis=title or "",
        gdd_content=gdd_txt,
        lore_content=lore_txt,
        main_story=story_txt,
        test_mode=False,
    )

    print("🚀 深度增强：从检查点继续扩展……")
    print(f"   city={city}, character={character}")
    print(f"   target_depth={target_depth}, max_depth={max_depth}")
    print(f"   extend_attempts={extend_attempts}, critical_interval={force_critical_interval}")
    print(f"   max_total_nodes={max_total_nodes}, plateau_limit={plateau_limit}")
    print(f"   seconds_per_choice={seconds_per_choice}, concurrency={concurrency}")

    # 继续生成
    tree = builder.generate_tree(
        max_depth=max_depth,
        min_main_path_depth=target_depth,
        checkpoint_path=checkpoint_path,
    )

    # 生成完成后做一份校验报告
    report = TimeValidator().get_validation_report(tree)
    print("\n📊 深度增强完成：")
    print(f"   总节点数: {report['total_nodes']}")
    print(f"   主线深度: {report['main_path_depth']}")
    print(f"   预计时长: {report['estimated_duration_minutes']} 分钟")
    print(f"   结局数量: {report['ending_count']}")
    print(f"   结局达标: {'是' if report.get('passes_endings_check') else '否'} (≥ {TimeValidator().min_endings})")

    # 可选：把结果回写角色级检查点聚合文件，便于后续一次性入库
    agg_path = Path(f"checkpoints/{city}_characters.json")
    if agg_path.exists():
        try:
            payload = json.loads(agg_path.read_text(encoding="utf-8"))
            trees = payload.get("dialogue_trees", {})
            trees[character] = tree
            payload["dialogue_trees"] = trees
            agg_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"💾 已更新聚合检查点：{agg_path}")
        except Exception as e:
            print(f"⚠️ 回写聚合检查点失败（已忽略）：{e}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="从检查点继续扩展对话树，强制拉深主线")
    parser.add_argument("--city", required=True, help="城市名，例如 上海")
    parser.add_argument("--character", required=True, help="角色名，例如 夜班地铁维保员")
    parser.add_argument("--title", help="故事标题（用于命中 deliverables 缓存）")
    parser.add_argument("--gdd", help="GDD 文件路径，可选")
    parser.add_argument("--lore", help="Lore v2 文件路径，可选")
    parser.add_argument("--story", help="主线故事文件路径，可选")

    parser.add_argument("--target-depth", type=int, default=int(os.getenv("MIN_MAIN_PATH_DEPTH", "30")), help="目标主线最小深度")
    parser.add_argument("--max-depth", type=int, default=int(os.getenv("MAX_DEPTH", "50")), help="最大搜索深度")
    parser.add_argument("--extend", type=int, default=int(os.getenv("EXTEND_ON_FAIL_ATTEMPTS", "4")), help="扩展轮次（失败后同轮继续）")
    parser.add_argument("--force-critical", type=int, default=int(os.getenv("FORCE_CRITICAL_INTERVAL", "2")), help="关键分支注入间隔（步）")
    parser.add_argument("--max-nodes", type=int, default=int(os.getenv("MAX_TOTAL_NODES", "800")), help="本轮节点上限")
    parser.add_argument("--plateau", type=int, default=int(os.getenv("PROGRESS_PLATEAU_LIMIT", "3")), help="平台期阈值（连续无进展轮数）")
    parser.add_argument("--seconds-per-choice", type=int, default=int(os.getenv("SECONDS_PER_CHOICE", "90")), help="每个选择的预估秒数")
    parser.add_argument("--concurrency", type=int, default=int(os.getenv("TREE_BUILDER_CONCURRENCY", "6")), help="并发工作线程数")

    args = parser.parse_args(argv)

    run_boost(
        city=args.city,
        character=args.character,
        title=args.title,
        gdd_path=args.gdd,
        lore_path=args.lore,
        story_path=args.story,
        target_depth=args.target_depth,
        max_depth=args.max_depth,
        extend_attempts=args.extend,
        force_critical_interval=args.force_critical,
        max_total_nodes=args.max_nodes,
        plateau_limit=args.plateau,
        seconds_per_choice=args.seconds_per_choice,
        concurrency=args.concurrency,
    )


if __name__ == "__main__":
    main()


