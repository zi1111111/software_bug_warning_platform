<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import SidebarLayout from '../components/SidebarLayout.vue'
import { storeToRefs } from "pinia"
import { useRepoStore } from "../stores/repository"
import { http } from "../request/request"
import { useRouter } from 'vue-router'
import type { 
  GetRiskAssessmentResponse, 
  RiskScoreData,
  RiskDistributionItem,
  ComponentRiskItem,
  AttackSurfaceData,
  PriorityRecommendationItem,
  RiskTrendPoint,
  Repository 
} from "../response/response"
import {Calendar, Timer, Warning} from "@element-plus/icons-vue";

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
  loadRiskData()
}

// 时间范围选择
const timeRange = ref('30d')
const timeRangeOptions = [
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' },
  { label: '最近90天', value: '90d' }
]

// 数据状态
const riskScore = ref<RiskScoreData>({
  overall: 0,
  breakdown: { critical: 0, high: 0, medium: 0, low: 0 }
})

const riskDistribution = ref<RiskDistributionItem[]>([])
const componentRisks = ref<ComponentRiskItem[]>([])
const attackSurface = ref<AttackSurfaceData>({
  entry_points: 0,
  exposed_apis: 0,
  third_party_deps: 0,
  vulnerable_deps: 0
})
const priorityRecommendations = ref<PriorityRecommendationItem[]>([])
const riskTrendData = ref<RiskTrendPoint[]>([])

// 风险详情对话框
const detailDialogVisible = ref(false)
const selectedComponent = ref<ComponentRiskItem | null>(null)

// 加载风险评估数据
const loadRiskData = async () => {
  if (!currentRepo.value) return
  
  loading.value = true
  try {
    const res = await http.post<GetRiskAssessmentResponse>('/api/getRiskAssessment', {
      id: currentRepo.value.id,
      time_range: timeRange.value
    })
    
    if (res.code === 200 && res.data) {
      riskScore.value = res.data.risk_score || { overall: 0, breakdown: { critical: 0, high: 0, medium: 0, low: 0 } }
      riskDistribution.value = res.data.risk_distribution || []
      componentRisks.value = res.data.component_risks || []
      attackSurface.value = res.data.attack_surface || { entry_points: 0, exposed_apis: 0, third_party_deps: 0, vulnerable_deps: 0 }
      priorityRecommendations.value = res.data.priority_recommendations || []
    } else {
      ElMessage.error(res.message || '加载风险评估数据失败')
    }
  } catch (error) {
    ElMessage.error('网络请求失败，请稍后重试')
    console.error('Load risk data error:', error)
  } finally {
    loading.value = false
  }
}

// 计算属性：总体风险等级
const overallRiskLevel = computed(() => {
  if (riskScore.value.overall >= 80) return { level: '极高', type: 'danger' }
  if (riskScore.value.overall >= 60) return { level: '高', type: 'warning' }
  if (riskScore.value.overall >= 40) return { level: '中', type: 'primary' }
  return { level: '低', type: 'success' }
})

// 获取风险分数颜色
const getRiskScoreColor = (score: number) => {
  if (score >= 80) return '#f56c6c'
  if (score >= 60) return '#e6a23c'
  if (score >= 40) return '#409eff'
  return '#67c23a'
}

