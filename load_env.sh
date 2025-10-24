#!/bin/bash
# 快速加载 .env 环境变量

export $(cat .env | grep -v '^#' | xargs)
echo "✅ 环境变量已加载"
echo "KIMI_API_KEY: ${KIMI_API_KEY:0:20}..."
