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

## 快速开始

### 1. 环境要求

- Python 3.9+
- pip 或 conda

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置

复制配置示例文件并修改：

```bash
cp docs/config-example.yaml config/config.yaml
```

编辑 `config/config.yaml`，填入你的 GLM API Key 等配置。

### 4. 运行服务

```bash
# 开发模式
python src/main.py

# 或使用 uvicorn
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

### 5. 访问服务

- API 文档: http://localhost:8080/docs
- 健康检查: http://localhost:8080/health

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
