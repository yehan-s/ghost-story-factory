#!/bin/bash
# Ghost Story Factory - 完整游戏启动脚本

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     Ghost Story Factory - 完整游戏引擎启动                     ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  未找到虚拟环境"
    echo "正在创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 加载本地环境变量（如果存在）
if [ -f "./load_env.sh" ]; then
    source ./load_env.sh
    echo "✅ 已加载本地环境变量"
fi

# 生成相关的默认阈值/并发（可被外部环境覆盖）
export MIN_DURATION_MINUTES=${MIN_DURATION_MINUTES:-12}
export MIN_MAIN_PATH_DEPTH=${MIN_MAIN_PATH_DEPTH:-30}
export MAX_DEPTH=${MAX_DEPTH:-50}
export MAX_TOTAL_NODES=${MAX_TOTAL_NODES:-300}
export PROGRESS_PLATEAU_LIMIT=${PROGRESS_PLATEAU_LIMIT:-2}
export MAX_RETRIES=${MAX_RETRIES:-0}
export AUTO_RESTART_ON_FAIL=${AUTO_RESTART_ON_FAIL:-0}
export KIMI_CONCURRENCY=${KIMI_CONCURRENCY:-1}
export KIMI_CONCURRENCY_CHOICES=${KIMI_CONCURRENCY_CHOICES:-1}

# 显式避免误用 OpenAI 直连（我们走 Kimi 的 OpenAI 兼容接口）
unset OPENAI_API_KEY
unset OPENAI_BASE_URL

# 检查依赖
echo "📦 检查依赖..."
python3 -c "import pydantic, rich" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖包"
    echo "正在安装基础依赖..."
    pip install -q pydantic rich python-dotenv
    echo "✅ 基础依赖已安装"
fi

python3 -c "import crewai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少 CrewAI"
    echo ""
    echo "完整游戏需要 CrewAI 和 Kimi API"
    echo "是否安装？(y/n)"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        echo "正在安装 CrewAI..."
        pip install -q crewai langchain-community langchain-openai
        echo "✅ CrewAI 已安装"
    else
        echo "❌ 无法运行完整游戏"
        echo ""
        echo "提示：你可以运行演示版："
        echo "  python3 play_game_correct.py"
        exit 1
    fi
fi

# 检查 API Key
if [ -z "$KIMI_API_KEY" ] && [ -z "$MOONSHOT_API_KEY" ]; then
    echo ""
    echo "⚠️  未找到 Kimi API Key"
    echo ""
    echo "请设置环境变量："
    echo "  export KIMI_API_KEY=your_key_here"
    echo ""
    echo "或创建 .env 文件："
    echo "  echo 'KIMI_API_KEY=your_key_here' > .env"
    echo ""
    echo "获取 API Key: https://platform.moonshot.cn/"
    echo ""
    exit 1
fi

# 检查故事资源
if [ ! -f "examples/hangzhou/杭州_GDD.md" ] || [ ! -f "examples/hangzhou/杭州_lore_v2.md" ]; then
    echo ""
    echo "⚠️  未找到杭州故事资源"
    echo ""
    echo "是否现在生成？(y/n)"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        echo "正在生成杭州故事..."
        gen-complete --city 杭州 --index 1
        if [ $? -eq 0 ]; then
            echo "✅ 故事资源已生成"
        else
            echo "❌ 生成失败"
            exit 1
        fi
    else
        echo "❌ 缺少故事资源，无法运行"
        exit 1
    fi
fi

# 启动游戏
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    🎮 启动游戏...                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
python3 play_game_full.py

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    👋 感谢游玩！                               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

