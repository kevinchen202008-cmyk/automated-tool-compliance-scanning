# 交付件自检（BMAD 流程）

> 自检日期：按执行日  
> 目的：前后逻辑一致、交付相对完整

## 1. 需求与规划一致性

| 来源 | 要点 | 实现/文档对齐 |
|------|------|----------------|
| **user demand.ini** | 工具名列表 → 合规报告；报告字段（许可、公司、商用限制、替代方案）；AI 优先分析 TOS；**新工具经用户确认后保存到工具信息库**；**存量工具经用户确认是否更新差异**；可浏览、按名字母序、定期清理 | ✅ PRD §6、架构 2.2、前端结果卡片与 create/update-from-report API 一致 |
| **user demand.ini** | 工具信息库保存信息示例（许可、公司、商用、可替代方案） | ✅ 报告与工具信息库结构一致，浏览/编辑表单覆盖上述字段 |

## 2. PRD 与架构

| 文档 | 检查项 | 结论 |
|------|--------|------|
| **prd.md** | §6 工具信息库与数据流：首次扫描仅用户确认后入库；再次扫描差异对比、仅用户确认后更新 | ✅ 与后端 report_service._prepare_kb_update_info、create/update-from-report 一致 |
| **prd.md** | §7.3 前端交互说明：新工具加入/暂不保存；已入库更新差异/保持不变 | ✅ index.html 根据 knowledge_base_update 展示并调用对应 API |
| **architecture.md** | 2.2 前端交互说明（与工具信息库一致） | ✅ 与实现一致；核心组件含 Tool Information Store、Report Service |

## 3. 流程与实现文档

| 文档 | 检查项 | 结论 |
|------|--------|------|
| **compliance-scanning-process.md** | 扫描流程、TOS 降级、报告结构 | ✅ 已含；已补充 data_source / knowledge_base_update、工具信息库浏览与维护（4.2 报告扩展、4.3） |
| **compliance-scanning-process.md** | 数据模型含 Tool、ComplianceReport | ✅ 已补充 ToolKnowledgeBase 概要 |

## 4. 前后端逻辑一致性

| 能力 | 后端 | 前端 | 一致性 |
|------|------|------|--------|
| 报告数据来源 | report 含 `data_source.ai_analysis`、`data_source.knowledge_base` | 结果卡片展示「数据来源：本次 AI / 工具信息库 / 混合 / 无」 | ✅ |
| 新工具入库 | `knowledge_base_update.action === pending_creation`；POST create-from-report | 展示「将本次结果加入工具信息库」「暂不保存」；仅点击加入时调用 API | ✅ |
| 存量工具更新 | `action === diff_available`，has_changes；POST update-from-report | 展示差异列表、「更新差异」「保持不变」；仅点击更新时调用 API | ✅ |
| 工具信息库浏览 | GET /knowledge-base 列表；GET /{tool_name}/detail 详情 | 加载列表、左侧列表+筛选、右侧详情、默认第一条 | ✅ |
| 工具信息库编辑 | GET /{tool_name} 取数；PUT /{tool_name} 保存 | 编辑表单合并原数据后 PUT；保存后刷新详情与列表 | ✅ |
| 工具信息库删除 | DELETE /{tool_name} | 确认后调用 DELETE；从缓存移除、刷新列表与详情 | ✅ |

## 5. 术语与命名

- 全项目统一使用「**工具信息库**」（Tool Information Store），无「知识库」对外表述。
- API 路径保持 `/knowledge-base`（兼容性），注释与日志、文档均为「工具信息库」。

## 6. 已知缺口与建议

- **PRD 4.2 报告字段**：FR-REPORT-01 仍含「合规性评分、建议、参考」等旧表述；实际报告以「使用许可、公司信息、商用限制、可替代方案」+ 工具信息库更新为主。建议后续 PRD 修订时与当前产品表述对齐。
- **运行方式**：README 与 run.bat 已改为 venv 一键运行；若存在 run-venv.bat 的引用需移除（当前 README 已不引用）。
- **_bmad-output**：planning-artifacts 下保留 user demand.ini、product-brief.md 等，PRD 附录引用路径正确。

## 7. 结论

- **需求→PRD→架构→流程文档→实现** 的主线一致：工具信息库的「仅用户确认后入库/更新」、浏览/编辑/删除、报告数据来源标识均已在文档与代码中对齐。
- 交付件相对完整；建议在下一迭代中同步 PRD 报告类 FR 与当前产品能力描述。
