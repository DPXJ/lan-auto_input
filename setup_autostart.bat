@echo off
chcp 65001 >nul
title 自动填充工具开机启动设置

echo ========================================
echo       自动填充工具开机启动设置
echo ========================================
echo.

:: 获取当前目录
set "CURRENT_DIR=%~dp0"
set "PYTHON_PATH=pythonw.exe"
set "SCRIPT_PATH=%CURRENT_DIR%smart_auto_fill_tray.py"

echo 当前目录: %CURRENT_DIR%
echo Python脚本: %SCRIPT_PATH%
echo.

:: 检查Python脚本是否存在
if not exist "%SCRIPT_PATH%" (
    echo 错误: 找不到 smart_auto_fill_tray.py 文件
    echo 请确保脚本文件在当前目录中
    pause
    exit /b 1
)

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 正在设置开机启动...
echo.

:: 创建启动命令
set "STARTUP_CMD=%PYTHON_PATH% "%SCRIPT_PATH%""

:: 方法1: 使用任务计划程序（推荐）
echo 方法1: 使用任务计划程序设置开机启动
schtasks /create /tn "智能自动填充工具" /tr "%STARTUP_CMD%" /sc onlogon /ru "%USERNAME%" /f >nul 2>&1
if errorlevel 1 (
    echo 任务计划程序设置失败，尝试方法2...
    goto method2
) else (
    echo ✓ 任务计划程序设置成功
    goto success
)

:method2
:: 方法2: 使用注册表
echo 方法2: 使用注册表设置开机启动
set "REG_KEY=HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run"
set "REG_VALUE=智能自动填充工具"
reg add "%REG_KEY%" /v "%REG_VALUE%" /t REG_SZ /d "%STARTUP_CMD%" /f >nul 2>&1
if errorlevel 1 (
    echo 注册表设置失败，尝试方法3...
    goto method3
) else (
    echo ✓ 注册表设置成功
    goto success
)

:method3
:: 方法3: 创建启动文件夹快捷方式
echo 方法3: 创建启动文件夹快捷方式
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\智能自动填充工具.lnk"

:: 创建VBS脚本来生成快捷方式
set "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_SCRIPT%"
echo sLinkFile = "%SHORTCUT_PATH%" >> "%VBS_SCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_SCRIPT%"
echo oLink.TargetPath = "%PYTHON_PATH%" >> "%VBS_SCRIPT%"
echo oLink.Arguments = "%SCRIPT_PATH%" >> "%VBS_SCRIPT%"
echo oLink.WorkingDirectory = "%CURRENT_DIR%" >> "%VBS_SCRIPT%"
echo oLink.Description = "智能自动填充工具" >> "%VBS_SCRIPT%"
echo oLink.Save >> "%VBS_SCRIPT%"

cscript //nologo "%VBS_SCRIPT%" >nul 2>&1
if errorlevel 1 (
    echo 快捷方式创建失败
    goto failed
) else (
    echo ✓ 启动文件夹快捷方式创建成功
    del "%VBS_SCRIPT%" >nul 2>&1
    goto success
)

:success
echo.
echo ========================================
echo 开机启动设置完成！
echo ========================================
echo.
echo 设置方法: %METHOD%
echo 启动命令: %STARTUP_CMD%
echo.
echo 下次开机时，智能自动填充工具将自动启动
echo 如需取消开机启动，请运行: setup_autostart_remove.bat
echo.
pause
exit /b 0

:failed
echo.
echo ========================================
echo 开机启动设置失败
echo ========================================
echo.
echo 请尝试以下方法手动设置:
echo 1. 按 Win+R，输入 shell:startup
echo 2. 将 smart_auto_fill.py 的快捷方式放入启动文件夹
echo 3. 或使用任务计划程序手动创建开机任务
echo.
pause
exit /b 1 