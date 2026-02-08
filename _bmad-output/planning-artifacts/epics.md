---
stepsCompleted: [1, 2, 3]
inputDocuments: ["docs/prd.md", "docs/architecture.md"]
---

# tool-compliance-scanning-agent - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for tool-compliance-scanning-agent, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**4.1 工具合规扫描（FR-TOOL-SCAN）**
- FR-TOOL-SCAN-01：支持单个工具名输入
- FR-TOOL-SCAN-02：支持通过文本框/多行输入提交多个工具名
- FR-TOOL-SCAN-03：支持上传简单文本文件（每行一个工具名）（可选，非 MVP 必须）
- FR-TOOL-SCAN-04：对每个工具执行合规扫描并生成独立结果
- FR-TOOL-SCAN-05：系统能够通过 GLM AI 服务或联网搜索获取和分析工具的 TOS（服务条款）信息，以便更好地识别合规风险

**4.2 合规报告生成（FR-REPORT）**
- FR-REPORT-01：每个工具生成一份结构化报告，包含：工具名称、工具版本（如可获取）、合规性评分（0–100 或 A/B/C 等级）、合规性建议（文本）、合规性参考（链接或标准名称）、是否合规（是/否）、不合规原因列表、不合规时的开源替代建议（包含推荐理由）
- FR-REPORT-02：支持浏览器中查看报告
- FR-REPORT-03：支持导出 JSON 格式（MVP）
- FR-REPORT-04：为后续 HTML/PDF 报告预留接口

**4.3 合规规则引擎（FR-RULE-ENGINE）**
- FR-RULE-ENGINE-01：规则引擎可从配置文件加载合规标准与权重（参考 `config-example.yaml` 的 `compliance` 段）
- FR-RULE-ENGINE-02：规则评估至少覆盖：安全性（security）、许可证合规（license）、维护性/更新情况（maintenance）、基础性能/稳定性（performance，初期可以弱化）、TOS（服务条款）合规性（基于 TOS 信息分析结果）
- FR-RULE-ENGINE-03：评分算法可在配置中调整权重

**4.4 部署与访问（FR-DEPLOY-ACCESS）**
- FR-DEPLOY-01：支持在本地 WSL 环境部署
- FR-DEPLOY-02：支持在主流公有云（阿里云/腾讯云/华为云）使用容器/虚机部署
- FR-DEPLOY-03：MVP 阶段仅支持浏览器访问（`web.access_mode = browser_only`）
- FR-DEPLOY-04：为后续 API 访问预留路由与版本规范（如 `/api/v1/compliance/scan`）

**4.5 AI 大模型服务（FR-AI）**
- FR-AI-01：系统通过配置文件 `config.yaml` 读取 AI 配置（`ai` 段）
- FR-AI-02：默认使用 GLM 官方 Open API：`provider = glm`、`glm.api_base = "https://open.bigmodel.cn/api/paas/v4"`、`glm.model = "glm-4"`
- FR-AI-03：支持通过配置切换到 OpenAI/Azure/local 等其他 provider
- FR-AI-04：AI 返回结果必须经过规则引擎处理后再对用户展示
- FR-AI-05：系统能够使用 GLM AI 服务或联网搜索功能获取工具的 TOS（服务条款）信息，并进行分析以识别合规风险

**6.2 外部接口（MVP 展望）**
- API-GET `/health`：健康检查
- API-POST `/api/v1/compliance/scan`：提交工具名列表进行扫描（为第二阶段准备）

### NonFunctional Requirements

**5.1 性能（NFR-PERF）**
- NFR-PERF-01：单个工具扫描与报告生成时间 < 5 分钟（正常网络与模型延迟下）
- NFR-PERF-02：支持至少 5 个并发扫描请求（可配置）

**5.2 可用性（NFR-AVAIL）**
- NFR-AVAIL-01：服务可用性目标 > 99.5%（生产环境）

**5.3 安全（NFR-SEC）**
- NFR-SEC-01：不在日志中记录敏感信息（如 API Key、用户隐私）
- NFR-SEC-02：配置文件 `config.yaml` 不提交到 Git 仓库（已在 `.gitignore` 中配置）

