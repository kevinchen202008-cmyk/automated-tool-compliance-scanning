# GLM API 调用问题总结

## 当前问题状态

### 1. TOS分析JSON解析失败

**现象**：
- 日志显示：`"TOS分析JSON解析失败: Docker Desktop"`
- UI显示：大部分字段为"未知"（类型、模式、公司名称等）

**可能原因**：
- GLM API返回的响应不是纯JSON格式
- 可能包含markdown代码块（如 ```json ... ```）
- JSON格式不规范（缺少引号、多余逗号等）

### 2. 替代方案JSON格式错误

**现象**：
- 日志显示：`"AI返回的替代方案JSON格式不正确: Docker Desktop"`
- UI显示：`"暂无替代方案建议,TOS分析中..."`

**可能原因**：
- 与TOS分析相同的问题
- AI返回的格式不符合预期

### 3. 商用限制信息部分可用

**现象**：
- UI显示：`"需购买License: 否 ✓"` 和 `"允许免费商用: 否"`
- 说明部分数据解析成功

**分析**：
- 可能TOS分析返回了部分数据，但JSON解析失败后使用了降级处理
- 降级处理可能从文本中提取了部分信息

## 已完成的改进

### 1. 增强错误日志记录

✅ 将DEBUG级别改为WARNING级别，确保能看到实际响应内容
✅ 记录API响应的前500字符
✅ 记录JSON解析错误的详细信息
✅ 记录HTTP错误响应的详细内容

### 2. 代码更新

- `src/services/ai_client.py`：
  - `analyze_tos()`: 记录TOS分析失败的详细响应
  - `get_alternative_tools()`: 记录替代方案获取失败的详细响应
  - `_call_api()`: 记录API调用失败的详细信息

## 下一步行动

### 1. 重新测试并查看详细日志

**操作**：
1. 重启服务（如果还没有重启）
2. 重新扫描"Docker Desktop"
3. 查看 `logs/app.log` 中的WARNING级别日志

**预期结果**：
- 能看到GLM API实际返回的响应内容（前500字符）
- 能看到JSON解析错误的具体原因
- 能判断响应格式是否符合预期

### 2. 根据响应内容改进解析逻辑

**如果响应包含markdown代码块**：
```python
# 提取JSON部分
import re
json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
if json_match:
    json_str = json_match.group(1)
    return json.loads(json_str)
```

**如果JSON格式不规范**：
- 使用更宽松的JSON解析库（如`json5`）
- 或手动清理JSON字符串

**如果响应是纯文本**：
- 使用AI再次解析文本内容
- 或使用正则表达式提取关键信息

### 3. 验证GLM API配置

**检查项**：
- ✅ API Key是否正确配置
- ✅ API endpoint是否正确：`https://open.bigmodel.cn/api/paas/v4`
- ✅ 模型名称是否正确：`glm-4`
- ✅ 请求格式是否符合GLM API要求

### 4. 测试GLM API直接调用

**建议**：
- 创建一个简单的测试脚本，直接调用GLM API
- 验证返回格式是否符合预期
- 检查是否有响应长度限制

## 预期改进效果

完成上述改进后，应该能够：
1. ✅ 看到GLM API实际返回的内容
2. ✅ 正确解析TOS分析结果
3. ✅ 正确解析替代方案建议
4. ✅ UI显示完整的关键信息

## 临时解决方案

如果GLM API持续返回非JSON格式，可以考虑：
1. 使用文本解析作为降级方案
2. 使用正则表达式提取关键信息
3. 改进prompt，明确要求返回纯JSON格式

## 注意事项

- 确保日志级别设置为INFO或更低（WARNING/ERROR会被记录）
- 检查日志文件大小，避免日志过大
- 如果响应内容很长，可能需要调整截取长度
