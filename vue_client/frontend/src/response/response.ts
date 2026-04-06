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
