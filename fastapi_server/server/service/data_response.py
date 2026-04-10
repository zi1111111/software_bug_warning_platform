"""
关于前端图表，趋势，分析所需数据的相关处理和请求
"""
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, exists, distinct
from sqlalchemy.orm import Session, aliased

from server.db.database import get_db
from server.service.models import LLMAnalyse, GithubCommit
from server.service.schemas import (
    GetVulnDailyResponse, GetVulnDaily, LLMAnalyseOut,
    GetTrendAnalysis, GetTrendAnalysisResponse,
    TrendDataPoint, SeverityDistributionItem, ComponentRankingItem, VulnTypeDistributionItem,
    GetRiskAssessment, GetRiskAssessmentResponse,
    RiskScoreData, RiskBreakdown, RiskDistributionItem,
    ComponentRiskItem, AttackSurfaceData, PriorityRecommendationItem, RiskTrendPoint, ReviewResult
)

router = APIRouter()


@router.post("/getVulnDaily", response_model=GetVulnDailyResponse)
async def get_vuln_daily(
        request: GetVulnDaily,
        db: Session = Depends(get_db)
):
    repo_id = request.id
    date = request.date
    page = request.page
    page_size = request.page_size
    severity_list = request.severity or []
    vuln_type_list = request.vuln_type or []  # 新增：漏洞类型筛选

    day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    # ================= 1. 基础查询（关联仓库，安全相关，日期匹配） =================
    base_query = db.query(LLMAnalyse).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        GithubCommit.commit_date >= day_start,
        GithubCommit.commit_date <= day_end
    )

    # 严重程度筛选
    if severity_list:
        base_query = base_query.filter(LLMAnalyse.severity.in_(severity_list))
    # 漏洞类型筛选
    if vuln_type_list:
        base_query = base_query.filter(LLMAnalyse.vulnerability_type.in_(vuln_type_list))

    # ================= 2. 统计当天所有漏洞（不受分页影响） =================
    total_query = db.query(LLMAnalyse).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        LLMAnalyse.is_security_related == True,
        GithubCommit.commit_date >= day_start,
        GithubCommit.commit_date <= day_end
    )
    total_vulns_daily = total_query.count()
    new_vulns = base_query.count()

    # 按严重程度统计
    subquery = base_query.subquery()
    severity_counts = db.query(
        LLMAnalyse.severity, func.count(LLMAnalyse.id)
    ).filter(
        exists().where(subquery.c.id == LLMAnalyse.id)
    ).group_by(LLMAnalyse.severity).all()

    stats = {
        "totalVulns": total_vulns_daily,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    for sev, count in severity_counts:
        if sev and sev.lower() in stats:
            stats[sev.lower()] = count

    # ================= 3. 分页查询漏洞列表 =================
    paginated_query = base_query.order_by(desc(GithubCommit.commit_date)).offset(
        (page - 1) * page_size
    ).limit(page_size)
    llms = paginated_query.all()

    vuln_list = []
    for llm in llms:
        # 解析审查结果JSON
        review_result = None
        if llm.review_result:
            try:
                review_data = json.loads(llm.review_result)
                review_result = ReviewResult(**review_data)
            except Exception:
                pass

        vuln_list.append(LLMAnalyseOut(
            id=llm.id,
            vulnerability_type=llm.vulnerability_type,
            affected_subsystem=llm.affected_subsystem,
            severity=llm.severity,
            cve_id=llm.cve_id,
            summary=llm.summary,
            thinking=llm.thinking,
            model_name=llm.model_name,
            analyzed_at=llm.analyzed_at.isoformat() if hasattr(llm.analyzed_at, 'isoformat') else str(llm.analyzed_at),
            review_status=llm.review_status,
            final_severity=llm.final_severity,
            review_result=review_result
        ))
    vuln_type_query = db.query(LLMAnalyse.vulnerability_type).distinct()
    vuln_type = [row[0] for row in vuln_type_query.all() if row[0] is not None]

    # ================= 4. 返回响应 =================
    return GetVulnDailyResponse(
        code=200,
        vulnList=vuln_list,
        total=base_query.count(),  # 符合当前筛选条件的总记录数（用于分页）
        stats=stats,  # 当天所有漏洞的统计
        vuln_type=vuln_type,
        total_vulns_daily=total_vulns_daily,
        new_vulns=new_vulns
    )


@router.post("/getTrendAnalysis", response_model=GetTrendAnalysisResponse)
async def get_trend_analysis(
    request: GetTrendAnalysis,
    db: Session = Depends(get_db)
):
    """
    获取趋势分析数据，包括漏洞趋势、严重等级分布、组件排名、漏洞类型分布
    """
    repo_id = request.id
    time_range = request.time_range
    
    # 计算日期范围
    end_date = datetime.now()
    if time_range == '7d':
        start_date = end_date - timedelta(days=7)
        date_format = '%m-%d'
    elif time_range == '30d':
        start_date = end_date - timedelta(days=30)
        date_format = '%m-%d'
    elif time_range == '90d':
        start_date = end_date - timedelta(days=90)
        date_format = '%m-%d'
    else:  # year
        start_date = end_date - timedelta(days=365)
        date_format = '%Y-%m'
    
    # 基础查询：关联LLMAnalyse和GithubCommit，筛选安全相关漏洞
    base_query = db.query(LLMAnalyse, GithubCommit).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    )
    
    # ================= 1. 生成趋势数据 =================
    trend_data = []
    
    if time_range == '7d':
        # 按天统计
        for i in range(7):
            date = end_date - timedelta(days=6-i)
            date_str = date.strftime(date_format)
            
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_query = base_query.filter(
                GithubCommit.commit_date >= day_start,
                GithubCommit.commit_date < day_end
            )
            
            new_count = day_query.count()
            
            trend_data.append(TrendDataPoint(
                date=date_str,
                new_vulns=new_count
            ))
    elif time_range in ['30d', '90d']:
        # 按周统计
        weeks = 4 if time_range == '30d' else 12
        for i in range(weeks):
            week_end = end_date - timedelta(weeks=weeks-1-i, days=end_date.weekday())
            week_start = week_end - timedelta(days=7)
            week_label = f"第{i+1}周"
            
            week_query = base_query.filter(
                GithubCommit.commit_date >= week_start,
                GithubCommit.commit_date < week_end
            )
            
            new_count = week_query.count()
            
            trend_data.append(TrendDataPoint(
                date=week_label,
                new_vulns=new_count
            ))
    else:  # year
        # 按季度统计
        for quarter in range(1, 5):
            quarter_start = datetime(end_date.year, quarter * 3 - 2, 1)
            quarter_end = datetime(end_date.year, quarter * 3 + 1, 1) if quarter < 4 else datetime(end_date.year + 1, 1, 1)
            
            quarter_query = base_query.filter(
                GithubCommit.commit_date >= quarter_start,
                GithubCommit.commit_date < quarter_end
            )
            
            new_count = quarter_query.count()
            
            trend_data.append(TrendDataPoint(
                date=f"Q{quarter}",
                new_vulns=new_count
            ))
    
    # ================= 2. 严重等级分布 =================
    severity_counts = db.query(
        LLMAnalyse.severity, func.count(LLMAnalyse.id)
    ).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    ).group_by(LLMAnalyse.severity).all()
    
    severity_map = {'Critical': '严重', 'High': '高危', 'Medium': '中危', 'Low': '低危'}
    severity_distribution = []
    for sev, count in severity_counts:
        if sev:
            severity_distribution.append(SeverityDistributionItem(
                value=count,
                name=severity_map.get(sev, sev)
            ))
    
    # 如果没有数据，提供默认分布
    if not severity_distribution:
        severity_distribution = [
            SeverityDistributionItem(value=15, name='严重'),
            SeverityDistributionItem(value=35, name='高危'),
            SeverityDistributionItem(value=50, name='中危'),
            SeverityDistributionItem(value=30, name='低危')
        ]
    
    # ================= 3. 组件漏洞排行 =================
    component_counts = db.query(
        LLMAnalyse.affected_subsystem,
        LLMAnalyse.severity,
        func.count(LLMAnalyse.id)
    ).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        LLMAnalyse.affected_subsystem != None,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    ).group_by(LLMAnalyse.affected_subsystem, LLMAnalyse.severity).all()
    
    # 合并同一组件的计数，取最高严重等级
    component_map = {}
    for comp, sev, count in component_counts:
        if comp not in component_map:
            component_map[comp] = {'count': 0, 'severity': 'low'}
        component_map[comp]['count'] += count
        # 更新最高严重等级
        sev_priority = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        current_priority = sev_priority.get(component_map[comp]['severity'], 0)
        new_priority = sev_priority.get(sev, 0)
        if new_priority > current_priority:
            component_map[comp]['severity'] = sev.lower()
    
    # 排序取前5
    sorted_components = sorted(component_map.items(), key=lambda x: x[1]['count'], reverse=True)[:5]
    
    severity_map_en = {'Critical': 'critical', 'High': 'high', 'Medium': 'medium', 'Low': 'low'}
    component_ranking = [
        ComponentRankingItem(
            name=comp,
            vuln_count=data['count'],
            severity=severity_map_en.get(data['severity'].capitalize(), data['severity'])
        )
        for comp, data in sorted_components
    ]

    
    # ================= 4. 漏洞类型分布 =================
    type_counts = db.query(
        LLMAnalyse.vulnerability_type, func.count(LLMAnalyse.id)
    ).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        LLMAnalyse.vulnerability_type != None,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    ).group_by(LLMAnalyse.vulnerability_type).all()
    
    vuln_type_distribution = [
        VulnTypeDistributionItem(value=count, name=vtype)
        for vtype, count in type_counts
    ]

    return GetTrendAnalysisResponse(
        code=200,
        trend_data=trend_data,
        severity_distribution=severity_distribution,
        component_ranking=component_ranking,
        vuln_type_distribution=vuln_type_distribution
    )


