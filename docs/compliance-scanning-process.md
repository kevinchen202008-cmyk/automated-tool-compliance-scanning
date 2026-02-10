# 工具合规性扫描过程和核心处理逻辑

> **文档版本**: v2.1  
> **最后更新**: 2026-02-09  
> **更新内容**: 添加工具信息库浏览、用户确认入库/更新差异、差异对比、429错误重试、进度显示等功能

## 1. 整体架构

工具合规扫描服务采用**分层架构**，包含以下核心组件：

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (前端)                         │
│             用户输入工具名称/列表                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              API 层 (FastAPI)                           │
│  /api/v1/tools/batch  - 批量创建工具                    │
│  /api/v1/scan/start   - 启动扫描                        │
│  /api/v1/reports/{id} - 获取报告                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│           应用层 (Scan Service)                          │
│  任务管理、并发控制、流程编排                            │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────────┐ ┌──────────┐ ┌──────────────┐
│ 工具信息服务  │ │ TOS服务  │ │ 合规引擎     │
│ Tool Info    │ │ TOS      │ │ Compliance  │
│ Service      │ │ Service  │ │ Engine      │
└──────┬───────┘ └────┬─────┘ └──────┬───────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
            ┌─────────────────┐
            │   AI Client      │
            │   (GLM API)      │
            └─────────────────┘
```

## 2. 扫描流程详解

### 2.1 用户输入阶段

**入口**：`POST /api/v1/tools/batch`

1. **工具名称解析**
   - 支持多行输入（每行一个工具名）
   - 支持逗号分隔的列表
   - 解析逻辑：`src/services/tool_service.py::parse_tool_names()`

2. **工具记录创建**
   - 检查工具是否已存在（按名称）
   - 如果不存在，创建新工具记录
   - 保存到数据库 `Tool` 表

### 2.2 扫描启动阶段

**入口**：`POST /api/v1/scan/start`

**核心类**：`ScanService` (`src/services/scan_service.py`)

#### 2.2.1 任务创建

```python
def create_scan_tasks(self, tool_ids: List[int], db: Session) -> List[ScanTask]:
    """
    为每个工具创建扫描任务
    - 验证工具是否存在
    - 创建 ScanTask 对象
    - 初始状态：PENDING
    """
```

#### 2.2.2 并发控制

- 使用 `asyncio.Semaphore` 控制最大并发数
- 默认配置：`config.scanning.max_concurrent`
- 防止过多并发请求导致系统过载

#### 2.2.3 异步执行

```python
async def scan_tools(self, tool_ids: List[int], db: Session):
    """
    并发扫描多个工具
    - 创建所有扫描任务
    - 使用 asyncio.gather() 并发执行
    - 返回任务状态映射
    """
```

### 2.3 单个工具扫描流程

**核心方法**：`ScanService.scan_tool()`

#### 阶段1：获取工具信息

**服务**：`ToolInfoService` (`src/services/tool_info_service.py`)

```python
async def get_tool_info(tool: Tool, db: Session) -> Dict[str, Any]:
    """
    1. 尝试获取工具版本信息
       - 调用 fetch_tool_version() (当前为占位实现)
       - 可通过API、包管理器、搜索引擎获取
    2. 更新工具信息到数据库
       - 如果无法获取版本，设置为 "unknown"
    3. 返回工具信息字典
    """
```

**输出**：
```python
{
    "tool_id": 1,
    "name": "Docker Desktop",
    "version": "unknown",  # 或实际版本号
    "source": "external",
    "tos_url": None,
    "tos_info": None
}
```

#### 阶段2：TOS信息获取和分析

**服务**：`TOSService` (`src/services/tos_service.py`)

**核心方法**：`get_and_analyze_tos()`

##### 2.3.2.1 TOS链接搜索

```python
async def search_tos_url(tool_name: str) -> Optional[str]:
    """
    通过AI服务搜索工具的TOS链接
    - 调用 GLM API 搜索官方服务条款链接
    - 返回TOS文档URL
    """
```

**降级策略**：
1. 首先尝试AI搜索TOS链接
2. 如果失败，再次尝试AI搜索
3. 如果仍然失败，进入直接分析模式

##### 2.3.2.2 TOS内容获取

```python
async def fetch_tos_content(tos_url: str) -> Optional[str]:
    """
    从URL获取TOS文档内容
    - 使用 httpx 异步HTTP客户端
    - 超时设置：30秒
    - 返回文档文本内容
    """
