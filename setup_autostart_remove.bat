@echo off
chcp 65001 >nul
title 取消自动填充工具开机启动

echo ========================================
echo     取消自动填充工具开机启动
echo ========================================
echo.

echo 正在取消开机启动设置...
echo.

:: 方法1: 删除任务计划程序任务
echo 方法1: 删除任务计划程序任务
schtasks /delete /tn "智能自动填充工具" /f >nul 2>&1
if not errorlevel 1 (
    echo ✓ 任务计划程序任务已删除
)

:: 方法2: 删除注册表项
echo 方法2: 删除注册表项
set "REG_KEY=HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
set "REG_VALUE=智能自动填充工具"
reg delete "%REG_KEY%" /v "%REG_VALUE%" /f >nul 2>&1
if not errorlevel 1 (
    echo ✓ 注册表项已删除
)

:: 方法3: 删除启动文件夹快捷方式
echo 方法3: 删除启动文件夹快捷方式
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\智能自动填充工具.lnk"

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%" >nul 2>&1
    if not errorlevel 1 (
        echo ✓ 启动文件夹快捷方式已删除
    )
)

echo.
echo ========================================
echo 开机启动已取消！
echo ========================================
echo.
echo 智能自动填充工具将不再开机自动启动
echo 如需重新设置开机启动，请运行: setup_autostart.bat
echo.
pause 