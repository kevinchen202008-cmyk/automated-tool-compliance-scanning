---
title: 工具合规扫描 Agent 服务 架构设计
version: 0.6.0
status: aligned-with-implementation
date: 2026-02-12
author: Architect (BMAD)
# 阶段性交付归档: v0.5 技术架构见 docs/delivery/architecture-v0.5.md
---

## 1. 架构概要

### 1.1 架构风格
- Web 服务 + 后端微服务风格（单体起步，预留拆分）
- 分层结构：
  - 接入层（HTTP / 将来 API）
  - 应用层（任务编排、报告生成）
  - 领域层（合规规则引擎、评分模型）
  - 基础设施层（AI 客户端、数据库、配置）

### 1.2 核心组件
- `Web UI`：浏览器访问的前端（当前为静态 `/ui` 单页），负责工具输入、进度展示与合规结果卡片展示
- `Scan Service`：工具合规扫描服务，负责任务编排、并发控制、进度更新
- `TOS Service`：TOS 信息搜索与拉取服务
- `AI Client`：对接 GLM 官方 Open API（以及可选其他模型），执行 TOS 分析与替代方案分析
- `Compliance Engine`：整理 AI / 工具信息库数据，生成合规报告所需结构（多维评分字段保留为后续扩展）
- `Tool Information Store`（工具信息库）：存放经用户确认的工具合规信息（数据库 `ToolKnowledgeBase` + 内置工具信息）
- `Report Service`：报告生成与导出，封装工具信息库更新建议
- `Storage`：SQLite / MySQL 等持久化存储

---

## 2. 逻辑架构

### 2.1 请求流程（工具扫描）

1. 用户在 Web UI 输入工具名或工具名列表
2. Web 层将请求发送到 `Scan Service`
3. `Scan Service`：
   - 解析工具名列表
   - 调用 `Compliance Engine` 执行规则检查
   - 视需要调用 `AI Client` 获取智能分析/建议/替代工具
4. `Compliance Engine`：
   - 读取配置（`config.yaml` 中的 `compliance` 段）
   - 根据安全、许可证、维护性等维度进行打分
5. `Report Service`：
   - 聚合规则检查结果与 AI 输出
   - 生成结构化报告实体（JSON）
   - 持久化到数据库（可选）
6. Web UI 将报告以页面形式展示，并提供 JSON 导出

### 2.2 前端交互说明（与工具信息库一致）

- **扫描结果卡片**：每个工具完成后展示使用许可、公司信息、商用限制、可替代方案；同时读取报告中的 `knowledge_base_update`。
- **新工具（pending_creation）**：提示“本次 AI 分析结果尚未写入工具信息库”，提供「将本次结果加入工具信息库」与「暂不保存，只查看本次结果」；仅用户点击加入时调用 `POST /api/v1/knowledge-base/{tool_name}/create-from-report?report_id=...`。
- **存量工具（diff_available）**：展示与工具信息库的差异摘要及字段级 changes；有差异时提供「用本次 AI 结果更新工具信息库差异」与「保持工具信息库不变」；仅用户点击更新时调用 `POST /api/v1/knowledge-base/{tool_name}/update-from-report?report_id=...`。
- **不操作**：选择暂不保存或保持不变时，不调用后端，工具信息库内容不变。

---

## 3. 部署架构

### 3.1 本地 WSL 部署

- 部署方式：
  - 在 WSL 环境中运行后端服务（如 Python/FastAPI 或 Node.js）
  - 使用本地端口映射，浏览器通过 `http://localhost:PORT` 访问
- 文件路径：
  - 参考 `deployment.wsl.base_path = "/mnt/d/Projects/tool compliance scanning agent"`

### 3.2 公有云部署

- 支持阿里云 / 腾讯云 / 华为云：
  - 容器化部署（Docker + 云厂商容器服务）或
  - 直接部署在云服务器（ECS/CVM/云主机）
- 通过 Nginx/ALB/SLB 暴露 HTTP 入口
- 数据库可选：
  - 单机 SQLite（小规模）
  - 云数据库 MySQL（中大规模）

---

## 4. 配置与秘密管理

### 4.1 配置文件

- 主配置文件：`config.yaml`（根据 `docs/config-example.yaml` 创建）
- 主要配置块：
  - `service`: 服务元数据与监听端口
  - `ai`: AI 大模型配置（默认 GLM）
  - `compliance`: 合规规则与权重
  - `database`: 数据库配置
  - `logging`: 日志配置
  - `deployment`: 部署环境
  - `web`: Web 访问与安全配置

### 4.2 AI Client 配置（GLM）

- 从 `config.yaml.ai.glm` 读取：
  - `api_base = "https://open.bigmodel.cn/api/paas/v4"`
  - `api_key`（从环境变量或安全存储加载）
  - `model = "glm-4"`
  - `temperature`, `max_tokens`, `timeout`
