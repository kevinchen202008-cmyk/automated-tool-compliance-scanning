# 🤖 自动化工具合规扫描 Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-0.128-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/LLM-GLM%20%7C%20Claude%20%7C%20Gemini-blueviolet?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Docker-ready-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
  <img src="https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white"/>
</p>

<p align="center">
  <b>基于 BMAD 方法论构建的企业级 AI Agent，一键完成第三方工具的合规风险扫描与报告生成</b>
</p>

---

## 🎯 项目背景

企业在采购或使用第三方工具时，需要评估其许可证合规性、商用限制、数据安全条款等。传统方式依赖人工查阅文档，效率低、易遗漏。本项目通过 LLM Agent 自动化这一流程：

- ⏱ **效率提升**：从人工数小时 → AI 几十秒完成扫描
- 📋 **标准化输出**：统一格式的合规报告，可导出存档
- 🏢 **企业就绪**：支持工具库管理、CI/CD 集成、Docker 部署

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🔍 **一键合规扫描** | 输入工具名称，AI 自动分析 TOS/协议，生成完整合规报告 |
| 📊 **结构化报告** | 包含许可证类型、商用限制、数据条款、替代方案等关键字段 |
| 🗃 **工具知识库** | 沉淀历史扫描结果，支持浏览、编辑、删除、导出 |
| 🌐 **Web 界面** | 开箱即用的前端，无需额外配置 |
| 🔄 **CI/CD 集成** | GitHub Actions 自动部署到阿里云 ECS |
| 🐳 **Docker 支持** | 容器化部署，环境一致性保障 |

---

## 🖥 Demo

```
输入: "Slack"

输出合规报告:
  ✅ 许可证类型:    商业软件（免费层 + 付费层）
  ⚠️  商用限制:     免费层功能受限，企业使用需付费订阅
  🔐 数据条款:     数据存储于美国服务器，受 GDPR/CCPA 约束
  🔄 替代方案:     飞书、钉钉、Mattermost（开源自托管）
  📅 扫描时间:     2026-04-21 08:00:00
```

---

## 🚀 快速开始

### 方式一：一键运行（推荐）

```bash
git clone https://github.com/kevinchen202008-cmyk/automated-tool-compliance-scanning.git
cd automated-tool-compliance-scanning

# Linux / macOS
chmod +x run.sh && ./run.sh

# Windows
run.bat
```

脚本自动完成：创建虚拟环境 → 安装依赖 → 复制配置模板 → 启动服务

访问 http://localhost:8000 打开 Web 界面。

### 方式二：Docker

```bash
docker build -t tool-compliance-scanner .
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  tool-compliance-scanner
```

### 方式三：手动安装

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp docs/config-example.yaml config/config.yaml
# 编辑 config/config.yaml，填入 LLM API Key
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## ⚙️ 配置

编辑 `config/config.yaml`：

```yaml
llm:
  provider: glm          # 支持: glm / claude / gemini
  api_key: YOUR_API_KEY
  model: glm-4-flash

server:
  host: 0.0.0.0
  port: 8000

database:
  type: sqlite           # MVP 默认 SQLite，生产可切换 MySQL
  path: data/compliance.db
```

---

## 🏗 项目架构

```
automated-tool-compliance-scanning/
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── routers/             # API 路由（scan / kb / report）
│   ├── services/            # 核心业务逻辑
│   │   ├── scanner.py       # LLM 驱动的合规扫描服务
│   │   ├── kb_service.py    # 工具知识库 CRUD
│   │   └── report.py        # 报告生成与导出
│   └── static/              # Web 前端（HTML + JS）
├── config/                  # 运行时配置
├── docs/                    # 架构文档、部署指南、PRD
├── tests/                   # 单元测试 + API 测试
├── .github/workflows/       # CI/CD（部署 + CodeQL 安全扫描）
├── Dockerfile
└── requirements.txt
```

---

## 📡 API 文档

启动后访问 http://localhost:8000/docs 查看完整 Swagger API 文档。

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/scan` | POST | 触发工具合规扫描 |
| `/api/kb` | GET | 获取工具知识库列表 |
| `/api/kb/{id}` | GET/PUT/DELETE | 知识库条目管理 |
| `/api/report/{id}` | GET | 获取扫描报告 |

---

## 🛠 技术栈

- **后端**：FastAPI 0.128 + Python 3.10+
- **AI**：GLM / Claude / Gemini（可配置切换）
- **数据库**：SQLite（MVP）→ MySQL（生产）
- **日志**：Loguru
- **配置**：YAML + Pydantic
- **部署**：Docker + GitHub Actions + 阿里云 ECS
- **安全**：CodeQL 自动安全扫描

---

## 🗺 Roadmap

- [x] v0.5 — 核心扫描功能 + Web UI + 工具知识库
- [x] v1.0 — Docker 支持 + CI/CD + 阿里云 ECS 自动部署
- [ ] v1.1 — 多 LLM 并行扫描 + 结果对比
- [ ] v1.2 — 批量扫描 + 定时自动扫描
- [ ] v2.0 — 企业级多租户 + 审批流程

---

## 🤝 Contributing

欢迎 Issue 和 PR！请查阅 [开发文档](docs/architecture.md) 了解架构设计。

---

## 📄 License

MIT License — 详见 [LICENSE](LICENSE)

---

<p align="center">
  Built with ❤️ using <a href="https://github.com/bmadcode/bmad-method">BMAD Methodology</a> + Claude Code
</p>
