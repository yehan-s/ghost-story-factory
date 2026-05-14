#!/usr/bin/env python3
"""统一测试入口 — v7 沙盒播放器版。

LLM 流水线相关的脚本测试和单元测试已随代码归档到 `legacy/llm-pipeline` 分支,
本脚本只跑剧本播放器主线相关的 pytest 套件。
"""
from __future__ import annotations

import subprocess
import sys

from rich.console import Console
from rich.table import Table

console = Console()


PYTEST_SUITES: list[tuple[str, list[str]]] = [
    (
        "运行时契约 / state 派生",
        [
            "tests/test_save_manager_query.py",
            "tests/test_ending_seen.py",
            "tests/test_behavior_profile.py",
            "tests/test_shifts_completed_derived.py",
            "tests/test_shifts_skipped_derived.py",
            "tests/test_state_save_binding.py",
            "tests/test_state_sim.py",
            "tests/test_effects_learn.py",
            "tests/test_reaction_engine.py",
            "tests/test_reaction_contracts_schema.py",
            "tests/test_reaction_coverage.py",
        ],
    ),
    (
        "剧本审计(audit_*)",
        [
            "tests/test_audit_pass22.py",
            "tests/test_audit_paths_linmou.py",
            "tests/test_audit_playability.py",
            "tests/test_audit_reactions.py",
            "tests/test_audit_script_depth.py",
            "tests/test_audit_state.py",
            "tests/test_audit_variants.py",
            "tests/test_npc_accountability_pass8.py",
            "tests/test_npc_drowned_official_variants.py",
            "tests/test_lore_data.py",
            "tests/test_linmou_sandbox.py",
        ],
    ),
    (
        "v7 TUI / 表达层",
        [
            "tests/test_archive_view.py",
            "tests/test_menu_registry.py",
            "tests/test_player_presentation.py",
            "tests/test_choice_affordance.py",
            "tests/test_tui_presenter.py",
            "tests/test_tui_experience_pass14.py",
            "tests/test_picker_variant_renders.py",
            "tests/test_path_explorer_variants.py",
            "tests/test_view_tree_progress.py",
        ],
    ),
]


def run_suite(name: str, files: list[str]) -> tuple[str, bool, str]:
    console.print(f"\n🧪 {name}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "--tb=short", *files],
            timeout=180,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            console.print(f"   ✅ 通过\n")
            return (name, True, "")
        tail = (result.stdout + result.stderr).strip().split("\n")[-1]
        console.print(f"   ❌ 失败: {tail}\n")
        return (name, False, tail[:200])
    except subprocess.TimeoutExpired:
        console.print(f"   ⏰ 超时\n")
        return (name, False, "超时")


def main() -> int:
    results = [run_suite(n, fs) for n, fs in PYTEST_SUITES]

    table = Table(title="测试结果")
    table.add_column("套件")
    table.add_column("状态")
    table.add_column("备注")
    for name, ok, msg in results:
        table.add_row(name, "✅ 通过" if ok else "❌ 失败", msg)
    console.print(table)

    total = len(results)
    passed = sum(1 for _, ok, _ in results if ok)
    console.print(f"\n总套件: {total}  ✅ 通过: {passed}  ❌ 失败: {total - passed}")
    console.print(f"成功率: {passed / total * 100:.1f}%")

    if passed == total:
        console.print("\n🎉 所有套件通过！")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
