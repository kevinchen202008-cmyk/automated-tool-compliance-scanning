"""
合规规则引擎
Compliance rule engine for multi-dimensional compliance assessment
"""

import json
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from src.models import Tool, ComplianceReport
from src.logger import get_logger
from src.config import get_config
from src.services.ai_client import get_ai_client

logger = get_logger()


class ComplianceEngine:
    """合规规则引擎"""
    
    def __init__(self):
        self.config = get_config()
        self.compliance_config = self.config.compliance
        self.ai_client = get_ai_client()
    
    async def assess_security(self, tool: Tool, tool_info: Dict[str, Any]) -> float:
        """
        评估安全性维度
        
        Args:
            tool: 工具对象
            tool_info: 工具信息
        
        Returns:
            float: 安全性评分（0-100）
        """
        # TODO: 实现实际的安全性评估逻辑
        # 可以检查：
        # 1. 已知漏洞数据库
        # 2. 安全配置
        # 3. 安全最佳实践
        
        logger.debug(f"评估安全性: {tool.name}")
        
        # 使用AI辅助评估
        try:
            ai_result = await self.ai_client.generate_compliance_suggestions(
                tool.name,
                tool_info,
                {"dimension": "security"}
            )
            
            if "security_score" in ai_result:
                return float(ai_result["security_score"])
        except Exception as e:
            logger.warning(f"AI安全性评估失败: {e}")
        
        # 默认评分
        return 70.0
    
    async def assess_license(self, tool: Tool, tool_info: Dict[str, Any], tos_analysis: Optional[Dict[str, Any]] = None) -> float:
        """
        评估许可证合规维度
        
        Args:
            tool: 工具对象
            tool_info: 工具信息
            tos_analysis: TOS分析结果（可选）
        
        Returns:
            float: 许可证合规评分（0-100）
        """
        logger.debug(f"评估许可证合规: {tool.name}")
        
        # 如果TOS分析中包含license信息，优先使用
        if tos_analysis:
            commercial_license_required = tos_analysis.get("commercial_license_required", False)
            free_for_commercial = tos_analysis.get("free_for_commercial", False)
            
            # 如果商业用户必须购买license，评分降低
            if commercial_license_required and not free_for_commercial:
                logger.warning(f"工具 {tool.name} 需要商业license，可能增加合规成本")
                return 60.0  # 需要购买license，评分较低
            elif free_for_commercial:
                logger.info(f"工具 {tool.name} 允许免费商业使用")
                return 90.0  # 允许免费商业使用，评分较高
            else:
                # 需要进一步分析
                return 70.0
        
        # 如果没有TOS分析，使用AI评估
        try:
            ai_result = await self.ai_client.generate_compliance_suggestions(
                tool.name,
                tool_info,
                {"dimension": "license"}
            )
            
            if "license_score" in ai_result:
                return float(ai_result["license_score"])
        except Exception as e:
            logger.warning(f"AI许可证评估失败: {e}")
        
        return 75.0
    
    async def assess_maintenance(self, tool: Tool, tool_info: Dict[str, Any]) -> float:
        """
        评估维护性维度
        
        Args:
            tool: 工具对象
            tool_info: 工具信息
        
        Returns:
            float: 维护性评分（0-100）
        """
        logger.debug(f"评估维护性: {tool.name}")
        
        # TODO: 实现维护性检查逻辑
        # 可以检查：
        # 1. 更新频率
        # 2. 社区活跃度
        # 3. 维护状态
        
        try:
            ai_result = await self.ai_client.generate_compliance_suggestions(
                tool.name,
                tool_info,
                {"dimension": "maintenance"}
            )
            
            if "maintenance_score" in ai_result:
                return float(ai_result["maintenance_score"])
        except Exception as e:
            logger.warning(f"AI维护性评估失败: {e}")
        
        return 65.0
    
    async def assess_performance(self, tool: Tool, tool_info: Dict[str, Any]) -> float:
        """
        评估性能/稳定性维度
        
        Args:
            tool: 工具对象
            tool_info: 工具信息
        
        Returns:
            float: 性能评分（0-100）
        """
        logger.debug(f"评估性能: {tool.name}")
        
        # 初期可以弱化此维度
        return 80.0
    
    async def assess_tos(self, tool: Tool, tos_analysis: Optional[Dict[str, Any]]) -> float:
        """
        评估TOS（服务条款）合规性维度
        
        Args:
            tool: 工具对象
            tos_analysis: TOS分析结果
        
        Returns:
            float: TOS合规性评分（0-100）
        """
        logger.debug(f"评估TOS合规性: {tool.name}")
        
        if not tos_analysis:
            logger.warning(f"工具 {tool.name} 没有TOS分析结果")
            return 50.0  # 没有TOS信息时给中等评分
        
        # 根据TOS分析结果评估
        risk_points = tos_analysis.get("risk_points", [])
        risk_count = len(risk_points) if isinstance(risk_points, list) else 0
        
        # 风险点越多，评分越低
        base_score = 100.0
        if risk_count > 0:
            base_score = max(0, 100 - risk_count * 10)
        
        # 检查关键合规项
        data_usage = tos_analysis.get("data_usage", "unknown")
        privacy_policy = tos_analysis.get("privacy_policy", "unknown")
        
        if data_usage == "restrictive" or privacy_policy == "unclear":
            base_score = max(0, base_score - 20)
        
        return base_score
    
    async def assess_all_dimensions(
        self,
        tool: Tool,
        tool_info: Dict[str, Any],
        tos_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        评估所有维度
        
        Args:
            tool: 工具对象
            tool_info: 工具信息
            tos_analysis: TOS分析结果
        
        Returns:
            Dict[str, float]: 各维度评分
        """
        logger.info(f"开始多维度合规评估: {tool.name}")
        
        scores = {
            "security": await self.assess_security(tool, tool_info),
            "license": await self.assess_license(tool, tool_info, tos_analysis),  # 传递TOS分析结果以评估商业license要求
            "maintenance": await self.assess_maintenance(tool, tool_info),
            "performance": await self.assess_performance(tool, tool_info),
            "tos": await self.assess_tos(tool, tos_analysis)
        }
        
        logger.info(f"合规评估完成: {tool.name} - {scores}")
        return scores
    
    def calculate_overall_score(self, dimension_scores: Dict[str, float]) -> float:
        """
        计算综合合规评分
        
        Args:
            dimension_scores: 各维度评分
        
        Returns:
            float: 综合评分（0-100）
        """
        scoring = self.compliance_config.scoring
        
        # 计算加权平均
        weights = {
            "security": scoring.security,
            "license": scoring.license,
            "maintenance": scoring.maintenance,
            "performance": scoring.performance,
            "tos": scoring.tos if hasattr(scoring, 'tos') else 0.0
        }
        
        # 确保权重总和为1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}
        
        overall_score = sum(
            dimension_scores.get(dim, 0) * weight
            for dim, weight in weights.items()
        )
        
        return round(overall_score, 2)
    
    def is_compliant(self, overall_score: float, threshold: float = 70.0) -> bool:
        """
        判断是否合规
        
        Args:
            overall_score: 综合评分
            threshold: 合规阈值（默认70）
        
        Returns:
            bool: 是否合规
        """
        return overall_score >= threshold
    
    async def generate_compliance_report(
        self,
        tool: Tool,
        db: Session,
        tool_info: Dict[str, Any],
        tos_analysis: Optional[Dict[str, Any]] = None
    ) -> ComplianceReport:
        """
        生成合规报告
        
        Args:
            tool: 工具对象
            db: 数据库会话
            tool_info: 工具信息
            tos_analysis: TOS分析结果
        
        Returns:
            ComplianceReport: 合规报告对象
        """
        # 检查是否启用多维度评估
        enable_assessment = self.compliance_config.enable_multi_dimension_assessment
        
        if enable_assessment:
            # 评估所有维度
            dimension_scores = await self.assess_all_dimensions(tool, tool_info, tos_analysis)
            
            # 计算综合评分
            overall_score = self.calculate_overall_score(dimension_scores)
            
            # 判断是否合规
            is_compliant = self.is_compliant(overall_score)
            
            # 生成建议和原因（传递TOS分析结果以获取替代工具信息）
            recommendations = self._generate_recommendations(dimension_scores, tool_info, tos_analysis)
            reasons = self._generate_reasons(dimension_scores, is_compliant, tos_analysis)
        else:
            # 简化模式：仅保存TOS分析结果，不进行多维度评估
            logger.info(f"使用简化模式生成报告: {tool.name}（跳过多维度评估）")
            dimension_scores = {}
            overall_score = None
            is_compliant = None
            recommendations = {"recommendations": [], "alternative_tools": []}
            reasons = {"is_compliant": None, "reasons": []}
        
        # 获取或创建报告
        report = db.query(ComplianceReport).filter(
            ComplianceReport.tool_id == tool.id
        ).first()
        
        if not report:
            report = ComplianceReport(tool_id=tool.id)
            db.add(report)
        
        # 更新报告
        if enable_assessment:
            report.score_overall = overall_score
            report.score_security = dimension_scores.get("security")
            report.score_license = dimension_scores.get("license")
            report.score_maintenance = dimension_scores.get("maintenance")
            report.score_performance = dimension_scores.get("performance")
            report.score_tos = dimension_scores.get("tos")
            report.is_compliant = is_compliant
        else:
            # 简化模式：评分字段设为None
            report.score_overall = None
            report.score_security = None
            report.score_license = None
            report.score_maintenance = None
            report.score_performance = None
            report.score_tos = None
            report.is_compliant = None
        
        report.reasons = json.dumps(reasons, ensure_ascii=False)
        report.recommendations = json.dumps(recommendations, ensure_ascii=False)
        report.tos_analysis = json.dumps(tos_analysis or {}, ensure_ascii=False)
        report.references = json.dumps({}, ensure_ascii=False)
        
        db.commit()
        db.refresh(report)
        
        if enable_assessment:
            logger.info(f"合规报告生成完成: {tool.name} - 综合评分: {overall_score}")
        else:
            logger.info(f"合规报告生成完成: {tool.name} - 简化模式（仅TOS分析）")
        return report
    
    def _generate_recommendations(
        self,
        dimension_scores: Dict[str, float],
        tool_info: Dict[str, Any],
        tos_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成合规建议"""
        recommendations = []
        alternative_tools = []
        
        # 从TOS分析中提取替代工具信息
        if tos_analysis:
            tos_alternatives = tos_analysis.get("alternative_tools", [])
            if tos_alternatives:
                alternative_tools = tos_alternatives
        
        # 检查商业license要求
        if tos_analysis:
            commercial_license_required = tos_analysis.get("commercial_license_required", False)
            free_for_commercial = tos_analysis.get("free_for_commercial", False)
            license_type = tos_analysis.get("license_type", "未知")
            commercial_restrictions = tos_analysis.get("commercial_restrictions", "")
            
            if commercial_license_required and not free_for_commercial:
                recommendations.append({
                    "dimension": "license",
                    "priority": "high",
                    "suggestion": f"⚠️ 商业用户必须购买license（类型：{license_type}）。{commercial_restrictions}",
                    "action": "需要评估license成本和预算",
                    "alternatives_available": len(alternative_tools) > 0
                })
            elif free_for_commercial:
                recommendations.append({
                    "dimension": "license",
                    "priority": "low",
                    "suggestion": "✓ 允许免费商业使用，无需购买license",
                    "action": "可继续使用"
                })
        
        # 检查其他维度
        for dimension, score in dimension_scores.items():
            if score < 70 and dimension != "license":  # license已在上面处理
                recommendations.append({
                    "dimension": dimension,
                    "score": score,
                    "priority": "medium",
                    "suggestion": f"建议改进 {dimension} 维度的合规性（当前评分：{score}）"
                })
        
        return {
            "recommendations": recommendations,
            "alternative_tools": alternative_tools  # 使用TOS分析中的替代工具
        }
    
    def _generate_reasons(
        self,
        dimension_scores: Dict[str, float],
        is_compliant: bool,
        tos_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成不合规原因"""
        reasons = []
        
        # 检查商业license要求
        if tos_analysis:
            commercial_license_required = tos_analysis.get("commercial_license_required", False)
            free_for_commercial = tos_analysis.get("free_for_commercial", False)
            
            if commercial_license_required and not free_for_commercial:
                reasons.append({
                    "dimension": "license",
                    "score": dimension_scores.get("license", 0),
                    "reason": f"商业用户必须购买license。{tos_analysis.get('commercial_restrictions', '')}",
                    "impact": "high"
                })
        
        if not is_compliant:
            for dimension, score in dimension_scores.items():
                if score < 70 and dimension != "license":  # license已在上面处理
                    reasons.append({
                        "dimension": dimension,
                        "score": score,
                        "reason": f"{dimension} 维度评分低于阈值（{score} < 70）",
                        "impact": "medium"
                    })
        
        return {
            "is_compliant": is_compliant,
            "reasons": reasons,
            "commercial_license_required": tos_analysis.get("commercial_license_required", False) if tos_analysis else False
        }


def get_compliance_engine() -> ComplianceEngine:
    """
    获取合规引擎实例（单例模式）
    
    Returns:
        ComplianceEngine: 合规引擎实例
    """
    return ComplianceEngine()
