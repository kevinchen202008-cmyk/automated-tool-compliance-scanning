"""
工具知识库：提供常见工具的基本信息（作为AI分析失败的降级方案）
Tool knowledge base: Provides basic information for common tools (as fallback when AI analysis fails)

支持两种数据源：
1. 内置知识库（代码中的TOOL_KNOWLEDGE_BASE字典）
2. 数据库知识库（用户可更新）
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

# 常见工具的基本信息（开源工具优先）
TOOL_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "Docker CE": {
        "license_type": "Apache 2.0",
        "license_version": "2.0",
        "license_mode": "开源",
        "company_name": None,  # 开源工具
        "company_country": None,
        "company_headquarters": None,
        "china_office": False,
        "commercial_license_required": False,
        "free_for_commercial": True,
        "commercial_restrictions": "Docker CE采用Apache 2.0许可证，允许商业使用，但需遵守许可证条款，包括保留版权声明和许可证文本。",
        "user_limit": "无用户数量限制",
        "feature_restrictions": "Docker CE提供核心容器化功能，企业级功能如Docker Trusted Registry、Docker Datacenter等需要商业版Docker Enterprise。",
        "alternative_tools": [
            {
                "name": "Podman",
                "type": "开源",
                "license": "Apache 2.0",
                "advantages": "Podman是无守护进程的容器引擎，与Docker兼容，无需root权限运行，更适合安全敏感环境，且完全开源无商业限制。",
                "use_case": "适合需要容器化但希望避免守护进程风险的组织，以及希望完全控制容器运行环境的场景。"
            },
            {
                "name": "containerd",
                "type": "开源",
                "license": "Apache 2.0",
                "advantages": "containerd是行业标准容器运行时，被Docker、Kubernetes等广泛采用，轻量级、稳定可靠，专注于核心容器功能。",
                "use_case": "适合构建自定义容器解决方案或需要更底层容器控制的企业环境。"
            }
        ]
    },
    "Docker Desktop": {
        "license_type": "商业许可证",
        "license_version": "",
        "license_mode": "商业",
        "company_name": "Docker Inc.",
        "company_country": "美国",
        "company_headquarters": "旧金山",
        "china_office": False,
        "commercial_license_required": True,
        "free_for_commercial": False,
        "commercial_restrictions": "Docker Desktop个人使用免费，但商业使用需要购买Docker Desktop Business或Docker Enterprise订阅。",
        "user_limit": "个人版免费，商业版按用户数收费",
        "feature_restrictions": "个人版功能受限，商业版提供完整功能和支持。",
        "alternative_tools": [
            {
                "name": "Docker CE",
                "type": "开源",
                "license": "Apache 2.0",
                "advantages": "Docker CE是Docker的开源版本，提供核心容器化功能，完全免费且允许商业使用，适合不需要企业级功能的场景。",
                "use_case": "适合个人开发者、小团队或不需要企业级支持的组织。"
            },
            {
                "name": "Podman",
                "type": "开源",
                "license": "Apache 2.0",
                "advantages": "Podman是无守护进程的容器引擎，与Docker兼容，无需root权限运行，更适合安全敏感环境，且完全开源无商业限制。",
                "use_case": "适合需要容器化但希望避免守护进程风险的组织，以及希望完全控制容器运行环境的场景。"
            }
        ]
    },
    "Anaconda": {
        "license_type": "商业许可证（个人版免费）",
        "license_version": "",
        "license_mode": "混合",
        "company_name": "Anaconda Inc.",
        "company_country": "美国",
        "company_headquarters": "奥斯汀",
        "china_office": False,
        "commercial_license_required": True,
        "free_for_commercial": False,
        "commercial_restrictions": "Anaconda个人版免费，但商业使用（超过200名员工的组织）需要购买商业许可证。",
        "user_limit": "个人版免费，商业版按组织规模收费",
        "feature_restrictions": "个人版功能完整，但商业使用需要许可证。",
        "alternative_tools": [
            {
                "name": "Miniconda",
                "type": "开源",
                "license": "BSD",
                "advantages": "Miniconda是Anaconda的轻量级版本，只包含conda和Python，完全免费且允许商业使用，适合需要最小化安装的场景。",
                "use_case": "适合需要conda包管理但不需要Anaconda完整发行版的用户和组织。"
            },
            {
                "name": "Python + pip",
                "type": "开源",
                "license": "PSF",
                "advantages": "Python官方发行版配合pip包管理器，完全免费开源，允许商业使用，是Python生态系统的标准选择。",
                "use_case": "适合不需要conda环境管理功能的Python项目。"
            }
        ]
    },
    "Postman": {
        "license_type": "商业许可证（免费版有限制）",
        "license_version": "",
        "license_mode": "商业",
        "company_name": "Postman Inc.",
        "company_country": "美国",
        "company_headquarters": "旧金山",
        "china_office": False,
        "commercial_license_required": True,
        "free_for_commercial": False,
        "commercial_restrictions": "Postman个人版免费，但商业使用需要购买Postman Business或Enterprise许可证。免费版有API调用次数限制和团队协作功能限制。",
        "user_limit": "个人版免费，商业版按用户数收费",
        "feature_restrictions": "免费版功能受限，商业版提供完整功能、无限制API调用和团队协作功能。",
        "alternative_tools": [
            {
                "name": "Bruno",
                "type": "开源",
                "license": "MIT",
                "advantages": "数据完全存储在本地文件系统中，解决了Postman的云端数据隐私和厂商锁定问题。原生支持Git版本控制，便于团队协作和代码审查。轻量级、启动速度快，无广告干扰。脚本语法与Postman高度兼容，迁移成本低。",
                "use_case": "适合注重数据隐私与安全的开发者，需要通过Git管理API集合的团队，寻求轻量级且开源的Postman替代方案的用户。"
            },
            {
                "name": "Insomnia",
                "type": "免费商业",
                "license": "专有软件（部分核心组件开源）",
                "advantages": "界面简洁现代，响应速度快。原生支持GraphQL、gRPC和Socket.IO，不仅限于REST API。拥有强大的插件生态。免费版功能已足够满足大多数个人和小型团队的需求，且没有Postman那样频繁的弹窗干扰。",
                "use_case": "适合需要调试GraphQL或gRPC接口的开发者，喜欢极简UI设计的用户，寻找稳定且功能丰富的免费商业工具的团队。"
            }
        ]
    },
    # 可以继续添加其他常见工具
}


def get_tool_basic_info(tool_name: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
    """
    从知识库获取工具的基本信息
    
    优先从数据库知识库获取，如果不存在则从内置知识库获取
    
    Args:
        tool_name: 工具名称
        db: 数据库会话（可选）
    
    Returns:
        Optional[Dict[str, Any]]: 工具基本信息，如果不存在返回None
    """
    # 1. 优先从数据库知识库获取
    if db:
        try:
            from src.services.knowledge_base_service import get_knowledge_base_dict
            db_entry = get_knowledge_base_dict(db, tool_name)
            if db_entry:
                # 移除元数据字段，只返回数据字段
                result = {k: v for k, v in db_entry.items() 
                         if k not in ['source', 'updated_by', 'created_at', 'updated_at']}
                return result
        except Exception as e:
            # 如果数据库查询失败，继续使用内置知识库
            pass
    
    # 2. 从内置知识库获取
    # 精确匹配
    if tool_name in TOOL_KNOWLEDGE_BASE:
        return TOOL_KNOWLEDGE_BASE[tool_name].copy()
    
    # 模糊匹配（不区分大小写）
    tool_name_lower = tool_name.lower()
    for key, value in TOOL_KNOWLEDGE_BASE.items():
        if key.lower() == tool_name_lower:
            return value.copy()
    
    # 部分匹配（如 "Docker" 匹配 "Docker CE"）
    for key, value in TOOL_KNOWLEDGE_BASE.items():
        if tool_name_lower in key.lower() or key.lower() in tool_name_lower:
            return value.copy()
    
    return None


def merge_tos_analysis_with_knowledge_base(
    tool_name: str,
    tos_analysis: Optional[Dict[str, Any]],
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    合并TOS分析结果和知识库信息
    
    优先使用AI分析结果，知识库数据仅作为补充
    
    Args:
        tool_name: 工具名称
        tos_analysis: TOS分析结果（可能为空或部分数据）
        db: 数据库会话（可选）
    
    Returns:
        Dict[str, Any]: 合并后的分析结果
    """
    # 获取知识库数据
    kb_info = get_tool_basic_info(tool_name, db)
    
    # 如果TOS分析有数据，优先使用AI结果
    if tos_analysis and len(tos_analysis) > 0 and "error" not in tos_analysis:
        # 如果TOS分析中缺少关键信息（license_type为空、None或"未知"），尝试从知识库补充
        license_type = tos_analysis.get("license_type")
        if not license_type or license_type == "未知" or license_type == "unknown" or license_type.lower() == "null":
            if kb_info:
                # 补充缺失的字段
                if not tos_analysis.get("license_type") or tos_analysis.get("license_type") in ["未知", "unknown", "null", None]:
                    tos_analysis["license_type"] = kb_info.get("license_type")
                if not tos_analysis.get("license_version"):
                    tos_analysis["license_version"] = kb_info.get("license_version")
                if not tos_analysis.get("license_mode") or tos_analysis.get("license_mode") in ["未知", "unknown", "null", None]:
                    tos_analysis["license_mode"] = kb_info.get("license_mode")
                # 补充公司信息（如果缺失）
                if not tos_analysis.get("company_name") or tos_analysis.get("company_name") in ["未知", "unknown", "null", None]:
                    tos_analysis["company_name"] = kb_info.get("company_name")
                # 如果TOS分析中没有替代方案，使用知识库的
                if not tos_analysis.get("alternative_tools"):
                    tos_analysis["alternative_tools"] = kb_info.get("alternative_tools", [])
        return tos_analysis
    
    # 如果TOS分析失败或为空（None或空字典），使用知识库信息
    if kb_info:
        return kb_info
    
    # 如果知识库也没有，返回空字典
    return {}
