<script setup>
import { ref, computed } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'
import {ArrowRight, Clock, Download, Refresh, Setting, Timer} from "@element-plus/icons-vue";

// 当前选中的仓库
const currentRepo = ref({
  id: 1,
  name: 'vuejs/vue',
  description: 'Vue.js 框架'
})

// 处理仓库切换
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

// 趋势图表数据
const trendData = ref([
  { date: '01-10', count: 3 },
  { date: '01-11', count: 5 },
  { date: '01-12', count: 2 },
  { date: '01-13', count: 7 },
  { date: '01-14', count: 4 },
  { date: '01-15', count: 6 },
  { date: '01-16', count: 3 }
])

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
  {
    id: 'CVE-2024-5678',
    title: 'Pinia 状态管理器 XSS 漏洞',
    severity: 'medium',
    package: 'pinia',
    version: '< 2.1.0',
    fixedVersion: '2.1.7',
    publishedAt: '2024-01-14',
    status: 'fixed'
  },
  {
    id: 'CVE-2024-9012',
    title: 'Axios 请求拦截器认证绕过',
    severity: 'critical',
    package: 'axios',
    version: '< 1.6.0',
    fixedVersion: '1.6.2',
    publishedAt: '2024-01-13',
    status: 'unfixed'
  }
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

// 获取严重等级标签
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
  <SidebarLayout :current-repo="currentRepo" @select-repo="handleRepoChange">
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
        <el-col :span="4">
          <el-card class="stat-card resolved" shadow="hover">
            <div class="stat-value">{{ stats.resolved }}</div>
            <div class="stat-label">已修复</div>
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
              <p class="repo-desc">{{ currentRepo.description }}</p>
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
            <span>最后扫描: 2024-01-15 10:30:00</span>
          </div>
          <div class="meta-item">
            <el-icon><Clock /></el-icon>
            <span>下次扫描: 2024-01-16 10:30:00</span>
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
            <el-button type="primary" text>
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
          <el-table-column label="CVE ID" width="130">
            <template #default="{ row }">
              <el-link type="primary" :underline="false">{{ row.id }}</el-link>
            </template>
          </el-table-column>

          <el-table-column label="漏洞标题" min-width="250">
            <template #default="{ row }">
              <span class="vuln-title">{{ row.title }}</span>
            </template>
          </el-table-column>

          <el-table-column label="影响组件" width="150">
            <template #default="{ row }">
              <el-tag size="small">{{ row.package }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="影响版本" width="150">
            <template #default="{ row }">
              <span class="version-text">{{ row.version }}</span>
            </template>
          </el-table-column>

          <el-table-column label="严重等级" width="100">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" effect="dark">
                {{ getSeverityLabel(row.severity) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="修复版本" width="120">
            <template #default="{ row }">
              <span class="version-text fixed">{{ row.fixedVersion }}</span>
            </template>
          </el-table-column>

          <el-table-column label="发布时间" width="120">
            <template #default="{ row }">
              <span class="date-text">{{ row.publishedAt }}</span>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'fixed' ? 'success' : 'danger'" size="small">
                {{ row.status === 'fixed' ? '已修复' : '待修复' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small">
                详情
              </el-button>
              <el-button type="success" link size="small" :disabled="row.status === 'fixed'">
                标记修复
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </SidebarLayout>
</template>

<style scoped>

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
