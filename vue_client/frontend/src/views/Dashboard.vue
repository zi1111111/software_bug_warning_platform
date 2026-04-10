<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SidebarLayout from '../components/SidebarLayout.vue'
import { Clock, Download, Refresh, Setting, Timer, Collection, Plus, Cpu } from "@element-plus/icons-vue"
import { storeToRefs } from "pinia"
import { useRepoStore } from "../stores/repository"
import {BaseResponse, http} from "../request/request"
import {Stats, VulnItem} from "../response/response"
import { useRoute, useRouter } from 'vue-router'

const repoTS = useRepoStore()
const { repositories } = storeToRefs(repoTS)
const route = useRoute()
const router = useRouter()

// 当前选中的仓库
const currentRepo = ref<any>(null)

// 统计数据
const stats = ref<Stats>({
  totalVulns: 0,
  critical: 0,
  high: 0,
  medium: 0,
  low: 0,
})// 添加类型注解


// 漏洞列表（分页）
const vulnList = ref<VulnItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const severityFilter = ref('')  // 筛选严重等级: Critical, High, Medium, Low, ''

// 漏洞详情弹窗
const detailVisible = ref(false)
const currentVuln = ref<any>(null)

// 获取默认仓库
const getDefaultRepo = () => {
  const repos = repositories.value
  if (!repos.length) return null
  const activeRepo = repos.find(r => r.is_active === true)
  return activeRepo || repos[0]
}



// 加载统计卡片数据
const loadStats = async () => {
  if (!currentRepo.value) return
    const res = await http.post<
  {
    'stats':Stats,
    'code':number
  }
  >('/api/getVulnStats',
        { id: currentRepo.value.id  })
    if (res.code === 200 && res.data) {
      stats.value = res.data.stats
    } else {
      console.warn('统计数据加载失败')
    }
}

// 加载漏洞列表
const loadVulnList = async () => {
  if (!currentRepo.value) return
  loading.value = true
    const res = await http.post<{
      'vulnList': VulnItem[],
      'total':number,
      'code':number
    }>('/api/getVulnerabilities', {
        id: currentRepo.value.id,
        page: currentPage.value,
        page_size: pageSize.value,
        severity: severityFilter.value || undefined
    })
    if (res.code === 200 && res.data) {
      vulnList.value = res.data.vulnList
      total.value =  res.data.total
    } else {
      vulnList.value = []
      total.value = 0
    }
}

// 立即扫描
const handleScan = async () => {
  if (!currentRepo.value) return

    await ElMessageBox.confirm(`确定要立即扫描仓库 "${currentRepo.value.name}" 吗？此操作可能需要几分钟。`, '确认扫描', {
      confirmButtonText: '开始扫描',
      cancelButtonText: '取消',
      type: 'info'
    })
    const res = await http.post('/api/searchCommit', { id: currentRepo.value.id })
    if (res.code === 200) {
      ElMessage.success('扫描任务已启动，请稍后查看结果')
      // 可选：延迟刷新数据
      setTimeout(() => {
        loadStats()
        loadVulnList()
      }, 3000)
    } else {
      ElMessage.error('扫描失败：' + (res.message || '未知错误'))
    }
}

