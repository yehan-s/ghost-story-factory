#!/bin/bash

echo "═══════════════════════════════════════"
echo "未完成的生成任务"
echo "═══════════════════════════════════════"

if [ ! -d "checkpoints" ] || [ -z "$(ls -A checkpoints 2>/dev/null)" ]; then
    echo "❌ 没有未完成的生成任务"
    exit 0
fi

for file in checkpoints/*_characters.json; do
    if [ -f "$file" ]; then
        city=$(basename "$file" | sed 's/_characters.json//')

        if command -v jq &> /dev/null; then
            completed=$(jq -r '.completed_count' "$file" 2>/dev/null || echo "?")
            total=$(jq -r '.total_count' "$file" 2>/dev/null || echo "?")
        else
            completed="?"
            total="?"
        fi

        echo ""
        echo "📍 城市：$city"
        echo "   进度：$completed/$total 个角色"
        echo "   提示：重新运行时输入 '$city'"
    fi
done

echo ""
echo "═══════════════════════════════════════"

