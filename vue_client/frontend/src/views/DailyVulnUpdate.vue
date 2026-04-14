<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
import {
  ArrowRight, Box, CirclePlus, Document, Download, Timer, Warning, WarningFilled
} from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import { storeToRefs } from "pinia";
import { useRepoStore } from "../stores/repository.js";
import { GetVulnDailyResponse, Repository, VulnItem } from "../response/response";
import { http } from "../request/request";
import { useRouter } from 'vue-router'

// 仓库相关
const repoTS = useRepoStore()
const currentRepo = ref<Repository | null>(null)
const { repositories } = storeToRefs(repoTS)
const router = useRouter()

// 分页
const currentPage = ref(1)
const pageSize = ref(5)
const total = ref(0)

// 日期选择
const selectedDate = ref(new Date().toISOString().split('T')[0])

// 搜索关键词（仅前端过滤）
const searchKeyword = ref('')

// 严重程度筛选（后端筛选）
const severityFilter = ref<string[]>([])
const severityOptions = [
  { label: '严重', value: 'critical', color: '#f56c6c' },
  { label: '高危', value: 'high', color: '#e6a23c' },
  { label: '中危', value: 'medium', color: '#409eff' },
  { label: '低危', value: 'low', color: '#67c23a' }
]

// 漏洞类型筛选（后端筛选）
const typeFilter = ref<string[]>([])
const typeOptions = ref<string[]>([])

// 数据
const dailyVulns = ref<VulnItem[]>([])
const newVulns = ref<number>(0)
const stats = ref({
  totalVulns: 0,
  critical: 0,
  high: 0,
  medium: 0,
  low: 0
})

const loading = ref(false)

// 获取默认仓库
const getDefaultRepo = () => {
  const repos = repositories.value
  if (!repos.length) return null
  const activeRepo = repos.find(r => r.is_active === true)
  return activeRepo || repos[0]
}

// 加载数据
const loadData = async () => {
  if (!currentRepo.value) return
  loading.value = true
  try {
    const requestBody = {
      id: currentRepo.value.id,
      page: currentPage.value,
      date: selectedDate.value,
      page_size: pageSize.value,
      severity: severityFilter.value,
      vuln_type: typeFilter.value   // 新增：类型筛选传给后端
    }
    const res = await http.post<GetVulnDailyResponse>('/api/getVulnDaily', requestBody)
    if (res.code === 200 && res.data) {
      console.log(res.data)
      typeOptions.value = res.data.vuln_type || []
      dailyVulns.value = res.data.vulnList || []
      newVulns.value = res.data.new_vulns || 0
      total.value = res.data.total || 0
      stats.value = res.data.stats || {
        totalVulns: 0, critical: 0, high: 0, medium: 0, low: 0
      }
    } else {
      ElMessage.error(res.message || "后端出错啦！请稍后重试")
      dailyVulns.value = []
      total.value = 0
    }
  } catch (error) {
    ElMessage.error("网络请求失败")
  } finally {
    loading.value = false
  }
}

// 前端搜索过滤（仅对已加载的数据进行标题搜索）
const filteredVulns = computed(() => {
  if (!searchKeyword.value) return dailyVulns.value
  const keyword = searchKeyword.value.toLowerCase()
  return dailyVulns.value.filter(vuln =>
      vuln.title.toLowerCase().includes(keyword)
  )
})

// 统计卡片数据（直接使用后端返回的 stats，不再前端计算）
const dailyStats = computed(() => ({
  total: stats.value.totalVulns,
  new: newVulns.value,
  critical: stats.value.critical,
  high: stats.value.high
}))

// 辅助函数
const getSeverityType = (severity: string) => {
  const map: Record<string, string> = {
    critical: 'danger', high: 'warning', medium: 'primary', low: 'info'
  }
  return map[severity] || 'info'
}

const getSeverityLabel = (severity: string) => {
  const map: Record<string, string> = {
    critical: '严重', high: '高危', medium: '中危', low: '低危'
  }
  return map[severity] || severity
}

const getTypeLabel = (type: string) => type



