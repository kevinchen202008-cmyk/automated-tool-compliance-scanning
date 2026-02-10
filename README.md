# 工具合规扫描 Agent 服务 (automated-tool-compliance-scanning)

基于BMAD方法论开发自动化工具合规扫描服务Agent，并提供工具使用方法。

## 项目概述

本项目旨在开发一个智能化的工具合规扫描agent服务，通过AI驱动的开发方法论（BMAD）来构建和维护。

## 技术栈

- **后端框架**: FastAPI (Python 3.9+)
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
│   └── main.py              # FastAPI 应用入口
├── tests/                    # 测试目录
├── config/                   # 配置文件目录
├── logs/                     # 日志目录
├── data/                     # 数据存储目录
├── docs/                     # 项目文档目录
│   ├── prd.md               # 产品需求文档
│   ├── architecture.md      # 架构设计文档
│   └── config-example.yaml  # 配置示例
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

编辑 `config/config.yaml`，填入 GLM API Key 等配置。

**4. 运行服务**

```bash
python start_server.py
```

### 访问服务

- **Web UI**（无需授权）: 默认 `http://localhost:8080/ui`（端口可在 `config/config.yaml` 的 `service.port` 中调整）  
- **API 文档**: `http://localhost:<port>/docs`  
- **健康检查**: `http://localhost:<port>/health`

## 开发流程

使用BMAD方法论进行开发：

1. **分析阶段**: 使用产品简介和研究工作流 ✅
2. **规划阶段**: 使用UX设计和PRD工作流 ✅
3. **解决方案阶段**: 使用架构创建工作流 ✅
4. **实现阶段**: 使用Story开发、代码审查等工作流 🚧

## 功能特性

- ✅ 工具合规扫描（基于工具名）
- ✅ 合规规则引擎
- ✅ AI 集成（GLM Open API）
- ✅ 合规报告生成
- ✅ TOS（服务条款）信息分析
- 🚧 Web 界面（开发中）
- 🚧 部署支持（开发中）

## 文档

- [产品需求文档](./docs/prd.md)
- [架构设计文档](./docs/architecture.md)
- [配置指南](./docs/config-guide.md)
- [Epics 和 Stories](./_bmad-output/planning-artifacts/epics.md)

## 许可证

（待添加）
