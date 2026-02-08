# 扫描结果重点信息展示更新

## 更新内容

### 1. TOS 分析提示词更新

已更新 `src/services/ai_client.py` 中的 `analyze_tos` 方法，现在明确要求分析以下**重点信息**：

1. **工具使用许可或开源协议类型**
   - 许可证类型（MIT、Apache、GPL、BSD、商业许可证等）
   - 许可证版本号
   - 许可证模式（开源/商业/混合）

2. **工具所属公司和公司所属国家**
   - 公司名称
   - 公司所属国家/地区
   - 公司总部所在地
   - 是否有中国分公司或服务

3. **商用用户使用的限制**
   - 商业用户是否必须购买license
   - 是否允许免费商业使用
   - 具体限制说明（用户数、功能、服务器等）

4. **工具可替代方案**
   - 建议的免费开源替代工具
   - 建议的免费商业替代工具
   - 每个替代方案的优势和适用场景
   - 替代方案的许可证类型

### 2. 报告生成服务更新

已更新 `src/services/report_service.py`，报告现在包含**独立的重点信息字段**：

```json
{
    "license_info": {
        "license_type": "许可证类型",
        "license_version": "版本号",
        "license_mode": "许可证模式"
    },
    "company_info": {
        "company_name": "公司名称",
        "company_country": "所属国家",
        "company_headquarters": "总部所在地",
        "china_office": true/false
    },
    "commercial_restrictions": {
        "commercial_license_required": true/false,
        "free_for_commercial": true/false,
        "restrictions": "限制说明",
        "user_limit": "用户限制",
        "feature_restrictions": "功能限制"
    },
    "alternative_tools": [
        {
            "name": "替代工具名称",
            "type": "开源/免费商业",
            "license": "许可证类型",
            "advantages": "优势",
            "use_case": "适用场景",
            "link": "链接"
        }
    ]
}
```

### 3. Web UI 更新

已更新 `src/static/index.html`，现在会**重点展示**：

- ✅ 使用许可/开源协议信息（独立卡片）
- ✅ 公司信息（独立卡片，标注是否有中国服务）
- ✅ 商用用户使用限制（独立卡片，高亮显示）
- ✅ 可替代方案（独立卡片，列出所有替代工具）

### 4. 合规引擎更新

已更新 `src/services/compliance_engine.py`：

- ✅ 建议生成逻辑整合了TOS分析中的替代工具信息
- ✅ 原因生成逻辑包含商业license要求说明

## 报告结构

扫描结果现在按以下结构组织：

```
{
    "tool": { ... },                    // 工具基本信息
    "license_info": { ... },            // ⭐ 重点：许可证信息
    "company_info": { ... },            // ⭐ 重点：公司信息
    "commercial_restrictions": { ... }, // ⭐ 重点：商用限制
    "alternative_tools": [ ... ],       // ⭐ 重点：替代方案
    "compliance_report": { ... },       // 完整合规报告
    "metadata": { ... }                 // 元数据
}
```

## 使用示例

扫描 "Docker Desktop" 时，报告会包含：

1. **许可证信息**：
   - 类型：商业许可证
   - 模式：商业

2. **公司信息**：
   - 公司名称：Docker Inc.
   - 所属国家：美国
   - 是否有中国服务：是/否

3. **商用限制**：
   - 需购买License：是 ⚠️
   - 允许免费商用：否
   - 限制说明：商业使用需要购买Docker Desktop商业版license

4. **替代方案**：
   - Podman（开源，免费商用）
   - Containerd（开源，免费商用）
   - 等等...

## 测试建议

1. 重启服务以应用更新
2. 测试扫描需要商业license的工具（如Docker Desktop）
3. 验证报告中是否包含所有4个重点信息
4. 检查Web UI是否正确展示这些信息

## 注意事项

- 所有信息都来自GLM AI对TOS协议的分析
- 如果TOS信息获取失败，这些字段可能为空或显示"未知"
- 替代方案建议基于AI分析，可能需要人工验证
