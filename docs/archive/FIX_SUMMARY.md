# 修复总结：Docker Desktop 和 Anaconda 显示"未知"问题

## 问题分析

从数据库检查发现：
1. **Docker Desktop**：数据已保存（12个keys），包括 `license_type: "商业许可证"`、`license_mode: "商业"` 等
2. **Docker CE**：数据已保存（13个keys），包括 `license_type: "Apache 2.0"` 等
3. **Anaconda**：数据为空（0个keys），因为知识库中没有Anaconda的信息

## 已完成的修复

### 1. 添加 Anaconda 到知识库
- 许可证类型：商业许可证（个人版免费）
- 模式：混合
- 公司：Anaconda Inc.（美国）
- 商用限制：商业使用需要购买许可证
- 替代方案：Miniconda、Python + pip

### 2. 补充 Docker Desktop 的替代方案
- 添加了 `alternative_tools` 字段
- 替代方案：Docker CE、Podman

## 解决方案

### 方案1：重新扫描（推荐）
由于数据库中已有旧的报告数据（可能是在添加知识库之前生成的），需要重新扫描工具以获取最新数据：

1. 在Web界面重新输入并扫描：
   - Docker Desktop
   - Anaconda

2. 系统会：
   - 尝试AI分析（可能失败）
   - 自动从知识库获取信息
   - 保存完整的TOS分析结果

### 方案2：清理旧数据（可选）
如果需要清理旧的报告数据，可以删除数据库中的旧报告，然后重新扫描。

## 验证步骤

1. **重新扫描 Docker Desktop**：
   - 应该显示：许可证类型 = "商业许可证"
   - 模式 = "商业"
   - 公司 = "Docker Inc."
   - 有替代方案：Docker CE、Podman

2. **重新扫描 Anaconda**：
   - 应该显示：许可证类型 = "商业许可证（个人版免费）"
   - 模式 = "混合"
   - 公司 = "Anaconda Inc."
   - 有替代方案：Miniconda、Python + pip

3. **验证 Docker CE**（应该已经正常）：
   - 许可证类型 = "Apache 2.0"
   - 模式 = "开源"
   - 有替代方案：Podman、containerd

## 知识库当前内容

- ✅ Docker CE：完整信息 + 替代方案
- ✅ Docker Desktop：完整信息 + 替代方案（新增）
- ✅ Anaconda：完整信息 + 替代方案（新增）

## 注意事项

- 如果重新扫描后仍然显示"未知"，请检查：
  1. 服务是否已重启（加载新的知识库代码）
  2. 日志中是否有"已从知识库补充工具信息"的消息
  3. 数据库中 `tos_analysis` 字段是否包含完整数据
