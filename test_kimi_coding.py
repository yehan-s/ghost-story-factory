#!/usr/bin/env python3
"""快速测试 Kimi Coding 配置"""
import os
import sys

# 设置环境变量
os.environ['KIMI_API_KEY'] = 'sk-kimi-sJz4nnl3ngZh7BIoUmfXRlzpgGzL0VRFJ6SqVa8xj3cDwL5Fg5ggb56PzmkZLeQh'
os.environ['KIMI_API_BASE'] = 'https://api.kimi.com/coding/v1'
os.environ['KIMI_MODEL'] = 'kimi-for-coding'

# 导入 LLMClient
sys.path.insert(0, 'src')
from ghost_story_factory.utils.llm_client import LLMClient

print("=" * 70)
print("测试 Kimi Coding (使用 kimi-coding provider)")
print("=" * 70)

try:
    # 使用 kimi-coding provider
    client = LLMClient(provider="kimi-coding")
    
    print(f"\n配置信息:")
    print(f"  Provider: {client.provider}")
    print(f"  API Format: {client.api_format}")
    print(f"  Base URL: {client.base_url}")
    print(f"  Model: {client.default_model}")
    
    print("\n发送测试请求...")
    result = client.call(
        prompt="你好，请回复'测试成功'",
        model=client.default_model,
        max_tokens=50,
        temperature=0.7
    )
    
    print(f"\n✅ 成功！")
    print(f"响应: {result}")
    
except Exception as e:
    print(f"\n❌ 失败: {type(e).__name__}")
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("测试完成！Kimi Coding 配置正常工作")
print("=" * 70)