// 获取严重等级样式
const getSeverityType = (severity: string) => {
  const map: Record<string, string> = {
    critical: 'danger',
    high: 'warning',
    medium: 'primary',
    low: 'info'
  }
  return map[severity] || 'info'
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

// 查看组件详情
const viewComponentDetail = (component: ComponentRiskItem) => {
  selectedComponent.value = component
  detailDialogVisible.value = true
}

// 导出风险评估报告
const exportReport = () => {
  // 生成CSV报告
  const headers = ['组件名称', '版本', '风险评分', '漏洞数量', '最高严重等级', '暴露程度', '修复建议']
  const rows = componentRisks.value.map(c => [
    c.name,
    c.version,
    c.risk_score,
    c.vuln_count,
    getSeverityLabel(c.max_severity),
    c.exposure === 'high' ? '高' : c.exposure === 'medium' ? '中' : '低',
    c.recommendation
  ])
  
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.href = url
  link.setAttribute('download', `${currentRepo.value?.name || '仓库'}_风险评估报告.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('风险评估报告导出成功')
}

// 监听时间范围变化
watch(timeRange, () => {
  loadRiskData()
})

// 初始化
onMounted(() => {
  if (repositories.value.length) {
    currentRepo.value = getDefaultRepo()
    if (currentRepo.value) {
      loadRiskData()
    }
  }
})

// 监听仓库列表变化
watch(repositories, (newRepos) => {
  if (newRepos.length && !currentRepo.value) {
    currentRepo.value = getDefaultRepo()
    if (currentRepo.value) {
      loadRiskData()
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
      {{ currentRepo ? currentRepo.name + ' - 风险评估' : '风险评估' }}
    </template>

    <!-- 无仓库时的空状态 -->
    <div v-if="!currentRepo" class="empty-state">
      <el-empty description="暂无仓库数据">
        <template #image>
          <el-icon :size="80" color="#c0c4cc"><Box /></el-icon>
        </template>
        <el-button type="primary" @click="goToRepoManagement">前往添加仓库</el-button>
      </el-empty>
    </div>

    <div v-else class="risk-assessment" v-loading="loading">
      <!-- 顶部操作区 -->
      <el-card class="filter-card" shadow="never">
        <div class="filter-content">
          <div class="time-selector">
            <span class="filter-label">评估周期:</span>
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
          <el-button type="primary" @click="exportReport">
            <el-icon><Download /></el-icon>
            导出评估报告
          </el-button>
        </div>
      </el-card>

      <!-- 总体风险评分 -->
      <el-row :gutter="20" class="main-stats-row">
        <el-col :span="8">
          <el-card class="risk-score-card" shadow="hover">
            <template #header>
              <span class="card-title">总体风险评分</span>
            </template>
            <div class="score-display">
              <div 
                class="score-circle"
                :style="{ borderColor: getRiskScoreColor(riskScore.overall) }"
              >
                <span 
                  class="score-value"
                  :style="{ color: getRiskScoreColor(riskScore.overall) }"
                >
                  {{ riskScore.overall }}
                </span>
                <span class="score-total">/100</span>
              </div>
              <div class="risk-level">
                <el-tag :type="overallRiskLevel.type" size="large" effect="dark">
                  {{ overallRiskLevel.level }}风险
                </el-tag>
              </div>
            </div>
            <div class="score-breakdown">
              <div class="breakdown-item">
                <span class="breakdown-label">严重漏洞贡献</span>
                <el-progress :percentage="riskScore.breakdown.critical" color="#f56c6c" />
              </div>
              <div class="breakdown-item">
                <span class="breakdown-label">高危漏洞贡献</span>
                <el-progress :percentage="riskScore.breakdown.high" color="#e6a23c" />
              </div>
              <div class="breakdown-item">
                <span class="breakdown-label">中危漏洞贡献</span>
                <el-progress :percentage="riskScore.breakdown.medium" color="#409eff" />
              </div>
              <div class="breakdown-item">
                <span class="breakdown-label">低危漏洞贡献</span>
                <el-progress :percentage="riskScore.breakdown.low" color="#67c23a" />
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card class="risk-distribution-card" shadow="hover">
            <template #header>
              <span class="card-title">风险等级分布</span>
            </template>
            <div class="distribution-list">
              <div 
                v-for="item in riskDistribution" 
                :key="item.level"
                class="distribution-item"
              >
                <div class="distribution-header">
                  <span class="level-name" :style="{ color: item.color }">{{ item.level }}</span>
                  <span class="level-count">{{ item.count }}个</span>
                </div>
                <el-progress 
                  :percentage="item.percentage" 
                  :color="item.color"
                  :stroke-width="12"
                  :show-text="false"
                />
                <div class="percentage-text">{{ item.percentage }}%</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <el-card class="attack-surface-card" shadow="hover">
            <template #header>
              <span class="card-title">攻击面分析</span>
            </template>
            <div class="attack-stats">
              <div class="attack-item">
                <div class="attack-icon blue">
                  <el-icon><Connection /></el-icon>
                </div>
                <div class="attack-info">
                  <div class="attack-value">{{ attackSurface.entry_points }}</div>
                  <div class="attack-label">入口点数量</div>
                </div>
              </div>
              <div class="attack-item">
                <div class="attack-icon orange">
                  <el-icon><Link /></el-icon>
                </div>
                <div class="attack-info">
                  <div class="attack-value">{{ attackSurface.exposed_apis }}</div>
                  <div class="attack-label">暴露API数</div>
                </div>
              </div>
              <div class="attack-item">
                <div class="attack-icon purple">
                  <el-icon><Box /></el-icon>
                </div>
                <div class="attack-info">
                  <div class="attack-value">{{ attackSurface.third_party_deps }}</div>
                  <div class="attack-label">第三方依赖</div>
                </div>
              </div>
              <div class="attack-item">
                <div class="attack-icon red">
                  <el-icon><Warning /></el-icon>
                </div>
                <div class="attack-info">
                  <div class="attack-value">{{ attackSurface.vulnerable_deps }}</div>
                  <div class="attack-label">存在漏洞依赖</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 组件风险评估 -->
      <el-card class="component-risk-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span class="card-title">组件风险评估</span>
          </div>
        </template>
        
        <el-table :data="componentRisks" style="width: 100%">
          <el-table-column label="组件" width="150">
            <template #default="{ row }">
              <div class="component-cell">
                <el-icon :size="20"><Box /></el-icon>
                <div class="component-info">
                  <div class="component-name">{{ row.name }}</div>
                  <div class="component-version">{{ row.version }}</div>
                </div>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="风险评分" width="120">
            <template #default="{ row }">
              <div 
                class="risk-score-badge"
                :style="{ background: getRiskScoreColor(row.risk_score) }"
              >
                {{ row.risk_score }}
              </div>
            </template>
          </el-table-column>

          <el-table-column label="漏洞数量" width="100">
            <template #default="{ row }">
              <el-tag :type="row.vuln_count > 3 ? 'danger' : row.vuln_count > 1 ? 'warning' : 'info'">
                {{ row.vuln_count }}个
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="最高严重等级" width="120">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.max_severity)" effect="dark">
                {{ getSeverityLabel(row.max_severity) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="暴露程度" width="100">
            <template #default="{ row }">
              <el-tag 
                :type="row.exposure === 'high' ? 'danger' : row.exposure === 'medium' ? 'warning' : 'success'"
                size="small"
              >
                {{ row.exposure === 'high' ? '高' : row.exposure === 'medium' ? '中' : '低' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="修复建议" min-width="250">
            <template #default="{ row }">
              <span class="recommendation-text">{{ row.recommendation }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="viewComponentDetail(row)">
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 修复优先级建议 -->
      <el-card class="priority-card" shadow="hover">
        <template #header>
          <span class="card-title">修复优先级建议</span>
        </template>
        
        <div class="priority-list">
          <div 
            v-for="(item, index) in priorityRecommendations" 
            :key="index"
            class="priority-item"
          >
            <div class="priority-number" :class="`priority-${item.priority}`">
              {{ item.priority }}
            </div>
            <div class="priority-content">
              <div class="priority-header">
                <span class="priority-title">{{ item.title }}</span>
                <el-tag :type="getSeverityType(item.severity)" size="small">
                  {{ getSeverityLabel(item.severity) }}
                </el-tag>
              </div>
              <div class="priority-details">
                <span class="detail-item">
                  <el-icon><Warning /></el-icon>
                  影响: {{ item.impact }}
                </span>
                <span class="detail-item">
                  <el-icon><Timer /></el-icon>
                  工作量: {{ item.effort }}
                </span>
                <span class="detail-item">
                  <el-icon><Calendar /></el-icon>
                  建议时间: {{ item.timeframe }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 组件详情对话框 -->
      <el-dialog
        v-model="detailDialogVisible"
        title="组件风险详情"
        width="600px"
      >
        <div v-if="selectedComponent" class="component-detail">
          <div class="detail-header">
            <h3>{{ selectedComponent.name }} @ {{ selectedComponent.version }}</h3>
            <div 
              class="detail-score"
              :style="{ color: getRiskScoreColor(selectedComponent.risk_score) }"
            >
              风险评分: {{ selectedComponent.risk_score }}
            </div>
          </div>
          
          <el-divider />
          
          <div class="detail-section">
            <h4>风险因素</h4>
            <ul>
              <li>存在 {{ selectedComponent.vuln_count }} 个已知漏洞</li>
              <li>最高严重等级: {{ getSeverityLabel(selectedComponent.max_severity) }}</li>
              <li>暴露程度: {{ selectedComponent.exposure === 'high' ? '高' : selectedComponent.exposure === 'medium' ? '中' : '低' }}</li>
            </ul>
          </div>
          
          <div class="detail-section">
            <h4>修复建议</h4>
            <p>{{ selectedComponent.recommendation }}</p>
          </div>
        </div>
      </el-dialog>
    </div>
  </SidebarLayout>
</template>

<style scoped>
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 200px);
}

.risk-assessment {
  padding: 0;
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.time-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-weight: 500;
  color: #606266;
}

.main-stats-row {
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 风险评分卡片 */
.risk-score-card {
  border-radius: 8px;
  height: 100%;
}

.score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 8px solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.score-value {
  font-size: 42px;
  font-weight: 700;
  line-height: 1;
}

.score-total {
  font-size: 14px;
  color: #909399;
}

.risk-level {
  margin-bottom: 24px;
}

.score-breakdown {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.breakdown-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.breakdown-label {
  font-size: 13px;
  color: #606266;
}

/* 风险分布卡片 */
.risk-distribution-card {
  border-radius: 8px;
  height: 100%;
}

.distribution-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 10px 0;
}

.distribution-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.distribution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.level-name {
  font-weight: 600;
  font-size: 14px;
}

.level-count {
  font-size: 13px;
  color: #606266;
}

.percentage-text {
  font-size: 12px;
  color: #909399;
  text-align: right;
}

/* 攻击面卡片 */
.attack-surface-card {
  border-radius: 8px;
  height: 100%;
}

.attack-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.attack-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.attack-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.attack-icon.blue {
  background: #ecf5ff;
  color: #409eff;
}

.attack-icon.orange {
  background: #fdf6ec;
  color: #e6a23c;
}

.attack-icon.purple {
  background: #f0f2ff;
  color: #7b68ee;
}

.attack-icon.red {
  background: #fef0f0;
  color: #f56c6c;
}

.attack-info {
  flex: 1;
}

.attack-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.attack-label {
  font-size: 12px;
  color: #909399;
}

/* 组件风险卡片 */
.component-risk-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.component-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.component-info {
  flex: 1;
}

.component-name {
  font-weight: 600;
  color: #303133;
}

.component-version {
  font-size: 12px;
  color: #909399;
}

.risk-score-badge {
  padding: 6px 12px;
  border-radius: 4px;
  color: white;
  font-weight: 700;
  text-align: center;
}

.recommendation-text {
  font-size: 13px;
  color: #606266;
}

/* 优先级卡片 */
.priority-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.priority-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.priority-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: transform 0.3s ease;
}

.priority-item:hover {
  transform: translateX(4px);
}

.priority-number {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.priority-1 {
  background: #f56c6c;
}

.priority-2 {
  background: #e6a23c;
}

.priority-3 {
  background: #409eff;
}

.priority-content {
  flex: 1;
}

.priority-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.priority-title {
  font-weight: 600;
  color: #303133;
}

.priority-details {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #606266;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 趋势卡片 */
.trend-card {
  border-radius: 8px;
}

.trend-chart {
  display: flex;
  height: 200px;
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
  flex-direction: column;
  padding: 0 20px;
}

.trend-line {
  flex: 1;
  position: relative;
}

.trend-line svg {
  width: 100%;
  height: 100%;
}

.x-axis {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.x-axis-label {
  font-size: 12px;
  color: #606266;
}

/* 详情对话框 */
.component-detail {
  padding: 10px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.detail-score {
  font-size: 20px;
  font-weight: 700;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  font-size: 15px;
  color: #606266;
}

.detail-section ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 1.8;
}

.detail-section p {
  margin: 0;
  color: #606266;
  line-height: 1.6;
}
</style>
