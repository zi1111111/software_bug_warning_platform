<script setup lang = "ts">
import {ref, reactive, computed} from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {CircleCheck, Collection, Delete, Edit, House, Plus, Refresh, Timer, Warning} from "@element-plus/icons-vue";
import {useRepoStore} from "../stores/repository";
import {Repository} from "../response/response";
import {storeToRefs} from "pinia";
import {http} from "../request/request";
import { useRouter } from 'vue-router'
import SidebarLayout from "../components/SidebarLayout.vue";   // 新增

const router = useRouter()
const dialogVisible = ref(false)
const isEditing = ref(false)
const currentRepo = ref<Repository>(null)
//repoTS调用
const repoTS = useRepoStore()

//仓库列表
const { repositories } = storeToRefs(repoTS)


// 表单数据
const form = reactive({
  name: "",
  repo_url: "",
  default_branch: "",
  is_active: true,
})
// 搜索关键词
const searchQuery = ref('')

// 过滤后的仓库列表
const filteredRepos = computed(() => {
  if (!searchQuery.value) return repositories.value
  const query = searchQuery.value.toLowerCase()
  return repositories.value.filter(repo =>
    repo.name.toLowerCase().includes(query)
  )
})

//最近时间
const latestScanTime = computed(() => {
  const times = repositories.value
      .map(repo => repo.last_fetched_at)
      .filter(time => time) // 过滤掉 null/undefined/空字符串
      .sort()
      .reverse(); // 降序排序（最新的在前）

  if (times.length === 0) return '暂无扫描记录';
  return times[0]; // 返回最新的时间字符串
});
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
  form.repo_url = ''
  form.default_branch= ""
  form.is_active= true
  currentRepo.value = null
}

// 保存仓库
const saveRepo = async () => {
  if (isEditing.value) {
    // 更新现有仓库
    const index = repositories.value.findIndex(r => r.id === currentRepo.value.id)
    if (index !== -1) {
      repositories[index] = { ...repositories[index], ...form }
    }
    const res = await repoTS.changeRepository({
      id:currentRepo.value.id,
      default_branch: form.default_branch,
      is_active: form.is_active})
    if(res === true)
      ElMessage.success('仓库更新成功')

    else
      ElMessage.error("仓库更新失败")

  } else {
    const res = await repoTS.addRepository({
      name:form.name,
      repo_url:form.repo_url,
      default_branch:form.default_branch,
      is_active:form.is_active,
    })
    if (res === true) {
      ElMessage.success('仓库添加成功')
    }
    else
      ElMessage.error("仓库添加失败")
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
  ).then(async() => {
    const index = repositories.value.findIndex(r => r.id === repo.id)
    if (index !== -1) {
      const res = await repoTS.deleteRepository({id: repo.id})
      if(res === true) {
        repositories.value.splice(index, 1)
        ElMessage.success('仓库删除成功')
      }
      else
        ElMessage.error("仓库删除失败")
    }
  })
}

// 切换仓库状态
const toggleStatus = async (repo: Repository) => {
  const newStatus = !repo.is_active   // 计算新状态（布尔取反）
  const res = await repoTS.changeRepository({
    id: repo.id,
    default_branch: repo.default_branch,
    is_active: newStatus
  })
  if (res === true) {
    repo.is_active = newStatus   // 请求成功后更新本地状态
    ElMessage.success(`仓库已${newStatus ? '启用' : '禁用'}`)
  } else {
    ElMessage.error('操作失败，请重试')
  }
}

// 手动扫描
const manualScan = async(repo) => {
  ElMessage.info(`正在扫描仓库: ${repo.name}`)
  // 模拟扫描过程
    const res = await http.post("/api/searchCommit",{id:repo.id})
    if(res.code === 200) {
      repo.last_fetched_at = new Date().toLocaleString()
      ElMessage.success('扫描任务已启动，请稍后刷新')
    }
}

// 查看漏洞详情
const viewVulns = (repo: Repository) => {
  router.push({ path: '/dashboard', query: { repoId: repo.id } })
}

// 返回首页
const goToHome = () => {
  router.push('/')   // 替换为你的实际首页路径
}
</script>

