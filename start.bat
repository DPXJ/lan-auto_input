@echo off
chcp 65001 >nul
title 自动填充工具启动器

echo ========================================
echo           自动填充工具启动器
echo ========================================
echo.
echo 请选择要启动的版本:
echo.
echo 1. 基础版本 (命令行)
echo 2. 高级版本 (系统托盘)
echo 3. GUI版本 (图形界面)
echo 4. 安装依赖
echo 5. 退出
echo.
set /p choice=请输入选择 (1-5): 

if "%choice%"=="1" (
    echo 启动基础版本...
    python auto_fill.py
) else if "%choice%"=="2" (
    echo 启动高级版本...
    python auto_fill_advanced.py
) else if "%choice%"=="3" (
    echo 启动GUI版本...
    python auto_fill_gui.py
) else if "%choice%"=="4" (
    echo 安装依赖...
    pip install -r requirements.txt
    echo 依赖安装完成！
    pause
) else if "%choice%"=="5" (
    echo 退出程序
    exit
) else (
    echo 无效选择，请重新运行程序
    pause
) 