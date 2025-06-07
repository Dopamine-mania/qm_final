#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 激活conda环境（如果需要）
# source activate emoheal_conda_v2

# 运行测试脚本
python "$SCRIPT_DIR/test_model.py" "$@" 