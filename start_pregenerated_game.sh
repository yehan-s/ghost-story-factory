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

# 禁用 CrewAI 遥测（避免30秒超时）
export OTEL_SDK_DISABLED=true

# 检查依赖
echo "📦 检查依赖..."
pip install -q rich crewai

# 启动游戏
echo "🎮 启动游戏..."
echo ""
python3 play_game_pregenerated.py

# 退出虚拟环境
deactivate