// 切换仓库
const handleRepoChange = (repo: Repository) => {
  currentRepo.value = repo
  currentPage.value = 1          // 重置分页
  loadData()
}

// 监听筛选条件变化（重新加载，重置页码）
watch([selectedDate, severityFilter, typeFilter], () => {
  currentPage.value = 1
  loadData()
})

// 监听分页变化
watch(currentPage, () => {
  loadData()
})

// 跳转到仓库管理页面
const goToRepoManagement = () => {
  router.push('/repositories')
}

// 初始化
onMounted(() => {
  if (repositories.value.length) {
    currentRepo.value = getDefaultRepo()
    if (currentRepo.value) loadData()
  }
})
</script>

<template>
  <SidebarLayout :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo ? currentRepo.name + ' - 每日漏洞更新' : '每日漏洞更新' }}
    </template>

    <!-- 无仓库时的空状态 -->
    <div v-if="!currentRepo" class="empty-state">
      <el-empty description="暂无仓库数据">
        <template #image>
          <el-icon :size="80" color="#c0c4cc"><Calendar /></el-icon>
        </template>
        <el-button type="primary" @click="goToRepoManagement">前往添加仓库</el-button>
      </el-empty>
    </div>

    <div v-else class="daily-vuln-update" v-loading="loading">
      <!-- 日期选择和操作区 -->
      <el-card class="filter-card" shadow="never">
        <div class="filter-content">
          <div class="date-selector">
            <span class="filter-label">选择日期：</span>
            <el-date-picker
                v-model="selectedDate"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                size="large"
            />
          </div>
        </div>
      </el-card>

      <!-- 统计概览 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <el-icon class="stat-icon primary"><Document /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ dailyStats.total }}</div>
                <div class="stat-label">今日漏洞总数</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <el-icon class="stat-icon success"><CirclePlus /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ dailyStats.new }}</div>
                <div class="stat-label">本仓库新增漏洞</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <el-icon class="stat-icon danger"><Warning /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ dailyStats.critical }}</div>
                <div class="stat-label">严重漏洞</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-content">
              <el-icon class="stat-icon warning"><WarningFilled /></el-icon>
              <div class="stat-info">
                <div class="stat-value">{{ dailyStats.high }}</div>
                <div class="stat-label">高危漏洞</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 筛选条件 -->
      <el-card class="filter-detail-card" shadow="never">
        <div class="filter-row">
          <div class="filter-item">
            <span class="filter-label">搜索：</span>
            <el-input
                v-model="searchKeyword"
                placeholder="搜索CVE ID、漏洞标题或组件名称"
                clearable
                prefix-icon="Search"
                style="width: 300px"
            />
          </div>
          <div class="filter-item">
            <span class="filter-label">严重程度：</span>
            <el-checkbox-group v-model="severityFilter">
              <el-checkbox-button
                  v-for="opt in severityOptions"
                  :key="opt.value"
                  :label="opt.value"
              >
                <span :style="{ color: opt.color }">{{ opt.label }}</span>
              </el-checkbox-button>
            </el-checkbox-group>
          </div>
          <div class="filter-item">
            <span class="filter-label">漏洞类型：</span>
            <el-select
                v-model="typeFilter"
                multiple
                collapse-tags
                placeholder="选择漏洞类型"
                style="width: 300px"
            >
              <el-option
                  v-for="opt in typeOptions"
                  :key="opt"
                  :label="opt"
                  :value="opt"
              />
            </el-select>
          </div>
        </div>
      </el-card>

      <!-- 漏洞列表 -->
      <el-card class="vuln-list-card" shadow="never">
        <template #header>
          <div class="list-header">
            <span class="list-title">
              {{ selectedDate }} 漏洞更新列表
              <el-tag type="primary" size="small" style="margin-left: 8px;">
                共 {{ total }} 条
              </el-tag>
            </span>
          </div>
        </template>

        <div v-if="filteredVulns.length === 0" class="empty-state">
          <el-empty description="该日期暂无漏洞更新" />
        </div>

        <div v-else class="vuln-list">
          <div v-for="vuln in filteredVulns" :key="vuln.id" class="vuln-item">
            <div class="vuln-header">
              <div class="vuln-id-section">
                <el-link type="primary" :underline="false" class="vuln-id">
                  {{ vuln.id }}
                </el-link>
                <el-tag :type="getSeverityType(vuln.severity)" effect="dark">
                  {{ getSeverityLabel(vuln.severity) }}
                </el-tag>
              </div>
            </div>
            <h3 class="vuln-title">{{ vuln.title }}</h3>
            <p class="vuln-desc">{{ vuln.summary }}</p>
            <div class="vuln-meta">
              <div class="meta-item">
                <el-icon><Box /></el-icon>
                <span>影响组件：<el-tag size="small">{{ vuln.affected_subsystem }}</el-tag></span>
              </div>
              <div class="meta-item">
                <el-icon><Timer /></el-icon>
                <span>更新时间：{{ vuln.analyzed_at }}</span>
              </div>
            </div>
            <div class="vuln-footer">
              <div class="vuln-tags">
                <el-tag size="small" type="info">{{ getTypeLabel(vuln.vulnerability_type) }}</el-tag>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
              background
              layout="prev, pager, next, jumper, ->, total"
              :total="total"
              :page-size="pageSize"
              :current-page="currentPage"
              @current-change="(val) => currentPage = val"
              class="pagination"
          />
        </div>
      </el-card>
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
</style>


