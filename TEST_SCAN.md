# 测试扫描功能说明

## 已修复的问题

1. ✅ 修复了 `ComplianceReport` 和 `Tool` 模型导入缺失的问题
2. ✅ 修复了扫描服务中重复创建报告的逻辑问题

## 测试步骤

### 1. 创建工具

```bash
curl -X POST "http://localhost:8080/api/v1/tools/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_names": "Docker Desktop",
    "source": "external"
  }'
```

### 2. 启动扫描

从步骤1的响应中获取 `tool_id`，然后：

```bash
curl -X POST "http://localhost:8080/api/v1/scan/start" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_ids": [1]
  }'
```

### 3. 获取报告

从步骤2的响应中获取 `report_id`，然后：

```bash
curl "http://localhost:8080/api/v1/reports/1"
```

### 4. 通过 Web UI 测试

访问 http://localhost:8080/ui，输入 "Docker Desktop" 并点击"开始扫描"。

## 预期结果

扫描完成后应该返回：
- 工具信息
- 各维度评分（安全性、许可证、维护性、性能、TOS）
- 综合合规评分
- 合规建议
- 不合规原因（如有）

## 注意事项

- 扫描过程可能需要一些时间（特别是AI调用）
- 如果TOS信息获取失败，系统会继续其他维度的评估
- 所有结果都会保存到数据库中
