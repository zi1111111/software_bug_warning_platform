<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
import { ArrowRight, Clock, Download, Refresh, Setting, Timer, Collection } from "@element-plus/icons-vue"
import { storeToRefs } from "pinia"
import { useRepoStore } from "../stores/repository"

const repoTS = useRepoStore()
const { repositories } = storeToRefs(repoTS)

// 当前选中的仓库 - 初始化为 null
const currentRepo = ref<any>(null)

// 获取默认仓库：优先取 is_active 为 true 的第一个，否则取 repositories 第一个
const getDefaultRepo = () => {
  const repos = repositories.value
  if (!repos.length) return null
  const activeRepo = repos.find(r => r.is_active === true)
  return activeRepo || repos[0]
}

// 监听 repositories 变化，自动设置默认仓库
watch(repositories, (newRepos) => {
  if (newRepos.length && !currentRepo.value) {
    currentRepo.value = getDefaultRepo()
  }
}, { immediate: true })

// 组件挂载时若已有数据则设置
onMounted(() => {
  if (!currentRepo.value && repositories.value.length) {
    currentRepo.value = getDefaultRepo()
  }
})

// 处理仓库切换（来自 SidebarLayout）
const handleRepoChange = (repo) => {
  currentRepo.value = repo
}

// 统计数据
const stats = ref({
  totalVulns: 12,
  critical: 2,
  high: 4,
  medium: 3,
  low: 3,
  resolved: 8,
  pending: 4
})



// 最新漏洞列表
const recentVulns = ref([
  {
    id: 'CVE-2024-1234',
    title: 'Vue Router 路径遍历漏洞',
    severity: 'high',
    package: 'vue-router',
    version: '< 4.2.0',
    fixedVersion: '4.2.5',
    publishedAt: '2024-01-15',
    status: 'unfixed'
  },
])

// 获取严重等级样式
const getSeverityType = (severity) => {
  const map = {
    critical: 'danger',
    high: 'warning',
    medium: 'primary',
    low: 'info'
  }
  return map[severity] || 'info'
}

const getSeverityLabel = (severity) => {
  const map = {
    critical: '严重',
    high: '高危',
    medium: '中危',
    low: '低危'
  }
  return map[severity] || severity
}
</script>

<template>
  <!-- 只有当 currentRepo 存在时才渲染，避免报错 -->
  <SidebarLayout v-if="currentRepo" :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo.name }} - 漏洞预警
    </template>

    <div class="dashboard">
      <!-- 统计卡片（只保留5个，避免溢出） -->
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
              <!-- 如果没有 description，显示 repo_url 或默认文本 -->
              <p class="repo-desc">{{ currentRepo.repo_url || '暂无描述' }}</p>
            </div>
          </div>
          <div class="repo-actions">
            <el-button type="primary">
              <el-icon><Refresh /></el-icon>
              立即扫描
            </el-button>
            <el-button>
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
            <span class="card-title">最新漏洞</span>
            <el-button type="primary" link>  <!-- 修改 link -->
              查看全部
              <el-icon class="el-icon--right"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </template>

        <el-table
            :data="recentVulns"
            style="width: 100%"
            :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
        >
          <!-- 表格列保持不变 -->
        </el-table>
      </el-card>
    </div>
  </SidebarLayout>
  <!-- 如果 currentRepo 为 null，显示加载中 -->
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
body{
  display: flex;
  justify-content: center;    /* 水平居中 */
  align-items: center;        /* 垂直居中 */
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

.stat-card.resolved {
  background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%);
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

.vuln-title {
  font-weight: 500;
  color: #303133;
}

.version-text {
  font-family: monospace;
  font-size: 12px;
  color: #606266;
}

.version-text.fixed {
  color: #67c23a;
}

.date-text {
  font-size: 13px;
  color: #909399;
}
</style>