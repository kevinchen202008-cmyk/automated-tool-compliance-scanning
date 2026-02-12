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

# 复制示例配置，便于在 ECS 上通过 docker cp 获取
COPY docs/config-example.yaml /app/config/config-example.yaml

# 创建持久化目录（与 docker-compose volume 挂载点对齐）
# 容器内路径: /app/data, /app/logs — 通过 volume 映射到宿主机
RUN mkdir -p /app/data /app/logs

# 默认配置路径（可通过环境变量 CONFIG_PATH 覆盖）
ENV CONFIG_PATH=/app/config/config.yaml

# 声明数据卷（提示运维需要挂载这些目录以持久化数据）
VOLUME ["/app/data", "/app/logs", "/app/config"]

# 暴露默认端口（实际端口由 config/service.port 控制）
EXPOSE 8080

# 启动服务
CMD ["python", "start_server.py"]

