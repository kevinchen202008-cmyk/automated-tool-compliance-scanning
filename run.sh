#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "=================================================="
echo "工具合规扫描 Agent - 一键运行"
echo "=================================================="

if ! command -v python3 &>/dev/null; then
  echo "[错误] 未找到 python3，请先安装 Python 3.10+"
  exit 1
fi

PY_VER=$(python3 -c 'import sys; print(sys.version_info[1])' 2>/dev/null || echo 0)
if [ "$PY_VER" -lt 10 ]; then
  echo "[错误] 需要 Python 3.10+"
  python3 --version
  exit 1
fi

if [ ! -d "venv" ]; then
  echo "[1/3] 创建虚拟环境 venv ..."
  python3 -m venv venv
fi
echo "[2/3] 安装依赖 ..."
# shellcheck source=/dev/null
. venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

mkdir -p config data logs
if [ ! -f "config/config.yaml" ] && [ -f "docs/config-example.yaml" ]; then
  echo "[提示] 已从 docs/config-example.yaml 复制到 config/config.yaml，请编辑 config/config.yaml 填入 GLM API Key。"
  cp docs/config-example.yaml config/config.yaml
elif [ ! -f "config/config.yaml" ]; then
  echo "[提示] 请创建 config/config.yaml 并填入 GLM API Key，否则将使用默认配置。"
fi

echo "[3/3] 启动服务 ..."
echo ""
python start_server.py
