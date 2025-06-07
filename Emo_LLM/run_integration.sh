#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 如果需要，激活conda环境
# source activate emoheal_conda_v2

# 检查是否提供了输入文本
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 \"用户输入文本\""
    echo "Example: $0 \"我今天心情不太好，感到有点焦虑\""
    exit 1
fi

# 运行集成示例脚本
python "$SCRIPT_DIR/integration_example.py" --input "$1" --output_dir "$SCRIPT_DIR/../output"

# 如果成功，提示输出目录
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 集成示例运行成功！"
    echo "  输出文件保存在: $SCRIPT_DIR/../output"
fi 