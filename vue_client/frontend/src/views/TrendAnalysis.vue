<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import SidebarLayout from '../components/SidebarLayout.vue'
import { storeToRefs } from "pinia"
import { useRepoStore } from "../stores/repository"
import { http } from "../request/request"
import type { 
  GetTrendAnalysisResponse, 
  TrendDataPoint,
  SeverityDistributionItem,
  ComponentRankingItem,
  VulnTypeDistributionItem,
  Repository 
} from "../response/response"

// 仓库相关
const repoTS = useRepoStore()
const { repositories } = storeToRefs(repoTS)

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
const severityDistribution = ref<SeverityDistributionItem[]>([])
const componentRanking = ref<ComponentRankingItem[]>([])
const vulnTypeDistribution = ref<VulnTypeDistributionItem[]>([])

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
      severityDistribution.value = res.data.severity_distribution || []
      componentRanking.value = res.data.component_ranking || []
      vulnTypeDistribution.value = res.data.vuln_type_distribution || []
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
const getSeverityColor = (severity: string) => {
  const map: Record<string, string> = {
    critical: '#f56c6c',
    high: '#e6a23c',
    medium: '#409eff',
    low: '#67c23a'
  }
  return map[severity] || '#909399'
}

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
</script>

<template>
  <SidebarLayout v-if="currentRepo" :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo.name }} - 趋势分析
    </template>

    <div class="trend-analysis" v-loading="loading">
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
            <div class="stat-value">{{ severityDistribution.reduce((a: number, b) => a + b.value, 0) }}</div>
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

      <el-row :gutter="20" class="bottom-row">
        <!-- 严重等级分布 -->
        <el-col :span="8">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">严重等级分布</span>
            </template>
            <div class="distribution-chart" v-if="severityDistribution.length > 0">
              <div 
                v-for="(item, index) in severityDistribution" 
                :key="item.name"
                class="distribution-item"
              >
                <div class="distribution-bar-container">
                  <span class="distribution-label">{{ item.name }}</span>
                  <div class="distribution-bar-wrapper">
                    <div 
                      class="distribution-bar"
                      :style="{ 
                        width: (item.value / severityDistribution.reduce((a, b) => a + b.value, 0) * 100) + '%',
                        background: chartColors[index % chartColors.length]
                      }"
                    ></div>
                  </div>
                  <span class="distribution-value">{{ item.value }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无分布数据" />
          </el-card>
        </el-col>

        <!-- 组件漏洞排行 -->
        <el-col :span="8">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">组件漏洞排行</span>
            </template>
            <div class="ranking-list" v-if="componentRanking.length > 0">
              <div 
                v-for="(item, index) in componentRanking" 
                :key="item.name"
                class="ranking-item"
              >
                <div class="ranking-number" :class="{ 'top3': index < 3 }">{{ index + 1 }}</div>
                <div class="ranking-info">
                  <div class="ranking-name">{{ item.name }}</div>
                  <el-tag 
                    :type="item.severity === 'critical' ? 'danger' : item.severity === 'high' ? 'warning' : 'info'"
                    size="small"
                  >
                    {{ getSeverityLabel(item.severity) }}
                  </el-tag>
                </div>
                <div class="ranking-count">{{ item.vuln_count }}</div>
              </div>
            </div>
            <el-empty v-else description="暂无排行数据" />
          </el-card>
        </el-col>

        <!-- 漏洞类型分布 -->
        <el-col :span="8">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">漏洞类型分布</span>
            </template>
            <div class="type-distribution" v-if="vulnTypeDistribution.length > 0">
              <div 
                v-for="(item, index) in vulnTypeDistribution" 
                :key="item.name"
                class="type-item"
              >
                <div class="type-info">
                  <span class="type-color" :style="{ background: chartColors[index % chartColors.length] }"></span>
                  <span class="type-name">{{ item.name }}</span>
                </div>
                <div class="type-bar-container">
                  <div 
                    class="type-bar"
                    :style="{ 
                      width: (item.value / vulnTypeDistribution.reduce((a, b) => a + b.value, 0) * 100) + '%',
                      background: chartColors[index % chartColors.length]
                    }"
                  ></div>
                  <span class="type-value">{{ item.value }}</span>
                </div>
              </div>
            </div>
            <el-empty v-else description="暂无类型数据" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </SidebarLayout>
  <div v-else class="loading-container">加载中...</div>
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
  border-radius: 8px;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stat-icon {
  font-size: 24px;
  padding: 10px;
  border-radius: 8px;
}

.stat-icon.red {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-icon.green {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-icon.blue {
  background: #ecf5ff;
  color: #409eff;
}

.stat-icon.orange {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-trend {
  font-size: 13px;
  font-weight: 500;
}

.stat-trend.up {
  color: #67c23a;
}

.stat-trend.down {
  color: #f56c6c;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.chart-card {
  border-radius: 8px;
  margin-bottom: 20px;
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
</style>
