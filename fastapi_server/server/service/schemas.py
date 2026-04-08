#数据验证与序列化
#定义API相关Response的输入输出数据结构
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from server.service.models import Repository, LLMAnalyse


# request
class RepositoryOut(BaseModel):
    id: int
    name: str
    repo_url: str
    default_branch: str
    is_active: bool
    last_fetched_at: Optional[datetime] = None
    created_at: datetime
    vuln_count:int
    class Config:
        from_attributes = True

class LLMAnalyseOut(BaseModel):
    id: int
    vulnerability_type: Optional[str] = None
    affected_subsystem: Optional[str] = None
    severity: Optional[str] = None
    cve_id: Optional[str] = None
    summary: str
    model_name: Optional[str] = None
    analyzed_at: str


class AnalyzeRepo(BaseModel):
    id:int


class GetVulnStats(BaseModel):
    id:int

class RepositoryAdd(BaseModel):
    name : str
    repo_url : str
    default_branch : str
    is_active : bool

class RepositoryDelete(BaseModel):
    id:int

class RepositoryChange(BaseModel):
    id:int
    default_branch: str
    is_active: bool

class SearchCommit(BaseModel):
    id:int

class GetVulnerabilities(BaseModel):
    id:int
    page:int
    page_size:int
    severity: Optional[str] = None

class GetVulnDaily(BaseModel):
    date:datetime
    severity: Optional[List[str]] = None
    id:int
    page: int
    page_size: int
    vuln_type:Optional[List[str]] = None


# 趋势分析相关Schema
class GetTrendAnalysis(BaseModel):
    id: int
    time_range: str  # '7d', '30d', '90d', 'year'

class TrendDataPoint(BaseModel):
    date: str
    new_vulns: int

class SeverityDistributionItem(BaseModel):
    value: int
    name: str

class ComponentRankingItem(BaseModel):
    name: str
    vuln_count: int
    severity: str

class VulnTypeDistributionItem(BaseModel):
    value: int
    name: str

class GetTrendAnalysisResponse(BaseModel):
    code: int
    trend_data: List[TrendDataPoint]
    severity_distribution: List[SeverityDistributionItem]
    component_ranking: List[ComponentRankingItem]
    vuln_type_distribution: List[VulnTypeDistributionItem]


# 风险评估相关Schema
class GetRiskAssessment(BaseModel):
    id: int
    time_range: str  # '7d', '30d', '90d'

class RiskBreakdown(BaseModel):
    critical: int
    high: int
    medium: int
    low: int

class RiskScoreData(BaseModel):
    overall: int
    breakdown: RiskBreakdown

class RiskDistributionItem(BaseModel):
    level: str
    count: int
    percentage: int
    color: str

class ComponentRiskItem(BaseModel):
    name: str
    version: str
    risk_score: int
    vuln_count: int
    max_severity: str
    exposure: str
    recommendation: str

class AttackSurfaceData(BaseModel):
    entry_points: int
    exposed_apis: int
    third_party_deps: int
    vulnerable_deps: int

class PriorityRecommendationItem(BaseModel):
    priority: int
    title: str
    severity: str
    impact: str
    effort: str
    timeframe: str

class RiskTrendPoint(BaseModel):
    date: str
    score: int

class GetRiskAssessmentResponse(BaseModel):
    code: int
    risk_score: RiskScoreData
    risk_distribution: List[RiskDistributionItem]
    component_risks: List[ComponentRiskItem]
    attack_surface: AttackSurfaceData
    priority_recommendations: List[PriorityRecommendationItem]
    risk_trend: List[RiskTrendPoint]


 #response
class RepositoryDeleteResponse(BaseModel):
    code : int
    message : str

class RepositoryGetAllResponse(BaseModel):
    code:   int
    repositories:   List[RepositoryOut]

class RepositoryChangeResponse(BaseModel):
    code:   int
    message:    str

class SearchCommitResponse(BaseModel):
    code:int

class RepositoryAddResponse(BaseModel):
    code: int
    message: str

class GetVulnStatsResponse(BaseModel):
    code:int
    stats:dict


class GetVulnerabilitiesResponse(BaseModel):
    code:int
    vulnList: List[LLMAnalyseOut]
    total:int

class AnalyzeRepoResponse(BaseModel):
    code:int

class GetVulnDailyResponse(BaseModel):
    code: int
    vulnList: List[LLMAnalyseOut]
    total: int
    stats:dict
    vuln_type:List[str]
    total_vulns_daily :int
    new_vulns:int