**5.4 可运维性（NFR-OPS）**
- NFR-OPS-01：日志输出到文件并支持轮转（参考 `logging` 段）
- NFR-OPS-02：关键指标（请求量、错误率）预留采集点（后续可接入 Prometheus 等）

### Additional Requirements

**架构要求（来自 Architecture.md）**

**1. 架构风格与分层结构**
- 采用 Web 服务 + 后端微服务风格（单体起步，预留拆分）
- 分层结构：接入层（HTTP / 将来 API）、应用层（任务编排、报告生成）、领域层（合规规则引擎、评分模型）、基础设施层（AI 客户端、数据库、配置）

**2. 核心组件**
- Web UI：浏览器访问的前端（可先用简单模板/后端渲染）
- Scan Service：工具合规扫描服务
- Compliance Engine：合规规则与评分引擎
- AI Client：对接 GLM 官方 Open API（以及可选其他模型）
- Report Service：报告生成与导出
- Storage：SQLite / MySQL 等持久化存储

**3. 数据模型**
- Tool：id, name, version（可空）, source（internal / external / unknown）, tos_info（JSON/text，TOS 信息和分析结果）, tos_url（TOS 文档链接）
- ComplianceReport：id, tool_id, score_overall, score_security, score_license, score_maintenance, score_performance, score_tos（TOS 合规性评分）, is_compliant（boolean）, reasons（JSON/text）, recommendations（JSON/text）, references（JSON）, tos_analysis（JSON/text，TOS 分析结果）
- AlternativeTool：id, name, reason, link, license

**4. 技术选型建议**
- 后端框架：FastAPI / Flask / Express.js（择一）
- 数据库：SQLite（MVP）+ MySQL（云端扩展）
- 前端：后端模板渲染 或 轻量级 SPA（如 Vue/React，视资源而定）
- AI 调用：HTTP 客户端（requests / axios），封装为独立模块

**5. 部署要求**
- 本地 WSL 部署：在 WSL 环境中运行后端服务，使用本地端口映射
- 公有云部署：支持容器化部署（Docker + 云厂商容器服务）或直接部署在云服务器

**6. 配置管理**
- 主配置文件：`config.yaml`（根据 `docs/config-example.yaml` 创建）
- 配置块：service, ai, compliance, database, logging, deployment, web
- AI Client 封装：统一的调用接口、统一错误处理与重试逻辑

**7. 安全要求**
- 不在日志中记录敏感字段（如 API Key、用户私密数据）
- 对外 API 需要预留鉴权机制（Token / API Key），MVP 可暂不开启
- 部署在云环境时，建议结合云厂商的安全组 / WAF 能力

### FR Coverage Map

**工具合规扫描：**
- FR-TOOL-SCAN-01: Epic 2 - 单个工具名输入
- FR-TOOL-SCAN-02: Epic 2, Epic 6 - 多工具名输入（后端 + UI）
- FR-TOOL-SCAN-03: 可选，暂不包含在 MVP
- FR-TOOL-SCAN-04: Epic 2 - 独立扫描结果
- FR-TOOL-SCAN-05: Epic 2 - TOS 信息获取和分析

**合规报告生成：**
- FR-REPORT-01: Epic 5 - 结构化报告生成
- FR-REPORT-02: Epic 5, Epic 6 - 浏览器查看（后端 + UI）
- FR-REPORT-03: Epic 5 - JSON 导出
- FR-REPORT-04: 预留接口，暂不实现

**合规规则引擎：**
- FR-RULE-ENGINE-01: Epic 3 - 配置加载
- FR-RULE-ENGINE-02: Epic 3 - 多维度评估（包含 TOS 合规性）
- FR-RULE-ENGINE-03: Epic 3 - 权重调整

**部署与访问：**
- FR-DEPLOY-01: Epic 7 - WSL 部署
- FR-DEPLOY-02: Epic 7 - 公有云部署
- FR-DEPLOY-03: Epic 6 - 浏览器访问
- FR-DEPLOY-04: Epic 7 - API 预留

**AI 大模型服务：**
- FR-AI-01: Epic 1 - 配置读取
- FR-AI-02: Epic 4 - GLM 默认配置
- FR-AI-03: Epic 4 - 多 provider 支持
- FR-AI-04: Epic 4 - 结果处理
- FR-AI-05: Epic 2 - TOS 信息获取和分析（使用 GLM AI 或联网搜索）

