#!/bin/bash

# Ghost Story Factory - 完整故事生成脚本
# 用法: ./generate_full_story.sh 武汉

if [ -z "$1" ]; then
    echo "错误: 请提供城市名称"
    echo "用法: ./generate_full_story.sh <城市名>"
    echo "示例: ./generate_full_story.sh 武汉"
    exit 1
fi

CITY=$1
OUTPUT_DIR="deliverables/程序-${CITY}"

echo "==========================="
echo "Ghost Story Factory v3.1"
echo "目标城市: ${CITY}"
echo "输出目录: ${OUTPUT_DIR}"
echo "==========================="
echo ""

# 调用Python生成器
python generate_full_story.py --city "${CITY}" --output "${OUTPUT_DIR}"

echo ""
echo "==========================="
echo "✅ 完成！"
echo "所有文件已保存到: ${OUTPUT_DIR}"
echo "==========================="