- `AI Client` 封装：
  - 统一的调用接口（如 `generate_compliance_suggestions(tools, context)`）
  - 统一错误处理与重试逻辑

---

## 5. 数据模型（高层）

### 5.1 Tool
- `id`
- `name`
- `version`（可空）
- `source`（internal / external / unknown）
- `tos_info`（JSON/text，TOS 信息和分析结果，新增）
- `tos_url`（TOS 文档链接，新增）

### 5.2 ComplianceReport
- `id`
- `tool_id`
- `score_overall`
- `score_security`
- `score_license`
- `score_maintenance`
- `score_performance`
- `score_tos`（TOS 合规性评分，新增）
- `is_compliant`（boolean）
- `reasons`（JSON/text）
- `recommendations`（JSON/text）
- `references`（JSON）
- `tos_analysis`（JSON/text，TOS 分析结果，新增）

### 5.3 AlternativeTool
- `id`
- `name`
- `reason`
- `link`
- `license`

---

## 6. 技术选型（当前实现）

- **后端框架**：FastAPI 0.128 + Uvicorn（Python 3.10+）
- **数据库**：SQLite（默认/开发）+ MySQL（云端扩展）
- **ORM**：SQLAlchemy 2.0+，Pydantic v2 配置校验
- **前端**：原生 HTML + JS SPA（`index.html` + 拆分的 JS 模块：`scan.js` / `kb-browse.js` / `utils.js`）
- **AI 调用**：httpx，封装为 `ai_client.py`（支持 GLM / OpenAI / Azure / Local 多 provider）
- **日志**：Loguru，支持敏感信息自动脱敏
- **CI/CD**：GitHub Actions（测试 + 安全扫描 + Docker 构建 + 阿里云 ECS 部署）
- **代码安全**：CodeQL（自动）+ bandit + pip-audit（CI 流水线）

### 6.1 后端模块结构（v0.6）

```
src/
├── main.py              # FastAPI 入口（lifespan 管理、路由注册）
├── config.py            # 配置管理（Pydantic models）
├── database.py          # 数据库引擎与会话管理
├── models.py            # SQLAlchemy ORM 模型
├── schemas.py           # Pydantic 请求/响应模型
├── logger.py            # 日志系统（敏感信息脱敏）
├── routers/             # API 路由模块
│   ├── tools.py         # /api/v1/tools（工具管理）
│   ├── scan.py          # /api/v1/scan, /api/v1/reports（扫描与报告）
│   └── knowledge_base.py # /api/v1/knowledge-base（工具信息库）
└── services/            # 业务逻辑层
    ├── scan_service.py  # 扫描任务编排
    ├── tos_service.py   # TOS 搜索与分析
    ├── ai_client.py     # AI 多 provider 客户端
    ├── compliance_engine.py # 合规引擎（多维评分，当前简化）
    ├── report_service.py # 报告生成与导出
    ├── knowledge_base_service.py # 工具信息库 CRUD
    ├── kb_diff_service.py # 工具信息库差异对比
    ├── tool_service.py  # 工具记录管理
    └── tool_knowledge_base.py # 内置工具信息 + 合并逻辑
```

---

## 7. 安全与合规考量

- 不在日志中记录敏感字段（如 API Key、用户私密数据）
- 对外 API 需要预留鉴权机制（Token / API Key），MVP 可暂不开启
- 部署在云环境时，建议结合云厂商的安全组 / WAF 能力

---

## 8. CI/CD 流水线架构

### 8.1 GitHub Actions 流水线（deploy-aliyun.yml）

```
push to main
    └── check-secrets        # 检查是否误提交敏感文件
          ├── test            # 71 个单元/集成测试 (pytest)
          └── security-scan   # pip-audit 依赖漏洞 + bandit 代码安全
                └── build-and-push-image  # Docker 构建 → 阿里云 ACR
                      └── deploy-to-ecs   # SSH → docker compose up
```

### 8.2 Branch Protection

- `main` 分支已配置保护规则：`check-secrets` / `test` / `security-scan` 必须全部通过
- 禁止强制推送和删除分支

### 8.3 CodeQL（codeql.yml）

- 自动扫描 Python / JavaScript / Actions 代码安全问题
- 每周定时扫描 + 每次 push/PR 触发

---

## 9. 后续演进方向

- 启用多维合规评分（`enable_multi_dimension_assessment: true`），需优化 AI 调用性能
- 将 `Scan Service` 与 `Compliance Engine` 拆分为独立微服务
- 引入消息队列（如 RabbitMQ/Kafka）处理大规模扫描任务
- 引入监控与告警系统（Prometheus + Grafana）