**外部接口：**
- API-GET `/health`: Epic 7 - 健康检查
- API-POST `/api/v1/compliance/scan`: 第二阶段，暂不包含

## Epic List

### Epic 1: 项目初始化与基础架构
让系统能够运行起来，具备基础配置管理和数据存储能力。
**FRs covered:** FR-AI-01, 架构要求（数据模型、配置管理、技术选型）

### Epic 2: 工具合规扫描核心功能
用户可以输入单个或多个工具名，系统能够接收并处理扫描请求。
**FRs covered:** FR-TOOL-SCAN-01, FR-TOOL-SCAN-02, FR-TOOL-SCAN-04, FR-TOOL-SCAN-05, FR-AI-05

### Epic 3: 合规规则引擎
系统能够根据配置的合规规则评估工具，生成合规性评分。
**FRs covered:** FR-RULE-ENGINE-01, FR-RULE-ENGINE-02（包含 TOS 合规性评估）, FR-RULE-ENGINE-03

### Epic 4: AI 集成与智能分析
系统能够调用 AI 大模型获取合规建议和开源替代工具推荐。
**FRs covered:** FR-AI-02, FR-AI-03, FR-AI-04

### Epic 5: 合规报告生成与展示
用户可以查看包含完整合规信息的结构化报告，并导出为 JSON 格式。
**FRs covered:** FR-REPORT-01, FR-REPORT-02, FR-REPORT-03

### Epic 6: Web 界面与用户体验
用户可以通过浏览器访问系统，完成工具输入、查看报告等操作。
**FRs covered:** FR-DEPLOY-03, FR-TOOL-SCAN-02（UI 部分）

### Epic 7: 部署与运维支持
系统可以在本地 WSL 环境和公有云平台部署，具备健康检查和基础运维能力。
**FRs covered:** FR-DEPLOY-01, FR-DEPLOY-02, FR-DEPLOY-04, API-GET `/health`, NFR-OPS-01, NFR-OPS-02

## Epic 1: 项目初始化与基础架构

让系统能够运行起来，具备基础配置管理和数据存储能力。

### Story 1.1: 项目初始化和技术栈选择

As a 开发人员,  
I want 创建项目基础结构和选择合适的技术栈,  
So that 可以开始构建工具合规扫描服务。

**Acceptance Criteria:**

**Given** 项目目录为空或新创建  
**When** 初始化项目结构  
**Then** 创建以下目录结构：
- `src/` - 源代码目录
- `tests/` - 测试目录
- `docs/` - 文档目录（已存在）
- `config/` - 配置文件目录
- `logs/` - 日志目录
- `data/` - 数据存储目录

**And** 创建项目依赖管理文件（如 `requirements.txt` 或 `package.json`）  
**And** 选择并配置后端框架（FastAPI/Flask/Express.js 之一）  
**And** 创建基础的 README 和项目说明文档

### Story 1.2: 配置文件系统实现

As a 系统管理员,  
I want 系统能够从配置文件读取配置信息,  
So that 可以灵活配置服务参数而不需要修改代码。

**Acceptance Criteria:**

**Given** 存在 `docs/config-example.yaml` 配置文件模板  
**When** 系统启动时  
**Then** 系统能够读取 `config.yaml` 文件（如果不存在则使用默认值）  
**And** 支持读取以下配置块：`service`, `ai`, `compliance`, `database`, `logging`, `deployment`, `web`  
**And** 配置读取失败时提供清晰的错误信息  
**And** 实现配置验证逻辑，确保必需配置项存在

### Story 1.3: 数据库初始化和数据模型创建

As a 开发人员,  
I want 创建数据库和数据模型,  
So that 可以存储工具信息和合规报告。

**Acceptance Criteria:**

**Given** 已选择数据库类型（SQLite for MVP）  
**When** 系统首次启动时  
**Then** 自动创建数据库文件（如果不存在）  
**And** 创建 `Tool` 表，包含字段：`id`, `name`, `version`, `source`, `tos_info`, `tos_url`  
**And** 创建 `ComplianceReport` 表，包含字段：`id`, `tool_id`, `score_overall`, `score_security`, `score_license`, `score_maintenance`, `score_performance`, `score_tos`, `is_compliant`, `reasons`, `recommendations`, `references`, `tos_analysis`  
**And** 创建 `AlternativeTool` 表，包含字段：`id`, `name`, `reason`, `link`, `license`  
**And** 在 `Tool` 表中添加字段：`tos_info`（JSON/text）, `tos_url`（用于存储 TOS 信息）  
**And** 建立表之间的外键关系（ComplianceReport.tool_id -> Tool.id）

