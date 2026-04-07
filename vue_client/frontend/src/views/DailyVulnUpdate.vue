<script setup>
import { ref, computed } from 'vue'
import SidebarLayout from '../components/SidebarLayout.vue'

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

// 日期选择
const selectedDate = ref(new Date().toISOString().split('T')[0])
const dateShortcuts = [
  {
    text: '今天',
    value: new Date()
  },
  {
    text: '昨天',
    value: () => {
      const date = new Date()
      date.setTime(date.getTime() - 3600 * 1000 * 24)
      return date
    }
  },
  {
    text: '一周前',
    value: () => {
      const date = new Date()
      date.setTime(date.getTime() - 3600 * 1000 * 24 * 7)
      return date
    }
  }
]

// 搜索关键词
const searchKeyword = ref('')

// 严重程度筛选
const severityFilter = ref([])
const severityOptions = [
  { label: '严重', value: 'critical', color: '#f56c6c' },
  { label: '高危', value: 'high', color: '#e6a23c' },
  { label: '中危', value: 'medium', color: '#409eff' },
  { label: '低危', value: 'low', color: '#67c23a' }
]

// 漏洞类型筛选
const typeFilter = ref([])
const typeOptions = [
  { label: 'XSS攻击', value: 'xss' },
  { label: 'SQL注入', value: 'sqli' },
  { label: '路径遍历', value: 'path-traversal' },
  { label: '权限绕过', value: 'auth-bypass' },
  { label: '信息泄露', value: 'info-disclosure' },
  { label: '其他', value: 'other' }
]

// 模拟每日漏洞数据
const dailyVulns = ref([
  {
    id: 'CVE-2024-1234',
    title: 'Vue Router 路径遍历漏洞',
    description: '在特定配置下，攻击者可以通过构造恶意URL访问受限资源',
    severity: 'high',
    type: 'path-traversal',
    package: 'vue-router',
    version: '< 4.2.0',
    fixedVersion: '4.2.5',
    publishedAt: '2024-01-15',
    updatedAt: '2024-01-15 08:30:00',
    references: ['https://example.com/cve-2024-1234'],
    isNew: true,
    cvssScore: 7.5
  },
  {
    id: 'CVE-2024-5678',
    title: 'Pinia 状态管理器 XSS 漏洞',
    description: '存储的数据未经过滤可能导致XSS攻击',
    severity: 'medium',
    type: 'xss',
    package: 'pinia',
    version: '< 2.1.0',
    fixedVersion: '2.1.7',
    publishedAt: '2024-01-15',
    updatedAt: '2024-01-15 09:15:00',
    references: ['https://example.com/cve-2024-5678'],
    isNew: true,
    cvssScore: 6.1
  },
  {
    id: 'CVE-2024-9012',
    title: 'Axios 请求拦截器认证绕过',
    description: '特定条件下可绕过请求拦截器的认证检查',
    severity: 'critical',
    type: 'auth-bypass',
    package: 'axios',
    version: '< 1.6.0',
    fixedVersion: '1.6.2',
    publishedAt: '2024-01-15',
    updatedAt: '2024-01-15 10:45:00',
    references: ['https://example.com/cve-2024-9012'],
    isNew: true,
    cvssScore: 9.1
  },
  {
    id: 'CVE-2024-3456',
    title: 'Webpack 配置信息泄露',
    description: '生产环境可能泄露敏感配置信息',
    severity: 'low',
    type: 'info-disclosure',
    package: 'webpack',
    version: '< 5.88.0',
    fixedVersion: '5.89.0',
    publishedAt: '2024-01-15',
    updatedAt: '2024-01-15 11:20:00',
    references: ['https://example.com/cve-2024-3456'],
    isNew: false,
    cvssScore: 3.7
  },
  {
    id: 'CVE-2024-7890',
    title: 'Lodash 原型污染漏洞',
    description: 'merge 函数存在原型污染风险',
    severity: 'high',
    type: 'other',
    package: 'lodash',
    version: '< 4.17.21',
    fixedVersion: '4.17.21',
    publishedAt: '2024-01-15',
    updatedAt: '2024-01-15 14:00:00',
    references: ['https://example.com/cve-2024-7890'],
    isNew: true,
    cvssScore: 8.2
  }
])

// 过滤后的漏洞列表
const filteredVulns = computed(() => {
  return dailyVulns.value.filter(vuln => {
    // 搜索关键词过滤
    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      const matchTitle = vuln.title.toLowerCase().includes(keyword)
      const matchId = vuln.id.toLowerCase().includes(keyword)
      const matchPackage = vuln.package.toLowerCase().includes(keyword)
      if (!matchTitle && !matchId && !matchPackage) return false
    }
    
    // 严重程度过滤
    if (severityFilter.value.length > 0 && !severityFilter.value.includes(vuln.severity)) {
      return false
    }
    
    // 类型过滤
    if (typeFilter.value.length > 0 && !typeFilter.value.includes(vuln.type)) {
      return false
    }
    
    return true
  })
})