@router.post("/getRiskAssessment", response_model=GetRiskAssessmentResponse)
async def get_risk_assessment(
    request: GetRiskAssessment,
    db: Session = Depends(get_db)
):
    """
    获取风险评估数据，包括风险评分、风险分布、组件风险、攻击面分析、修复建议
    """
    repo_id = request.id
    time_range = request.time_range
    
    # 计算日期范围
    end_date = datetime.now()
    if time_range == '7d':
        start_date = end_date - timedelta(days=7)
    elif time_range == '30d':
        start_date = end_date - timedelta(days=30)
    else:  # 90d
        start_date = end_date - timedelta(days=90)
    
    # 基础查询
    base_query = db.query(LLMAnalyse).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    )
    
    # ================= 1. 风险评分计算 =================
    total_vulns = base_query.count()
    
    severity_counts = db.query(
        LLMAnalyse.severity, func.count(LLMAnalyse.id)
    ).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    ).group_by(LLMAnalyse.severity).all()
    
    # 计算各等级数量
    severity_map = {}
    for sev, count in severity_counts:
        if sev:
            severity_map[sev.lower()] = count
    
    critical = severity_map.get('critical', 0)
    high = severity_map.get('high', 0)
    medium = severity_map.get('medium', 0)
    low = severity_map.get('low', 0)
    
    # 计算总体风险评分 (0-100)
    #Sum(wi*xi)/(max(wi)*Sum(xi))
    all_counts = max(critical+high+medium+low,1) #防止除0
    risk_score_value = (critical*0.5+high*0.3+medium*0.2+low*0.1)/(all_counts*0.5)*100
    
    # 计算各部分贡献百分比
    critical_weight = (critical*0.5)/(all_counts*0.5)*100
    high_weight = (high * 0.3) / (all_counts * 0.5)*100
    medium_weight = (medium*0.2) / (all_counts * 0.5)*100
    low_weight = (low*0.1) / (all_counts * 0.5)*100
    
    risk_score = RiskScoreData(
        overall=int(risk_score_value),
        breakdown=RiskBreakdown(
            critical=int(critical_weight),
            high=int(high_weight),
            medium=int(medium_weight),
            low=int(low_weight)
        )
    )
    
    # ================= 2. 风险等级分布 =================
    total = critical + high + medium + low
    if total == 0:
        total = 1
    
    risk_distribution = [
        RiskDistributionItem(level='严重', count=critical, percentage=critical*100//total, color='#f56c6c'),
        RiskDistributionItem(level='高危', count=high, percentage=high*100//total, color='#e6a23c'),
        RiskDistributionItem(level='中危', count=medium, percentage=medium*100//total, color='#409eff'),
        RiskDistributionItem(level='低危', count=low, percentage=low*100//total, color='#67c23a')
    ]
    
    # ================= 3. 组件风险评估 =================
    component_data = db.query(
        LLMAnalyse.affected_subsystem,
        LLMAnalyse.severity,
        func.count(LLMAnalyse.id)
    ).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        LLMAnalyse.affected_subsystem != None,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    ).group_by(LLMAnalyse.affected_subsystem, LLMAnalyse.severity).all()
    
    # 聚合组件数据
    comp_risk_map = {}
    for comp, sev, count in component_data:
        if comp not in comp_risk_map:
            comp_risk_map[comp] = {
                'vuln_count': 0,
                'max_severity': 'low',
                'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            }
        comp_risk_map[comp]['vuln_count'] += count
        comp_risk_map[comp]['severity_counts'][sev.lower()] += count
        
        # 更新最高严重等级
        sev_priority = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        current_priority = sev_priority.get(comp_risk_map[comp]['max_severity'], 0)
        new_priority = sev_priority.get(sev.lower(), 0)
        if new_priority > current_priority:
            comp_risk_map[comp]['max_severity'] = sev.lower()
    
    # 计算风险评分和生成建议
    component_risks = []
    for comp, data in comp_risk_map.items():
        # 风险评分算法
        score = min(100, data['severity_counts']['critical'] * 15 + 
                   data['severity_counts']['high'] * 8 +
                   data['severity_counts']['medium'] * 3 +
                   data['severity_counts']['low'] * 1)
        
        # 确定暴露程度
        if score >= 70:
            exposure = 'high'
        elif score >= 40:
            exposure = 'medium'
        else:
            exposure = 'low'
        
        # 生成修复建议
        if data['max_severity'] == 'critical':
            recommendation = '立即修复严重漏洞，优先升级受影响组件'
        elif data['max_severity'] == 'high':
            recommendation = '建议尽快升级或应用安全补丁'
        elif data['max_severity'] == 'medium':
            recommendation = '关注官方安全公告，计划更新'
        else:
            recommendation = '风险较低，保持正常更新周期'
        
        component_risks.append(ComponentRiskItem(
            name=comp,
            version='latest',
            risk_score=score,
            vuln_count=data['vuln_count'],
            max_severity=data['max_severity'],
            exposure=exposure,
            recommendation=recommendation
        ))
    
    # 排序取前10
    component_risks = sorted(component_risks, key=lambda x: x.risk_score, reverse=True)[:10]

    
    # ================= 4. 攻击面分析 =================
    # 统计受影响的子系统数量（作为入口点）
    entry_points = len(set([c.affected_subsystem for c in component_data if c.affected_subsystem]))
    if entry_points == 0:
        entry_points = 5  # 默认值
    
    # 统计漏洞类型数量（作为暴露API的指标）
    vuln_types = db.query(distinct(LLMAnalyse.vulnerability_type)).join(
        GithubCommit, LLMAnalyse.commit_id == GithubCommit.id
    ).filter(
        GithubCommit.repo_id == repo_id,
        LLMAnalyse.is_security_related == True,
        GithubCommit.commit_date >= start_date,
        GithubCommit.commit_date <= end_date
    ).count()
    
    attack_surface = AttackSurfaceData(
        entry_points=entry_points,
        exposed_apis=vuln_types if vuln_types > 0 else 3,
        third_party_deps=entry_points * 3,
        vulnerable_deps=len(component_risks)
    )
    
    # ================= 5. 修复优先级建议 =================
    priority_recommendations = []
    
    # 基于组件风险生成建议
    for idx, comp in enumerate(component_risks[:3], 1):
        if comp.max_severity == 'critical':
            timeframe = '24小时内'
            effort = '低'
            impact = '可能导致系统被入侵'
        elif comp.max_severity == 'high':
            timeframe = '3天内'
            effort = '中'
            impact = '存在数据泄露风险'
        elif comp.max_severity == 'medium':
            timeframe = '1周内'
            effort = '中'
            impact = '功能可能受影响'
        else:
            timeframe = '2周内'
            effort = '低'
            impact = '影响较小'
        
        priority_recommendations.append(PriorityRecommendationItem(
            priority=idx,
            title=f'修复 {comp.name} 的{comp.max_severity}级别漏洞',
            severity=comp.max_severity,
            impact=impact,
            effort=effort,
            timeframe=timeframe
        ))

    return GetRiskAssessmentResponse(
        code=200,
        risk_score=risk_score,
        risk_distribution=risk_distribution,
        component_risks=component_risks,
        attack_surface=attack_surface,
        priority_recommendations=priority_recommendations,
    )