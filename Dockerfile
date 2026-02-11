FROM python:3.10-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# 安装运行依赖
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 默认配置路径（可通过环境变量 CONFIG_PATH 覆盖）
ENV CONFIG_PATH=/app/config/config.yaml

# 暴露默认端口（实际端口由 config/service.port 控制）
EXPOSE 8080

# 启动服务
CMD ["python", "start_server.py"]