```

##### 2.3.2.3 TOS内容分析

```python
async def analyze_tos_with_ai(tool_name: str, tos_content: str):
    """
    使用AI分析TOS内容
    - 限制TOS内容长度（前5000字符）
    - 调用 GLM API 分析TOS
    - 提取关键信息：
      * 许可证类型和版本
      * 公司信息（开源工具为null）
      * 商用限制
      * 替代方案
    """
```

**AI分析重点**：
1. **工具使用许可或开源协议类型**（最重要）
   - 许可证类型（MIT、Apache、GPL、BSD、商业许可证等）
   - 许可证版本号
   - 许可证模式（开源/商业/混合）

2. **工具所属公司和公司所属国家**（最重要）
   - 公司名称（开源工具填写null）
   - 公司注册国家/地区
   - 是否有中国分公司或服务

3. **商用用户使用的限制**（最重要）
   - 商业用户是否必须购买license？
   - 是否允许免费商业使用？
   - 用户数量、服务器数量等限制

4. **工具可替代方案**（最重要）
   - 优先推荐免费开源替代工具
   - 限制为1-2个最合适的方案

##### 2.3.2.4 降级处理

如果TOS获取失败，使用AI直接分析工具：

```python
async def analyze_tool_directly(tool_name: str):
    """
    直接分析工具信息（不依赖TOS文档）
    - 基于工具名称直接分析
    - 不依赖TOS文档内容
    - 返回相同的结构化信息
    """
```

#### 阶段3：独立获取替代方案

**服务**：`AIClient` (`src/services/ai_client.py`)

```python
async def get_alternative_tools(tool_name: str) -> List[Dict[str, Any]]:
    """
    独立获取工具的替代方案（不依赖TOS分析）
    - 即使TOS分析失败，也会尝试获取替代方案
    - 优先推荐免费开源替代工具
    - 限制为最多2个替代方案
    """
