#!/usr/bin/env python3
"""
统一测试套件

运行所有核心测试并生成报告
"""

import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.table import Table


def run_test(test_name: str, test_file: str) -> tuple:
    """运行单个脚本型测试文件（如 test_full_flow.py）"""
    console = Console()

    console.print(f"\n🧪 运行测试: {test_name}")
    console.print(f"   文件: {test_file}")
    console.print("─" * 70)

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            console.print(f"✅ {test_name}: 通过\n")
            return (test_name, True, "")
        else:
            console.print(f"❌ {test_name}: 失败\n")
            console.print(f"错误输出:\n{result.stderr[:500]}\n")
            return (test_name, False, result.stderr[:200])

    except subprocess.TimeoutExpired:
        console.print(f"⏰ {test_name}: 超时\n")
        return (test_name, False, "测试超时")
    except Exception as e:
        console.print(f"❌ {test_name}: 异常 - {e}\n")
        return (test_name, False, str(e)[:200])


def run_pytest_suite(test_name: str, pytest_args) -> tuple:
    """运行一组 pytest 测试（例如 tests/test_*.py）"""
    console = Console()

    console.print(f"\n🧪 运行 Pytest 测试: {test_name}")
    console.print(f"   pytest 参数: {' '.join(pytest_args)}")
    console.print("─" * 70)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *pytest_args],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            console.print(f"✅ {test_name}: 通过\n")
            return (test_name, True, "")
        else:
            console.print(f"❌ {test_name}: 失败\n")
            console.print(f"错误输出:\n{result.stderr[:500]}\n")
            return (test_name, False, result.stderr[:200])

    except subprocess.TimeoutExpired:
        console.print(f"⏰ {test_name}: 超时\n")
        return (test_name, False, "pytest 测试超时")
    except Exception as e:
        console.print(f"❌ {test_name}: 异常 - {e}\n")
        return (test_name, False, str(e)[:200])


def main():
    """主函数"""
    console = Console()

    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════════╗")
    console.print("║              🧪 Ghost Story Factory - 测试套件                 ║")
    console.print("╚══════════════════════════════════════════════════════════════════╝")
    console.print("\n")

    results = []

    # 一、脚本型测试（历史测试）
    script_tests = [
        ("数据库系统测试", "test_database.py"),
        ("完整流程测试", "test_full_flow.py"),
        ("GameEngine集成测试", "test_engine_integration.py"),
    ]
    for test_name, test_file in script_tests:
        results.append(run_test(test_name, test_file))

    # 二、Pytest 单元测试（骨架 & guided TreeBuilder）
    pytest_suites = [
        (
            "骨架模型 / SkeletonGenerator / guided TreeBuilder / StoryGenerator 模式 / 文本填充 / 报告单元测试",
            [
                "tests/test_skeleton_model.py",
                "tests/test_skeleton_generator.py",
                "tests/test_tree_builder_guided.py",
                "tests/test_text_filler.py",
                "tests/test_story_report.py",
                "tests/test_story_generator_modes.py",
            ],
        ),
    ]
    for test_name, args in pytest_suites:
        results.append(run_pytest_suite(test_name, args))

    # 生成报告
    console.print("\n")
    console.print("╔══════════════════════════════════════════════════════════════════╗")
    console.print("║              📊 测试报告                                        ║")
    console.print("╚══════════════════════════════════════════════════════════════════╝")
    console.print("\n")

    # 创建结果表格
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("测试名称", style="cyan", width=30)
    table.add_column("状态", width=10)
    table.add_column("备注", width=30)

    passed = 0
    failed = 0

    for test_name, success, error in results:
        if success:
            table.add_row(test_name, "[green]✅ 通过[/green]", "")
            passed += 1
        else:
            table.add_row(test_name, "[red]❌ 失败[/red]", error[:30])
            failed += 1

    console.print(table)
    console.print("\n")

    # 总结
    total = passed + failed
    success_rate = (passed / total * 100) if total > 0 else 0

    console.print(f"总测试数: {total}")
    console.print(f"✅ 通过: {passed}")
    console.print(f"❌ 失败: {failed}")
    console.print(f"成功率: {success_rate:.1f}%")
    console.print("\n")

    if failed == 0:
        console.print("🎉 所有测试通过！系统状态良好！\n")
        return 0
    else:
        console.print(f"⚠️  有 {failed} 个测试失败，请检查错误信息\n")
        return 1


if __name__ == "__main__":
    exit(main())
