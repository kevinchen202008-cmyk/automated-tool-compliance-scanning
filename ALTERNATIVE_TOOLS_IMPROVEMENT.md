# 替代方案获取逻辑改进

## 问题分析

用户反馈：**替代方案与TOS分析没有关系，为什么没有替代方案建议？**

### 原有问题

1. **替代方案只依赖TOS分析**：
   - 替代方案仅从TOS分析的`alternative_tools`字段中获取
   - 如果TOS分析失败或没有返回替代工具，就没有替代方案
   - 这导致即使工具信息完整，也可能缺少替代方案建议

2. **逻辑不合理**：
   - 替代方案应该是独立的分析结果，不应该完全依赖TOS分析
   - TOS分析主要关注服务条款、许可证、商业限制等
   - 替代方案应该基于工具的功能、特性、社区活跃度等独立分析

## 改进方案

### 1. 新增独立替代方案获取方法 (`src/services/ai_client.py`)

**新增方法**：`get_alternative_tools(tool_name: str)`

- **功能**：独立获取工具的替代方案，不依赖TOS分析
- **特点**：
  - 专门针对替代方案分析
  - 优先推荐免费开源替代工具
  - 其次推荐免费商业替代工具
  - 每个替代方案包含：名称、类型、许可证、优势、适用场景
  - 限制为最多2个替代方案

### 2. 扫描服务改进 (`src/services/scan_service.py`)

**改进逻辑**：
```python
# 2.5. 独立获取替代方案（不依赖TOS分析）
alternative_tools = []
if not tos_analysis or not tos_analysis.get("alternative_tools"):
    try:
        ai_client = get_ai_client()
        alternative_tools = await ai_client.get_alternative_tools(tool.name)
        if alternative_tools:
            # 补充到TOS分析结果中
            if tos_analysis:
                tos_analysis["alternative_tools"] = alternative_tools
            else:
                tos_analysis = {"alternative_tools": alternative_tools}
    except Exception as e:
        logger.warning(f"独立获取替代方案失败: {tool.name} - {e}")
```

**改进点**：
- 即使TOS分析失败，也会尝试独立获取替代方案
- 如果TOS分析中没有替代方案，会自动补充
- 确保替代方案始终可用

### 3. 报告服务改进 (`src/services/report_service.py`)

**改进逻辑**：
- 优先从TOS分析中获取替代工具
- 如果TOS分析中没有，则从数据库中获取（如果有）
- 确保替代方案始终显示

## 替代方案获取流程

```
1. 执行TOS分析
   ├─ 成功 → 检查是否有替代方案
   │   ├─ 有 → 使用TOS分析中的替代方案
   │   └─ 无 → 执行独立替代方案获取
   └─ 失败 → 执行独立替代方案获取

2. 独立替代方案获取
   ├─ 调用AI分析工具特性、功能、社区等
   ├─ 推荐1-2个最合适的替代方案
   └─ 补充到TOS分析结果中

3. 报告生成
   └─ 从TOS分析结果中提取替代方案（已包含独立获取的）
```

## 优势

1. **独立性**：替代方案不再完全依赖TOS分析
2. **可靠性**：即使TOS分析失败，也能获取替代方案
3. **专业性**：专门的替代方案分析，更准确
4. **完整性**：确保报告始终包含替代方案建议

## 测试建议

1. 测试TOS分析成功但无替代方案的情况
2. 测试TOS分析失败的情况
3. 验证替代方案是否正确显示
4. 检查替代方案的质量和相关性

## 注意事项

- 替代方案获取是独立的AI调用，会增加API调用次数
- 如果GLM API调用失败，替代方案可能为空
- 建议检查日志确认替代方案获取状态
