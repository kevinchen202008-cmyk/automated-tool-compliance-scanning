# 项目上下文 (Project Context)

## 项目概述
**项目名称**: 工具合规扫描 Agent 服务 (Tool Compliance Scanning Agent Service)  
**项目类型**: Agent Service  
**开发方法论**: BMAD (BMad Method Agile-AI Driven-Development)  
**创建日期**: 2026-02-06

## 项目目标
开发一个智能化的工具合规扫描agent服务，能够：
- 自动扫描和检测工具使用中的合规性问题
- 提供详细的合规性报告和建议
- 支持多种工具和合规标准的检查
- 提供可扩展的规则引擎

## 技术栈
（待确定 - 将在架构设计阶段确定）

## 开发规范

### 代码规范
- 遵循BMAD开发方法论
- 使用BMAD工作流进行开发
- 所有代码变更需要通过BMAD代码审查工作流

### 文档规范
- 所有文档使用中文（简体）
- 文档存放在 `docs/` 目录
- 规划产物存放在 `_bmad-output/planning-artifacts/`
- 实现产物存放在 `_bmad-output/implementation-artifacts/`

### 测试规范
- 使用ATDD（验收测试驱动开发）
- 遵循BMAD测试架构工作流
- 确保测试覆盖率

### Git规范
- 规划产物会被Git跟踪
- 其他输出文件会被忽略（见.gitignore）
- 遵循BMAD工作流状态跟踪

## BMAD工作流使用

### 当前阶段
项目初始化阶段

### 推荐工作流
1. **分析阶段**
   - 使用 `create-product-brief` 创建产品简介
   - 使用 `research` 进行市场和技术研究

2. **规划阶段**
   - 使用 `create-ux-design` 设计用户体验（如适用）
   - 使用 `prd` 创建产品需求文档

3. **解决方案阶段**
   - 使用 `create-architecture` 创建系统架构
   - 使用 `create-epics-and-stories` 创建Epic和Story

4. **实现阶段**
   - 使用 `dev-story` 开发Story
   - 使用 `code-review` 进行代码审查

## 重要路径
- 项目根目录: `{project-root}`
- BMAD输出: `{project-root}/_bmad-output`
- 项目文档: `{project-root}/docs`
- BMAD配置: `{project-root}/_bmad/_config`

## 注意事项
- 所有AI agent在实现代码时必须遵循此项目上下文
- 当存在冲突时，Story文件要求优先于项目上下文
- 定期更新此文件以反映项目当前状态
