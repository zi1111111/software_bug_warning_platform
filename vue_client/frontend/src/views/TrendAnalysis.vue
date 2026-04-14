<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import SidebarLayout from '../components/SidebarLayout.vue'
import { storeToRefs } from "pinia"
import { useRepoStore } from "../stores/repository"
import { http } from "../request/request"
import { useRouter } from 'vue-router'
import type { 
  GetTrendAnalysisResponse, 
  TrendDataPoint,
  AIInsightsData,
  Repository 
} from "../response/response"

// 仓库相关
const repoTS = useRepoStore()
const { repositories } = storeToRefs(repoTS)
const router = useRouter()

// 当前选中的仓库
const currentRepo = ref<Repository | null>(null)

// 加载状态
const loading = ref(false)

// 获取默认仓库
const getDefaultRepo = () => {
  const repos = repositories.value
  if (!repos.length) return null
  const activeRepo = repos.find(r => r.is_active === true)
  return activeRepo || repos[0]
}

// 处理仓库切换
const handleRepoChange = (repo: Repository) => {
  currentRepo.value = repo
  loadTrendData()
}

// 时间范围选择
const timeRange = ref('7d')
const timeRangeOptions = [
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' },
  { label: '最近90天', value: '90d' },
  { label: '今年', value: 'year' }
]

// 数据状态
const trendData = ref<TrendDataPoint[]>([])
const aiInsights = ref<AIInsightsData | null>(null)

// 加载趋势分析数据
const loadTrendData = async () => {
  if (!currentRepo.value) return
  
  loading.value = true
  try {
    const res = await http.post<GetTrendAnalysisResponse>('/api/getTrendAnalysis', {
      id: currentRepo.value.id,
      time_range: timeRange.value
    })
    
    if (res.code === 200 && res.data) {
      trendData.value = res.data.trend_data || []
      aiInsights.value = res.data.ai_insights || null
    } else {
      ElMessage.error(res.message || '加载趋势数据失败')
    }
  } catch (error) {
    ElMessage.error('网络请求失败，请稍后重试')
    console.error('Load trend data error:', error)
  } finally {
    loading.value = false
  }
}

// 计算当前数据
const currentData = computed(() => {
  return {
    dates: trendData.value.map(d => d.date),
    newVulns: trendData.value.map(d => d.new_vulns)
  }
})

// 获取图表颜色
const chartColors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a']

// 严重等级颜色映射
const getSeverityLabel = (severity: string) => {
  const map: Record<string, string> = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危'
  }
  return map[severity] || severity
}

// 监听时间范围变化
watch(timeRange, () => {
  loadTrendData()
})

// 初始化
onMounted(() => {
  if (repositories.value.length) {
    currentRepo.value = getDefaultRepo()
    if (currentRepo.value) {
      loadTrendData()
    }
  }
})

// 监听仓库列表变化
watch(repositories, (newRepos) => {
  if (newRepos.length && !currentRepo.value) {
    currentRepo.value = getDefaultRepo()
    if (currentRepo.value) {
      loadTrendData()
    }
  }
}, { immediate: true })

// 跳转到仓库管理页面
const goToRepoManagement = () => {
  router.push('/repositories')
}
</script>

