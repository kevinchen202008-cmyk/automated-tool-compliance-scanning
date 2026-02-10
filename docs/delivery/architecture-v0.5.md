---
title: 工具合规扫描 Agent 服务 - 技术架构（阶段性交付）
version: 0.5
status: archived
date: 2026-02-09
delivery: 阶段性交付文档归档
---

# 系统技术架构 v0.5

## 1. 架构风格与分层

- **风格**：单体 Web 服务，按“微服务式”职责划分模块，便于后续拆成多服务。
- **分层**：
  - **接入层**：HTTP（FastAPI），浏览器访问 `/ui`，REST API 挂载在 `/api/v1/`。
  - **应用层**：扫描任务编排（Scan Service）、报告生成与工具信息库更新建议（Report Service）。
  - **领域层**：合规规则与评分（Compliance Engine）、TOS 分析流程（TOS Service）、工具信息库差异与更新逻辑（KB Diff Service）。
  - **基础设施层**：AI 调用（AI Client）、数据库与会话（SQLAlchemy + SQLite/MySQL）、配置（config.yaml）、日志（Loguru）。

---

## 2. 技术栈

| 层次 | 技术 |
|------|------|
| **后端** | Python 3.9+，FastAPI |
| **数据** | SQLAlchemy ORM；MVP 用 SQLite，可切换 MySQL |
| **AI** | 默认 GLM 官方 Open API（httpx 异步调用），可配置 model/timeout 等 |
| **配置** | YAML（config.yaml）+ Pydantic，支持环境变量覆盖 |
| **前端** | 单页静态 HTML（`/ui` → `static/index.html`），原生 JS，无构建 |
| **日志** | Loguru，可输出到文件并轮转 |

---

## 3. 核心组件与职责

```
                    ┌─────────────────────────────────────────┐
                    │            Web UI (静态单页)              │
                    │  工具输入 / 进度 / 结果卡片 / 工具信息库   │
                    └────────────────────┬────────────────────┘
                                         │ HTTP
                    ┌────────────────────▼────────────────────┐
                    │         FastAPI (接入层)                 │
                    │  /api/v1/tools, /scan, /reports,         │
                    │  /api/v1/knowledge-base, /ui, /health   │
                    └────────────────────┬────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
┌───────────────┐              ┌─────────────────┐              ┌─────────────────┐
│ Scan Service  │              │ Report Service  │              │ Knowledge Base  │
│ 任务编排      │──────────────│ 报告生成        │              │ 列表/详情/编辑   │
│ 并发控制      │              │ data_source     │              │ /删除/入库/更新  │
│ 进度更新      │              │ kb_update 建议  │              │ (API 实现)      │
└───────┬───────┘              └────────┬────────┘              └────────┬────────┘
        │                               │                               │
        │    ┌──────────────────────────┼───────────────────────────────┘
        │    │                          │
        ▼    ▼                          ▼
┌───────────────┐              ┌─────────────────┐              ┌─────────────────┐
│ TOS Service   │              │ Compliance      │              │ KB Diff Service │
│ TOS 搜索/拉取 │              │ Engine          │              │ 差异对比        │
│ AI 分析 TOS   │              │ 多维度评分      │              │ 更新建议构造    │
└───────┬───────┘              │ 报告结构组装    │              └────────┬────────┘
        │                      └────────┬────────┘                       │
        ▼                               │                               │
┌───────────────┐                       │                       ┌────────▼────────┐
│ AI Client     │◄─────────────────────┴───────────────────────│ Knowledge Base  │
│ GLM API 调用  │   (分析 TOS、替代方案、直接分析工具)           │ Service         │
│ 重试/超时     │                                               │ CRUD / 合并逻辑  │
└───────┬───────┘                                               └────────┬────────┘
        │                                                                │
        └────────────────────────────┬───────────────────────────────────┘
                                     ▼
                    ┌────────────────────────────────────┐
                    │  Storage (SQLite / MySQL)           │
                    │  Tool, ComplianceReport,            │
                    │  ToolKnowledgeBase, AlternativeTool │
                    └────────────────────────────────────┘
```

- **Scan Service**：接收工具 ID 列表，创建扫描任务，控制并发（Semaphore），按工具依次执行：拉取工具信息 → TOS 搜索/拉取/分析（TOS Service + AI Client）→ 合并工具信息库 → 替代方案补全 → Compliance Engine 生成报告并落库。
- **TOS Service**：负责 TOS URL 搜索、内容拉取、调用 AI 分析 TOS 内容；失败时降级为“AI 直接分析工具”。
- **AI Client**：封装 GLM（或可配置其他）调用，提供 TOS 分析、直接分析工具、替代方案推荐等；统一超时、重试与错误/429 日志。
- **Compliance Engine**：多维度评分（安全、许可证、维护性、性能、TOS），综合合规结论与建议，输出报告所需结构。
- **Report Service**：基于 ComplianceReport 与 TOS/工具信息库数据生成对外 JSON 报告，包含 `data_source`、`knowledge_base_update` 等；不直接写库，由前端确认后调用知识库 API。
- **Knowledge Base Service**：工具信息库 CRUD；与 **KB Diff Service** 配合，计算“新数据 vs 库内数据”差异，供 Report 生成“是否可入库/是否可更新”建议。
- **Web UI**：单页，调用 `/api/v1/tools/batch`、`/scan/start`、`/scan/status/:id`、`/reports/:id` 完成扫描与展示；根据 `knowledge_base_update` 调用 create-from-report / update-from-report；工具信息库浏览使用列表/详情/编辑/删除等 API。

---

## 4. 数据流要点

- **扫描链路**：输入工具名 → 批量创建/获取 Tool → 启动扫描 → 每工具：ToolInfo → TOS（搜索→拉取→AI 分析，失败则 AI 直接分析）→ 与工具信息库合并 → 替代方案补全 → Compliance Engine → Report Service 写 ComplianceReport 并生成 JSON。
- **报告内容**：工具元数据、许可/公司/商用限制/可替代方案、合规评分与结论、**data_source**（ai_analysis / knowledge_base）、**knowledge_base_update**（pending_creation / diff_available 等）。
- **工具信息库**：仅在前端“加入”或“更新差异”时调用 `create-from-report` / `update-from-report`；浏览、编辑、删除走独立 CRUD API，数据存 ToolKnowledgeBase 表。

---

## 5. 部署与配置

- **部署**：单进程运行（如 `python start_server.py`），可部署在本地 WSL 或公有云（阿里云/腾讯云/华为云等），通过 Nginx/ALB 暴露 HTTP。
- **配置**：`config/config.yaml`（参考 `docs/config-example.yaml`），包含 service、ai（GLM）、compliance 权重、database、logging、deployment、web 等；敏感信息（如 API Key）可通过环境变量覆盖，不提交仓库。

---

*本文档为 v0.5 阶段性交付归档，与当前实现对齐。后续版本见 `docs/architecture.md` 及交付目录。*
