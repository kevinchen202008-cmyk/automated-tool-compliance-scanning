@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ==================================================
echo 工具合规扫描 Agent - 一键运行
echo ==================================================

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.9 或 3.10。
    echo 建议: 从 https://www.python.org/downloads/ 安装并勾选 "Add Python to PATH"
    exit /b 1
)

for /f "tokens=2 delims=: " %%v in ('python -c "import sys; print(sys.version_info[0], sys.version_info[1])" 2^>nul') do set PY_MIN=%%v
if "%PY_MIN%" lss "9" (
    echo [错误] 需要 Python 3.9+，当前可能版本较低。
    python --version
    exit /b 1
)

if not exist "venv" (
    echo [1/3] 创建虚拟环境 venv ...
    python -m venv venv
    if errorlevel 1 ( echo 创建 venv 失败 & exit /b 1 )
)
echo [2/3] 安装依赖 ...
call venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 ( echo 安装依赖失败 & exit /b 1 )

if not exist "config" mkdir config
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "config\config.yaml" (
    if exist "docs\config-example.yaml" (
        echo [提示] 已从 docs\config-example.yaml 复制到 config\config.yaml，请编辑 config\config.yaml 填入 GLM API Key。
        copy "docs\config-example.yaml" "config\config.yaml" >nul
    ) else (
        echo [提示] 请创建 config\config.yaml 并填入 GLM API Key，否则扫描将使用默认配置。
    )
)

echo [3/3] 启动服务 ...
echo.
python start_server.py
endlocal
