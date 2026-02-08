# 性能优化说明

## 优化策略

为了提升系统处理性能，当前版本**暂时禁用了多维度合规评估**，仅保留核心功能：

### ✅ 保留的核心功能

1. **TOS（服务条款）分析**
   - AI分析工具的TOS文档
   - 提取关键信息：
     * 使用许可/开源协议类型
     * 公司信息（开源工具为null）
     * 商用用户使用限制
     * 工具可替代方案

2. **替代方案获取**
   - 独立获取替代工具建议（不依赖TOS分析）
   - 优先推荐免费开源替代工具
   - 限制为1-2个最合适的方案

### ❌ 暂时禁用的功能

以下功能已暂时禁用，以提升处理性能：

1. **多维度合规评估**
   - 安全性评估（Security）
   - 许可证合规评估（License）
   - 维护性评估（Maintenance）
   - 性能/稳定性评估（Performance）
   - TOS合规性评分（TOS Score）

2. **综合评分计算**
   - 综合合规评分（Overall Score）
   - 合规判断（Is Compliant）

3. **详细建议生成**
   - 基于多维度评分的详细建议
   - 不合规原因分析

## 性能提升

### 优化效果

- **减少AI API调用次数**：从5-6次减少到2-3次
- **缩短处理时间**：预计减少60-70%的处理时间
- **降低系统负载**：减少计算和数据库操作

### 处理流程对比

**优化前**：
```
1. 获取工具信息
2. TOS信息获取和分析
3. 替代方案获取
4. 安全性评估（AI调用）
5. 许可证评估（AI调用）
6. 维护性评估（AI调用）
7. 性能评估
8. TOS合规性评估
9. 综合评分计算
10. 生成详细建议
```

**优化后**：
```
1. 获取工具信息
2. TOS信息获取和分析（核心）
3. 替代方案获取（核心）
4. 生成简化报告（仅保存TOS分析和替代方案）
```

## 配置说明

### 启用/禁用多维度评估

在 `config/config.yaml` 中配置：

```yaml
compliance:
  # 设置为 true 启用多维度评估
  # 设置为 false 仅执行TOS分析和替代方案获取（推荐，性能更好）
  enable_multi_dimension_assessment: false
```

### 后续启用

如果后续需要启用多维度评估，只需：

1. 修改配置文件：
   ```yaml
   compliance:
     enable_multi_dimension_assessment: true
   ```

2. 重启服务

3. 系统将自动执行完整的多维度评估流程

## 报告结构

### 简化模式（当前）

```json
{
  "tool": {...},
  "license_info": {...},           // 从TOS分析提取
  "company_info": {...},           // 从TOS分析提取
  "commercial_restrictions": {...}, // 从TOS分析提取
  "alternative_tools": [...],       // 从TOS分析或独立获取
  "compliance_report": {
    "id": 1,
    "score_overall": null,          // 已禁用
    "score_security": null,         // 已禁用
    "score_license": null,          // 已禁用
    "score_maintenance": null,      // 已禁用
    "score_performance": null,      // 已禁用
    "score_tos": null,              // 已禁用
    "is_compliant": null,           // 已禁用
    "tos_analysis": {...}          // TOS分析结果（核心）
  }
}
```

### 完整模式（启用后）

```json
{
  "tool": {...},
  "license_info": {...},
  "company_info": {...},
  "commercial_restrictions": {...},
  "alternative_tools": [...],
  "compliance_report": {
    "id": 1,
    "score_overall": 70.0,          // 综合评分
    "score_security": 70.0,         // 安全性评分
    "score_license": 75.0,          // 许可证评分
    "score_maintenance": 65.0,      // 维护性评分
    "score_performance": 80.0,     // 性能评分
    "score_tos": 100.0,             // TOS评分
    "is_compliant": true,           // 是否合规
    "reasons": {...},               // 不合规原因
    "recommendations": {...},       // 详细建议
    "tos_analysis": {...}
  }
}
```

## 前端显示

前端已优化，**不显示评分信息**，仅显示4个重点信息：

1. ✅ 使用许可/开源协议类型
2. ✅ 公司信息（开源工具显示"开源工具（无特定公司）"）
3. ✅ 商用用户使用限制
4. ✅ 可替代方案（1-2个）

## 注意事项

1. **数据库兼容性**：评分字段在数据库中仍存在，但值为 `NULL`
2. **API兼容性**：API响应结构保持不变，评分字段为 `null`
3. **后续启用**：只需修改配置即可，无需修改代码
4. **性能监控**：建议监控处理时间和API调用次数

## 建议

- **当前阶段**：保持 `enable_multi_dimension_assessment: false`，专注于TOS分析和替代方案
- **后续需求**：当需要详细合规评分时，再启用多维度评估
- **性能测试**：启用前后对比处理时间和资源消耗