### Story 1.4: 日志系统实现

As a 运维人员,  
I want 系统具备日志记录和轮转功能,  
So that 可以追踪系统运行状态和排查问题。

**Acceptance Criteria:**

**Given** 系统已配置日志参数（来自 `config.yaml` 的 `logging` 段）  
**When** 系统运行时  
**Then** 日志输出到指定文件（`logs/agent_service.log`）  
**And** 支持日志级别配置（DEBUG, INFO, WARNING, ERROR）  
**And** 实现日志轮转功能（当文件达到 `max_bytes` 时自动轮转，保留 `backup_count` 个备份文件）  
**And** 确保不在日志中记录敏感信息（如 API Key）（NFR-SEC-01）

## Epic 2: 工具合规扫描核心功能

用户可以输入单个或多个工具名，系统能够接收并处理扫描请求。

### Story 2.1: 工具名输入接口实现

As a 用户,  
I want 能够输入单个工具名,  
So that 可以启动对该工具的合规扫描。

**Acceptance Criteria:**

**Given** 系统已启动并运行  
**When** 用户提交单个工具名（如 "Docker"）  
**Then** 系统能够接收并验证工具名输入（非空、有效字符）  
**And** 将工具名存储到 `Tool` 表中（如果不存在则创建新记录）  
**And** 返回工具 ID 用于后续扫描流程

### Story 2.2: 多工具名输入处理

As a 用户,  
I want 能够一次输入多个工具名,  
So that 可以批量扫描多个工具的合规性。

**Acceptance Criteria:**

**Given** 系统已实现单个工具名输入功能  
**When** 用户通过文本框/多行输入提交多个工具名（每行一个或逗号分隔）  
**Then** 系统能够解析并分割多个工具名  
**And** 为每个工具名创建独立的 `Tool` 记录  
**And** 返回所有工具 ID 列表用于后续批量扫描

### Story 2.3: 扫描服务基础框架

As a 系统,  
I want 具备扫描服务框架,  
So that 可以处理工具合规扫描请求。

**Acceptance Criteria:**

**Given** 系统已接收工具名输入  
**When** 启动扫描流程时  
**Then** 创建 `Scan Service` 模块，能够接收工具 ID 列表  
**And** 为每个工具创建独立的扫描任务  
**And** 支持并发扫描（至少 5 个并发，可配置）（NFR-PERF-02）  
**And** 实现扫描任务状态跟踪（pending, processing, completed, failed）

### Story 2.4: 工具信息获取

As a 扫描服务,  
I want 能够获取工具的基本信息,  
So that 可以为合规评估提供上下文。

**Acceptance Criteria:**

**Given** 工具名已输入到系统  
**When** 执行扫描时  
**Then** 尝试获取工具版本信息（如可通过公开 API 或数据库查询）  
**And** 如果无法获取版本，则标记为 "unknown"  
**And** 将工具信息（名称、版本、来源）存储到 `Tool` 表  
**And** 为后续的合规评估提供工具上下文

### Story 2.5: 工具 TOS 信息获取和分析

As a 合规规则引擎,  
I want 能够获取和分析工具的 TOS（服务条款）信息,  
So that 可以更准确地识别工具的合规风险。

**Acceptance Criteria:**

**Given** 工具信息已获取（Story 2.4）  
**When** 执行合规扫描时  
**Then** 系统能够通过以下方式之一获取工具的 TOS 信息：
- 使用 GLM AI 服务搜索和分析工具的 TOS 文档
- 通过联网搜索功能获取工具的官方 TOS 链接和内容

**And** 将获取的 TOS 信息存储到数据库（可在 `Tool` 表中添加 `tos_info` 字段或创建独立的 `ToolTOS` 表）  
**And** 使用 AI 服务分析 TOS 内容，识别潜在的合规风险点（如数据使用条款、隐私政策、服务限制等）  
**And** 将 TOS 分析结果传递给合规规则引擎用于评估（FR-AI-05）  
**And** 如果无法获取 TOS 信息，记录原因并继续其他维度的合规评估

