#!/usr/bin/env python3
"""测试 LangGraph 流水线 (ADR-005)

验证内容：
1. LangGraph 模块可导入
2. StateGraph 可创建
3. 开关功能正常
4. 节点函数可调用（不实际运行 LLM）
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass


def test_imports():
    """测试模块导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)

    try:
        from ghost_story_factory.orchestration import run_story_pipeline, create_story_graph
        from ghost_story_factory.orchestration.state import StoryPipelineState, create_initial_state
        from ghost_story_factory.orchestration.nodes import stage_docs, stage_skeleton, stage_tree, stage_report
        from ghost_story_factory.orchestration.graph import should_use_langgraph

        print("✅ ghost_story_factory.orchestration 导入成功")
        print("✅ run_story_pipeline 可用")
        print("✅ create_story_graph 可用")
        print("✅ StoryPipelineState 可用")
        print("✅ 所有节点函数可用")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_creation():
    """测试 StateGraph 创建"""
    print("\n" + "=" * 60)
    print("测试 2: StateGraph 创建")
    print("=" * 60)

    try:
        from ghost_story_factory.orchestration.graph import create_story_graph

        app = create_story_graph()
        print(f"✅ StateGraph 创建成功")
        print(f"   类型: {type(app).__name__}")

        # 检查图结构
        # LangGraph 1.0.x 的 CompiledGraph 结构
        if hasattr(app, 'nodes'):
            print(f"   节点数: {len(app.nodes)}")
        return True
    except Exception as e:
        print(f"❌ StateGraph 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_switch():
    """测试开关功能"""
    print("\n" + "=" * 60)
    print("测试 3: 开关功能")
    print("=" * 60)

    try:
        from ghost_story_factory.orchestration.graph import should_use_langgraph

        # 测试默认值（关闭）
        original = os.environ.get("USE_LANGGRAPH_PIPELINE")
        os.environ.pop("USE_LANGGRAPH_PIPELINE", None)

        result = should_use_langgraph()
        print(f"✅ 默认值: {result} (期望: False)")
        assert result == False, "默认应为 False"

        # 测试开启
        os.environ["USE_LANGGRAPH_PIPELINE"] = "1"
        result = should_use_langgraph()
        print(f"✅ 设为 '1': {result} (期望: True)")
        assert result == True, "设为 '1' 应为 True"

        # 测试关闭
        os.environ["USE_LANGGRAPH_PIPELINE"] = "0"
        result = should_use_langgraph()
        print(f"✅ 设为 '0': {result} (期望: False)")
        assert result == False, "设为 '0' 应为 False"

        # 恢复原值
        if original:
            os.environ["USE_LANGGRAPH_PIPELINE"] = original
        else:
            os.environ.pop("USE_LANGGRAPH_PIPELINE", None)

        return True
    except Exception as e:
        print(f"❌ 开关测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_creation():
    """测试状态创建"""
    print("\n" + "=" * 60)
    print("测试 4: 状态创建")
    print("=" * 60)

    try:
        from ghost_story_factory.orchestration.state import create_initial_state

        state = create_initial_state(
            city="测试城市",
            synopsis_title="测试标题",
            synopsis_text="测试简介",
            synopsis_protagonist="测试主角",
            synopsis_location="测试场景",
            synopsis_duration=20,
            test_mode=True,
        )

        print(f"✅ 初始状态创建成功")
        print(f"   city: {state['city']}")
        print(f"   synopsis_title: {state['synopsis_title']}")
        print(f"   docs_stage_status: {state['docs_stage_status']}")
        print(f"   test_mode: {state['test_mode']}")

        return True
    except Exception as e:
        print(f"❌ 状态创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stage_docs_node():
    """测试 stage_docs 节点（不调用 LLM）"""
    print("\n" + "=" * 60)
    print("测试 5: stage_docs 节点")
    print("=" * 60)

    try:
        from ghost_story_factory.orchestration.state import create_initial_state
        from ghost_story_factory.orchestration.nodes import stage_docs

        state = create_initial_state(
            city="测试城市",
            synopsis_title="测试标题",
            synopsis_text="测试简介",
            synopsis_protagonist="测试主角",
            synopsis_location="测试场景",
            synopsis_duration=20,
            test_mode=True,
        )

        # 运行 stage_docs（会生成简化文档，不调用 LLM）
        result = stage_docs(state)

        print(f"✅ stage_docs 执行成功")
        print(f"   docs_stage_status: {result['docs_stage_status']}")
        print(f"   gdd_content 长度: {len(result.get('gdd_content', ''))}")
        print(f"   lore_content 长度: {len(result.get('lore_content', ''))}")
        print(f"   main_story 长度: {len(result.get('main_story', ''))}")

        if result.get("telemetry", {}).get("stage_docs"):
            tel = result["telemetry"]["stage_docs"]
            print(f"   遥测状态: {tel.get('status')}")
            print(f"   耗时: {tel.get('duration_seconds', 0):.2f}s")

        return result["docs_stage_status"] == "success"
    except Exception as e:
        print(f"❌ stage_docs 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("\n🔍 LangGraph 流水线测试 (ADR-005)")
    print("=" * 60)

    results = []

    results.append(("模块导入", test_imports()))
    results.append(("StateGraph 创建", test_graph_creation()))
    results.append(("开关功能", test_switch()))
    results.append(("状态创建", test_state_creation()))
    results.append(("stage_docs 节点", test_stage_docs_node()))

    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{status}  {test_name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！LangGraph 集成正常。")
        print("\n💡 下一步：")
        print("   1. 设置 USE_LANGGRAPH_PIPELINE=1 启用 LangGraph 路径")
        print("   2. 运行完整故事生成测试")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
