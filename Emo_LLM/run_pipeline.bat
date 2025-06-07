@echo off
echo ========================================
echo 情感反馈全流程系统启动
echo ========================================

:: 检查是否指定了输入文本
if "%1"=="" (
    :: 没有指定输入，使用交互模式
    echo 启动交互模式...
    python full_pipeline.py --interactive
) else (
    :: 使用命令行输入
    echo 处理文本: %1
    python full_pipeline.py --input "%1"
)

echo.
echo 处理完成！
echo ========================================
pause 