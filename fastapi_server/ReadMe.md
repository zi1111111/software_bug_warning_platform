# 开源软件漏洞预警平台 — 后端服务

基于 FastAPI 构建的开源软件漏洞预警平台后端，提供 Git 仓库数据采集、LLM 漏洞分析、多模型审查投票、趋势/风险评估、AI 洞察分析等核心功能。

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **ORM**: SQLAlchemy 2.0 + PyMySQL
- **数据库**: MySQL（连接池: 20常规 + 30溢出）
- **定时调度**: APScheduler（CronTrigger）
- **LLM 接入**: OpenAI SDK（DeepSeek / GLM-5 / Qwen / Hunyuan）
- **认证**: JWT (python-jose) + bcrypt (passlib)
- **邮件**: SMTP + Redis 验证码缓存
- **Git 采集**: PyGithub + GitPython

## 项目结构

```
fastapi_server/
├── app.py                      # FastAPI 应用入口、CORS、路由挂载、生命周期
├── .env / .env.example         # 环境变量配置
├── requirements.txt            # Python 依赖
├── logs/                       # 运行日志
├── data/                       # 数据文件（数据集等）
├── scripts/                    # 工具脚本
│   ├── extract_linux_kernel_cves.py   # CVE 数据集提取
│   └── validate_llm_review.py         # LLM 审查功能验证
├── server/
│   ├── db/
│   │   └── database.py         # 数据库连接池、Session 工厂、get_db 依赖注入
│   └── service/
│       ├── models.py           # SQLAlchemy ORM 模型（5张表）
│       ├── schemas.py          # Pydantic 请求/响应数据结构
│       ├── base_service.py     # 仓库管理 + 漏洞查询 API
│       ├── data_response.py    # 趋势分析 + 风险评估 + AI洞察 API
│       ├── data_collector.py   # GitHub 仓库 Commit 采集器
│       ├── LLM_layer.py        # LLM 漏洞初分析 + AI洞察分析 + 分层取样
│       ├── LLM_censorship.py   # 多模型严重性审查投票系统
│       ├── analysis_service.py # 分析编排服务（初分析 + 审查）
│       ├── maintenance_service.py  # 定时调度器
│       ├── user_service.py     # 用户认证 API（注册/登录/验证码）
│       ├── auth_utils.py       # JWT 工具 + 密码哈希
│       └── email_utils.py      # 邮件发送 + Redis 验证码
```

## 数据库模型

### `repository` — 监控仓库

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| name | VARCHAR(100) | 仓库名称 |
| repo_url | VARCHAR(500) | Git 仓库 URL |
| default_branch | VARCHAR(100) | 默认分支 |
| is_active | BOOLEAN | 是否启用监测 |
| last_fetched_at | DATETIME | 最后拉取时间 |
| created_at | DATETIME | 创建时间 |

### `github_commits` — 原始 Commit 记录

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| repo_id | INT FK | 关联仓库 |
| commit_hash | VARCHAR(40) | Git SHA（唯一索引） |
| author / author_email | VARCHAR | 作者信息 |
| commit_date | DATETIME | 提交日期（索引） |
| message | TEXT | Commit 消息 |
| diff | TEXT | 代码变更（智能截断至2000字符） |
| branch | VARCHAR(100) | 分支名 |
| is_analysed | BOOLEAN | 是否已分析 |

### `llm_analyses` — LLM 分析结果

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| commit_id | INT FK | 关联 Commit |
| is_security_related | BOOLEAN | 是否安全相关（索引） |
| vulnerability_type | VARCHAR(100) | 漏洞类型（如 use-after-free） |
| affected_subsystem | VARCHAR(100) | 影响子系统 |
| severity | ENUM | Critical / High / Medium / Low |
| cve_id | VARCHAR(50) | CVE 编号 |
| summary / thinking | TEXT | 摘要 / 思考过程 |
| model_name | VARCHAR(50) | 模型名称 |
| review_status | VARCHAR(20) | 审查状态: pending/completed/failed |
| review_result | TEXT | 多模型审查结果 JSON |
| final_severity | VARCHAR(20) | 投票后最终严重性 |

**复合索引**: `(commit_id, severity)`, `(is_security_related, analyzed_at)`

### `ai_insights_cache` — AI 洞察缓存

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| repo_id | INT FK | 关联仓库 |
| time_range | VARCHAR(10) | 7d / 30d / 90d / year |
| insights | TEXT | 洞察列表 JSON |
| common_vuln_types | TEXT | 常见漏洞类型 JSON |
| recommendations | TEXT | 改进建议 |
| llm_identified_count | INT | LLM 识别漏洞数 |
| summary | TEXT | 整体总结 |
| commit_count | INT | 分析的 commit 数 |

**唯一索引**: `(repo_id, time_range)`

### `users` — 用户表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | 自增主键 |
| email | VARCHAR(100) | 邮箱（唯一索引） |
| hashed_password | VARCHAR(100) | bcrypt 哈希密码 |
| is_active | BOOLEAN | 是否启用 |

## API 接口

所有接口前缀: `/api`

### 仓库管理 (`base_service.py`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/addRepository` | 添加监控仓库 |
| POST | `/deleteRepository` | 删除仓库（级联删除） |
| GET | `/getAllRepositories` | 获取所有仓库（含漏洞计数） |
| POST | `/changeRepository` | 修改仓库配置（分支/启用状态） |
| POST | `/searchCommit` | 手动触发仓库同步（后台执行） |
| POST | `/getVulnStats` | 获取仓库漏洞统计 |
| POST | `/getVulnerabilities` | 分页获取漏洞列表（支持严重程度筛选） |
| POST | `/analyzeRepo` | 手动触发仓库分析（后台执行） |

