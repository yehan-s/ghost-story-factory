#!/usr/bin/env bash
set -euo pipefail

# ADR-006 验证脚本（v4 真入口）
# - 目标：验证 response 默认走 LLMClient、超时不再“卡死式失败”、guided 近似合并不再跨 depth 压扁结构
# - 注意：不要用 legacy 的 generate_full_story.py 验证（那是 CrewAI 流水线）

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

if [[ ! -x "$PY" ]]; then
  echo "❌ 未找到可执行 Python: $PY"
  echo "   你可以设置 PYTHON_BIN=/path/to/python 或创建 .venv。"
  exit 1
fi

mask_env_key() {
  local k="$1"
  if [[ -n "${!k:-}" ]]; then
    echo "${k}=***"
  else
    echo "${k}=(not set)"
  fi
}

echo "="
echo "ADR-006 验证（v4 真入口）"
echo "="

echo "[env] $(mask_env_key KIMI_API_KEY)"
echo "[env] $(mask_env_key MOONSHOT_API_KEY)"
echo "[env] $(mask_env_key OPENAI_API_KEY)"

if [[ -z "${KIMI_API_KEY:-}" && -z "${MOONSHOT_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
  echo "⚠️  未检测到 API Key（可能依赖 .env 在运行时加载）。"
  echo "   若最终仍无 key，本次只能验证‘不崩溃/有兜底’，无法验证真实 LLM 质量与超时表现。"
fi

echo
echo "[config] USE_PLOT_SKELETON=1"
echo "[config] USE_LLMCLIENT_RESPONSE=1"
echo "[config] RESPONSE_MAX_TOKENS=${RESPONSE_MAX_TOKENS:-900}"
echo "[config] LLM_TIMEOUTS=${LLM_TIMEOUTS:-30,60}"
echo "[config] LLM_MAX_RETRIES=${LLM_MAX_RETRIES:-1}"
echo "[config] MAX_DEPTH=${MAX_DEPTH:-8}"
echo "[config] MIN_MAIN_PATH_DEPTH=${MIN_MAIN_PATH_DEPTH:-4}"
echo

export USE_PLOT_SKELETON=1
export USE_LLMCLIENT_RESPONSE=1
export RESPONSE_MAX_TOKENS="${RESPONSE_MAX_TOKENS:-900}"
export LLM_TIMEOUTS="${LLM_TIMEOUTS:-30,60}"
export LLM_MAX_RETRIES="${LLM_MAX_RETRIES:-1}"
export MAX_DEPTH="${MAX_DEPTH:-8}"
export MIN_MAIN_PATH_DEPTH="${MIN_MAIN_PATH_DEPTH:-4}"

# 运行一次 MVP 生成（使用 examples 文档，走 v4 pregenerator 真入口）
"$PY" tools/generate_mvp.py || true

echo

echo "="
echo "日志快速检查"
echo "="

# 最近的日志文件（包含 full_generation / generate_mvp 等）
LATEST_LOG="$(ls -t logs/*.log 2>/dev/null | head -n 1 || true)"

if [[ -z "$LATEST_LOG" ]]; then
  echo "⚠️  未找到 logs/*.log（可能未生成日志或目录不可写）。"
  exit 0
fi

echo "[log] latest: $LATEST_LOG"

echo

echo "--- LLMClient 请求摘要（最近 20 行） ---"
rg "\[LLMClient\] Request" "$LATEST_LOG" -n | tail -n 20 || true

echo

echo "--- 超时/限流/403（若有） ---"
rg "ReadTimeout|timeout|HTTP 429|HTTP 403" "$LATEST_LOG" -n || true

echo

echo "--- CrewAI 黑盒错误（必须为 0） ---"
rg "Invalid format specifier" "$LATEST_LOG" -n || true

echo

echo "✅ 完成：若无 format specifier 且超时可快速失败，则 ADR-006 基本稳。"
