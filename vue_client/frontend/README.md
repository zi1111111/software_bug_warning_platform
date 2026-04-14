# 开源软件漏洞预警平台 — 前端应用

基于 Vue 3 + Element Plus 构建的开源软件漏洞预警平台前端，提供仓库管理、漏洞监控、趋势分析、风险评估等功能界面。

## 技术栈

- **框架**: Vue 3 (Composition API + `<script setup>`)
- **构建工具**: Vite 5
- **UI 组件库**: Element Plus + @element-plus/icons-vue
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **语言**: TypeScript / JavaScript 混合

## 项目结构

```
frontend/
├── index.html                  # HTML 入口
├── package.json                # 依赖配置
├── vite.config.js              # Vite 配置（含 API 代理）
├── public/                     # 静态资源
├── src/
│   ├── main.js                 # 应用入口（Vue + Pinia + Router + ElementPlus）
│   ├── App.vue                 # 根组件
│   ├── style.css               # 全局样式
│   ├── assets/                 # 静态资源
│   ├── components/             # 公共组件
│   ├── router/
│   │   └── index.js            # 路由配置 + 路由守卫
│   ├── stores/                 # Pinia 状态管理
│   │   ├── user.ts             # 用户状态（登录/注册/Token管理）
│   │   └── repository.ts       # 仓库状态（仓库列表/当前仓库/CRUD）
│   ├── request/
│   │   └── request.ts          # Axios HTTP 封装 + 拦截器 + API 方法
│   ├── response/
│   │   └── response.ts         # TypeScript 类型定义（响应数据结构）
│   └── views/                  # 页面组件
│       ├── Login.vue           # 登录页
│       ├── Register.vue        # 注册页
│       ├── Dashboard.vue       # 仪表盘首页
│       ├── RepositoryManagement.vue  # 仓库管理页
│       ├── DailyVulnUpdate.vue # 每日漏洞更新页
│       ├── TrendAnalysis.vue   # 趋势分析页
│       ├── RiskAssessment.vue  # 风险评估页
│       └── VulnDetail.vue      # 漏洞详情页
```

## 页面说明

### 登录 / 注册

- **Login.vue** — 支持密码登录 + 验证码登录，发送邮箱验证码
- **Register.vue** — 邮箱验证码注册，密码强度校验

### Dashboard 仪表盘

- **Dashboard.vue** — 系统概览首页
  - 仓库漏洞统计卡片（总数/Critical/High/Medium/Low）
  - 漏洞趋势折线图
  - 最近漏洞列表
  - 仓库选择器切换

### 仓库管理

- **RepositoryManagement.vue** — 仓库 CRUD 管理
  - 添加/删除/修改仓库
  - 启用/停用监测
  - 手动触发同步 / 手动触发分析
  - 仓库漏洞计数展示

### 每日漏洞更新

- **DailyVulnUpdate.vue** — 按日期查看漏洞
  - 日期选择器
  - 漏洞列表（分页 + 严重程度筛选 + 漏洞类型筛选）
  - 漏洞详情弹窗（含多模型审查结果展示）
  - 当日统计概览

### 趋势分析

- **TrendAnalysis.vue** — 漏洞趋势可视化
  - 仓库 + 时间范围选择（7d / 30d / 90d / year）
  - 漏洞趋势折线图
  - 严重等级分布饼图
  - 组件漏洞排行
  - 漏洞类型分布饼图
  - AI 洞察卡片（洞察列表 + 常见漏洞类型 + 建议 + 总结）

### 风险评估

- **RiskAssessment.vue** — 风险评分与建议
  - 仓库 + 时间范围选择（7d / 30d / 90d）
  - 风险评分仪表盘（0-100 + 各等级贡献占比）
  - 风险等级分布柱状图
  - 组件风险评估表格（Top 10 + 风险评分 + 暴露程度 + 修复建议）
  - 漏洞类型分布饼图
  - 修复优先级建议列表

## 路由配置

| 路径 | 页面 | 需要认证 |
|------|------|----------|
| `/login` | 登录 | 否 |
| `/register` | 注册 | 否 |
| `/dashboard` | 仪表盘 | 是 |
| `/repositories` | 仓库管理 | 是 |
| `/analysis/trend` | 趋势分析 | 是 |
| `/analysis/risk` | 风险评估 | 是 |
| `/daily-update` | 每日漏洞更新 | 是 |

**路由守卫**: 未登录用户访问认证页面自动重定向至 `/login`；已登录用户访问登录/注册页自动重定向至 `/dashboard`。

## 状态管理

### `useUserStore` (Pinia)

