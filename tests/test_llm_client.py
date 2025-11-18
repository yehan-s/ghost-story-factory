"""LLMClient 单元测试

测试覆盖：
- 配置加载（Kimi/OpenAI）
- 正常调用流程
- 错误处理（超时、API 错误、重试）
- 日志记录
- 工厂函数
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import json

# 导入被测模块
from src.ghost_story_factory.utils.llm_client import (
    LLMClient,
    LLMClientError,
    LLMTimeoutError,
    LLMAPIError,
    create_llm_client,
)


class TestLLMClientConfig:
    """测试配置加载"""

    def test_kimi_provider_config(self, monkeypatch):
        """测试 Kimi provider 配置读取"""
        # 清理所有相关环境变量
        for key in ["KIMI_API_KEY", "MOONSHOT_API_KEY", "OPENAI_API_KEY",
                    "KIMI_API_BASE", "MOONSHOT_API_URL", "KIMI_MODEL", "MOONSHOT_MODEL"]:
            monkeypatch.delenv(key, raising=False)

        monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
        monkeypatch.setenv("KIMI_API_BASE", "https://test.kimi.com/v1")
        monkeypatch.setenv("KIMI_MODEL", "kimi-test-model")

        client = LLMClient(provider="kimi")

        assert client.provider == "kimi"
        assert client.api_key == "test-kimi-key"
        assert client.base_url == "https://test.kimi.com/v1"
        assert client.default_model == "kimi-test-model"

    def test_kimi_provider_defaults(self, monkeypatch):
        """测试 Kimi provider 默认值"""
        # 清理所有相关环境变量
        for key in ["KIMI_API_KEY", "MOONSHOT_API_KEY", "OPENAI_API_KEY",
                    "KIMI_API_BASE", "MOONSHOT_API_URL", "KIMI_MODEL", "MOONSHOT_MODEL",
                    "OPENAI_BASE_URL", "OPENAI_API_BASE", "OPENAI_MODEL"]:
            monkeypatch.delenv(key, raising=False)

        monkeypatch.setenv("KIMI_API_KEY", "test-key")

        client = LLMClient(provider="kimi")

        assert client.base_url == "https://api.moonshot.cn/v1"
        assert client.default_model == "kimi-k2-0905-preview"

    def test_moonshot_compatibility(self, monkeypatch):
        """测试 MOONSHOT_* 环境变量兼容性"""
        # 清理所有相关环境变量
        for key in ["KIMI_API_KEY", "MOONSHOT_API_KEY", "OPENAI_API_KEY",
                    "KIMI_API_BASE", "MOONSHOT_API_URL", "KIMI_MODEL", "MOONSHOT_MODEL"]:
            monkeypatch.delenv(key, raising=False)

        monkeypatch.setenv("MOONSHOT_API_KEY", "test-moonshot-key")
        monkeypatch.setenv("MOONSHOT_API_URL", "https://moonshot.test.com/v1")
        monkeypatch.setenv("MOONSHOT_MODEL", "moonshot-test-model")

        client = LLMClient(provider="kimi")

        assert client.api_key == "test-moonshot-key"
        assert client.base_url == "https://moonshot.test.com/v1"
        assert client.default_model == "moonshot-test-model"

    def test_openai_provider_config(self, monkeypatch):
        """测试 OpenAI provider 配置读取"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://test.openai.com/v1")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-test-model")

        client = LLMClient(provider="openai")

        assert client.provider == "openai"
        assert client.api_key == "test-openai-key"
        assert client.base_url == "https://test.openai.com/v1"
        assert client.default_model == "gpt-test-model"

    def test_openai_provider_defaults(self, monkeypatch):
        """测试 OpenAI provider 默认值"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_API_BASE", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)

        client = LLMClient(provider="openai")

        assert client.base_url == "https://api.openai.com/v1"
        assert client.default_model == "gpt-4o"

    def test_missing_api_key_raises(self, monkeypatch):
        """测试缺少 API Key 时抛出异常"""
        monkeypatch.delenv("KIMI_API_KEY", raising=False)
        monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)

        with pytest.raises(ValueError, match="需要设置 KIMI_API_KEY"):
            LLMClient(provider="kimi")

    def test_unsupported_provider_raises(self, monkeypatch):
        """测试不支持的 provider 抛出异常"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")

        with pytest.raises(ValueError, match="不支持的 provider"):
            LLMClient(provider="unknown_provider")


