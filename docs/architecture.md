---
title: 工具合规扫描 Agent 服务 架构设计
version: 0.1.0
status: draft
date: 2026-02-06
author: Architect (BMAD)
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
- `Web UI`：浏览器访问的前端（可先用简单模板/后端渲染）
- `Scan Service`：工具合规扫描服务
- `Compliance Engine`：合规规则与评分引擎
- `AI Client`：对接 GLM 官方 Open API（以及可选其他模型）
- `Report Service`：报告生成与导出
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

## 6. 技术选型（候选）

> 具体技术栈可在实现阶段由 Dev / Architect 进一步细化，这里给出初步建议。

- 后端框架：FastAPI / Flask / Express.js（择一）
- 数据库：SQLite（MVP）+ MySQL（云端扩展）
- 前端：后端模板渲染 或 轻量级 SPA（如 Vue/React，视资源而定）
- AI 调用：HTTP 客户端（requests / axios），封装为独立模块

---

## 7. 安全与合规考量

- 不在日志中记录敏感字段（如 API Key、用户私密数据）
- 对外 API 需要预留鉴权机制（Token / API Key），MVP 可暂不开启
- 部署在云环境时，建议结合云厂商的安全组 / WAF 能力

---

## 8. 后续演进方向

- 将 `Scan Service` 与 `Compliance Engine` 拆分为独立微服务
- 引入消息队列（如 RabbitMQ/Kafka）处理大规模扫描任务
- 引入监控与告警系统（Prometheus + Grafana）

