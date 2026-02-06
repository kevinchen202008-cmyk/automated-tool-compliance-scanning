# 工具合规扫描 Agent 服务

基于BMAD方法论开发的工具合规扫描agent服务。

## 项目概述

本项目旨在开发一个智能化的工具合规扫描agent服务，通过AI驱动的开发方法论（BMAD）来构建和维护。

## 项目结构

```
.
├── _bmad/                    # BMAD核心配置目录
│   ├── _config/             # BMAD配置文件
│   │   ├── agents/          # Agent自定义配置
│   │   └── custom/          # 自定义配置
│   └── _memory/            # BMAD内存配置
├── _bmad-output/            # BMAD输出目录
│   ├── planning-artifacts/  # 规划产物（Git跟踪）
│   ├── implementation-artifacts/  # 实现产物
│   └── bmb-creations/       # BMB创建的文件
├── docs/                    # 项目文档目录
├── BMAD-配置说明.md         # BMAD配置说明
├── 为什么使用BMAD.md        # BMAD使用说明
└── README.md                # 本文件
```

## BMAD配置

本项目已配置BMAD开发环境，包括：

- ✅ BMAD核心目录结构
- ✅ 配置文件（manifest.yaml等）
- ✅ Agent和工作流清单
- ✅ Git环境配置（.gitignore）

详细配置说明请参考 [BMAD-配置说明.md](./BMAD-配置说明.md)

## 快速开始

1. **安装BMAD模块**
   - 按照BMAD官方文档安装Core、BMB、BMM、CIS模块

2. **配置IDE集成**
   - 配置Cursor、OpenCode等IDE工具

3. **启动BMAD Master Agent**
   - 在Cursor中使用 `/bmad-master` 命令
   - 开始使用BMAD工作流进行开发

## 开发流程

使用BMAD方法论进行开发：

1. **分析阶段**: 使用产品简介和研究工作流
2. **规划阶段**: 使用UX设计和PRD工作流
3. **解决方案阶段**: 使用架构创建工作流
4. **实现阶段**: 使用Story开发、代码审查等工作流

## 参考项目

本项目参考了 `D:\Projects\Android and IOS program-GreenPrj` 的BMAD配置。

## 许可证

（待添加）
