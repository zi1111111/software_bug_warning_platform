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

// 时间范围选择
const timeRange = ref('7d')
const timeRangeOptions = [
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' },
  { label: '最近90天', value: '90d' },
  { label: '今年', value: 'year' }
]

// 模拟趋势数据
const trendData = ref({
  '7d': {
    dates: ['01-01', '01-02', '01-03', '01-04', '01-05', '01-06', '01-07'],
    newVulns: [3, 5, 2, 7, 4, 6, 3],
    fixedVulns: [1, 2, 3, 1, 4, 2, 5],
    totalVulns: [12, 15, 14, 20, 20, 24, 22]
  },
  '30d': {
    dates: ['第1周', '第2周', '第3周', '第4周'],
    newVulns: [15, 22, 18, 25],
    fixedVulns: [8, 12, 15, 18],
    totalVulns: [45, 55, 58, 65]
  },
  '90d': {
    dates: ['1月', '2月', '3月'],
    newVulns: [80, 65, 90],
    fixedVulns: [45, 55, 70],
    totalVulns: [150, 160, 180]
  },
  'year': {
    dates: ['Q1', 'Q2', 'Q3', 'Q4'],
    newVulns: [235, 180, 220, 195],
    fixedVulns: [170, 160, 190, 210],
    totalVulns: [450, 470, 500, 485]
  }
})

// 严重等级分布数据
const severityDistribution = ref([
  { value: 15, name: '严重' },
  { value: 35, name: '高危' },
  { value: 50, name: '中危' },
  { value: 30, name: '低危' }
])

// 组件漏洞排行
const componentRanking = ref([
  { name: 'lodash', vulnCount: 12, severity: 'high' },
  { name: 'axios', vulnCount: 8, severity: 'critical' },
  { name: 'express', vulnCount: 6, severity: 'medium' },
  { name: 'webpack', vulnCount: 5, severity: 'low' },
  { name: 'babel-core', vulnCount: 4, severity: 'medium' }
])

// 漏洞类型分布
const vulnTypeDistribution = ref([
  { value: 45, name: 'XSS攻击' },
  { value: 32, name: 'SQL注入' },
  { value: 28, name: '路径遍历' },
  { value: 20, name: '权限绕过' },
  { value: 15, name: '信息泄露' },
  { value: 10, name: '其他' }
])

// 计算当前数据
const currentData = computed(() => trendData.value[timeRange.value])

// 获取图表颜色
const chartColors = ['#f56c6c', '#e6a23c', '#409eff', '#67c23a']

// 严重等级颜色映射
const getSeverityColor = (severity) => {
  const map = {
    critical: '#f56c6c',
    high: '#e6a23c',
    medium: '#409eff',
    low: '#67c23a'
  }
  return map[severity] || '#909399'
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
  <SidebarLayout :current-repo="currentRepo" @select-repo="handleRepoChange">
    <template #title>
      {{ currentRepo.name }} - 趋势分析
    </template>

    <div class="trend-analysis">
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
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-header">
              <el-icon class="stat-icon red"><TrendCharts /></el-icon>
              <span class="stat-trend up">+15%</span>
            </div>
            <div class="stat-value">{{ currentData.newVulns.reduce((a, b) => a + b, 0) }}</div>
            <div class="stat-label">新增漏洞</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-header">
              <el-icon class="stat-icon green"><CircleCheck /></el-icon>
              <span class="stat-trend up">+22%</span>
            </div>
            <div class="stat-value">{{ currentData.fixedVulns.reduce((a, b) => a + b, 0) }}</div>
            <div class="stat-label">已修复漏洞</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-header">
              <el-icon class="stat-icon blue"><Warning /></el-icon>
              <span class="stat-trend down">-5%</span>
            </div>
            <div class="stat-value">{{ currentData.totalVulns[currentData.totalVulns.length - 1] }}</div>
            <div class="stat-label">现存漏洞</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-header">
              <el-icon class="stat-icon orange"><Timer /></el-icon>
              <span class="stat-trend">--</span>
            </div>
            <div class="stat-value">{{ Math.round(currentData.fixedVulns.reduce((a, b) => a + b, 0) / currentData.newVulns.reduce((a, b) => a + b, 0) * 100) }}%</div>
            <div class="stat-label">修复率</div>
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
              <span class="legend-item">
                <span class="legend-dot" style="background: #67c23a;"></span>
                已修复
              </span>
              <span class="legend-item">
                <span class="legend-dot" style="background: #409eff;"></span>
                现存总数
              </span>
            </div>
          </div>
        </template>
        
        <!-- 简单的柱状图展示 -->
        <div class="trend-chart">
          <div class="chart-y-axis">
            <div v-for="i in 5" :key="i" class="y-axis-label">
              {{ Math.max(...currentData.totalVulns) - (i - 1) * Math.ceil(Math.max(...currentData.totalVulns) / 4) }}
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
                    height: (currentData.newVulns[index] / Math.max(...currentData.totalVulns) * 200) + 'px' 
                  }"
                >
                  <el-tooltip :content="`新增: ${currentData.newVulns[index]}`" placement="top">
                    <div class="bar-inner"></div>
                  </el-tooltip>
                </div>
                <div 
                  class="bar fixed"
                  :style="{ 
                    height: (currentData.fixedVulns[index] / Math.max(...currentData.totalVulns) * 200) + 'px' 
                  }"
                >
                  <el-tooltip :content="`修复: ${currentData.fixedVulns[index]}`" placement="top">
                    <div class="bar-inner"></div>
                  </el-tooltip>
                </div>
                <div 
                  class="bar total"
                  :style="{ 
                    height: (currentData.totalVulns[index] / Math.max(...currentData.totalVulns) * 200) + 'px' 
                  }"
                >
                  <el-tooltip :content="`总数: ${currentData.totalVulns[index]}`" placement="top">
                    <div class="bar-inner"></div>
                  </el-tooltip>
                </div>
              </div>
              <div class="x-axis-label">{{ date }}</div>
            </div>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20" class="bottom-row">
        <!-- 严重等级分布 -->
        <el-col :span="8">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">严重等级分布</span>
            </template>
            <div class="distribution-chart">
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
                        background: chartColors[index]
                      }"
                    ></div>
                  </div>
                  <span class="distribution-value">{{ item.value }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 组件漏洞排行 -->
        <el-col :span="8">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">组件漏洞排行</span>
            </template>
            <div class="ranking-list">
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
                <div class="ranking-count">{{ item.vulnCount }}</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 漏洞类型分布 -->
        <el-col :span="8">
          <el-card class="chart-card" shadow="hover">
            <template #header>
              <span class="card-title">漏洞类型分布</span>
            </template>
            <div class="type-distribution">
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

.bar.fixed .bar-inner {
  background: #67c23a;
}

.bar.total .bar-inner {
  background: #409eff;
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
