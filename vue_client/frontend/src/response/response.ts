import {ref} from "vue";

export interface Repository {
    id:number;
    name: string;
    repo_url: string;
    default_branch: string;
    is_active: boolean;
    last_fetched_at: string;
    created_at: string;
    vuln_count:number;
}

export interface RepositoriesData {
    code: number
    repositories: Repository[]
}

export interface GithubCommit{
    id:number;
    repo_id: string;
    commit_hash: string;
    author: string;
    author_email: string;
    commit_date: string;
    message: string;
    repo_url: string;
    branch: string;
    created_at: string;
}

export interface LLMAnalyse{
    id:number;
    commit_id:number;
    is_security_related: boolean;
    vulnerability_type: string;
    affected_subsystem: string;
    severity: string;
    cve_id: string;
    summary: string;
    model_name: string;
    analysis_cost: number;
    analyzed_at: string;
}

// 定义统计数据类型
export  interface Stats {
    totalVulns: number
    critical: number
    high: number
    medium: number
    low: number
}

// 定义漏洞条目类型（根据实际字段补充）
export  interface VulnItem {
    id:number
    cve_id?: string
    summary?: string
    title?: string
    severity?: string
    vulnerability_type?: string
    analyzed_at?: string
    affected_subsystem?: string
    model_name?: string
}

//复杂类型相应，请求定义

export interface GetVulnDailyResponse{
    stats: Stats
    code:number
    vulnList:VulnItem[]
    total:number
    vuln_type:string[]
    total_vulns_daily:number
    new_vulns:number
}

// 趋势分析相关类型
export interface TrendDataPoint {
    date: string
    new_vulns: number
}

export interface SeverityDistributionItem {
    value: number
    name: string
}

export interface ComponentRankingItem {
    name: string
    vuln_count: number
    severity: string
}

export interface VulnTypeDistributionItem {
    value: number
    name: string
}

export interface GetTrendAnalysisResponse {
    code: number
    trend_data: TrendDataPoint[]
    severity_distribution: SeverityDistributionItem[]
    component_ranking: ComponentRankingItem[]
    vuln_type_distribution: VulnTypeDistributionItem[]
}

// 风险评估相关类型
export interface RiskBreakdown {
    critical: number
    high: number
    medium: number
    low: number
}

export interface RiskScoreData {
    overall: number
    breakdown: RiskBreakdown
}

export interface RiskDistributionItem {
    level: string
    count: number
    percentage: number
    color: string
}

export interface ComponentRiskItem {
    name: string
    version: string
    risk_score: number
    vuln_count: number
    max_severity: string
    exposure: string
    recommendation: string
}

export interface AttackSurfaceData {
    entry_points: number
    exposed_apis: number
    third_party_deps: number
    vulnerable_deps: number
}

export interface PriorityRecommendationItem {
    priority: number
    title: string
    severity: string
    impact: string
    effort: string
    timeframe: string
}

export interface RiskTrendPoint {
    date: string
    score: number
}

export interface GetRiskAssessmentResponse {
    code: number
    risk_score: RiskScoreData
    risk_distribution: RiskDistributionItem[]
    component_risks: ComponentRiskItem[]
    attack_surface: AttackSurfaceData
    priority_recommendations: PriorityRecommendationItem[]
    risk_trend: RiskTrendPoint[]
}
