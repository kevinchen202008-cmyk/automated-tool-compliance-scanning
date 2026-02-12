"""
报告生成服务
Report generation service
"""

import json
from typing import Dict, Any, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from src.models import Tool, ComplianceReport, AlternativeTool
from src.logger import get_logger
from src.services.tool_knowledge_base import get_tool_basic_info
from src.services.knowledge_base_service import get_knowledge_base_dict, create_or_update_knowledge_base
from src.services.kb_diff_service import check_and_prepare_kb_update
from src.config import get_config

logger = get_logger()


class ReportService:
    """报告生成服务"""
    
    def __init__(self):
        self.config = get_config()
        self.output_path = Path(self.config.reporting.output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
    
    def generate_json_report(
        self,
        tool: Tool,
        report: ComplianceReport,
        db: Session
    ) -> Dict[str, Any]:
        """
        生成JSON格式的合规报告（包含工具信息库更新建议）
        
        Args:
            tool: 工具对象
            report: 合规报告对象
            db: 数据库会话
        
        Returns:
            Dict[str, Any]: JSON报告数据
        """
        # 解析JSON字段
        reasons = json.loads(report.reasons) if report.reasons else {}
        recommendations = json.loads(report.recommendations) if report.recommendations else {}
        references = json.loads(report.references) if report.references else {}
        
        # 解析TOS分析结果
        tos_analysis = {}
        if report.tos_analysis:
            try:
                tos_analysis = json.loads(report.tos_analysis) if isinstance(report.tos_analysis, str) else report.tos_analysis
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"解析TOS分析结果失败: {e}")
                tos_analysis = {}
        
        logger.debug(f"TOS分析结果: {tos_analysis}")
        
        # 获取知识库数据（用于对比）
        knowledge_base_data = get_knowledge_base_dict(db, tool.name)
        
        # 如果TOS分析数据不完整，尝试从知识库补充（用于处理旧数据）
        if not tos_analysis or len(tos_analysis) == 0 or not tos_analysis.get("license_type") or tos_analysis.get("license_type") == "未知":
            # 优先从数据库知识库获取，如果没有则从内置知识库获取
            if not knowledge_base_data:
                kb_info = get_tool_basic_info(tool.name, db)
                if kb_info:
                    tos_analysis = kb_info
                    logger.info(f"从知识库补充报告数据: {tool.name}")
            else:
                tos_analysis = knowledge_base_data
                logger.info(f"从数据库知识库补充报告数据: {tool.name}")
        
        # 获取替代工具
        alternatives = db.query(AlternativeTool).filter(
            AlternativeTool.id.in_(
                # TODO: 从recommendations中获取替代工具ID
                []
            )
        ).all()
        
        # 从TOS分析中提取关键信息
        license_info = {
            "license_type": tos_analysis.get("license_type", "未知"),
            "license_version": tos_analysis.get("license_version", ""),
            "license_mode": tos_analysis.get("license_mode", "未知")
        }
        
        # 处理公司信息，开源工具的公司名称可能为null
        company_name_raw = tos_analysis.get("company_name")
        company_name = None
        if company_name_raw is None or company_name_raw == "null" or company_name_raw == "":
            company_name = "开源工具（无特定公司）"
        elif company_name_raw != "未知":
            company_name = company_name_raw
        else:
            company_name = "未知"
        
        company_info = {
            "company_name": company_name,
            "company_country": tos_analysis.get("company_country") or "未知",
            "company_headquarters": tos_analysis.get("company_headquarters") or "未知",
            "china_office": tos_analysis.get("china_office", False)
        }
        
        commercial_restrictions = {
            "commercial_license_required": tos_analysis.get("commercial_license_required", False),
            "free_for_commercial": tos_analysis.get("free_for_commercial", False),
            "restrictions": tos_analysis.get("commercial_restrictions", ""),
            "user_limit": tos_analysis.get("user_limit", ""),
            "feature_restrictions": tos_analysis.get("feature_restrictions", "")
        }
        
        # 从TOS分析中获取替代工具，如果没有则使用数据库中的
        # 只取前2个替代方案
        tos_alternatives = tos_analysis.get("alternative_tools", [])[:2] if tos_analysis else []  # 限制为最多2个
        
        # 如果TOS分析中没有替代工具，尝试从数据库获取
        if not tos_alternatives:
            tos_alternatives = [
                {
                    "name": alt.name,
                    "type": "开源/免费商业",
                    "license": alt.license,
                    "advantages": alt.reason,
                    "use_case": "替代方案",
                    "link": alt.link
                }
                for alt in alternatives[:2]  # 限制为最多2个
            ]
        
        json_report = {
            "tool": {
                "id": tool.id,
                "name": tool.name,
                "version": tool.version,
                "source": tool.source,
                "tos_url": tool.tos_url
            },
            # 数据来源标识
            "data_source": {
                "ai_analysis": tos_analysis and len(tos_analysis) > 0 and "error" not in tos_analysis,
                "knowledge_base": knowledge_base_data is not None
            },
            # 知识库数据（用于对比，如果存在）
            "knowledge_base_data": knowledge_base_data,
            # 重点信息：许可证信息
            "license_info": license_info,
            # 重点信息：公司信息
            "company_info": company_info,
            # 重点信息：商用限制
            "commercial_restrictions": commercial_restrictions,
            # 重点信息：替代方案
            "alternative_tools": tos_alternatives,
            "compliance_report": {
                "id": report.id,
                # 多维度评分（暂时禁用，提升性能）
                "score_overall": report.score_overall if report.score_overall is not None else None,
                "score_security": report.score_security if report.score_security is not None else None,
                "score_license": report.score_license if report.score_license is not None else None,
                "score_maintenance": report.score_maintenance if report.score_maintenance is not None else None,
                "score_performance": report.score_performance if report.score_performance is not None else None,
                "score_tos": report.score_tos if report.score_tos is not None else None,
                "is_compliant": report.is_compliant if report.is_compliant is not None else None,
                "reasons": reasons,
                "recommendations": recommendations,
                "references": references,
                "tos_analysis": tos_analysis  # 完整的TOS分析结果
            },
            "metadata": {
                "generated_at": report.created_at.isoformat() if hasattr(report, 'created_at') else None,
                "report_version": "1.0"
            },
            # 知识库更新信息
            "knowledge_base_update": self._prepare_kb_update_info(tool, tos_analysis, db)
        }
        
        return json_report
    
    def _prepare_kb_update_info(
        self,
        tool: Tool,
        tos_analysis: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        准备工具信息库（Tool Information Store）更新信息
        
        Args:
            tool: 工具对象
            tos_analysis: TOS分析结果
            db: 数据库会话
        
        Returns:
            Dict[str, Any]: 知识库更新信息
        """
        if not tos_analysis or len(tos_analysis) == 0:
            return {
                "available": False,
                "reason": "TOS 分析数据不完整，无法更新工具信息库"
            }
        
        try:
            kb_update_info = check_and_prepare_kb_update(tool.name, tos_analysis, db)
            
            if kb_update_info["should_auto_create"]:
                # 新工具，需要用户确认后才创建到工具信息库
                logger.info(f"发现新工具，等待用户确认入库: {tool.name}")
                return {
                    "available": True,
                    "action": "pending_creation",
                    "message": "发现新工具，请确认是否添加到工具信息库",
                    "new_data": kb_update_info["new_data"],
                    "tool_name": tool.name
                }
            else:
                # 工具信息库中已存在记录，返回差异对比信息
                diff = kb_update_info["diff"]
                return {
                    "available": True,
                    "action": "diff_available",
                    "exists": True,
                    "has_changes": diff["has_changes"],
                    "change_count": diff["change_count"],
                    "summary": diff["summary"],
                    "changes": diff["changes"][:10]  # 只返回前10个差异，避免数据过大
                }
        except Exception as e:
            logger.error(f"准备工具信息库更新信息失败: {tool.name} - {e}")
            return {
                "available": False,
                "reason": "处理失败，请查看服务端日志"
            }
    
    def save_json_report(
        self,
        tool: Tool,
        report: ComplianceReport,
        db: Session
    ) -> Path:
        """
        保存JSON报告到文件
        
        Args:
            tool: 工具对象
            report: 合规报告对象
            db: 数据库会话
        
        Returns:
            Path: 保存的文件路径
        """
        json_report = self.generate_json_report(tool, report, db)
        
        # 生成文件名
        filename = f"report_{tool.name}_{report.id}.json"
        filepath = self.output_path / filename
        
        # 保存文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON报告已保存: {filepath}")
        return filepath
    
    def get_report_summary(
        self,
        tool: Tool,
        report: ComplianceReport
    ) -> Dict[str, Any]:
        """
        获取报告摘要
        
        Args:
            tool: 工具对象
            report: 合规报告对象
        
        Returns:
            Dict[str, Any]: 报告摘要
        """
        reasons = json.loads(report.reasons) if report.reasons else {}
        
        return {
            "tool_name": tool.name,
            "tool_version": tool.version,
            "is_compliant": report.is_compliant,
            "overall_score": report.score_overall,
            "key_issues": reasons.get("reasons", []),
            "summary": f"工具 {tool.name} 的合规性评分为 {report.score_overall}，"
                      f"{'符合' if report.is_compliant else '不符合'}合规要求。"
        }


def get_report_service() -> ReportService:
    """
    获取报告服务实例（单例模式）
    
    Returns:
        ReportService: 报告服务实例
    """
    return ReportService()