<template>
  <SidebarLayout :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo ? currentRepo.name + ' - 趋势分析' : '趋势分析' }}
    </template>

    <!-- 无仓库时的空状态 -->
    <div v-if="!currentRepo" class="empty-state">
      <el-empty description="暂无仓库数据">
        <template #image>
          <el-icon :size="80" color="#c0c4cc"><Collection /></el-icon>
        </template>
        <el-button type="primary" @click="goToRepoManagement">前往添加仓库</el-button>
      </el-empty>
    </div>

    <div v-else class="trend-analysis" v-loading="loading">
      <!-- 时间范围选择 -->
      <el-card class="filter-card" shadow="never">
        <div class="filter-content">
          <span class="filter-label">时间范围:</span>
          <el-radio-group v-model="timeRange" size="large">
            <el-radio-button 
              v-for="option in timeRangeOptions" 
              :key="option.value" 
              :label="option.value"
            >
              {{ option.label }}
            </el-radio-button>
          </el-radio-group>
        </div>
      </el-card>

      <!-- 统计概览 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="12">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-header">
              <el-icon class="stat-icon red"><TrendCharts /></el-icon>
              <span class="stat-trend up">+15%</span>
            </div>
            <div class="stat-value">{{ currentData.newVulns.reduce((a: number, b: number) => a + b, 0) }}</div>
            <div class="stat-label">新增漏洞</div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-header">
              <el-icon class="stat-icon blue"><Warning /></el-icon>
              <span class="stat-trend">--</span>
            </div>
            <div class="stat-value">{{ currentData.newVulns.reduce((a: number, b: number) => a + b, 0) }}</div>
            <div class="stat-label">漏洞总数</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 漏洞趋势图表 -->
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">漏洞趋势</span>
            <div class="legend">
              <span class="legend-item">
                <span class="legend-dot" style="background: #f56c6c;"></span>
                新增漏洞
              </span>
            </div>
          </div>
        </template>
        
        <!-- 简单的柱状图展示 -->
        <div class="trend-chart" v-if="currentData.dates.length > 0">
          <div class="chart-y-axis">
            <div v-for="i in 5" :key="i" class="y-axis-label">
              {{(i - 1) * Math.ceil(Math.max(...currentData.newVulns, 1) / 4)  }}
            </div>
          </div>
          <div class="chart-content">
            <div 
              v-for="(date, index) in currentData.dates" 
              :key="date"
              class="chart-bar-group"
            >
              <div class="bars-container">
                <div 
                  class="bar new-vuln"
                  :style="{ 
                    height: (currentData.newVulns[index] / Math.max(...currentData.newVulns, 1) * 200) + 'px' 
                  }"
                >
                  <el-tooltip :content="`新增: ${currentData.newVulns[index]}`" placement="top">
                    <div class="bar-inner"></div>
                  </el-tooltip>
                </div>
              </div>
              <div class="x-axis-label">{{ date }}</div>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无趋势数据" />
      </el-card>

      <!-- AI洞察分析 -->
      <el-row :gutter="20" class="bottom-row" v-if="aiInsights && aiInsights.insights.length > 0">
        <el-col :span="24">
          <el-card class="ai-insights-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title">
                  <el-icon class="ai-icon"><Magic /></el-icon>
                  AI 智能洞察
                </span>
                <el-tag v-if="aiInsights.llm_identified_count > 0" type="success" size="small">
                  {{ aiInsights.llm_identified_count }} 个LLM识别漏洞
                </el-tag>
              </div>
            </template>
            
            <div class="ai-content">
              <!-- 总结 -->
              <div class="ai-summary" v-if="aiInsights.summary">
                <el-alert type="info" :closable="false">
                  <template #title>
                    <span class="summary-text">{{ aiInsights.summary }}</span>
                  </template>
                </el-alert>
              </div>

              <!-- 洞察列表 -->
              <div class="insights-section" v-if="aiInsights.insights.length > 0">
                <h4 class="section-title">关键发现</h4>
                <div class="insights-list">
                  <div 
                    v-for="(insight, index) in aiInsights.insights" 
                    :key="index"
                    class="insight-item"
                  >
                    <el-icon class="insight-icon"><StarFilled /></el-icon>
                    <span class="insight-text">{{ insight }}</span>
                  </div>
                </div>
              </div>

              <!-- 常见漏洞类型 -->
              <div class="vuln-types-section" v-if="aiInsights.common_vuln_types.length > 0">
                <h4 class="section-title">常见漏洞类型</h4>
                <div class="vuln-types-tags">
                  <el-tag 
                    v-for="(vtype, index) in aiInsights.common_vuln_types" 
                    :key="index"
                    :type="index === 0 ? 'danger' : index === 1 ? 'warning' : 'info'"
                    class="vuln-type-tag"
                    effect="light"
                  >
                    {{ vtype }}
                  </el-tag>
                </div>
              </div>

              <!-- 建议 -->
              <div class="recommendation-section" v-if="aiInsights.recommendations">
                <h4 class="section-title">改进建议</h4>
                <div class="recommendation-text">
                  <el-icon class="reco-icon"><InfoFilled /></el-icon>
                  {{ aiInsights.recommendations }}
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </SidebarLayout>
</template>