<template>
  <SidebarLayout :disableRepoSelection="true"  >
    <template #title>
      仓库管理
    </template>
  <div class="repo-management">
    <!-- 页面标题和操作区 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="title">仓库管理</h1>
        <p class="subtitle">管理您的代码仓库</p>
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
        <el-button @click="goToHome" style="margin-right: 16px;">
          <el-icon><House /></el-icon>
          返回首页
        </el-button>
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
              <div class="stat-value">{{ repositories.filter(r => r.is_active === true).length }}</div>
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
              <div class="stat-value">{{ latestScanTime }}</div>
              <div class="stat-label">上次扫描时间</div>
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
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="150">
          <template #default="{ row }">
            <el-tag :type="row.is_active === true ? false : 'info'">
              {{ row.is_active === true ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="扫描设置" width="150">
          <template #default="{ row }">
            <div class="scan-settings">
              <el-tag type="info" size="small">自动</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="漏洞" width="180" fixed="right">
          <template #default="{ row }">
            <div style=" text-align: start">
              <el-badge
                  :value="row.vuln_count"
                  :type="row.vuln_count > 0 ? 'danger' : 'success'"
                  :offset="[0, 0]"
              >
                <el-button
                    type="text"
                    :disabled="row.vuln_count === 0"
                    @click="viewVulns(row)"
                >
                  查看
                </el-button>
              </el-badge>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="最后扫描" width="180">
          <template #default="{ row }">
            <span class="last-scan">{{ row.last_fetched_at }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" size="small" @click="openEditDialog(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button
                :type="row.is_active === true ? false :'success'"
                size="small"
                @click="toggleStatus(row)"
              >
                <el-icon><component :is="row.is_active === true ?  'CircleClose' : 'CircleCheck'" /></el-icon>
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
          <el-input v-model="form.name" placeholder="例如: vuejs/vue" :readonly ="isEditing"/>
        </el-form-item>

        <el-form-item label="仓库地址" required>
          <el-input v-model="form.repo_url" placeholder="例如:https://github.com/owner/repo" :readonly ="isEditing"/>
        </el-form-item>

        <el-form-item label="分支" required>
          <el-input v-model="form.default_branch" placeholder="例如:master" />
        </el-form-item>

        <el-form-item label="状态" required>
          <el-switch
            v-model="form.is_active"
            active-text="活跃"
            inactive-text="不活跃"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRepo">保存</el-button>
      </template>
    </el-dialog>
  </div>
  </SidebarLayout>
</template>

<style scoped>
:deep(.el-table .el-table__cell) {
  overflow: visible;
}
:deep(.el-table .cell) {
  overflow: visible;
}

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
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #1a1f3c 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header-left .subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
  font-weight: 500;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right .el-button {
  border-radius: 12px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.header-right .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  transition: all 0.4s ease;
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
  transform: translateY(-4px);
  box-shadow: 
    0 12px 30px rgba(102, 126, 234, 0.15),
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
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1) rotate(5deg);
}

.stat-icon.blue {
  background: linear-gradient(135deg, #ecf5ff 0%, #d9ecff 100%);
  color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.stat-icon.green {
  background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
  color: #1dd1a1;
  box-shadow: 0 4px 12px rgba(29, 209, 161, 0.2);
}

.stat-icon.red {
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
  color: #ff416c;
  box-shadow: 0 4px 12px rgba(255, 65, 108, 0.2);
}

.stat-icon.orange {
  background: linear-gradient(135deg, #fdf6ec 0%, #fce6d4 100%);
  color: #ff9f43;
  box-shadow: 0 4px 12px rgba(255, 159, 67, 0.2);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 800;
  background: linear-gradient(135deg, #1a1f3c 0%, #667eea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  font-weight: 500;
}

.repo-table-card {
  border-radius: 20px;
  background: linear-gradient(135deg, #ffffff 0%, #f8f9fc 100%);
  border: 1px solid rgba(102, 126, 234, 0.1);
  box-shadow: 
    0 4px 20px rgba(0, 0, 0, 0.08),
    0 0 0 1px rgba(255, 255, 255, 0.8) inset;
  overflow: hidden;
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