```

**逻辑**：
- 如果TOS分析中没有替代方案，自动调用此方法
- 确保替代方案始终可用

#### 阶段4：合规评估

**服务**：`ComplianceEngine` (`src/services/compliance_engine.py`)

**核心方法**：`generate_compliance_report()`

##### 2.3.4.1 多维度评估

```python
async def assess_all_dimensions(
    tool: Tool,
    tool_info: Dict[str, Any],
    tos_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    评估所有合规维度：
    1. 安全性 (Security) - 0-100分
    2. 许可证合规 (License) - 0-100分
    3. 维护性 (Maintenance) - 0-100分
    4. 性能/稳定性 (Performance) - 0-100分
    5. TOS合规性 (TOS) - 0-100分
    """
```

**各维度评估逻辑**：

1. **安全性评估** (`assess_security`)
   - 使用AI辅助评估
   - 可检查：已知漏洞、安全配置、最佳实践
   - 默认评分：70.0

2. **许可证合规评估** (`assess_license`)
   - **优先使用TOS分析结果**：
     - 如果商业用户必须购买license → 60.0分
     - 如果允许免费商业使用 → 90.0分
   - 如果没有TOS分析，使用AI评估
   - 默认评分：75.0

3. **维护性评估** (`assess_maintenance`)
   - 使用AI辅助评估
   - 可检查：更新频率、社区活跃度、维护状态
   - 默认评分：65.0

4. **性能评估** (`assess_performance`)
   - 初期可以弱化此维度
   - 默认评分：80.0

5. **TOS合规性评估** (`assess_tos`)
   - 根据TOS分析结果评估
   - 风险点越多，评分越低
   - 如果没有TOS信息，评分：50.0

##### 2.3.4.2 综合评分计算

```python
def calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
    """
    计算综合合规评分（加权平均）
    
    权重配置（config.yaml）：
    - security: 0.4 (40%)
    - license: 0.3 (30%)
    - maintenance: 0.2 (20%)
    - performance: 0.1 (10%)
    - tos: 根据配置（如果有）
    """
```

##### 2.3.4.3 合规判断

```python
def is_compliant(self, overall_score: float, threshold: float = 70.0) -> bool:
    """
    判断是否合规
    - 阈值：70.0（可配置）
    - >= 70.0：合规
    - < 70.0：不合规
    """
```

##### 2.3.4.4 生成建议和原因

```python
def _generate_recommendations(
    dimension_scores: Dict[str, float],
    tool_info: Dict[str, Any],
    tos_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    生成合规建议
    - 检查商业license要求
    - 检查各维度评分
    - 提取替代工具信息
    """
```

#### 阶段5：报告生成和保存

**服务**：`ReportService` (`src/services/report_service.py`)

```python
def generate_json_report(
    tool: Tool,
    report: ComplianceReport,
    db: Session
) -> Dict[str, Any]:
    """
    生成JSON格式的合规报告
    
    报告结构：
    {
        "tool": {...},
        "license_info": {...},      # 从TOS分析提取
        "company_info": {...},       # 从TOS分析提取
        "commercial_restrictions": {...},  # 从TOS分析提取
        "alternative_tools": [...],  # 从TOS分析提取（限制1-2个）
        "compliance_report": {...}
    }
    """
```

**关键信息提取**：
- 从TOS分析结果中提取4个重点信息
- 限制替代工具数量为1-2个
- 处理开源工具的公司信息（null值）

## 3. 核心处理逻辑

### 3.1 JSON解析增强

**问题**：GLM API返回的是包含markdown代码块的响应

**解决方案**：`AIClient._extract_json_from_markdown()`

```python
def _extract_json_from_markdown(self, text: str) -> str:
    """
    从markdown代码块中提取JSON内容
    
    处理逻辑：
    1. 尝试匹配 ```json {...} ``` 或 ``` {...} ```
    2. 如果失败，尝试直接查找 { ... } 对象
    3. 验证提取的内容是否为有效JSON
    4. 如果都失败，返回原始文本
    """
```

### 3.2 错误处理和降级策略

#### 3.2.1 TOS获取降级

```
TOS链接搜索
  ├─ 成功 → 获取TOS内容
  │   ├─ 成功 → AI分析TOS
  │   │   ├─ 成功 → 使用TOS分析结果 ✓
  │   │   └─ 失败 → AI直接分析工具 ✓
  │   └─ 失败 → AI直接分析工具 ✓
  └─ 失败 → AI直接分析工具 ✓
```

#### 3.2.2 替代方案获取降级

```
TOS分析
  ├─ 成功 → 检查替代方案
  │   ├─ 有 → 使用TOS中的替代方案 ✓
  │   └─ 无 → 独立获取替代方案 ✓
  └─ 失败 → 独立获取替代方案 ✓
```

### 3.3 开源工具特殊处理

**识别**：公司名称为 `null` 或 `"开源工具（无特定公司）"`

**处理**：
- 公司信息显示为"开源工具（无特定公司）"
- 不显示"所属国家"和"总部"信息
- 不显示"中国服务"状态（显示"不适用（开源工具）"）
- **重点突出开源协议类型**

### 3.4 并发控制

```python
class ScanService:
    def __init__(self):
        self.max_concurrent = config.scanning.max_concurrent
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def scan_tool(self, task: ScanTask, db: Session):
        async with self.semaphore:  # 控制并发数
            # 执行扫描逻辑
```

## 4. 数据流

### 4.1 数据模型

```
Tool (工具)
  ├─ id
  ├─ name
  ├─ version
  ├─ source
  ├─ tos_url
  └─ tos_info (JSON)

ComplianceReport (合规报告)
  ├─ id
  ├─ tool_id
  ├─ score_overall
  ├─ score_security
  ├─ score_license
  ├─ score_maintenance
  ├─ score_performance
  ├─ score_tos
  ├─ is_compliant
  ├─ reasons (JSON)
  ├─ recommendations (JSON)
  ├─ references (JSON)
  └─ tos_analysis (JSON)

ToolKnowledgeBase (工具信息库)
  ├─ tool_name
  ├─ license_type, license_version, license_mode
  ├─ company_*, china_office
  ├─ commercial_*, user_limit, feature_restrictions
  ├─ alternative_tools (JSON)
  └─ source, updated_at, updated_by
```

### 4.2 报告数据结构

```json
{
  "tool": {
    "id": 1,
    "name": "Docker Desktop",
    "version": "unknown",
    "source": "external",
    "tos_url": "https://..."
  },
  "license_info": {
    "license_type": "商业许可证",
    "license_version": "",
    "license_mode": "商业"
  },
  "company_info": {
    "company_name": "Docker Inc.",
    "company_country": "美国",
    "company_headquarters": "旧金山",
    "china_office": false
  },
  "commercial_restrictions": {
    "commercial_license_required": false,
    "free_for_commercial": false,
    "restrictions": "...",
    "user_limit": "",
    "feature_restrictions": ""
  },
  "alternative_tools": [
    {
      "name": "Podman",
      "type": "开源",
      "license": "Apache 2.0",
      "advantages": "...",
      "use_case": "..."
    }
  ],
  "compliance_report": {
    "id": 1,
    "is_compliant": true,
    "score_overall": 70.0,
    "reasons": {...},
    "recommendations": {...}
  },
  "data_source": {
    "ai_analysis": true,
    "knowledge_base": false
  },
  "knowledge_base_update": {
    "available": true,
    "action": "pending_creation",
    "tool_name": "Docker Desktop",
    "message": "...",
    "new_data": {...}
  }
}
```

- **data_source**：数据来源标识，与前端「数据来源」展示一致。
  - `ai_analysis`：本次扫描是否包含有效 AI 分析结果。
  - `knowledge_base`：是否用到了工具信息库数据（补全或回退）。
  - 前端展示：本次 AI / 工具信息库 / 混合（两者皆有）/ 无。
- **knowledge_base_update**：工具信息库更新建议，仅用户确认时写入。
  - 新工具：`action: pending_creation`，用户可「加入工具信息库」或「暂不保存」。
  - 已入库工具：`action: diff_available`，可查看差异并「更新差异」或「保持不变」。

### 4.3 工具信息库浏览与维护

- **列表与详情**：`GET /api/v1/knowledge-base` 列表，`GET /api/v1/knowledge-base/{tool_name}/detail` 详情；前端支持按名称筛选、左右分栏展示、默认选中第一条。
- **编辑**：`GET /api/v1/knowledge-base/{tool_name}` 拉取完整数据，前端编辑表单提交 `PUT /api/v1/knowledge-base/{tool_name}` 保存。
- **删除**：前端确认后调用 `DELETE /api/v1/knowledge-base/{tool_name}`，成功后从列表移除并刷新详情。
- **入库/更新**：扫描结果卡片根据 `knowledge_base_update` 调用 `create-from-report` 或 `update-from-report`，仅用户点击时写入。

## 5. 关键特性

### 5.1 多级降级策略

- **TOS获取失败** → AI直接分析工具
- **TOS分析失败** → 使用降级数据结构
- **替代方案缺失** → 独立获取替代方案
- **JSON解析失败** → 从markdown代码块提取

### 5.2 智能信息提取

- 自动识别开源工具（公司名称为null）
- 自动提取关键信息（许可证、公司、商用限制、替代方案）
- 自动限制替代方案数量（1-2个）

### 5.3 并发处理

- 支持批量工具扫描
- 可配置最大并发数
- 异步处理，提高效率

## 6. 配置说明

### 6.1 扫描配置

```yaml
scanning:
  max_concurrent: 3  # 最大并发扫描数
```

### 6.2 合规评分权重

```yaml
compliance:
  scoring:
    security: 0.4      # 安全性权重 40%
    license: 0.3      # 许可证合规权重 30%
    maintenance: 0.2  # 维护性权重 20%
    performance: 0.1  # 性能权重 10%
```

### 6.3 AI配置

```yaml
ai:
  provider: "glm"
  glm:
    api_base: "https://open.bigmodel.cn/api/paas/v4"
    api_key: "your-api-key"
    model: "glm-4"
    timeout: 30
```

## 7. 性能优化

1. **并发控制**：使用Semaphore限制并发数，避免过载
2. **异步处理**：所有IO操作使用async/await
3. **数据缓存**：TOS分析结果保存到数据库，避免重复分析
4. **超时控制**：HTTP请求设置超时，避免长时间等待

## 8. 错误处理

1. **日志记录**：详细记录每个步骤的执行情况
2. **降级策略**：多级降级确保即使部分失败也能生成报告
3. **用户友好**：前端显示"待分析"而不是错误信息
4. **详细日志**：记录API响应内容，便于调试

## 9. 扩展性

1. **插件化AI客户端**：支持切换不同的AI服务提供商
2. **可配置规则**：合规评分权重可配置
3. **数据库可扩展**：支持SQLite和MySQL
4. **报告格式可扩展**：支持JSON，可扩展其他格式