class TestLLMClientCall:
    """测试 LLM 调用"""

    @patch("requests.post")
    def test_successful_call(self, mock_post, monkeypatch):
        """测试成功调用"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")

        # Mock HTTP 响应
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response from LLM"}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(provider="kimi")
        result = client.call(
            prompt="Test prompt",
            model="kimi-test-model",
            max_tokens=1000,
            temperature=0.5,
        )

        # 验证返回值
        assert result == "Test response from LLM"

        # 验证 HTTP 请求参数
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.kwargs["json"]["model"] == "kimi-test-model"
        assert call_args.kwargs["json"]["max_tokens"] == 1000
        assert call_args.kwargs["json"]["temperature"] == 0.5
        assert call_args.kwargs["json"]["messages"] == [
            {"role": "user", "content": "Test prompt"}
        ]

    @patch("requests.post")
    def test_http_error_raises(self, mock_post, monkeypatch):
        """测试 HTTP 错误"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MAX_RETRIES", "0")  # 禁用重试

        # Mock HTTP 错误响应
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response

        client = LLMClient(provider="kimi")

        with pytest.raises(LLMAPIError, match="HTTP 429"):
            client.call(prompt="Test prompt")

    @patch("requests.post")
    def test_invalid_json_response_raises(self, mock_post, monkeypatch):
        """测试无效 JSON 响应"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MAX_RETRIES", "0")

        # Mock 无效 JSON
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
        mock_post.return_value = mock_response

        client = LLMClient(provider="kimi")

        with pytest.raises(LLMAPIError, match="Failed to parse JSON"):
            client.call(prompt="Test prompt")

    @patch("requests.post")
    def test_missing_content_raises(self, mock_post, monkeypatch):
        """测试响应缺少 content 字段"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MAX_RETRIES", "0")

        # Mock 缺少 content 的响应
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"choices": []}  # 空 choices
        mock_post.return_value = mock_response

        client = LLMClient(provider="kimi")

        with pytest.raises(LLMAPIError, match="Invalid response structure"):
            client.call(prompt="Test prompt")

    @patch("requests.post")
    @patch("time.sleep")
    def test_retry_on_failure(self, mock_sleep, mock_post, monkeypatch):
        """测试失败时重试"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MAX_RETRIES", "2")
        monkeypatch.setenv("LLM_RETRY_DELAY", "1.0")

        # Mock: 前两次失败，第三次成功
        mock_response_fail = Mock()
        mock_response_fail.ok = False
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Internal server error"

        mock_response_success = Mock()
        mock_response_success.ok = True
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }

        mock_post.side_effect = [
            mock_response_fail,
            mock_response_fail,
            mock_response_success,
        ]

        client = LLMClient(provider="kimi")
        result = client.call(prompt="Test prompt")

        # 验证成功
        assert result == "Success after retry"

        # 验证重试了 2 次
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("requests.post")
    def test_timeout_error_raised(self, mock_post, monkeypatch):
        """测试超时错误"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MAX_RETRIES", "0")

        # Mock 超时异常
        import requests
        mock_post.side_effect = requests.Timeout("Request timeout")

        client = LLMClient(provider="kimi")

        with pytest.raises(LLMTimeoutError, match="超时"):
            client.call(prompt="Test prompt")


class TestLLMClientLogging:
    """测试日志记录"""

    @patch("requests.post")
    @patch("src.ghost_story_factory.utils.llm_client.logger")
    def test_logging_on_success(self, mock_logger, mock_post, monkeypatch):
        """测试成功调用时的日志"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")

        # Mock 成功响应
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(provider="kimi")
        client.call(prompt="Test prompt", model="test-model")

        # 验证日志记录
        assert mock_logger.info.call_count >= 2  # 至少有请求和响应日志
        assert mock_logger.debug.call_count >= 2  # 至少有 prompt 和 response snippet

    @patch("requests.post")
    @patch("src.ghost_story_factory.utils.llm_client.logger")
    def test_logging_on_error(self, mock_logger, mock_post, monkeypatch):
        """测试错误时的日志"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MAX_RETRIES", "0")

        # Mock 错误响应
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Server error"
        mock_post.return_value = mock_response

        client = LLMClient(provider="kimi")

        with pytest.raises(LLMAPIError):
            client.call(prompt="Test prompt")

        # 验证错误日志
        assert mock_logger.error.call_count >= 1


class TestLLMClientFactory:
    """测试工厂函数"""

    def test_create_kimi_client_priority(self, monkeypatch):
        """测试优先创建 Kimi 客户端"""
        monkeypatch.setenv("KIMI_API_KEY", "kimi-key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

        client = create_llm_client()

        assert client.provider == "kimi"

    def test_create_openai_client_fallback(self, monkeypatch):
        """测试回退到 OpenAI 客户端"""
        monkeypatch.delenv("KIMI_API_KEY", raising=False)
        monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

        client = create_llm_client()

        assert client.provider == "openai"

    def test_create_explicit_provider(self, monkeypatch):
        """测试显式指定 provider"""
        monkeypatch.setenv("KIMI_API_KEY", "kimi-key")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

        client = create_llm_client(provider="openai")

        assert client.provider == "openai"

    def test_create_no_api_key_raises(self, monkeypatch):
        """测试没有可用 API Key 时抛出异常"""
        monkeypatch.delenv("KIMI_API_KEY", raising=False)
        monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError, match="未检测到可用的 API Key"):
            create_llm_client()


class TestLLMClientSnippet:
    """测试 snippet 功能"""

    def test_snippet_short_text(self, monkeypatch):
        """测试短文本不截断"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")

        client = LLMClient(provider="kimi")
        snippet = client._snippet("Short text", max_chars=100)

        assert snippet == "Short text"

    def test_snippet_long_text(self, monkeypatch):
        """测试长文本截断"""
        monkeypatch.setenv("KIMI_API_KEY", "test-key")

        client = LLMClient(provider="kimi")
        long_text = "A" * 1000
        snippet = client._snippet(long_text, max_chars=100)

        assert len(snippet) <= 110  # 100 + "...[截断]"
        assert snippet.startswith("A" * 100)
        assert snippet.endswith("...[截断]")
