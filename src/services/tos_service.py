"""
TOS（服务条款）信息获取和分析服务
Terms of Service information retrieval and analysis service
"""

import json
import httpx
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Tool
from src.logger import get_logger
from src.config import get_config
from src.services.ai_client import get_ai_client

logger = get_logger()


async def search_tos_url(tool_name: str) -> Optional[str]:
    """
    通过联网搜索获取工具的TOS链接
    
    Args:
        tool_name: 工具名称
    
    Returns:
        Optional[str]: TOS文档链接，如果无法获取返回None
    """
    try:
        # 使用AI客户端搜索TOS链接
        ai_client = get_ai_client()
        tos_url = await ai_client.search_tos_url(tool_name)
        
        if tos_url:
            logger.info(f"通过AI服务找到TOS链接: {tool_name} - {tos_url}")
            return tos_url
        
        logger.warning(f"无法找到工具 {tool_name} 的TOS链接")
        return None
        
    except Exception as e:
        logger.error(f"搜索TOS链接失败: {tool_name} - {e}")
        return None


async def fetch_tos_content(tos_url: str) -> Optional[str]:
    """
    获取TOS文档内容
    
    Args:
        tos_url: TOS文档链接
    
    Returns:
        Optional[str]: TOS文档内容，如果无法获取返回None
    """
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(tos_url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.warning(f"获取TOS内容失败: {tos_url} - {e}")
        return None


async def analyze_tos_with_ai(tool_name: str, tos_content: str) -> Optional[Dict[str, Any]]:
    """
    使用AI服务分析TOS内容
    
    Args:
        tool_name: 工具名称
        tos_content: TOS文档内容
    
    Returns:
        Optional[Dict[str, Any]]: TOS分析结果，如果分析失败返回None
    """
    try:
        # 使用AI客户端分析TOS
        ai_client = get_ai_client()
        analysis_result = await ai_client.analyze_tos(tool_name, tos_content)
        
        if "error" not in analysis_result:
            logger.info(f"TOS分析完成: {tool_name}")
            return analysis_result
        else:
            logger.warning(f"TOS分析失败: {tool_name} - {analysis_result.get('error')}")
            return None
            
    except Exception as e:
        logger.error(f"TOS分析异常: {tool_name} - {e}")
        return None


async def get_and_analyze_tos(tool: Tool, db: Session) -> Dict[str, Any]:
    """
    获取并分析工具的TOS信息
    
    Args:
        tool: 工具对象
        db: 数据库会话
    
    Returns:
        Dict[str, Any]: TOS信息和分析结果
    """
    result = {
        "tos_url": None,
        "tos_content": None,
        "tos_analysis": None,
        "success": False,
        "error": None
    }
    
    try:
        # 1. 搜索TOS链接
        tos_url = await search_tos_url(tool.name)
        
        if not tos_url:
            # 如果搜索不到，尝试使用AI服务搜索
            try:
                ai_client = get_ai_client()
                tos_url = await ai_client.search_tos_url(tool.name)
                logger.info(f"通过AI服务搜索TOS链接: {tool.name}")
            except Exception as e:
                logger.warning(f"AI搜索TOS链接失败: {e}")
        
        if not tos_url:
            logger.warning(f"无法找到工具 {tool.name} 的TOS链接，将使用AI直接分析")
            # 即使没有TOS链接，也尝试使用AI直接分析工具信息
            try:
                ai_client = get_ai_client()
                # 使用AI直接分析工具，不依赖TOS文档
                analysis_result = await ai_client.analyze_tool_directly(tool.name)
                if analysis_result and "error" not in analysis_result:
                    result["tos_analysis"] = analysis_result
                    result["success"] = True
                    # 保存到数据库
                    tool.tos_info = json.dumps(analysis_result, ensure_ascii=False)
                    db.commit()
                    db.refresh(tool)
                    logger.info(f"通过AI直接分析工具信息成功: {tool.name}")
                    return result
            except Exception as e:
                logger.error(f"AI直接分析失败: {e}")
            
            result["error"] = "无法找到TOS链接，且AI分析失败"
            # 返回空的分析结果，让前端显示"待分析"
            result["tos_analysis"] = {}
            return result
        
        result["tos_url"] = tos_url
        
        # 2. 获取TOS内容
        tos_content = await fetch_tos_content(tos_url)
        
        if not tos_content:
            result["error"] = "无法获取TOS内容"
            return result
        
        result["tos_content"] = tos_content
        
        # 3. 使用AI分析TOS
        tos_analysis = await analyze_tos_with_ai(tool.name, tos_content)
        
        if tos_analysis:
            result["tos_analysis"] = tos_analysis
            result["success"] = True
            
            # 4. 保存到数据库
            tool.tos_url = tos_url
            tool.tos_info = json.dumps({
                "content": tos_content[:1000],  # 只保存前1000字符
                "analysis": tos_analysis
            }, ensure_ascii=False)
            db.commit()
            db.refresh(tool)
            
            logger.info(f"成功获取并分析工具TOS: {tool.name}")
        else:
            result["error"] = "TOS分析失败"
            
    except Exception as e:
        logger.error(f"获取和分析TOS失败: {tool.name} - {e}")
        result["error"] = "获取和分析TOS失败，请查看服务端日志"
    
    return result
