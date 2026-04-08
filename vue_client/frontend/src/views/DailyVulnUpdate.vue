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

// 仓库相关
const repoTS = useRepoStore()
const currentRepo = ref<Repository | null>(null)
const { repositories } = storeToRefs(repoTS)

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

// 初始化
onMounted(() => {
  if (repositories.value.length) {
    currentRepo.value = getDefaultRepo()
    if (currentRepo.value) loadData()
  }
})
</script>

<template>
  <SidebarLayout v-if="currentRepo" :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo.name }} - 每日漏洞更新
    </template>

    <div class="daily-vuln-update" v-loading="loading">
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
                <div class="stat-label">新增漏洞</div>
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
  border-radius: 8px;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 40px;
  padding: 12px;
  border-radius: 12px;
}

.stat-icon.primary {
  background: #ecf5ff;
  color: #409eff;
}

.stat-icon.success {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-icon.danger {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-icon.warning {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.filter-detail-card {
  margin-bottom: 20px;
  border-radius: 8px;
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
  border-radius: 8px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
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
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  transition: all 0.3s ease;
}

.vuln-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.vuln-item.is-new {
  border-left: 4px solid #f56c6c;
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
