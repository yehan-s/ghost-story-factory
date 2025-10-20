#!/usr/bin/env bash
set -Eeuo pipefail

# 简易冒烟测试脚本：
# - 默认城市：广州（可通过第一个参数覆盖）
# - 优先使用：uvx --from . get-story
# - 备用方案：创建 .venv_smoke，安装 -e .，再运行 get-story

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CITY="${1:-广州}"

echo "[dev-run] 目标城市: $CITY"

# 加载 .env（若存在）
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# 关键环境变量检查：优先 KIMI_API_KEY，其次 OPENAI_API_KEY
if [[ -z "${KIMI_API_KEY:-}" && -z "${OPENAI_API_KEY:-}" ]]; then
  echo "[dev-run] 错误：未检测到 KIMI_API_KEY 或 OPENAI_API_KEY（可在 .env 中配置）。" >&2
  echo "[dev-run] 退出。" >&2
  exit 1
fi

run_with_uvx() {
  echo "[dev-run] 使用 uvx 本地临时环境运行..."
  uvx --from . get-story --city "$CITY"
}

run_with_venv() {
  echo "[dev-run] 未检测到 uvx，使用临时虚拟环境运行..."
  local venv_dir=".venv_smoke"
  if [[ ! -d "$venv_dir" ]]; then
    python3 -m venv "$venv_dir"
  fi
  # shellcheck disable=SC1090
  source "$venv_dir/bin/activate"
  python -m pip install -U pip >/dev/null
  python -m pip install -e . >/dev/null
  get-story --city "$CITY"
}

if command -v uvx >/dev/null 2>&1; then
  run_with_uvx
else
  run_with_venv
fi

# 计算与检查输出文件名（与 Python 逻辑保持一致的清理规则）
SAN_CITY="$(python3 - <<'PY'
import re,sys
s = sys.argv[1]
s = s.strip().replace('/', '_').replace('\\\\', '_')
s = re.sub(r"[^\\w\\-\\s\\u4e00-\\u9fff]", "_", s)
s = re.sub(r"\\s+", "_", s)
print(s or 'city')
PY
" "$CITY")"

OUT_FILE="${SAN_CITY}_story.md"
if [[ -f "$OUT_FILE" ]]; then
  echo "[dev-run] 成功：输出已生成 -> ./$OUT_FILE"
else
  echo "[dev-run] 警告：未发现期望的输出文件 ./$OUT_FILE（上方日志中可能有错误）。" >&2
  exit 2
fi
