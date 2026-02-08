# TOS 分析和商业 License 检查更新

## 更新内容

### 1. AI 客户端 TOS 分析提示词更新

已更新 `src/services/ai_client.py` 中的 `analyze_tos` 方法，提示词现在明确要求：

**重点分析商业使用许可要求**：
- ✅ 商业用户是否必须购买license？
- ✅ 是否有免费版本可用于商业用途？
- ✅ 商业使用的限制和条件是什么？
- ✅ 是否需要企业版或商业版license？

**返回的JSON格式包含**：
```json
{
    "commercial_license_required": true/false,
    "license_type": "免费/商业/企业",
    "commercial_restrictions": "具体限制说明",
    "free_for_commercial": true/false,
    "data_usage": "数据使用政策说明",
    "privacy_policy": "隐私政策说明",
    "service_restrictions": "服务限制说明",
    "risk_points": ["风险点1", "风险点2", ...],
    "compliance_notes": "合规性备注"
}
```

### 2. 合规引擎 License 评估更新

已更新 `src/services/compliance_engine.py` 中的 `assess_license` 方法：

- ✅ 现在接收 TOS 分析结果作为参数
- ✅ 根据 TOS 分析结果评估商业 license 要求
- ✅ 如果商业用户必须购买 license，评分降低（60分）
- ✅ 如果允许免费商业使用，评分提高（90分）

### 3. 报告生成更新

合规报告现在会：

- ✅ 在 `recommendations` 中明确标注商业 license 要求
- ✅ 在 `reasons` 中说明 license 相关的合规风险
- ✅ 包含 `commercial_license_required` 字段

## 使用示例

当扫描 "Docker Desktop" 时，系统会：

1. **获取 TOS 信息**：通过 AI 搜索并获取 Docker Desktop 的 TOS 文档
2. **分析 TOS**：使用更新后的提示词分析，重点关注商业 license 要求
3. **评估 License 合规性**：根据 TOS 分析结果评估 license 评分
4. **生成报告**：在报告中明确标注是否需要购买商业 license

## 预期结果

扫描完成后，报告会包含：

```json
{
    "compliance_report": {
        "score_license": 60.0,  // 如果需要购买license，评分较低
        "reasons": {
            "reasons": [
                {
                    "dimension": "license",
                    "reason": "商业用户必须购买license。具体限制说明...",
                    "impact": "high"
                }
            ],
            "commercial_license_required": true
        },
        "recommendations": {
            "recommendations": [
                {
                    "dimension": "license",
                    "priority": "high",
                    "suggestion": "⚠️ 商业用户必须购买license（类型：商业版）。具体限制...",
                    "action": "需要评估license成本和预算"
                }
            ]
        }
    }
}
```

## 测试建议

1. 重启服务以应用更新
2. 测试扫描 "Docker Desktop" 或其他需要商业 license 的工具
3. 检查报告中的 license 评估和建议
4. 验证 TOS 分析是否包含商业 license 要求信息

## 注意事项

- 确保 GLM API Key 已正确配置
- TOS 分析需要调用 GLM API，可能需要一些时间
- 如果 TOS 信息获取失败，系统会使用默认评分继续评估