## Epic 3: 合规规则引擎

系统能够根据配置的合规规则评估工具，生成合规性评分。

### Story 3.1: 合规规则配置加载

As a 系统管理员,  
I want 规则引擎能够从配置文件加载合规规则,  
So that 可以灵活调整合规标准和权重。

**Acceptance Criteria:**

**Given** 配置文件包含 `compliance` 配置段  
**When** 系统启动时  
**Then** 规则引擎能够读取合规标准列表（如 ISO27001, SOC2, GDPR, 等保2.0）  
**And** 读取评分权重配置（security, license, maintenance, performance）  
**And** 验证权重总和为 1.0（或提供默认权重）  
**And** 规则加载失败时提供清晰的错误信息

### Story 3.2: 多维度合规评估实现

As a 合规规则引擎,  
I want 能够从多个维度评估工具合规性,  
So that 可以生成全面的合规评分。

**Acceptance Criteria:**

**Given** 工具信息已获取，合规规则已加载，TOS 信息已分析（Story 2.5）  
**When** 执行合规评估时  
**Then** 评估安全性维度（security），检查已知漏洞、安全配置等  
**And** 评估许可证合规维度（license），检查许可证类型、兼容性等  
**And** 评估维护性维度（maintenance），检查更新频率、社区活跃度等  
**And** 评估性能/稳定性维度（performance），检查基础性能指标（初期可弱化）  
**And** 评估 TOS（服务条款）合规性维度，基于 TOS 分析结果检查数据使用、隐私政策、服务限制等合规风险点（FR-RULE-ENGINE-02）  
**And** 每个维度生成独立的评分（0-100 分）

### Story 3.3: 合规评分算法实现

As a 合规规则引擎,  
I want 能够根据配置的权重计算综合合规评分,  
So that 可以生成准确的合规性评分。

**Acceptance Criteria:**

**Given** 各维度评分已计算完成（包括 TOS 合规性评分），权重配置已加载  
**When** 计算综合合规评分时  
**Then** 根据配置的权重计算加权平均分：`score_overall = score_security * weight_security + score_license * weight_license + score_maintenance * weight_maintenance + score_performance * weight_performance + score_tos * weight_tos`（如果配置了 TOS 权重）  
**And** 根据综合评分判断是否合规（如评分 >= 70 为合规，可配置阈值）  
**And** 将评分结果存储到 `ComplianceReport` 表（包含 TOS 合规性评分）  
**And** 支持通过配置文件调整权重（包括 TOS 权重），无需修改代码

## Epic 4: AI 集成与智能分析

系统能够调用 AI 大模型获取合规建议和开源替代工具推荐。

### Story 4.1: AI Client 基础框架

As a 开发人员,  
I want 创建 AI Client 模块,  
So that 可以统一调用不同的 AI 大模型服务。

**Acceptance Criteria:**

**Given** 系统配置已包含 AI 配置段  
**When** 初始化 AI Client 时  
**Then** 创建统一的 AI Client 接口，支持不同 provider（GLM, OpenAI, Azure, local）  
**And** 实现统一的调用方法（如 `generate_compliance_suggestions(tools, context)`）  
**And** 实现统一的错误处理和重试逻辑（超时、网络错误等）  
**And** 确保不在日志中记录 API Key 等敏感信息（NFR-SEC-01）

### Story 4.2: GLM 官方 Open API 集成

As a 系统,  
I want 能够调用 GLM 官方 Open API,  
So that 可以获取智能合规分析和建议。

**Acceptance Criteria:**

**Given** 配置文件中已设置 GLM API 信息（`ai.provider = glm`, `glm.api_base`, `glm.api_key`, `glm.model`）  
**When** 调用 AI Client 生成合规建议时  
**Then** 使用 GLM 官方 Open API（`https://open.bigmodel.cn/api/paas/v4`）发送请求  
**And** 传递工具信息和合规评估上下文给 AI 模型  
**And** 解析 AI 返回的合规建议和开源替代工具推荐  
**And** 处理 API 调用失败的情况（网络错误、API 限制等）

