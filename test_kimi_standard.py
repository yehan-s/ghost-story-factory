#!/usr/bin/env python3
"""测试标准 Kimi API（非 Coding 版本）"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
    print(f"✅ 已加载 .env 文件")
except ImportError:
    print(f"使用手动加载 .env")
    with open(project_root / ".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

from ghost_story_factory.utils.llm_client import LLMClient, LLMClientError

def test_standard_kimi():
    """测试标准 Kimi API"""
    print("\n" + "=" * 60)
    print("测试: 标准 Kimi API（api.moonshot.cn）")
    print("=" * 60)

    try:
        # 创建标准 Kimi 客户端
        client = LLMClient(provider="kimi")

        print(f"✅ LLMClient 初始化成功")
        print(f"   Provider: {client.provider}")
        print(f"   Base URL: {client.base_url}")
        print(f"   Default Model: {client.default_model}")
        print(f"   API Key: {client.api_key[:10]}...{client.api_key[-4:]}")

        # 测试简单调用
        prompt = "用一句话描述一个恐怖场景"

        print(f"\n📤 发送测试请求...")
        print(f"   Prompt: {prompt}")
        print(f"   Max tokens: 200")

        response = client.call(
            prompt=prompt,
            model=client.default_model,
            max_tokens=200,
            temperature=0.7,
        )

        print(f"\n✅ API 调用成功！")
        print(f"   响应长度: {len(response)} 字符")
        print(f"\n📥 生成内容:")
        print("-" * 60)
        print(response)
        print("-" * 60)

        return True

    except LLMClientError as e:
        print(f"\n❌ Kimi API 调用失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 未知错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_standard_kimi()

    print("\n" + "=" * 60)
    if success:
        print("🎉 标准 Kimi API 工作正常！")
        print("\n💡 建议：")
        print("   1. 当前 Kimi Coding 会员已过期")
        print("   2. 可以使用标准 Kimi API 作为备选")
        print("   3. 或者续费 Kimi Coding 会员")
        sys.exit(0)
    else:
        print("⚠️  标准 Kimi API 也无法使用")
        print("\n请检查:")
        print("   1. KIMI_API_KEY 是否正确")
        print("   2. 账户余额是否充足")
        print("   3. API 限流问题")
        sys.exit(1)
