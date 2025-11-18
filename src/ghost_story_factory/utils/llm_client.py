"""轻量级 LLM 客户端

职责：
- 提供统一的 LLM 调用接口（支持 Kimi / OpenAI）
- 完整的 request/response 日志记录
- 统一的错误处理和重试策略
- 不做 JSON 解析（只负责可靠地拿回文本）

设计原则：
- 单一职责：prompt -> str
- 最小依赖：requests 或官方 SDK
- 可观测性：完整日志
- 可测试性：易于 mock
"""

from __future__ import annotations

import os
import time
import json
from typing import Optional, Dict, Any
from pathlib import Path

# 使用项目现有的日志工具
try:
    from .logging_utils import get_logger
    logger, _ = get_logger()  # get_logger() 返回 (logger, log_file_path)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """LLM 客户端错误基类"""
    pass


class LLMTimeoutError(LLMClientError):
    """LLM 调用超时"""
    pass


class LLMAPIError(LLMClientError):
    """LLM API 错误（网络、配额、限流等）"""
    pass


class LLMClient:
    """轻量级 LLM 客户端

    示例：
        >>> client = LLMClient(provider="kimi")
        >>> response = client.call(
        ...     prompt="你好，请生成一个 JSON 对象",
        ...     model="kimi-k2-0905-preview",
        ...     max_tokens=16000,
        ...     temperature=0.7,
        ... )
    """

    def __init__(self, provider: str = "kimi") -> None:
        """初始化 LLM 客户端

        Args:
            provider: 提供商，"kimi" 或 "openai"

        Raises:
            ValueError: 如果 provider 不支持或缺少 API Key
        """
        self.provider = provider.lower()

        if self.provider not in ("kimi", "openai"):
            raise ValueError(f"不支持的 provider: {provider}，仅支持 'kimi' 或 'openai'")

        # 读取配置
        self._load_config()

        # 请求计数器（用于日志）
        self._request_count = 0

    def _load_config(self) -> None:
        """从环境变量加载配置"""
        if self.provider == "kimi":
            self.api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "Kimi provider 需要设置 KIMI_API_KEY 或 MOONSHOT_API_KEY 环境变量"
                )

            self.base_url = os.getenv(
                "KIMI_API_BASE",
                os.getenv("MOONSHOT_API_URL", "https://api.moonshot.cn/v1")
            )
            self.default_model = os.getenv(
                "KIMI_MODEL",
                os.getenv("MOONSHOT_MODEL", "kimi-k2-0905-preview")
            )

        elif self.provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI provider 需要设置 OPENAI_API_KEY 环境变量")

            self.base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("OPENAI_API_BASE")
            if not self.base_url:
                self.base_url = "https://api.openai.com/v1"

            self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o")

        # 超时配置（秒）
        self.timeout = int(os.getenv("LLM_TIMEOUT", "180"))

        # 重试配置
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "1"))
        self.retry_delay = float(os.getenv("LLM_RETRY_DELAY", "2.0"))

    def call(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 16000,
        temperature: float = 0.7,
    ) -> str:
        """调用 LLM 并返回响应文本

        Args:
            prompt: 提示词
            model: 模型名称，不传则使用默认模型
            max_tokens: 最大 token 数
            temperature: 温度参数

        Returns:
            str: LLM 返回的文本

        Raises:
            LLMTimeoutError: 超时
            LLMAPIError: API 错误
            LLMClientError: 其他客户端错误
        """
        model = model or self.default_model
        self._request_count += 1
        request_id = f"{self.provider}-{self._request_count}-{int(time.time())}"

        # 记录请求开始
        logger.info(
            f"[LLMClient] Request {request_id} | "
            f"provider={self.provider} model={model} "
            f"max_tokens={max_tokens} temp={temperature}"
        )
        logger.debug(f"[LLMClient] Request {request_id} | Prompt snippet: {self._snippet(prompt, 400)}")

        # 重试逻辑
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response_text = self._call_internal(prompt, model, max_tokens, temperature, request_id)

                # 记录成功响应
                logger.info(f"[LLMClient] Request {request_id} | Success | Response length: {len(response_text)}")
                logger.debug(f"[LLMClient] Request {request_id} | Response snippet: {self._snippet(response_text, 400)}")

                return response_text

            except Exception as e:
                last_error = e

                # 记录错误
                logger.error(
                    f"[LLMClient] Request {request_id} | Attempt {attempt + 1}/{self.max_retries + 1} failed | "
                    f"Error: {type(e).__name__}: {str(e)}"
                )

                # 最后一次尝试，不再重试
                if attempt >= self.max_retries:
                    break

                # 重试延迟
                logger.info(f"[LLMClient] Request {request_id} | Retrying in {self.retry_delay}s...")
                time.sleep(self.retry_delay)

        # 所有重试都失败
        logger.error(
            f"[LLMClient] Request {request_id} | All {self.max_retries + 1} attempts failed | "
            f"Last error: {type(last_error).__name__}: {str(last_error)}"
        )

        # 包装错误
        if "timeout" in str(last_error).lower():
            raise LLMTimeoutError(f"LLM 调用超时: {last_error}") from last_error
        else:
            raise LLMAPIError(f"LLM API 错误: {last_error}") from last_error

    def _call_internal(
        self,
        prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        request_id: str,
    ) -> str:
        """内部调用逻辑（单次尝试）

        Args:
            prompt: 提示词
            model: 模型名称
            max_tokens: 最大 token 数
            temperature: 温度参数
            request_id: 请求 ID（用于日志）

        Returns:
            str: LLM 返回的文本

        Raises:
            Exception: 任何 HTTP/API 错误
        """
        import requests

        # 构建请求
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # 发送请求
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        # 检查 HTTP 状态码
        if not response.ok:
            error_detail = response.text[:500] if response.text else "No error detail"
            raise LLMAPIError(
                f"HTTP {response.status_code} | URL: {url} | Detail: {error_detail}"
            )

        # 解析响应
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise LLMAPIError(f"Failed to parse JSON response: {e}") from e

        # 提取文本
        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise LLMAPIError(f"Unexpected content type: {type(content)}")
            return content
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"[LLMClient] Request {request_id} | Invalid response structure: {data}")
            raise LLMAPIError(f"Invalid response structure: {e}") from e

    def _snippet(self, text: str, max_chars: int) -> str:
        """生成文本片段（用于日志）

        Args:
            text: 原始文本
            max_chars: 最大字符数

        Returns:
            str: 截断后的文本片段
        """
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "...[截断]"


# 工厂函数（便于测试和依赖注入）
def create_llm_client(provider: Optional[str] = None) -> LLMClient:
    """创建 LLM 客户端实例

    Args:
        provider: 提供商，不传则优先使用 Kimi

    Returns:
        LLMClient: 客户端实例

    Raises:
        ValueError: 如果没有可用的 provider
    """
    if provider:
        return LLMClient(provider=provider)

    # 优先使用 Kimi
    if os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY"):
        return LLMClient(provider="kimi")

    # 回退到 OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return LLMClient(provider="openai")

    raise ValueError(
        "未检测到可用的 API Key。请设置 KIMI_API_KEY 或 OPENAI_API_KEY 环境变量"
    )
