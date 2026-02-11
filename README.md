# 工具合规扫描 Agent 服务 (automated-tool-compliance-scanning)

基于 BMAD 方法论构建的自动化工具合规扫描 Agent，支持「按工具名一键扫描」+「工具库浏览与维护」，并提供本地 / Docker / 阿里云 ECS 多种部署方式。

## 项目概述

本项目面向企业内部的工具合规管理场景，核心能力包括：

- 通过工具名称一键触发合规扫描（调用 GLM 等大模型解析 TOS / 协议说明）；
- 生成包含许可证、公司信息、商用限制、替代方案等关键信息的合规报告；
- 将高质量扫描结果沉淀到「工具库」，支持后续集中浏览、编辑、删除与导出；
- 提供 Web 界面与 CI/CD 流水线，支持在阿里云 ECS 上自动部署与更新服务。

## 技术栈

- **后端框架**: FastAPI (Python 3.10，兼容 3.9+)
- **数据库**: SQLite (MVP) + MySQL (云端扩展)
- **AI 服务**: GLM 官方 Open API (默认)
- **配置管理**: YAML + Pydantic
- **日志**: Loguru

## 项目结构

```
.
├── _bmad/                    # BMAD核心配置目录
│   ├── _config/             # BMAD配置文件
│   └── _memory/             # BMAD内存配置
├── _bmad-output/            # BMAD输出目录
│   ├── planning-artifacts/  # 规划产物（Git跟踪）
│   └── implementation-artifacts/  # 实现产物
├── src/                      # 源代码目录
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口（REST API + Web UI）
│   ├── services/            # 合规扫描、工具信息库、报告等业务服务
│   └── static/              # 前端单页 Web UI（合规扫描 + 工具库浏览）
├── tests/                    # 测试目录
├── config/                   # 配置文件目录（运行时挂载）
├── logs/                     # 日志目录（本地/容器挂载）
├── data/                     # 数据存储目录（SQLite 等）
├── docs/                     # 项目文档目录
│   ├── prd.md               # 产品需求文档
│   ├── architecture.md      # 当前架构设计文档
│   ├── delivery/            # 阶段性交付文档（如 architecture-v0.5.md）
│   ├── deploy-aliyun.md     # 阿里云部署指南（ACR + ECS + GitHub Actions）
│   └── config-example.yaml  # 通用配置示例（镜像内打包为 /app/config/config-example.yaml）
├── .github/workflows/
│   └── deploy-aliyun.yml    # Push 到 main 自动构建镜像并部署到阿里云 ECS
├── Dockerfile               # Docker 镜像构建脚本（python:3.10-slim + start_server.py）
├── requirements.txt         # Python 依赖
└── README.md                # 本文件
```

## 快速开始（下载即可运行）

### 方式一：一键运行（推荐）

克隆项目后，在项目根目录执行：

**Windows：**
```batch
run.bat
```

**Linux / macOS：**
```bash
chmod +x run.sh
./run.sh
```

脚本会自动：创建 Python 虚拟环境（venv）、安装依赖、若缺少则创建 `config`/`data`/`logs` 目录，并启动服务。首次运行若存在 `docs/config-example.yaml` 会复制为 `config/config.yaml`，请编辑该文件填入 **GLM API Key**（远程 GLM 配置保持不变即可）。

### 方式二：手动安装

**1. 环境要求**

- Python 3.9 或 3.10（项目内提供 `.python-version`，可用 pyenv/uv 等对齐版本）
- pip

**2. 安装依赖**

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
```

**3. 配置**

复制配置示例并修改（若仓库中有示例）：

```bash
mkdir -p config
cp docs/config-example.yaml config/config.yaml
```

编辑 `config/config.yaml`，至少完成以下字段：

- `service.port`：本地 Web UI 端口，建议保持为 `8080`；
- `ai.glm.api_key`：填写你的 GLM 官方 Open API Key；
- `database.path`：本地可保持 `./data/compliance.db`，云环境建议改为 `"/data/compliance.db"`。

**4. 运行服务**

```bash
python start_server.py
```

### 访问服务

- **Web UI**（无需认证）: 默认 `http://localhost:8080/ui`（可在 `config/config.yaml` → `service.port` 调整）  
- **API 文档**: `http://localhost:<port>/docs`  
- **健康检查**: `http://localhost:<port>/health`

## Docker 与阿里云部署（摘要）

项目内置 Docker 支持与 CI/CD 流程：

- 使用根目录下 `Dockerfile` 构建镜像：

  ```bash
  docker build -t tool-compliance-scanning:local .
  ```

- 本地使用 Docker 运行：

  ```bash
  docker run --rm -p 8080:8080 ^
    -v %cd%\config:/config ^
    -v %cd%\data:/data ^
    -v %cd%\logs:/logs ^
    -e CONFIG_PATH=/config/config.yaml ^
    tool-compliance-scanning:local
  ```

- 阿里云部署：
  - 通过 `.github/workflows/deploy-aliyun.yml`，在 push 到 `main` 时：
    - 构建 Docker 镜像并推送至阿里云 ACR；
    - 使用 SSH 登录指定 ECS，执行 `docker compose pull && docker compose up -d` 实现自动滚动更新。
  - 详细步骤与所需 Secrets / Variables 配置见 [`docs/deploy-aliyun.md`](./docs/deploy-aliyun.md)。

## 功能特性

- ✅ **合规扫描**
  - 按工具名称一键创建扫描任务，自动调用大模型解析 TOS/许可与使用说明；
  - 生成包含许可证类型、公司信息、商用限制、替代方案等关键信息的 JSON 报告。
- ✅ **工具库浏览与维护**
  - 在 Web 界面中按名称、许可/协议类型筛选已入库工具；
  - 查看/编辑工具的许可证、公司信息、数据使用、隐私策略、服务限制、风险点等字段；
  - 支持一键从扫描结果「加入工具库」或「基于扫描结果更新工具库」；
  - 支持导出当前过滤后的工具列表为 CSV，方便线下复核。
- ✅ **配置与日志**
  - 基于 YAML + Pydantic 的强类型配置，支持默认值与格式校验；
  - 使用 Loguru 输出结构化日志，落盘到 `logs/`（容器内可挂载到 `/logs`），并自动轮转。
- ✅ **部署支持**
  - 支持本地 venv 运行、Docker 镜像、阿里云 ACR + ECS 自动部署；
  - 镜像内预置 `config-example.yaml`，ECS 上可通过 `docker cp` 快速恢复示例配置。

## 开发与方法论

本项目采用 BMAD 方法论推进：

1. **分析阶段**：梳理企业工具合规场景、角色与数据流 ✅  
2. **规划阶段**：编写 PRD、交互设计、用例与数据模型 ✅  
3. **解决方案阶段**：完成 v0.5 / v0.6 架构与交付文档（见 `docs/delivery/`）✅  
4. **实现阶段**：持续迭代合规扫描、工具库、部署与运维能力（进行中） ✅

## 文档

- [产品需求文档](./docs/prd.md)
- [架构设计文档](./docs/architecture.md)
- [配置指南](./docs/config-guide.md)
- [阿里云部署指南](./docs/deploy-aliyun.md)
- [v0.5 架构交付文档](./docs/delivery/architecture-v0.5.md)
- [Epics 和 Stories](./_bmad-output/planning-artifacts/epics.md)

## 许可证

（待添加）
