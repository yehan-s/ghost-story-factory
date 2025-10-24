#!/bin/bash
# 快速启动完整游戏脚本

# 禁用 CrewAI 遥测（避免30秒超时）
export OTEL_SDK_DISABLED=true

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          🎮 Ghost Story Factory - 完整版启动中...            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 检查并安装依赖
echo "📦 检查依赖..."
pip list | grep -q crewai
if [ $? -ne 0 ]; then
    echo "⚠️  CrewAI 未安装，正在安装（使用清华镜像源）..."
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple crewai langchain-community langchain-openai
    echo "✅ CrewAI 安装完成"
fi

# 检查故事资源
if [ ! -f "examples/hangzhou/杭州_GDD.md" ]; then
    echo ""
    echo "⚠️  未找到杭州故事资源"
    echo "正在使用 game_engine.py 启动（它会自动查找资源）..."
    echo ""
fi

# 启动游戏
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    🎭 游戏启动！                              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

python3 play_game_full.py

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                    👋 游戏结束                                 ║"
echo "╚══════════════════════════════════════════════════════════════════╝"