| 属性/方法 | 说明 |
|-----------|------|
| `token` | JWT Token（持久化到 localStorage） |
| `user` | 当前用户信息 |
| `isLoggedIn` | 计算属性：是否已登录 |
| `login(credentials)` | 密码登录 |
| `loginWithCode(credentials)` | 验证码登录 |
| `register(credentials)` | 注册 |
| `sendVerificationCode(email)` | 发送注册验证码 |
| `sendLoginCode(email)` | 发送登录验证码 |
| `fetchCurrentUser()` | 获取当前用户 |
| `logout()` | 退出登录 |

### `useRepoStore` (Pinia)

| 属性/方法 | 说明 |
|-----------|------|
| `repositories` | 仓库列表 |
| `currentRepoId` | 当前选中仓库 ID |
| `currentRepo` | 计算属性：当前仓库对象 |
| `activeRepos` | 计算属性：活跃仓库列表 |
| `fetchRepositories()` | 获取所有仓库 |
| `addRepository(data)` | 添加仓库 |
| `changeRepository(data)` | 修改仓库 |
| `deleteRepository(data)` | 删除仓库 |

## HTTP 请求封装

`request.ts` 基于 Axios 封装了 `HttpClient` 类：

- **BaseURL**: `http://localhost:8000`
- **请求拦截器**: 自动注入 `Authorization: Bearer <token>`
- **响应拦截器**: 统一处理 `{ code, data, message }` 格式
- **错误处理**: 统一捕获并格式化错误响应

### 已封装的 API 方法

```typescript
// 漏洞统计
getVulnStats(repo_id: number)

// 漏洞列表
getVulnerabilities(params: { repo_id, severity?, page, page_size })

// 漏洞详情
getVulnDetail(vuln_id: number)

// 手动触发分析
analyzeRepo(repo_id: number)
```

其他 API 调用通过 `http.post()` / `http.get()` 直接发起。

## TypeScript 类型定义

`response.ts` 定义了与后端 Pydantic Schema 对应的 TypeScript 接口：

| 类型 | 说明 |
|------|------|
| `TrendDataPoint` | 趋势数据点 |
| `SeverityDistributionItem` | 严重等级分布 |
| `ComponentRankingItem` | 组件排行 |
| `VulnTypeDistributionItem` | 漏洞类型分布 |
| `AIInsightsData` | AI 洞察数据 |
| `GetTrendAnalysisResponse` | 趋势分析响应 |
| `RiskScoreData` / `RiskBreakdown` | 风险评分 |
| `RiskDistributionItem` | 风险分布 |
| `ComponentRiskItem` | 组件风险 |
| `PriorityRecommendationItem` | 修复优先级建议 |
| `GetRiskAssessmentResponse` | 风险评估响应 |
| `Repository` | 仓库 |
| `LLMAnalyse` | LLM 分析结果 |
| `ModelResult` | 单模型审查结果 |
| `ReviewResult` | 多模型审查结果 |
| `VulnItem` | 漏洞条目 |
| `Stats` | 漏洞统计 |
| `GetVulnDailyResponse` | 每日漏洞响应 |

## Vite 开发代理

`vite.config.js` 配置了 API 代理，开发时前端请求 `/api/*` 自动转发至后端：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    }
  }
}
```

## 快速启动

```bash
# 1. 安装依赖
npm install

# 2. 启动开发服务器
npm run dev
# 默认访问 http://localhost:5173

# 3. 构建生产版本
npm run build

# 4. 预览生产构建
npm run preview
```

**前提**: 后端服务需先启动在 `http://localhost:8000`。

## 前后端交互概览

```
前端页面                    后端接口                     核心模块
─────────────────────────────────────────────────────────────────
Login.vue          →  POST /api/user/login         →  user_service.py
Register.vue       →  POST /api/user/register      →  user_service.py
Dashboard.vue      →  POST /api/getVulnStats       →  base_service.py
                   →  POST /api/getVulnerabilities  →  base_service.py
RepositoryMgmt.vue →  POST /api/addRepository      →  base_service.py
                   →  POST /api/searchCommit        →  base_service.py (后台)
                   →  POST /api/analyzeRepo         →  base_service.py (后台)
DailyVulnUpdate    →  POST /api/getVulnDaily        →  data_response.py
TrendAnalysis.vue  →  POST /api/getTrendAnalysis    →  data_response.py
RiskAssessment.vue →  POST /api/getRiskAssessment    →  data_response.py
```

所有数据分析接口均需传入 `{ id: repo_id, time_range: '7d'|'30d'|'90d'|'year' }` 参数。