### Story 4.3: 多 AI Provider 支持

As a 系统管理员,  
I want 能够通过配置切换不同的 AI 服务提供商,  
So that 可以根据需要选择最适合的 AI 模型。

**Acceptance Criteria:**

**Given** 配置文件支持多个 AI provider（GLM, OpenAI, Azure, local）  
**When** 系统启动时  
**Then** 根据 `ai.provider` 配置选择对应的 AI 服务  
**And** 支持切换到 OpenAI（如果配置了 `openai` 段）  
**And** 支持切换到 Azure OpenAI（如果配置了 `azure` 段）  
**And** 支持切换到本地模型（如果配置了 `local` 段）  
**And** 切换 provider 时无需修改代码，只需更新配置文件

### Story 4.4: AI 结果处理与规则引擎集成

As a 合规规则引擎,  
I want AI 返回的结果经过规则引擎处理,  
So that 确保 AI 建议符合合规标准并准确展示给用户。

**Acceptance Criteria:**

**Given** AI 已返回合规建议和开源替代工具推荐  
**When** 处理 AI 结果时  
**Then** 将 AI 建议传递给规则引擎进行验证和格式化  
**And** 提取开源替代工具信息并存储到 `AlternativeTool` 表  
**And** 将处理后的建议整合到合规报告中  
**And** 确保 AI 建议与规则引擎评分保持一致

## Epic 5: 合规报告生成与展示

用户可以查看包含完整合规信息的结构化报告，并导出为 JSON 格式。

### Story 5.1: 结构化报告生成

As a 用户,  
I want 系统能够生成包含完整合规信息的结构化报告,  
So that 可以全面了解工具的合规性状况。

**Acceptance Criteria:**

**Given** 工具合规扫描已完成  
**When** 生成合规报告时  
**Then** 报告包含以下字段：
- 工具名称（来自 Tool 表）
- 工具版本（来自 Tool 表，如可获取）
- 合规性评分（score_overall, score_security, score_license, score_maintenance, score_performance）
- 合规性建议（来自 AI 和规则引擎）
- 合规性参考（相关标准、文档或链接）
- 是否合规（is_compliant）
- 不合规原因列表（reasons）
- 开源替代建议（来自 AlternativeTool 表，包含推荐理由）

**And** 报告数据存储到 `ComplianceReport` 表

### Story 5.2: JSON 格式报告导出

As a 用户,  
I want 能够导出合规报告为 JSON 格式,  
So that 可以保存报告或与其他系统集成。

**Acceptance Criteria:**

**Given** 合规报告已生成  
**When** 用户请求导出 JSON 报告时  
**Then** 系统能够将报告数据序列化为标准 JSON 格式  
**And** JSON 包含所有报告字段（工具名称、版本、评分、建议、参考、合规状态、原因、替代建议）  
**And** JSON 格式符合标准规范，易于解析  
**And** 支持下载 JSON 文件到本地

### Story 5.3: 报告数据查询接口

As a 后端服务,  
I want 提供报告数据查询接口,  
So that 前端可以获取并展示报告内容。

**Acceptance Criteria:**

**Given** 合规报告已生成并存储  
**When** 前端请求报告数据时  
**Then** 提供 API 接口根据工具 ID 或报告 ID 查询报告  
**And** 返回完整的报告数据结构（JSON 格式）  
**And** 支持查询单个工具的报告  
**And** 支持查询多个工具的报告列表  
**And** 处理报告不存在的情况（返回 404 或空结果）

## Epic 6: Web 界面与用户体验

用户可以通过浏览器访问系统，完成工具输入、查看报告等操作。

### Story 6.1: Web 服务基础框架

As a 用户,  
I want 能够通过浏览器访问系统,  
So that 可以使用工具合规扫描服务。

**Acceptance Criteria:**

**Given** 后端服务已实现  
**When** 启动 Web 服务时  
**Then** 创建 HTTP 服务器，监听配置的端口（默认 8080）  
**And** 配置 CORS 支持（允许浏览器访问）  
**And** 提供基础路由结构（首页、扫描页面、报告页面）  
**And** 实现错误处理中间件，返回友好的错误信息

### Story 6.2: 工具输入界面

As a 用户,  
I want 在浏览器中输入工具名,  
So that 可以提交工具进行合规扫描。

