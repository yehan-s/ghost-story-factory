#!/usr/bin/env python3
"""测试 Kimi API 可用性

测试内容：
1. LLMClient 基础初始化
2. 简单文本生成调用
3. 响应生成路径（RuntimeResponseGenerator）
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 已加载 .env 文件")
    else:
        print(f"⚠️  .env 文件不存在: {env_file}")
except ImportError:
    print(f"⚠️  python-dotenv 未安装，尝试手动加载 .env")
    # 简单手动解析 .env
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print(f"✅ 已手动加载 .env 文件")

from ghost_story_factory.utils.llm_client import LLMClient, create_llm_client, LLMClientError


def test_llm_client_init():
    """测试 LLMClient 初始化"""
    print("=" * 60)
    print("测试 1: LLMClient 初始化")
    print("=" * 60)

    try:
        # 测试标准 kimi provider（根据 .env 配置自动选择）
        client = LLMClient(provider="kimi")
        print(f"✅ LLMClient 初始化成功")
        print(f"   Provider: {client.provider}")
        print(f"   Base URL: {client.base_url}")
        print(f"   Default Model: {client.default_model}")
        print(f"   API Key: {client.api_key[:10]}...{client.api_key[-4:]}")
        return client
    except Exception as e:
        print(f"❌ LLMClient 初始化失败: {e}")
        return None


def test_simple_call(client: LLMClient):
    """测试简单的 LLM 调用"""
    print("\n" + "=" * 60)
    print("测试 2: 简单文本生成调用")
    print("=" * 60)

    if not client:
        print("⚠️  跳过测试（客户端未初始化）")
        return False

    prompt = """请生成一个简短的恐怖故事开头（不超过100字），包含以下元素：
- 地点：废弃医院
- 时间：深夜
- 氛围：诡异、压抑

直接输出故事文本，无需其他说明。"""

    try:
        print(f"📤 发送请求...")
        print(f"   Prompt 长度: {len(prompt)} 字符")
        print(f"   Model: {client.default_model}")
        print(f"   Max tokens: 500")

        response = client.call(
            prompt=prompt,
            model=client.default_model,
            max_tokens=500,
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
        print(f"❌ LLM 调用失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {type(e).__name__}: {e}")
        return False


def test_response_generator():
    """测试 RuntimeResponseGenerator 的 LLMClient 路径"""
    print("\n" + "=" * 60)
    print("测试 3: RuntimeResponseGenerator LLMClient 模式")
    print("=" * 60)

    try:
        # 检查环境变量
        use_llmclient = os.getenv("USE_LLMCLIENT_RESPONSE", "1")
        print(f"   USE_LLMCLIENT_RESPONSE: {use_llmclient}")

        if use_llmclient != "1":
            print(f"⚠️  LLMClient 响应生成未启用（当前值: {use_llmclient}）")
            print(f"   提示：设置 USE_LLMCLIENT_RESPONSE=1 启用")
            return False

        # 简单测试：创建 LLMClient 并检查配置
        from ghost_story_factory.utils.llm_client import create_llm_client

        client = create_llm_client(provider="kimi")
        if client:
            print(f"✅ create_llm_client 工厂函数成功")
            print(f"   Provider: {client.provider}")
            print(f"   Base URL: {client.base_url}")
            print(f"   Default Model: {client.default_model}")
            return True
        else:
            print(f"❌ create_llm_client 返回 None")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("\n🔍 Kimi API 可用性测试")
    print("=" * 60)

    results = []

    # 测试 1: 初始化
    client = test_llm_client_init()
    results.append(("LLMClient 初始化", client is not None))

    # 测试 2: 简单调用
    if client:
        success = test_simple_call(client)
        results.append(("简单文本生成", success))
    else:
        results.append(("简单文本生成", False))

    # 测试 3: ResponseGenerator
    success = test_response_generator()
    results.append(("ResponseGenerator 集成", success))

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
        print("\n🎉 所有测试通过！Kimi API 工作正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查配置和代码。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