### 数据分析 (`data_response.py`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/getVulnDaily` | 获取指定日期漏洞列表（支持严重程度+漏洞类型筛选） |
| POST | `/getTrendAnalysis` | 获取趋势分析数据（漏洞趋势 + 严重等级分布 + 组件排行 + 漏洞类型分布 + AI洞察） |
| POST | `/getRiskAssessment` | 获取风险评估数据（风险评分 + 风险分布 + 组件风险 + 漏洞类型分布 + 修复建议） |
| POST | `/refreshAIInsights` | 手动刷新AI洞察（后台执行，不阻塞） |

### 用户认证 (`user_service.py`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/user/send-verification-code` | 发送注册验证码 |
| POST | `/user/register` | 邮箱验证注册 |
| POST | `/user/login` | 密码登录 |
| POST | `/user/login-with-code` | 验证码登录 |
| POST | `/user/send-login-code` | 发送登录验证码 |
| GET | `/user/me` | 获取当前用户信息 |
| POST | `/user/logout` | 退出登录 |

### 其他

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/` | 根路径欢迎信息 |

## 核心业务流程

### 1. 数据采集流程

```
GitHubCollector.sync_repository()
  ├── PyGithub 获取指定分支的 Commits（增量/首次最多300条）
  ├── 获取每个 Commit 的完整信息（含 diff）
  ├── smart_truncate_diff() 智能截断 diff（保留文件头+hunk头+变更行，≤2000字符）
  └── 批量写入 github_commits 表
```

### 2. LLM 漏洞分析流程

```
AnalysisService.analyze_commit_sync()
  ├── LLMAnalyzer.should_analyze()    — 安全关键词预过滤（正则匹配）
  ├── LLMAnalyzer.analyze_commit()     — DeepSeek 初分析
  │   ├── 构建 Prompt（commit message + diff）
  │   ├── 调用 DeepSeek API
  │   └── 解析 JSON 响应（severity, vuln_type, summary...）
  ├── LLMCensorship.review_severity()  — 多模型审查投票（仅安全相关）
  │   ├── 并行调用 4 个模型: DeepSeek(0.30) + GLM-5(0.30) + Qwen(0.25) + Hunyuan(0.15)
  │   ├── 加权投票（权重 × 置信度）
  │   └── 生成 final_severity + consensus_rate
  └── 写入 llm_analyses 表
```

### 3. 多模型审查投票机制

**模型权重**:

| 模型 | 接入方式 | 权重 |
|------|----------|------|
| DeepSeek | 原厂 API | 0.30 |
| GLM-5 | 智谱原厂 API | 0.30 |
| Qwen | 阿里原厂 API | 0.25 |
| Hunyuan | 硅基流动 API | 0.15 |

**投票算法**:
- 每个模型独立评估严重性 + 置信度
- 加权分数 = Σ(权重 × 置信度 × 严重性分数) / Σ(权重 × 置信度)
- 严重性分数: Critical=4, High=3, Medium=2, Low=1, None=0
- 最终等级: ≥3.5→Critical, ≥2.5→High, ≥1.5→Medium, ≥0.5→Low

**审查Prompt评估维度**:
1. 漏洞类型危害程度 (30%)
2. 影响范围与权限 (25%)
3. 利用难度与条件 (25%)
4. 修复紧迫性 (20%)

### 4. AI 洞察分析流程

```
analyze_and_cache_insights()
  ├── get_insights_commits()    — 分层取样（按严重程度比例取样，最多50条）
  │   ├── Critical: 30%, High: 30%, Medium: 25%, Low: 15%
  │   └── 不足部分按时间倒序补充
  ├── LLMAnalyzer.analyze_commits_insights()  — DeepSeek 批量洞察分析
  └── 写入 ai_insights_cache 表（按 repo_id + time_range 唯一缓存）
```

### 5. 定时调度

| 时间 | 任务 | 说明 |
|------|------|------|
| 启动时 | sync_all + analyze + insights | 首次全量同步分析 |
| 每日 02:00 | sync_all_repositories | 增量同步所有活跃仓库 |
| 每日 02:00 | analyze_unanalyzed_commits | 分析未处理的 Commits |
| 每日 02:30 | update_all_ai_insights | 更新所有仓库 AI 洞察缓存 |

## 环境变量配置

复制 `.env.example` 为 `.env` 并填写：

```env
# 应用
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=240

# 数据库
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=vuln_warning

# 邮箱
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-email-password
FAKE_EMAIL=0    # 设为1时验证码固定000000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM API
DEEPSEEK_API_KEY=your-deepseek-key
SILICONFLOW_API_KEY=your-siliconflow-key
GITHUB_TOKEN=your-github-token    # 可选，无token则匿名（60次/小时）

# 多模型审查（可选，按需配置）
GLM5_API_KEY=your-glm5-key
QIANWEN_API_KEY=your-qwen-key
```

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填写数据库、API Key 等

# 3. 初始化数据库表
python -c "from server.db.database import engine; from server.service.models import Base; Base.metadata.create_all(bind=engine)"

# 4. 启动服务
python app.py
# 或
uvicorn app:app --host 0.0.0.0 --port 8000
```

服务启动后访问:
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