**Acceptance Criteria:**

**Given** 用户访问工具输入页面  
**When** 用户输入工具名时  
**Then** 提供输入框支持单个工具名输入  
**And** 提供多行文本框支持多个工具名输入（每行一个或逗号分隔）  
**And** 实现输入验证（非空、有效字符）  
**And** 提供提交按钮，点击后发送扫描请求到后端  
**And** 显示扫描进度或状态提示

### Story 6.3: 报告展示界面

As a 用户,  
I want 在浏览器中查看合规报告,  
So that 可以了解工具的合规性状况。

**Acceptance Criteria:**

**Given** 合规报告已生成  
**When** 用户访问报告页面时  
**Then** 以清晰的格式展示所有报告字段：
- 工具名称和版本（突出显示）
- 合规性评分（可视化展示，如进度条或星级）
- 是否合规（醒目标识，如绿色/红色）
- 合规性建议（结构化展示）
- 不合规原因列表（如存在）
- 开源替代建议（如存在，包含链接）

**And** 提供导出 JSON 按钮  
**And** 界面响应式设计，适配不同屏幕尺寸

### Story 6.4: 错误处理和用户反馈

As a 用户,  
I want 系统提供清晰的错误提示和用户反馈,  
So that 可以了解操作结果和问题原因。

**Acceptance Criteria:**

**Given** 用户在使用 Web 界面  
**When** 发生错误时（如网络错误、扫描失败、工具名无效）  
**Then** 显示友好的错误提示信息  
**And** 提供错误原因说明（如 "工具名不能为空"、"扫描超时，请重试"）  
**And** 对于可恢复的错误，提供重试选项  
**And** 实现加载状态提示（扫描进行中时显示进度）

## Epic 7: 部署与运维支持

系统可以在本地 WSL 环境和公有云平台部署，具备健康检查和基础运维能力。

### Story 7.1: WSL 环境部署支持

As a 开发人员,  
I want 系统能够在 WSL 环境中部署和运行,  
So that 可以在本地开发环境中使用服务。

**Acceptance Criteria:**

**Given** WSL 环境已配置  
**When** 在 WSL 中部署系统时  
**Then** 提供部署脚本或说明文档  
**And** 系统能够在 WSL 中正常启动  
**And** 通过 `http://localhost:PORT` 可以在 Windows 浏览器中访问  
**And** 数据库文件存储在 WSL 文件系统中（路径可配置）  
**And** 日志文件正确写入到配置的日志目录

### Story 7.2: 健康检查接口实现

As a 运维人员,  
I want 系统提供健康检查接口,  
So that 可以监控系统运行状态。

**Acceptance Criteria:**

**Given** 系统已启动  
**When** 访问 `/health` 接口时  
**Then** 返回系统健康状态（200 OK 表示健康）  
**And** 响应包含系统基本信息（版本、运行时间等）  
**And** 检查关键组件状态（数据库连接、配置加载等）  
**And** 如果系统不健康，返回相应的错误状态码

### Story 7.3: 日志和监控指标预留

As a 运维人员,  
I want 系统具备日志记录和监控指标采集点,  
So that 可以进行系统监控和问题排查。

**Acceptance Criteria:**

**Given** 系统运行时  
**When** 发生关键操作时  
**Then** 记录请求量指标（扫描请求数、成功/失败数）  
**And** 记录错误率指标（错误请求数、错误类型）  
**And** 预留指标采集点，便于后续接入 Prometheus 等监控系统  
**And** 日志系统已实现（Story 1.4）正常工作  
**And** 关键操作都有日志记录（扫描开始、完成、失败等）

### Story 7.4: 公有云部署文档和配置

As a 系统管理员,  
I want 系统能够在公有云平台部署,  
So that 可以在生产环境中使用服务。

**Acceptance Criteria:**

**Given** 需要在公有云（阿里云/腾讯云/华为云）部署  
**When** 准备部署时  
**Then** 提供部署文档，说明容器化部署或虚拟机部署步骤  
**And** 支持 Docker 容器化（提供 Dockerfile）  
**And** 配置文件支持云环境配置（数据库、存储路径等）  
**And** 提供环境变量配置方式（用于云平台配置管理）  
**And** 说明安全组和网络配置要求
