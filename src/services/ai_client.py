"""
AI客户端模块
AI client module for unified AI service interface
"""

import json
import re
import asyncio
import httpx
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from src.config import get_config
from src.logger import get_logger

logger = get_logger()


class AIClientBase(ABC):
    """AI客户端基类"""
    
    @abstractmethod
    async def generate_compliance_suggestions(
        self,
        tool_name: str,
        tool_info: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成合规建议
        
        Args:
            tool_name: 工具名称
            tool_info: 工具信息
            context: 额外上下文信息
        
        Returns:
            Dict[str, Any]: 合规建议
        """
        pass
    
    @abstractmethod
    async def analyze_tos(
        self,
        tool_name: str,
        tos_content: str
    ) -> Dict[str, Any]:
        """
        分析TOS内容
        
        Args:
            tool_name: 工具名称
            tos_content: TOS文档内容
        
        Returns:
            Dict[str, Any]: TOS分析结果
        """
        pass
    
    @abstractmethod
    async def search_tos_url(
        self,
        tool_name: str
    ) -> Optional[str]:
        """
        搜索工具的TOS链接
        
        Args:
            tool_name: 工具名称
        
        Returns:
            Optional[str]: TOS链接
        """
        pass


class GLMClient(AIClientBase):
    """GLM AI客户端"""
    
    def __init__(self):
        config = get_config()
        glm_conf = getattr(config.ai, "glm", None)
        if glm_conf is None:
            # 无配置文件或配置中未提供 glm 段时，使用 GLMConfig 默认值，避免 NoneType 报错
            from src.config import GLMConfig
            glm_conf = GLMConfig()
        self.api_base = glm_conf.api_base
        self.api_key = glm_conf.api_key
        self.model = glm_conf.model
        self.temperature = glm_conf.temperature
        self.max_tokens = glm_conf.max_tokens
        self.timeout = glm_conf.timeout
    
    async def _call_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        调用GLM API
        
        Args:
            messages: 消息列表
        
        Returns:
            Optional[str]: API响应内容
        """
        if not self.api_key:
            logger.warning("GLM API Key未配置")
            return None
        
        # 获取重试配置
        config = get_config()
        max_retries = config.scanning.retry.max_attempts
        backoff_factor = config.scanning.retry.backoff_factor
        base_delay = 2  # 基础延迟（秒）
        
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # 重试机制：处理429速率限制错误
        last_exception = None
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(url, headers=headers, json=data)
                    
                    # 检查429错误（速率限制）
                    if response.status_code == 429:
                        error_detail = None
                        try:
                            error_json = response.json()
                            error_detail = error_json.get("error", {})
                            error_message = error_detail.get("message", "速率限制")
                            error_code = error_detail.get("code", "429")
                            logger.info("GLM API错误详情: %s", error_json)
                        except Exception:
                            error_message = "速率限制"
                            error_code = "429"
                        
                        if attempt < max_retries - 1:
                            # 计算退避延迟（指数退避）
                            delay = base_delay * (backoff_factor ** attempt)
                            logger.warning(
                                f"GLM API速率限制 (错误码: {error_code}), "
                                f"第 {attempt + 1}/{max_retries} 次重试, "
                                f"等待 {delay} 秒后重试..."
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            # 最后一次重试也失败
                            logger.error(
                                f"GLM API速率限制，已重试 {max_retries} 次仍失败: {error_message}"
                            )
                            raise httpx.HTTPStatusError(
                                f"速率限制: {error_message}",
                                request=response.request,
                                response=response
                            )
                    
                    # 其他HTTP错误
                    response.raise_for_status()
                    result = response.json()
                    
                    # 提取响应内容
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"]
                    
                    return None
                    
            except httpx.HTTPStatusError as e:
                # HTTP状态错误（包括429）
                last_exception = e
                if e.response.status_code == 429:
                    # 429错误已在上面处理，这里不应该到达
                    if attempt < max_retries - 1:
                        delay = base_delay * (backoff_factor ** attempt)
                        logger.warning(f"GLM API速率限制，等待 {delay} 秒后重试...")
                        await asyncio.sleep(delay)
                        continue
                else:
                    # 其他HTTP错误，不重试
                    logger.error(f"GLM API调用失败 (HTTP {e.response.status_code}): {e}")
                    raise
                    
            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(f"GLM API请求超时，等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"GLM API请求超时，已重试 {max_retries} 次。"
                        "（若频繁出现，可检查网络或 GLM 服务状态；额度限制会显示 429/速率限制）"
                    )
                    raise
                    
            except httpx.RequestError as e:
                # 网络错误，可以重试
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(f"GLM API网络错误，等待 {delay} 秒后重试: {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"GLM API网络错误，已重试 {max_retries} 次: {e}")
                    raise
                    
            except Exception as e:
                # 其他错误，不重试
                logger.error(f"GLM API调用失败: {e}", exc_info=True)
                raise
        
        # 所有重试都失败
        if last_exception:
            raise last_exception
        return None
    
    def _extract_json_from_markdown(self, text: str) -> str:
        """
        从markdown代码块中提取JSON内容
        
        Args:
            text: 可能包含markdown代码块的文本
        
        Returns:
            str: 提取的JSON字符串，如果提取失败则返回原始文本
        """
        if not text:
            return text
        
        # 尝试匹配markdown代码块中的JSON
        # 匹配 ```json ... ``` 或 ``` ... ```
        patterns = [
            r'```(?:json)?\s*(\{.*?\})\s*```',  # 匹配 ```json {...} ```
            r'```(?:json)?\s*(\[.*?\])\s*```',   # 匹配 ```json [...] ```
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                # 验证是否是有效的JSON
                try:
                    json.loads(json_str)
                    return json_str
                except json.JSONDecodeError:
                    continue
        
        # 如果没有找到代码块，尝试直接查找JSON对象
        # 查找第一个 { 到最后一个 } 之间的内容
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            json_str = brace_match.group(0).strip()
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        # 如果都失败了，返回原始文本
        return text
    
    async def generate_compliance_suggestions(
        self,
        tool_name: str,
        tool_info: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成合规建议"""
        prompt = f"""请分析工具 {tool_name} 的合规性，并提供建议。

工具信息：
- 名称: {tool_info.get('name', 'unknown')}
- 版本: {tool_info.get('version', 'unknown')}
- 来源: {tool_info.get('source', 'unknown')}

请从以下维度分析：
1. 安全性（security）
2. 许可证合规（license）
3. 维护性（maintenance）
4. 性能/稳定性（performance）
5. TOS合规性（如果可用）

请以JSON格式返回分析结果，包含：
- 各维度评分（0-100）
- 合规建议
- 潜在风险点
- 开源替代建议（如适用）
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的工具合规性分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._call_api(messages)
        
        if response:
            try:
                # 尝试从markdown代码块中提取JSON
                json_str = self._extract_json_from_markdown(response)
                return json.loads(json_str)
            except json.JSONDecodeError:
                # 如果不是JSON，返回文本响应
                return {"analysis": response, "format": "text"}
        
        return {"error": "AI服务调用失败"}
    
    async def analyze_tos(
        self,
        tool_name: str,
        tos_content: str
    ) -> Dict[str, Any]:
        """分析TOS内容"""
        # 限制TOS内容长度
        tos_preview = tos_content[:5000] if len(tos_content) > 5000 else tos_content
        
        prompt = f"""请分析工具 {tool_name} 的服务条款（TOS）文档，识别合规风险点。

TOS内容（摘要）：
{tos_preview}

请重点分析以下方面，并按优先级提供详细信息：

1. **工具使用许可或开源协议类型**（最重要）：
   - 许可证类型（如：MIT、Apache、GPL、BSD、商业许可证等）
   - 开源协议版本
   - 许可证的完整名称和版本号
   - 如果是商业软件，说明许可证模式（单用户、企业版、订阅制等）

2. **工具所属公司和公司所属国家**（最重要）：
   - 工具的开发商/公司名称
     * **重要：如果是开源工具（如Docker CE、Linux等），公司名称应填写为 null 或 "开源社区"**
     * 只有商业软件或由特定公司维护的开源项目才填写公司名称
   - 公司注册国家/地区（开源工具可为null）
   - 公司总部所在地（开源工具可为null）
   - 是否有中国分公司或服务（开源工具可为false或null）

3. **商用用户使用的限制**（最重要）：
   - 商业用户是否必须购买license？
   - 是否有免费版本可用于商业用途？
   - 商业使用的具体限制和条件
   - 是否需要企业版或商业版license？
   - 用户数量、服务器数量等限制
   - 功能限制（免费版vs商业版）

4. **工具可替代方案**（最重要，只提供1-2个最合适的方案）：
   - 优先推荐免费开源替代工具
   - 其次推荐免费商业替代工具
   - 每个替代方案的优势和适用场景（重点说明为什么适合替代）
   - 替代方案的许可证类型
   - **重要：只提供1-2个最合适的替代方案，不要提供过多选项**

5. **其他合规信息**：
   - 数据使用条款
   - 隐私政策
   - 服务限制
   - 合规风险点

请以JSON格式返回分析结果，必须包含以下字段：
{{
    "license_type": "许可证类型（如：MIT、Apache 2.0、GPL v3、商业许可证等）",
    "license_version": "许可证版本号",
    "license_mode": "许可证模式（开源/商业/混合）",
    "company_name": "工具所属公司名称（开源工具填写null，如Docker CE、Linux等）",
    "company_country": "公司所属国家/地区（开源工具可为null）",
    "company_headquarters": "公司总部所在地（开源工具可为null）",
    "china_office": true/false/null,  // 是否有中国分公司或服务（开源工具可为false或null）
    "commercial_license_required": true/false,  // 商业用户是否必须购买license
    "free_for_commercial": true/false,  // 是否允许免费商业使用
    "commercial_restrictions": "商用用户使用的具体限制说明（用户数、功能、服务器等）",
    "user_limit": "用户数量限制（如：免费版最多5用户）",
    "feature_restrictions": "功能限制说明",
    "alternative_tools": [
        {{
            "name": "替代工具名称",
            "type": "开源/免费商业",
            "license": "替代工具的许可证类型",
            "advantages": "替代方案的优势（重点说明为什么适合替代）",
            "use_case": "适用场景"
        }}
    ],
    // 注意：替代工具建议只提供1-2个最合适的方案，优先推荐免费开源或免费商业的替代方案。
    "data_usage": "数据使用政策说明",
    "privacy_policy": "隐私政策说明",
    "service_restrictions": "服务限制说明",
    "risk_points": ["风险点1", "风险点2", ...],  // 合规风险点列表
    "compliance_notes": "合规性备注"
}}
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的法律和合规分析专家。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._call_api(messages)
        
        if response:
            try:
                # 尝试从markdown代码块中提取JSON
                json_str = self._extract_json_from_markdown(response)
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"TOS分析JSON解析失败: {tool_name}")
                logger.warning(f"原始响应内容（前500字符）: {response[:500] if response else 'None'}")  # 记录前500字符
                logger.warning(f"JSON解析错误: {e}")
                return {
                    "analysis": response,
                    "format": "text",
                    "risk_points": [],
                    "data_usage": "unknown",
                    "privacy_policy": "unknown"
                }
        
        return {"error": "TOS分析失败"}
    
    async def search_tos_url(
        self,
        tool_name: str
    ) -> Optional[str]:
        """搜索工具的TOS链接"""
        prompt = f"""请帮我找到工具 {tool_name} 的官方服务条款（Terms of Service）或隐私政策（Privacy Policy）的链接。

请直接返回链接URL，如果找不到请返回"NOT_FOUND"。
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的网络搜索助手。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._call_api(messages)
        
        if response and "NOT_FOUND" not in response.upper():
            # 尝试提取URL
            import re
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', response)
            if urls:
                return urls[0]
        
        return None
    
    async def analyze_tool_directly(
        self,
        tool_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        直接分析工具信息（不依赖TOS文档）
        
        Args:
            tool_name: 工具名称
        
        Returns:
            Optional[Dict[str, Any]]: 分析结果
        """
        prompt = f"""请分析工具 {tool_name} 的合规信息，重点关注以下4个方面：

1. **工具使用许可或开源协议类型**：
   - 许可证类型（如：MIT、Apache、GPL、BSD、商业许可证等）
   - 许可证版本号
   - 许可证模式（开源/商业/混合）

2. **工具所属公司和公司所属国家**：
   - 工具的开发商/公司名称
     * **重要：如果是开源工具（如Docker CE、Linux、PostgreSQL等），公司名称应填写为 null**
     * 只有商业软件或由特定公司维护的开源项目才填写公司名称
   - 公司注册国家/地区（开源工具可为null）
   - 公司总部所在地（开源工具可为null）
   - 是否有中国分公司或服务（开源工具可为false或null）

3. **商用用户使用的限制**：
   - 商业用户是否必须购买license？
   - 是否有免费版本可用于商业用途？
   - 商业使用的具体限制和条件
   - 用户数量、服务器数量等限制
   - 功能限制（免费版vs商业版）

4. **工具可替代方案**（只提供1-2个最合适的方案）：
   - 优先推荐免费开源替代工具
   - 其次推荐免费商业替代工具
   - 每个替代方案的优势（重点说明为什么适合替代）
   - 替代方案的许可证类型

请以JSON格式返回分析结果，必须包含以下字段：
{{
    "license_type": "许可证类型",
    "license_version": "许可证版本号",
    "license_mode": "许可证模式（开源/商业/混合）",
    "company_name": "工具所属公司名称（开源工具填写null，如Docker CE、Linux等）",
    "company_country": "公司所属国家/地区（开源工具可为null）",
    "company_headquarters": "公司总部所在地（开源工具可为null）",
    "china_office": true/false/null,  // 是否有中国分公司或服务（开源工具可为false或null）
    "commercial_license_required": true/false,
    "free_for_commercial": true/false,
    "commercial_restrictions": "商用用户使用的具体限制说明",
    "user_limit": "用户数量限制",
    "feature_restrictions": "功能限制说明",
    "alternative_tools": [
        {{
            "name": "替代工具名称",
            "type": "开源/免费商业",
            "license": "替代工具的许可证类型",
            "advantages": "替代方案的优势（重点说明为什么适合替代）",
            "use_case": "适用场景"
        }}
    ]
}}
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的工具合规性分析专家，能够基于工具名称分析其合规信息。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._call_api(messages)
        
        if response:
            try:
                # 尝试从markdown代码块中提取JSON
                json_str = self._extract_json_from_markdown(response)
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning(f"AI返回的JSON格式不正确: {tool_name}")
                return None
        
        return None
    
    async def get_alternative_tools(
        self,
        tool_name: str
    ) -> List[Dict[str, Any]]:
        """
        独立获取工具的替代方案（不依赖TOS分析）
        
        Args:
            tool_name: 工具名称
        
        Returns:
            List[Dict[str, Any]]: 替代工具列表（最多2个）
        """
        prompt = f"""请为工具 {tool_name} 推荐1-2个最合适的替代方案。

要求：
1. **优先推荐免费开源替代工具**
2. **其次推荐免费商业替代工具**
3. 每个替代方案需要包含：
   - 工具名称
   - 类型（开源/免费商业）
   - 许可证类型
   - 优势（重点说明为什么适合替代，比如：功能相似、性能更好、更安全、更易维护等）
   - 适用场景

请以JSON格式返回，格式如下：
{{
    "alternative_tools": [
        {{
            "name": "替代工具名称",
            "type": "开源/免费商业",
            "license": "替代工具的许可证类型",
            "advantages": "替代方案的优势（重点说明为什么适合替代）",
            "use_case": "适用场景"
        }}
    ]
}}

**重要：只提供1-2个最合适的替代方案，不要提供过多选项。**
"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的工具选型专家，能够为各种开发工具推荐合适的替代方案。"},
            {"role": "user", "content": prompt}
        ]
        
        response = await self._call_api(messages)
        
        if response:
            try:
                # 尝试从markdown代码块中提取JSON
                json_str = self._extract_json_from_markdown(response)
                result = json.loads(json_str)
                alternatives = result.get("alternative_tools", [])
                # 限制为最多2个
                return alternatives[:2]
            except json.JSONDecodeError as e:
                logger.warning(f"AI返回的替代方案JSON格式不正确: {tool_name}")
                logger.warning(f"原始响应内容（前500字符）: {response[:500] if response else 'None'}")  # 记录前500字符
                logger.warning(f"JSON解析错误: {e}")
                # 尝试从文本中提取
                return []
        
        return []


class OpenAIClient(AIClientBase):
    """OpenAI客户端（类似实现）"""
    
    def __init__(self):
        config = get_config()
        self.api_base = config.ai.openai.api_base
        self.api_key = config.ai.openai.api_key
        self.model = config.ai.openai.model
        self.temperature = config.ai.openai.temperature
        self.max_tokens = config.ai.openai.max_tokens
        self.timeout = config.ai.openai.timeout
    
    async def _call_api(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """调用OpenAI API（实现类似GLM）"""
        # TODO: 实现OpenAI API调用
        logger.warning("OpenAI客户端未完全实现")
        return None
    
    async def generate_compliance_suggestions(self, tool_name: str, tool_info: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"error": "OpenAI客户端未实现"}
    
    async def analyze_tos(self, tool_name: str, tos_content: str) -> Dict[str, Any]:
        return {"error": "OpenAI客户端未实现"}
    
    async def search_tos_url(self, tool_name: str) -> Optional[str]:
        return None


def get_ai_client() -> AIClientBase:
    """
    获取AI客户端实例（根据配置）
    
    Returns:
        AIClientBase: AI客户端实例
    """
    config = get_config()
    provider = config.ai.provider.lower()
    
    if provider == "glm":
        return GLMClient()
    elif provider == "openai":
        return OpenAIClient()
    else:
        logger.warning(f"不支持的AI provider: {provider}，使用GLM作为默认")
        return GLMClient()