// 导出报告（CSV）
const exportReport = () => {
  if (!vulnList.value.length) {
    ElMessage.warning('没有漏洞数据可导出')
    return
  }
  const headers = ['CVE ID', '漏洞标题', '严重等级', '漏洞类型', '摘要', '分析时间']
  const rows = vulnList.value.map(v => [
    v.cve_id || '--',
    v.summary || v.title || '--',
    v.severity || '--',
    v.vulnerability_type || '--',
    (v.summary || '').substring(0, 100),
    v.analyzed_at ? new Date(v.analyzed_at).toLocaleString() : '--'
  ])
  const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
  const blob = new Blob(["\uFEFF" + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.href = url
  link.setAttribute('download', `${currentRepo.value.name}_vulnerabilities.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

// 查看漏洞详情
const viewDetail = (row: any) => {
  currentVuln.value = row
  detailVisible.value = true
}

// 查看详情
const showDetail = (vuln: VulnItem) => {
  currentVuln.value = vuln
  detailVisible.value = true
}

// 获取一致性颜色
const getConsensusColor = (rate: number) => {
  if (rate >= 0.9) return '#67c23a'  // 绿色 - 高度一致
  if (rate >= 0.6) return '#e6a23c'  // 黄色 - 基本一致
  return '#f56c6c'  // 红色 - 存在分歧
}

// 获取模型显示名称
const getModelDisplayName = (name: string) => {
  const nameMap: Record<string, string> = {
    'deepseek_v32': 'DeepSeek-V3.2',
    'qwen35_397b': 'Qwen3.5-397B',
    'glm5': 'GLM-5',
    'hunyuan': 'Hunyuan'
  }
  return nameMap[name] || name
}

// 手动分析（触发对未分析 commits 的分析）
const manualAnalyze = async () => {
  if (!currentRepo.value) return

    await ElMessageBox.confirm(`对仓库 "${currentRepo.value.name}" 中未分析的 commits 进行安全分析？`, '手动分析', {
      confirmButtonText: '开始分析',
      cancelButtonText: '取消',
      type: 'info'
    })
    const res = await http.post('/api/analyzeRepo', { id: currentRepo.value.id })
    if (res.code === 200) {
      ElMessage.success('分析任务已启动，请稍后刷新')
      setTimeout(() => {
        loadStats()
        loadVulnList()
      }, 300)
    } else {
      ElMessage.error('分析失败：' + (res.message || '未知错误'))
    }
}

// 监听仓库切换
watch(currentRepo, (newRepo) => {
  if (newRepo) {
    currentPage.value = 1
    severityFilter.value = ''
    loadStats()
    loadVulnList()
  }
})

// 监听分页和筛选变化
watch([currentPage, pageSize, severityFilter], () => {
  loadVulnList()
})

// 初始化
onMounted(() => {
  // 检查URL query参数中是否有指定的repoId
  const repoIdFromQuery = route.query.repoId
  if (repoIdFromQuery && repositories.value.length) {
    const targetRepo = repositories.value.find(r => r.id === Number(repoIdFromQuery))
    if (targetRepo) {
      currentRepo.value = targetRepo
      return
    }
  }
  
  if (repositories.value.length && !currentRepo.value) {
    currentRepo.value = getDefaultRepo()
  }
})

// 监听 repositories 变化
watch(repositories, (newRepos) => {
  if (newRepos.length && !currentRepo.value) {
    currentRepo.value = getDefaultRepo()
  }
}, { immediate: true })

// 处理仓库切换（来自 SidebarLayout）
const handleRepoChange = (repo: any) => {
  currentRepo.value = repo
}

// 跳转到仓库管理页面
const goToRepoManagement = () => {
  router.push('/repositories')
}

// 严重等级标签样式
const getSeverityType = (severity: string) => {
  const map: Record<string, string> = {
    Critical: 'danger',
    High: 'warning',
    Medium: 'primary',
    Low: 'info'
  }
  return map[severity] || 'info'
}

const getSeverityLabel = (severity: string) => {
  const map: Record<string, string> = {
    Critical: '严重',
    High: '高危',
    Medium: '中危',
    Low: '低危'
  }
  return map[severity] || severity
}
</script>

<template>
  <SidebarLayout :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo ? currentRepo.name + ' - 仪表盘' : '仪表盘' }}
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

    <div v-else class="dashboard">
      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="4">
          <el-card class="stat-card total" shadow="hover">
            <div class="stat-value">{{ stats.totalVulns }}</div>
            <div class="stat-label" style="color: white">漏洞总数</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card critical" shadow="hover">
            <div class="stat-value">{{ stats.critical }}</div>
            <div class="stat-label" style="color: white">严重</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card high" shadow="hover">
            <div class="stat-value">{{ stats.high }}</div>
            <div class="stat-label" style="color: white">高危</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card medium" shadow="hover">
            <div class="stat-value"  style="color: white">{{ stats.medium }}</div>
            <div class="stat-label" style="color: white">中危</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card low" shadow="hover">
            <div class="stat-value">{{ stats.low }}</div>
            <div class="stat-label" style="color: white">低危</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 仓库信息卡片 -->
      <el-card class="repo-info-card" shadow="hover">
        <div class="repo-header">
          <div class="repo-title-section">
            <el-icon :size="32" class="repo-icon"><Collection /></el-icon>
            <div class="repo-title-info">
              <h2 class="repo-name">{{ currentRepo.name }}</h2>
              <p class="repo-desc">{{ currentRepo.repo_url || '暂无描述' }}</p>
            </div>
          </div>
          <div class="repo-actions">
            <el-button type="primary" @click="handleScan">
              <el-icon><Refresh /></el-icon>
              立即扫描
            </el-button>
            <el-button @click="manualAnalyze">
              <el-icon><Plus /></el-icon>
              手动分析
            </el-button>
            <el-button @click="exportReport">
              <el-icon><Download /></el-icon>
              导出报告
            </el-button>
          </div>
        </div>

        <el-divider />

        <div class="repo-meta">
          <div class="meta-item">
            <el-icon><Timer /></el-icon>
            <span>最后扫描: {{ currentRepo.last_fetched_at || '暂无' }}</span>
          </div>
          <div class="meta-item">
            <el-icon><Clock /></el-icon>
            <span>下次扫描: 今天凌晨2点</span>
          </div>
          <div class="meta-item">
            <el-icon><Setting /></el-icon>
            <span>扫描频率: 每天</span>
          </div>
        </div>
      </el-card>

      <!-- 漏洞列表 -->
      <el-card class="vuln-list-card" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="card-title">安全漏洞列表</span>
            <div class="card-filters">
              <el-select v-model="severityFilter" placeholder="筛选严重等级" clearable style="width: 120px; margin-right: 12px;">
                <el-option label="严重" value="Critical" />
                <el-option label="高危" value="High" />
                <el-option label="中危" value="Medium" />
                <el-option label="低危" value="Low" />
              </el-select>
              <el-button type="primary" link @click="loadVulnList">
                刷新
                <el-icon class="el-icon--right"><Refresh /></el-icon>
              </el-button>
            </div>
          </div>
        </template>

        <el-table
            :data="vulnList"
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
        >
          <el-table-column label="影响的子系统" width="140">
            <template #default="{ row }">
              <el-link type="primary" :underline="false" @click="viewDetail(row)">{{ row. affected_subsystem || '--' }}</el-link>
            </template>
          </el-table-column>
          <el-table-column label="摘要" min-width="280">
            <template #default="{ row }">
              <span class="vuln-title">{{ row.summary || '暂无摘要' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="漏洞类型" width="150">
            <template #default="{ row }">{{ row.vulnerability_type || '--' }}</template>
          </el-table-column>
          <el-table-column label="初始严重等级" width="120">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" effect="dark">
                {{ getSeverityLabel(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="最终严重等级" width="120">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" effect="dark">
                {{ getSeverityLabel(row.final_severity) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分析时间" width="180">
            <template #default="{ row }">{{ row.analyzed_at ? new Date(row.analyzed_at).toLocaleString() : '--' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadVulnList"
              @current-change="loadVulnList"
          />
        </div>
      </el-card>
    </div>

    <!-- 漏洞详情弹窗 -->
    <el-dialog v-model="detailVisible" title="漏洞详情" width="800px">
      <div v-if="currentVuln">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="CVE ID">{{ currentVuln.cve_id || '无' }}</el-descriptions-item>
          <el-descriptions-item label="最终严重等级">
            <el-tag :type="getSeverityType(currentVuln.severity)">{{ getSeverityLabel(currentVuln.final_severity) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="漏洞类型">{{ currentVuln.vulnerability_type || '无' }}</el-descriptions-item>
          <el-descriptions-item label="影响子系统">{{ currentVuln.affected_subsystem || '无' }}</el-descriptions-item>
          <el-descriptions-item label="摘要">{{ currentVuln.summary || '无' }}</el-descriptions-item>
          <el-descriptions-item label="分析模型">{{ currentVuln.model_name || '--' }}</el-descriptions-item>
          <el-descriptions-item label="分析时间">{{ currentVuln.analyzed_at ? new Date(currentVuln.analyzed_at).toLocaleString() : '--' }}</el-descriptions-item>
        </el-descriptions>
        
        <!-- 模型思考过程 -->
        <div v-if="currentVuln.thinking" class="thinking-section">
          <el-divider />
          <h4 class="thinking-title">
            <el-icon><Cpu /></el-icon>
            模型思考过程
          </h4>
          <el-card class="thinking-card" shadow="never">
            <div class="thinking-content">{{ currentVuln.thinking }}</div>
          </el-card>
        </div>

        <!-- 多模型审查结果 -->
        <div v-if="currentVuln.review_result" class="review-section">
          <el-divider />
          <h4 class="review-title">
            <el-icon><ChatDotRound /></el-icon>
            多模型严重性审查
          </h4>

          <!-- 审查概览 -->
          <el-card class="review-overview" shadow="never">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="review-stat">
                  <div class="stat-label">原始判断</div>
                  <el-tag :type="getSeverityType(currentVuln.severity)" size="large">
                    {{ getSeverityLabel(currentVuln.severity) }}
                  </el-tag>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="review-stat">
                  <div class="stat-label">最终判定</div>
                  <el-tag :type="getSeverityType(currentVuln.final_severity)" size="large" effect="dark">
                    {{ getSeverityLabel(currentVuln.final_severity) }}
                  </el-tag>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="review-stat">
                  <div class="stat-label">一致性</div>
                  <el-progress
                    :percentage="Math.round(currentVuln.review_result.consensus_rate * 100)"
                    :color="getConsensusColor(currentVuln.review_result.consensus_rate)"
                    :stroke-width="8"
                  />
                </div>
              </el-col>
            </el-row>
            <div class="review-summary">{{ currentVuln.review_result.review_summary }}</div>
          </el-card>

          <!-- 各模型详细结果 -->
          <div class="model-results">
            <h5 class="model-results-title">各模型审查详情</h5>
            <el-collapse>
              <el-collapse-item
                v-for="(modelResult, modelName) in currentVuln.review_result.model_results"
                :key="modelName"
                :title="getModelDisplayName(modelName) + ' - ' + getSeverityLabel(modelResult.severity)"
              >
                <div class="model-detail">
                  <div class="confidence-bar">
                    <span class="label">置信度:</span>
                    <el-progress :percentage="Math.round(modelResult.confidence * 100)" :stroke-width="6" />
                  </div>
                  <div class="reasoning">
                    <div class="label">判断理由:</div>
                    <div class="reasoning-text">{{ modelResult.reasoning }}</div>
                  </div>
                  <div v-if="modelResult.key_factors?.length" class="key-factors">
                    <div class="label">关键因素:</div>
                    <el-tag
                      v-for="(factor, idx) in modelResult.key_factors"
                      :key="idx"
                      type="info"
                      size="small"
                      class="factor-tag"
                    >{{ factor }}</el-tag>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>

          <!-- 投票分布 -->
          <div v-if="currentVuln.review_result.voting_breakdown" class="voting-breakdown">
            <h5 class="voting-title">投票分布</h5>
            <el-row :gutter="10">
              <el-col
                v-for="(weight, severity) in currentVuln.review_result.voting_breakdown"
                :key="String(severity)"
                :span="6"
              >
                <el-card class="vote-card" :class="String(severity).toLowerCase()" shadow="hover">
                  <div class="vote-severity">{{ getSeverityLabel(String(severity)) }}</div>
                  <div class="vote-weight">{{ (Number(weight) * 100).toFixed(1) }}%</div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
      </div>
    </el-dialog>
  </SidebarLayout>
</template>

<style scoped>
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 200px);
}
body {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
}
.dashboard {
  padding: 0;
}
.stats-row {
  margin-bottom: 20px;
  justify-content: center;
}
.stat-card {
  text-align: center;
  border-radius: 8px;
  transition: transform 0.3s ease;
}
.stat-card:hover {
  transform: translateY(-4px);
}
.stat-card.total {
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
  color: white;
}
.stat-card.critical {
  background: linear-gradient(135deg, #c62828 0%, #e53935 100%);
  color: white;
}
.stat-card.high {
  background: linear-gradient(135deg, #e65100 0%, #f57c00 100%);
  color: white;
}
.stat-card.medium {
  background: linear-gradient(135deg, #f9a825 0%, #ffca28 100%);
  color: #333;
}
.stat-card.low {
  background: linear-gradient(135deg, #2e7d32 0%, #4caf50 100%);
  color: white;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
}
.stat-label {
  font-size: 13px;
  opacity: 0.9;
}
.repo-info-card {
  margin-bottom: 20px;
  border-radius: 8px;
}
.repo-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}
.repo-title-section {
  display: flex;
  align-items: center;
  gap: 16px;
}
.repo-icon {
  color: #1a237e;
}
.repo-title-info {
  flex: 1;
}
.repo-name {
  margin: 0 0 4px 0;
  font-size: 22px;
  font-weight: 600;
  color: #1a237e;
}
.repo-desc {
  margin: 0;
  color: #606266;
  font-size: 14px;
}
.repo-actions {
  display: flex;
  gap: 12px;
}
.repo-meta {
  display: flex;
  gap: 40px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 13px;
}

.vuln-list-card {
  border-radius: 8px;
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
.card-filters {
  display: flex;
  align-items: center;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.commit-info p {
  margin: 8px 0;
  font-size: 14px;
}

/* 模型思考过程样式 */
.thinking-section {
  margin-top: 20px;
}

.thinking-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a237e;
}

.thinking-card {
  background: #f8f9fa;
  border-left: 4px solid #1a237e;
}

.thinking-card :deep(.el-card__body) {
  padding: 16px;
}

.thinking-content {
  font-size: 14px;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* 多模型审查结果样式 */
.review-section {
  margin-top: 20px;
}

.review-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1a237e;
  margin: 16px 0;
}

.review-overview {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
}

.review-stat {
  text-align: center;
  padding: 16px;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.review-summary {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #dcdfe6;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.model-results {
  margin-bottom: 20px;
}

.model-results-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.model-detail {
  padding: 12px;
}

.confidence-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.confidence-bar .label {
  font-size: 13px;
  color: #606266;
  min-width: 60px;
}

.reasoning {
  margin-bottom: 12px;
}

.reasoning .label {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.reasoning-text {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.key-factors {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.key-factors .label {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-right: 8px;
}

.factor-tag {
  margin-right: 4px;
}

.voting-breakdown {
  margin-top: 16px;
}

.voting-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.vote-card {
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.vote-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.vote-card.critical {
  background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
  border-color: #f56c6c;
}

.vote-card.high {
  background: linear-gradient(135deg, #fdf6ec 0%, #ffffff 100%);
  border-color: #e6a23c;
}

.vote-card.medium {
  background: linear-gradient(135deg, #f0f9eb 0%, #ffffff 100%);
  border-color: #67c23a;
}

.vote-card.low {
  background: linear-gradient(135deg, #f4f4f5 0%, #ffffff 100%);
  border-color: #909399;
}

.vote-severity {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 4px;
}

.vote-weight {
  font-size: 12px;
  color: #909399;
}
</style>