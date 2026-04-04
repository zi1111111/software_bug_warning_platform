<script setup>
import { ref, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {CircleCheck, Collection, Plus, Timer, Warning} from "@element-plus/icons-vue";
const dialogVisible = ref(false)
const isEditing = ref(false)
const currentRepo = ref(null)


// 表单数据
const form = reactive({
  name: '',
  url: '',
  description: '',
  webhook_url: '',
  notify_email: '',
  auto_scan: true,
  scan_frequency: 'daily'
})

// 搜索关键词
const searchQuery = ref('')

// 仓库列表
const repositories = ref([
  {
    id: 1,
    name: 'vuejs/vue',
    url: 'https://github.com/vuejs/vue',
    description: 'Vue.js 是一个用于构建用户界面的渐进式框架',
    status: 'active',
    last_scan: '2024-01-15 10:30:00',
    vuln_count: 2,
    webhook_url: '',
    notify_email: 'admin@example.com',
    auto_scan: true,
    scan_frequency: 'daily'
  },
  {
    id: 2,
    name: 'facebook/react',
    url: 'https://github.com/facebook/react',
    description: '用于构建用户界面的 JavaScript 库',
    status: 'active',
    last_scan: '2024-01-14 15:20:00',
    vuln_count: 5,
    webhook_url: '',
    notify_email: 'admin@example.com',
    auto_scan: true,
    scan_frequency: 'weekly'
  },
  {
    id: 3,
    name: 'angular/angular',
    url: 'https://github.com/angular/angular',
    description: '现代 Web 开发平台',
    status: 'inactive',
    last_scan: '2024-01-10 09:00:00',
    vuln_count: 0,
    webhook_url: '',
    notify_email: '',
    auto_scan: false,
    scan_frequency: 'manual'
  }
])

// 过滤后的仓库列表
const filteredRepos = computed(() => {
  if (!searchQuery.value) return repositories.value
  const query = searchQuery.value.toLowerCase()
  return repositories.value.filter(repo =>
    repo.name.toLowerCase().includes(query) ||
    repo.description.toLowerCase().includes(query)
  )
})

// 打开添加对话框
const openAddDialog = () => {
  isEditing.value = false
  resetForm()
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (repo) => {
  isEditing.value = true
  currentRepo.value = repo
  Object.assign(form, repo)
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  form.name = ''
  form.url = ''
  form.description = ''
  form.webhook_url = ''
  form.notify_email = ''
  form.auto_scan = true
  form.scan_frequency = 'daily'
  currentRepo.value = null
}

// 保存仓库
const saveRepo = () => {
  if (isEditing.value) {
    // 更新现有仓库
    const index = repositories.value.findIndex(r => r.id === currentRepo.value.id)
    if (index !== -1) {
      repositories.value[index] = { ...repositories.value[index], ...form }
    }
    ElMessage.success('仓库更新成功')
  } else {
    // 添加新仓库
    const newRepo = {
      id: Date.now(),
      ...form,
      status: 'active',
      last_scan: '-',
      vuln_count: 0
    }
    repositories.value.push(newRepo)
    ElMessage.success('仓库添加成功')
  }
  dialogVisible.value = false
  resetForm()
}

// 删除仓库
const deleteRepo = (repo) => {
  ElMessageBox.confirm(
    `确定要删除仓库 "${repo.name}" 吗？此操作不可恢复。`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    const index = repositories.value.findIndex(r => r.id === repo.id)
    if (index !== -1) {
      repositories.value.splice(index, 1)
    }
    ElMessage.success('仓库删除成功')
  })
}

// 切换仓库状态
const toggleStatus = (repo) => {
  repo.status = repo.status === 'active' ? 'inactive' : 'active'
  ElMessage.success(`仓库已${repo.status === 'active' ? '启用' : '禁用'}`)
}

// 手动扫描
const manualScan = (repo) => {
  ElMessage.info(`正在扫描仓库: ${repo.name}`)
  // 模拟扫描过程
  setTimeout(() => {
    repo.last_scan = new Date().toLocaleString()
    ElMessage.success('扫描完成')
  }, 2000)
}

// 查看漏洞详情
const viewVulns = (repo) => {
  // 跳转到漏洞预警页面，并传入仓库ID
  // router.push(`/warnings?repo=${repo.id}`)
}
</script>

<template>
  <div class="repo-management">
    <!-- 页面标题和操作区 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="title">仓库管理</h1>
        <p class="subtitle">管理您的代码仓库，配置自动扫描和预警设置</p>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchQuery"
          placeholder="搜索仓库..."
          prefix-icon="Search"
          clearable
          class="search-input"
          style="width: 240px; margin-right: 16px;"
        />
        <el-button type="primary" @click="openAddDialog">
          <el-icon><Plus /></el-icon>
          添加仓库
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon blue">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ repositories.length }}</div>
              <div class="stat-label">总仓库数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon green">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ repositories.filter(r => r.status === 'active').length }}</div>
              <div class="stat-label">活跃仓库</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon red">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ repositories.reduce((sum, r) => sum + r.vuln_count, 0) }}</div>
              <div class="stat-label">漏洞总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon orange">
              <el-icon><Timer /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ repositories.filter(r => r.auto_scan).length }}</div>
              <div class="stat-label">自动扫描</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 仓库列表 -->
    <el-card class="repo-table-card" shadow="never">
      <el-table
        :data="filteredRepos"
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column type="index" width="50" />
        
        <el-table-column label="仓库信息" min-width="280">
          <template #default="{ row }">
            <div class="repo-info-cell">
              <el-avatar :size="40" :icon="Collection" class="repo-avatar" />
              <div class="repo-meta">
                <div class="repo-name">{{ row.name }}</div>
                <div class="repo-desc">{{ row.description }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="扫描设置" width="150">
          <template #default="{ row }">
            <div class="scan-settings">
              <el-tag v-if="row.auto_scan" type="primary" size="small">
                {{ row.scan_frequency === 'daily' ? '每天' : row.scan_frequency === 'weekly' ? '每周' : '每月' }}
              </el-tag>
              <el-tag v-else type="info" size="small">手动</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="漏洞" width="100">
          <template #default="{ row }">
            <el-badge
              :value="row.vuln_count"
              :type="row.vuln_count > 0 ? 'danger' : 'success'">
              <el-button
                type="text"
                :disabled="row.vuln_count === 0"
                @click="viewVulns(row)"
              >
                查看
              </el-button>
            </el-badge>
          </template>
        </el-table-column>

        <el-table-column label="最后扫描" width="160">
          <template #default="{ row }">
            <span class="last-scan">{{ row.last_scan }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" size="small" @click="openEditDialog(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button
                :type="row.status === 'active' ? 'warning' : 'success'"
                size="small"
                @click="toggleStatus(row)"
              >
                <el-icon><component :is="row.status === 'active' ? 'CircleClose' : 'CircleCheck'" /></el-icon>
              </el-button>
              <el-button type="info" size="small" @click="manualScan(row)">
                <el-icon><Refresh /></el-icon>
              </el-button>
              <el-button type="danger" size="small" @click="deleteRepo(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加/编辑仓库对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑仓库' : '添加仓库'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="form" label-width="120px" class="repo-form">
        <el-form-item label="仓库名称" required>
          <el-input v-model="form.name" placeholder="例如: vuejs/vue" />
        </el-form-item>

        <el-form-item label="仓库地址" required>
          <el-input v-model="form.url" placeholder="https://github.com/owner/repo" />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="仓库描述信息"
          />
        </el-form-item>

        <el-divider content-position="left">预警设置</el-divider>

        <el-form-item label="通知邮箱">
          <el-input v-model="form.notify_email" placeholder="接收漏洞预警的邮箱地址" />
        </el-form-item>

        <el-form-item label="Webhook URL">
          <el-input v-model="form.webhook_url" placeholder="接收通知的 Webhook 地址" />
        </el-form-item>

        <el-form-item label="自动扫描">
          <el-switch v-model="form.auto_scan" />
        </el-form-item>

        <el-form-item v-if="form.auto_scan" label="扫描频率">
          <el-select v-model="form.scan_frequency" style="width: 100%;">
            <el-option label="每天" value="daily" />
            <el-option label="每周" value="weekly" />
            <el-option label="每月" value="monthly" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRepo">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.repo-management {
  padding: 0;
  min-height: 100vh;
  background: #f5f7fa;   /* 与主界面背景一致 */
  width: 100%;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left .title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #1a237e;
}

.header-left .subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
}

.stat-icon.blue {
  background: #ecf5ff;
  color: #409eff;
}

.stat-icon.green {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-icon.red {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-icon.orange {
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
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.repo-table-card {
  border-radius: 8px;
}

.repo-info-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.repo-avatar {
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
}

.repo-meta {
  flex: 1;
}

.repo-name {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}

.repo-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.scan-settings {
  display: flex;
  align-items: center;
}

.last-scan {
  font-size: 13px;
  color: #606266;
}

.repo-form {
  padding: 20px 0;
}
</style>
