#!/bin/bash
echo "正在启动情感视频生成系统..."
echo ""

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 启动Flask应用
python app.py 