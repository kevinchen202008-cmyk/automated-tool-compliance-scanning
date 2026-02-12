# BMAD 配置说明

## 配置完成时间
2026-02-06

## 配置来源
参考项目：`D:\Projects\Android and IOS program-GreenPrj`

## 已安装的模块
- **Core**: BMAD 核心模块
- **BMB**: BMad Builder - Agent, Workflow 和 Module Builder
- **BMM**: BMad Method Agile-AI Driven-Development
- **CIS**: Creative Innovation Suite

## 已配置的 IDE 工具
- Cursor ⭐
- Google Antigravity ⭐
- OpenCode ⭐

## 目录结构

### 核心目录
- `_bmad/` - BMAD 核心文件目录
  - `_config/` - 配置文件
  - `_memory/` - 内存配置
  - `bmb/` - BMB 模块文件（待安装）
  - `bmm/` - BMM 模块文件（待安装）
  - `cis/` - CIS 模块文件（待安装）
  - `core/` - Core 模块文件（待安装）

### 输出目录
- `_bmad-output/` - BMAD 输出文件目录
  - `planning-artifacts/` - 规划产物
  - `implementation-artifacts/` - 实现产物
  - `bmb-creations/` - BMB 创建的文件

### 项目知识库
- `docs/` - 项目文档目录

### IDE 集成目录
- `.opencode/` - OpenCode 集成（agents 和 commands）（待创建）
- `.cursor/` - Cursor 集成（命令定义）（待创建）
- `.agent/` - Agent 工作流定义（待创建）

## 配置信息

### 用户信息
- 用户名: （待配置）
- 沟通语言: 中文 (China)
- 文档输出语言: 中文 (China)

### 项目信息
- 项目名称: tool-compliance-scanning-agent
- 项目类型: agent-service
- 项目描述: 基于BMAD方法论开发的工具合规扫描agent服务
- 用户技能水平: intermediate

### 路径配置
- 输出文件夹: `{project-root}/_bmad-output`
- 规划产物: `{project-root}/_bmad-output/planning-artifacts`
- 实现产物: `{project-root}/_bmad-output/implementation-artifacts`
- 项目知识库: `{project-root}/docs`
- BMB 创建输出: `{project-root}/_bmad-output/bmb-creations`

## 可用的 Agents

### Core Agents
- `core-bmad-master` - BMAD 主控 Agent

### BMM (BMad Method) Agents
（待安装BMM模块后可用）
- `bmm-analyst` - 分析师
- `bmm-architect` - 架构师
- `bmm-dev` - 开发者
- `bmm-pm` - 产品经理
- `bmm-sm` - Scrum Master
- `bmm-tea` - 测试架构师
- `bmm-tech-writer` - 技术文档编写者
- `bmm-ux-designer` - UX 设计师
- `bmm-quick-flow-solo-dev` - 快速流程独立开发者

### BMB (BMad Builder) Agents
（待安装BMB模块后可用）
- `bmb-agent-builder` - Agent 构建器
- `bmb-module-builder` - 模块构建器
- `bmb-workflow-builder` - 工作流构建器

### CIS (Creative Innovation Suite) Agents
（待安装CIS模块后可用）
- `cis-brainstorming-coach` - 头脑风暴教练
- `cis-creative-problem-solver` - 创意问题解决者
- `cis-design-thinking-coach` - 设计思维教练
- `cis-innovation-strategist` - 创新策略师
- `cis-presentation-master` - 演示大师
- `cis-storyteller` - 故事讲述者

## 可用的工作流

### Core 工作流
- 头脑风暴
- Party Mode

### BMM 工作流
（待安装BMM模块后可用）
- 分析阶段：产品简介、研究
- 规划阶段：UX 设计、Epic 和 Story 创建
- 解决方案阶段：架构创建
- 实现阶段：Story 开发、代码审查、Sprint 规划等
- 测试架构：ATDD、测试框架、CI 集成等
- 项目管理：工作流初始化、状态跟踪等

### CIS 工作流
（待安装CIS模块后可用）
- 设计思维
- 创新策略
- 问题解决
- 故事讲述

## 使用说明

1. **启动 BMAD Master Agent**
   - 在 Cursor 中使用 `/bmad-master` 命令
   - 或在 OpenCode 中激活 `bmad-agent-core-bmad-master`

2. **使用工作流**
   - 通过 Cursor 命令使用各种工作流
   - 例如：`/bmad-bmm-create-product-brief` 创建产品简介

3. **创建自定义 Agent/Workflow/Module**
   - 使用 BMB 模块的构建器来创建自定义内容

## 注意事项

- 所有输出文件将保存在 `_bmad-output/` 目录
- 项目文档应放在 `docs/` 目录
- 配置文件位于 `_bmad/_config/` 目录
- 如需自定义 Agent，请编辑 `_bmad/_config/agents/` 下的对应文件
- 规划产物（planning-artifacts）会被Git跟踪，其他输出文件会被忽略

## 版本信息
- BMAD 版本: 6.0.0-alpha.23
- 安装日期: 2026-02-06T21:17:00.000Z

## 下一步

1. 安装BMAD模块（Core, BMB, BMM, CIS）
2. 配置IDE集成（Cursor, OpenCode）
3. 开始使用BMAD工作流进行项目开发
