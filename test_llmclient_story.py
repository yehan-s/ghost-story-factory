#!/usr/bin/env python
"""测试 LLMClient 模式的完整故事生成

用途：验证 ADR-004 核心 LLM 重构后的生成路径
- 使用 LLMClient 生成骨架
- 使用 LLMClient 生成选择点
- 检查日志质量
- 验证 story_report 工具
"""

import os
import sys
from pathlib import Path

# 确保使用 LLMClient 模式
os.environ["USE_PLOT_SKELETON"] = "1"

from src.ghost_story_factory.pregenerator.story_generator import StoryGeneratorWithRetry
from src.ghost_story_factory.pregenerator.synopsis_generator import SynopsisGenerator
from src.ghost_story_factory.utils.logging_utils import get_logger

logger, log_file = get_logger()

def main():
    """运行 LLMClient 模式的故事生成测试"""

    print("=" * 70)
    print("🧪 LLMClient 模式故事生成验证测试")
    print("=" * 70)
    print()

    # 测试参数
    city = "杭州"  # 选择杭州作为测试城市
    print(f"📍 测试城市: {city}")
    print(f"📝 日志文件: {log_file}")
    print(f"🔧 USE_PLOT_SKELETON: {os.getenv('USE_PLOT_SKELETON', '1')}")
    print()

    try:
        # 步骤 1: 生成故事简介
        print("=" * 70)
        print("步骤 1/4: 生成故事简介")
        print("=" * 70)

        synopsis_gen = SynopsisGenerator(city=city)
        synopses = synopsis_gen.generate_synopses()

        if not synopses:
            print("❌ 故事简介生成失败")
            return 1

        print(f"✅ 生成了 {len(synopses)} 个故事简介")

        # 选择第一个简介
        selected = synopses[0]
        print(f"\n📖 选中故事: {selected.title}")
        print(f"   主角: {selected.protagonist}")
        print(f"   地点: {selected.location}")
        print(f"   预计时长: {selected.estimated_duration} 分钟")
        print()

        # 步骤 2: 初始化 StoryGenerator
        print("=" * 70)
        print("步骤 2/4: 初始化 StoryGenerator（LLMClient 模式）")
        print("=" * 70)

        generator = StoryGeneratorWithRetry(
            city=city,
            synopsis=selected
        )

        print("✅ StoryGenerator 初始化完成")
        use_skeleton = os.getenv("USE_PLOT_SKELETON", "1")
        print(f"   骨架模式: {'启用' if use_skeleton == '1' else '禁用'}")
        print()

        # 步骤 3: 生成完整故事
        print("=" * 70)
        print("步骤 3/4: 生成完整故事（包含骨架 + 对话树）")
        print("=" * 70)
        print("⚠️  这可能需要几分钟时间...")
        print()

        result = generator.generate_full_story()

        if not result:
            print("❌ 故事生成失败")
            return 1

        print("✅ 故事生成成功！")
        print()

        # 步骤 4: 检查结果
        print("=" * 70)
        print("步骤 4/4: 检查生成结果")
        print("=" * 70)

        story_id = result.get("story_id")
        metadata = result.get("metadata", {})

        # 从 metadata 中提取关键信息
        total_nodes = metadata.get("total_nodes", 0)
        max_depth = metadata.get("max_depth", 0)
        estimated_duration = metadata.get("estimated_duration", 0)
        structure_info = metadata.get("structure", {})
        has_report = bool(structure_info.get("report"))

        print(f"📊 故事 ID: {story_id}")
        print(f"🌳 对话树节点数: {total_nodes}")
        print(f"📏 主线深度: {max_depth} 层")
        print(f"⏱️  预计时长: {estimated_duration} 分钟")
        print(f"🦴 骨架模式: {'启用' if os.getenv('USE_PLOT_SKELETON', '1') == '1' else '禁用'}")
        print(f"📋 结构报告: {'已生成' if has_report else '未生成'}")
        print()

        if has_report:
            report = structure_info.get("report", {})
            quality_state = structure_info.get("quality_state", "unknown")
            verdict = report.get("verdict", {})

            print("📋 结构验收结果:")
            print(f"   质量状态: {quality_state}")
            print(f"   深度达标: {verdict.get('depth_ok', 'N/A')}")
            print(f"   时长达标: {verdict.get('duration_ok', 'N/A')}")
            print(f"   结局达标: {verdict.get('endings_ok', 'N/A')}")
            print()

            # 显示详细报告信息
            if report:
                print("📋 详细结构报告:")
                print(f"   主线深度: {report.get('main_depth', 'N/A')}")
                print(f"   结局数量: {report.get('num_endings', 'N/A')}")
                print(f"   时长估算: {report.get('estimated_duration_minutes', 'N/A')} 分钟")
                print()

        # 总结
        print("=" * 70)
        print("✅ LLMClient 模式验证测试完成")
        print("=" * 70)
        print()
        print(f"📝 完整日志: {log_file}")
        print()
        print("🔍 下一步验证:")
        print("   1. 查看日志中的 [LLMClient] 请求/响应记录")
        print("   2. 使用 story_report 工具分析生成的故事")
        print("   3. 使用 BMAD 工具评估选择点质量")
        print()

        return 0

    except Exception as e:
        print()
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