<style scoped>
.trend-analysis {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.filter-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-label {
  font-weight: 500;
  color: #606266;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  font-size: 16px;
  color: #909399;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 20px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  overflow: hidden;
  position: relative;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 
    0 20px 40px rgba(102, 126, 234, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.stat-icon {
  font-size: 28px;
  padding: 12px;
  border-radius: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-icon.red {
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  color: #ff416c;
  box-shadow: 0 4px 12px rgba(255, 65, 108, 0.2);
}

.stat-icon.green {
  background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
  color: #1dd1a1;
  box-shadow: 0 4px 12px rgba(29, 209, 161, 0.2);
}

.stat-icon.blue {
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.stat-icon.orange {
  background: linear-gradient(135deg, #fdf6ec 0%, #fce6d4 100%);
  color: #ff9f43;
  box-shadow: 0 4px 12px rgba(255, 159, 67, 0.2);
}

.stat-trend {
  font-size: 14px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.05);
}

.stat-trend.up {
  color: #1dd1a1;
  background: rgba(29, 209, 161, 0.1);
}

.stat-trend.down {
  color: #ff416c;
  background: rgba(255, 65, 108, 0.1);
}

.stat-value {
  font-size: 36px;
  font-weight: 800;
  background: linear-gradient(135deg, #1a1f3c 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 8px;
  text-shadow: 0 2px 10px rgba(102, 126, 234, 0.1);
}

.stat-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.chart-card {
  border-radius: 20px;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  transition: all 0.4s ease;
}

.chart-card:hover {
  box-shadow: 
    0 8px 30px rgba(102, 126, 234, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
}

.filter-card {
  margin-bottom: 24px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.ai-insights-card {
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.15);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  position: relative;
  overflow: hidden;
}

.ai-insights-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

.ai-icon {
  color: #667eea;
  margin-right: 8px;
  font-size: 20px;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(102, 126, 234, 0.05);
  border-radius: 12px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
  border-left: 3px solid #667eea;
}

.insight-item:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(4px);
}

.insight-icon {
  color: #667eea;
  font-size: 16px;
  margin-top: 2px;
}

.vuln-type-tag {
  margin: 4px;
  border-radius: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.vuln-type-tag:hover {
  transform: scale(1.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.legend {
  display: flex;
  gap: 20px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

/* 趋势图表样式 */
.trend-chart {
  display: flex;
  height: 250px;
  padding: 20px 0;
}

.chart-y-axis {
  display: flex;
  flex-direction: column-reverse;
  justify-content: space-between;
  padding-right: 12px;
  border-right: 1px solid #ebeef5;
}

.y-axis-label {
  font-size: 12px;
  color: #909399;
  height: 20px;
  line-height: 20px;
}

.chart-content {
  flex: 1;
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  padding: 0 20px;
}

.chart-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bars-container {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 200px;
}

.bar {
  width: 20px;
  display: flex;
  align-items: flex-end;
  transition: all 0.3s ease;
}

.bar:hover {
  opacity: 0.8;
}

.bar.new-vuln .bar-inner {
  background: #f56c6c;
}

.bar-inner {
  width: 100%;
  border-radius: 3px 3px 0 0;
  height: 100%;
}

.x-axis-label {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}

.bottom-row {
  margin-top: 20px;
}

/* 分布图表样式 */
.distribution-chart {
  padding: 10px 0;
}

.distribution-item {
  margin-bottom: 16px;
}

.distribution-bar-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.distribution-label {
  width: 50px;
  font-size: 13px;
  color: #606266;
  text-align: right;
}

.distribution-bar-wrapper {
  flex: 1;
  height: 20px;
  background: #f5f7fa;
  border-radius: 10px;
  overflow: hidden;
}

.distribution-bar {
  height: 100%;
  border-radius: 10px;
  transition: width 0.5s ease;
}

.distribution-value {
  width: 30px;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

/* 排行样式 */
.ranking-list {
  padding: 10px 0;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}

.ranking-item:last-child {
  border-bottom: none;
}

.ranking-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f5f7fa;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
}

.ranking-number.top3 {
  background: #1a237e;
  color: white;
}

.ranking-info {
  flex: 1;
}

.ranking-name {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.ranking-count {
  font-size: 18px;
  font-weight: 700;
  color: #f56c6c;
}

/* 类型分布样式 */
.type-distribution {
  padding: 10px 0;
}

.type-item {
  margin-bottom: 14px;
}

.type-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.type-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.type-name {
  font-size: 13px;
  color: #606266;
}

.type-bar-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-bar {
  height: 8px;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.type-value {
  font-size: 12px;
  color: #909399;
  min-width: 24px;
}

/* AI洞察卡片样式 */
.ai-insights-card {
  border-radius: 8px;
  margin-top: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
}

.ai-icon {
  margin-right: 8px;
  color: #409eff;
}

.ai-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ai-summary {
  margin-bottom: 10px;
}

.summary-text {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 12px 0;
}

.insights-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
}

.insights-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.insight-icon {
  color: #e6a23c;
  margin-top: 2px;
  flex-shrink: 0;
}

.insight-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.vuln-types-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
}

.vuln-types-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.vuln-type-tag {
  font-size: 12px;
}

.recommendation-section {
  background: white;
  padding: 16px;
  border-radius: 8px;
}

.recommendation-text {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.reco-icon {
  color: #67c23a;
  margin-top: 2px;
  flex-shrink: 0;
}
</style>
