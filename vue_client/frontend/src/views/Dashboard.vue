<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SidebarLayout from '../components/SidebarLayout.vue'
import { ArrowRight, Clock, Download, Refresh, Setting, Timer, Collection, Plus } from "@element-plus/icons-vue"
import { storeToRefs } from "pinia"
import { useRepoStore } from "../stores/repository"
import { http } from "../request/request"

const repoTS = useRepoStore()
const { repositories } = storeToRefs(repoTS)

// 当前选中的仓库
const currentRepo = ref<any>(null)

// 统计数据
const stats = ref({
  totalVulns: 0,
  critical: 0,
  high: 0,
  medium: 0,
  low: 0,
})

// 漏洞列表（分页）
const vulnList = ref([])
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
    const res = await http.post('/api/getVulnStats',
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
    const res = await http.post('/api/getVulnerabilities', {
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
  if (repositories.value.length && !currentRepo.value) {
    currentRepo.value = getDefaultRepo()
  } else if (currentRepo.value) {
    loadStats()
    loadVulnList()
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
  <SidebarLayout v-if="currentRepo" :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo.name }} - 漏洞预警
    </template>

    <div class="dashboard">
      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="4">
          <el-card class="stat-card total" shadow="hover">
            <div class="stat-value">{{ stats.totalVulns }}</div>
            <div class="stat-label">漏洞总数</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card critical" shadow="hover">
            <div class="stat-value">{{ stats.critical }}</div>
            <div class="stat-label">严重</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card high" shadow="hover">
            <div class="stat-value">{{ stats.high }}</div>
            <div class="stat-label">高危</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card medium" shadow="hover">
            <div class="stat-value">{{ stats.medium }}</div>
            <div class="stat-label">中危</div>
          </el-card>
        </el-col>
        <el-col :span="4">
          <el-card class="stat-card low" shadow="hover">
            <div class="stat-value">{{ stats.low }}</div>
            <div class="stat-label">低危</div>
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
            <span>下次扫描: 待配置</span>
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
          <el-table-column label="严重等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" effect="dark">
                {{ getSeverityLabel(row.severity) }}
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
    <el-dialog v-model="detailVisible" title="漏洞详情" width="700px">
      <div v-if="currentVuln">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="CVE ID">{{ currentVuln.cve_id || '无' }}</el-descriptions-item>
          <el-descriptions-item label="严重等级">
            <el-tag :type="getSeverityType(currentVuln.severity)">{{ getSeverityLabel(currentVuln.severity) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="漏洞类型">{{ currentVuln.vulnerability_type || '无' }}</el-descriptions-item>
          <el-descriptions-item label="影响子系统">{{ currentVuln.affected_subsystem || '无' }}</el-descriptions-item>
          <el-descriptions-item label="摘要">{{ currentVuln.summary || '无' }}</el-descriptions-item>
          <el-descriptions-item label="分析模型">{{ currentVuln.model_name || '--' }}</el-descriptions-item>
          <el-descriptions-item label="分析时间">{{ currentVuln.analyzed_at ? new Date(currentVuln.analyzed_at).toLocaleString() : '--' }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </SidebarLayout>
  <div v-else class="loading-container">加载中...</div>
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  font-size: 16px;
  color: #909399;
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
.meta-item .el-icon {
  color: #909399;
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
.raw-response {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 300px;
  overflow: auto;
}
</style>