<style scoped>
.daily-vuln-update {
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

.date-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-weight: 500;
  color: #606266;
}

.filter-actions {
  display: flex;
  gap: 12px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
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
  transform: translateY(-6px) scale(1.02);
  box-shadow: 
    0 16px 40px rgba(102, 126, 234, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 40px;
  padding: 14px;
  border-radius: 16px;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-icon.primary {
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.stat-icon.success {
  background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
  color: #1dd1a1;
  box-shadow: 0 4px 12px rgba(29, 209, 161, 0.2);
}

.stat-icon.danger {
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  color: #ff416c;
  box-shadow: 0 4px 12px rgba(255, 65, 108, 0.2);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #fdf6ec 0%, #fce6d4 100%);
  color: #ff9f43;
  box-shadow: 0 4px 12px rgba(255, 159, 67, 0.2);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  background: linear-gradient(135deg, #1a1f3c 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.filter-detail-card {
  margin-bottom: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.filter-row {
  display: flex;
  gap: 40px;
  margin-bottom: 16px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 30px;
}

.vuln-list-card {
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  overflow: hidden;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #1a1f3c 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.empty-state {
  padding: 60px 0;
}

.vuln-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.vuln-item {
  padding: 20px;
  border: 1px solid rgba(102, 126, 234, 0.1);
  border-radius: 16px;
  background: #fff;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.vuln-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.vuln-item:hover {
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateX(4px);
}

.vuln-item:hover::before {
  opacity: 1;
}

.vuln-item.is-new {
  border-left: 4px solid #ff416c;
  background: linear-gradient(135deg, #fff 0%, #fff5f5 100%);
}

.vuln-item.is-new::before {
  display: none;
}

.vuln-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.vuln-id-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vuln-id {
  font-family: monospace;
  font-size: 14px;
  font-weight: 600;
}

.vuln-score {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.score-label {
  font-size: 12px;
  color: #909399;
}

.score-value {
  font-size: 16px;
  font-weight: 700;
}

.score-value.danger {
  color: #f56c6c;
}

.score-value.warning {
  color: #e6a23c;
}

.score-value.primary {
  color: #409eff;
}

.score-value.info {
  color: #909399;
}

.vuln-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.vuln-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin: 0 0 16px 0;
}

.vuln-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #606266;
}

.meta-item .el-icon {
  color: #909399;
}

.meta-item code {
  font-family: monospace;
  padding: 2px 6px;
  background: #fff;
  border-radius: 3px;
  border: 1px solid #dcdfe6;
  font-size: 12px;
}

.meta-item code.fixed-version {
  color: #67c23a;
  border-color: #67c23a;
}

.vuln-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.vuln-tags {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}
</style>
