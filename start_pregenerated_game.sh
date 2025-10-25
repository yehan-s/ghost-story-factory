
#!/bin/bash

# Ghost Story Factory - 预生成模式启动脚本

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          Ghost Story Factory - 预生成模式                       ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安装"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 加载本地环境变量（如果存在）
if [ -f "./load_env.sh" ]; then
    source ./load_env.sh
fi

# 禁用 CrewAI 遥测（避免30秒超时）
export OTEL_SDK_DISABLED=true

# 生成相关的默认阈值/并发（可被外部环境覆盖）
export MIN_DURATION_MINUTES=${MIN_DURATION_MINUTES:-10}
export MIN_MAIN_PATH_DEPTH=${MIN_MAIN_PATH_DEPTH:-30}
export MAX_DEPTH=${MAX_DEPTH:-50}
export KIMI_CONCURRENCY=${KIMI_CONCURRENCY:-1}
export KIMI_CONCURRENCY_CHOICES=${KIMI_CONCURRENCY_CHOICES:-1}
export MAX_TOTAL_NODES=${MAX_TOTAL_NODES:-300}
export PROGRESS_PLATEAU_LIMIT=${PROGRESS_PLATEAU_LIMIT:-2}
export MAX_RETRIES=${MAX_RETRIES:-0}
export AUTO_RESTART_ON_FAIL=${AUTO_RESTART_ON_FAIL:-0}

# 显式避免误用 OpenAI 直连（我们走 Kimi 的 OpenAI 兼容接口）
unset OPENAI_API_KEY
unset OPENAI_BASE_URL

# 检查依赖
echo "📦 检查依赖..."
pip install -q rich crewai

# 启动游戏
echo "🎮 启动游戏..."
echo ""
python3 play_game_pregenerated.py

# 退出虚拟环境
deactivate