// 统计数据
const dailyStats = computed(() => {
  const newVulns = filteredVulns.value.filter(v => v.isNew)
  return {
    total: filteredVulns.value.length,
    new: newVulns.length,
    critical: filteredVulns.value.filter(v => v.severity === 'critical').length,
    high: filteredVulns.value.filter(v => v.severity === 'high').length
  }
})

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

// 获取漏洞类型标签
const getTypeLabel = (type) => {
  const option = typeOptions.find(o => o.value === type)
  return option ? option.label : type
}

// 查看详情
const viewDetail = (vuln) => {
  // 实现查看详情逻辑
  console.log('查看详情:', vuln)
}

// 导出日报
const exportReport = () => {
  // 实现导出逻辑
  ElMessage.success('日报导出成功')
}

// 订阅日报
const subscribeDaily = () => {
  ElMessage.success('已订阅每日漏洞更新提醒')
}
</script>

<template>
  <SidebarLayout :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo.name }} - 每日漏洞更新
    </template>

    <div class="daily-vuln-update">
      <!-- 日期选择和操作区 -->
      <el-card class="filter-card" shadow="never">
        <div class="filter-content">
          <div class="date-selector">
            <span class="filter-label">选择日期:</span>
            <el-date-picker
              v-model="selectedDate"
              type="date"
              placeholder="选择日期"
              :shortcuts="dateShortcuts"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              size="large"
            />
          </div>
          <div class="filter-actions">
            <el-button type="primary" @click="exportReport">
              <el-icon><Download /></el-icon>
              导出日报
            </el-button>
            <el-button @click="subscribeDaily">
              <el-icon><Bell /></el-icon>
              订阅更新
            </el-button>
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
            <span class="filter-label">搜索:</span>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索CVE ID、漏洞标题或组件名称"
              clearable
              prefix-icon="Search"
              style="width: 300px"
            />
          </div>
          <div class="filter-item">
            <span class="filter-label">严重程度:</span>
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
        </div>
        <div class="filter-row">
          <div class="filter-item">
            <span class="filter-label">漏洞类型:</span>
            <el-select
              v-model="typeFilter"
              multiple
              collapse-tags
              placeholder="选择漏洞类型"
              style="width: 300px"
            >
              <el-option
                v-for="opt in typeOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
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
                共 {{ filteredVulns.length }} 条
              </el-tag>
            </span>
          </div>
        </template>

        <div v-if="filteredVulns.length === 0" class="empty-state">
          <el-empty description="该日期暂无漏洞更新" />
        </div>

        <div v-else class="vuln-list">
          <div
            v-for="vuln in filteredVulns"
            :key="vuln.id"
            class="vuln-item"
            :class="{ 'is-new': vuln.isNew }"
          >
            <div class="vuln-header">
              <div class="vuln-id-section">
                <el-link type="primary" :underline="false" class="vuln-id">
                  {{ vuln.id }}
                </el-link>
                <el-tag v-if="vuln.isNew" type="danger" size="small" effect="dark">
                  NEW
                </el-tag>
                <el-tag :type="getSeverityType(vuln.severity)" effect="dark">
                  {{ getSeverityLabel(vuln.severity) }}
                </el-tag>
              </div>
              <div class="vuln-score">
                <span class="score-label">CVSS</span>
                <span class="score-value" :class="getSeverityType(vuln.severity)">
                  {{ vuln.cvssScore }}
                </span>
              </div>
            </div>

            <h3 class="vuln-title">{{ vuln.title }}</h3>
            <p class="vuln-desc">{{ vuln.description }}</p>

            <div class="vuln-meta">
              <div class="meta-item">
                <el-icon><Box /></el-icon>
                <span>影响组件: <el-tag size="small">{{ vuln.package }}</el-tag></span>
              </div>
              <div class="meta-item">
                <el-icon><Warning /></el-icon>
                <span>影响版本: <code>{{ vuln.version }}</code></span>
              </div>
              <div class="meta-item">
                <el-icon><CircleCheck /></el-icon>
                <span>修复版本: <code class="fixed-version">{{ vuln.fixedVersion }}</code></span>
              </div>
              <div class="meta-item">
                <el-icon><Timer /></el-icon>
                <span>更新时间: {{ vuln.updatedAt }}</span>
              </div>
            </div>

            <div class="vuln-footer">
              <div class="vuln-tags">
                <el-tag size="small" type="info">{{ getTypeLabel(vuln.type) }}</el-tag>
              </div>
              <div class="vuln-actions">
                <el-button type="primary" link @click="viewDetail(vuln)">
                  查看详情
                  <el-icon class="el-icon--right"><ArrowRight /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            background
            layout="prev, pager, next, jumper, ->, total"
            :total="filteredVulns.length"
            :page-size="10"
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
  gap: 12px;
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
