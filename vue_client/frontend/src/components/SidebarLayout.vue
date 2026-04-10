<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {useRoute, useRouter} from 'vue-router'
import {
  ArrowDown,
  Calendar,
  Collection,
  Expand,
  Fold, Link,
  Management,
  Monitor,
  Odometer, Setting,
  TrendCharts,
} from "@element-plus/icons-vue";
import { useRepoStore } from "../stores/repository";
import { useUserStore } from "../stores/user";
import { storeToRefs } from "pinia";
import { UserFilled, SwitchButton } from "@element-plus/icons-vue";

const props = defineProps({
  disableRepoSelection: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select-repo'])

const router = useRouter()
const route = useRoute()// 获取当前路由对象
const isCollapse = ref(false)
const showRepoDrawer = ref(false)
const searchQuery = ref('')   // 新增：抽屉搜索关键词

const repoTS = useRepoStore()
const { repositories } = storeToRefs(repoTS)

const userStore = useUserStore()

// 处理退出登录
const handleLogout = async () => {
  await userStore.logout()
  router.push('/login')
}

// 当前选中的仓库（内部状态）
const selectedRepo = ref<any>(null)

// 获取默认仓库：优先取 is_active 为 true 的第一个，否则取 repositories 第一个
const getDefaultRepo = () => {
  const repos = repositories.value
  if (!repos.length) return null
  const activeRepo = repos.find(r => r.is_active === true)
  return activeRepo || repos[0]
}

// 初始化默认仓库
const initDefaultRepo = () => {
  if (!selectedRepo.value && repositories.value.length) {
    const defaultRepo = getDefaultRepo()
    if (defaultRepo) {
      selectedRepo.value = defaultRepo
      emit('select-repo', defaultRepo)
    }
  }
}

// 监听 repositories 变化，自动设置默认仓库
watch(repositories, () => {
  initDefaultRepo()
}, { immediate: true })

// 组件挂载时初始化
onMounted(() => {
  initDefaultRepo()
})

// 选择仓库（从抽屉中点击）
const selectRepo = (repo: any) => {
  selectedRepo.value = repo
  emit('select-repo', repo)
  showRepoDrawer.value = false
}

// 当前仓库名称（用于显示）
const currentRepoName = computed(() => {
  return selectedRepo.value?.name || '未选择仓库'
})

// 导航菜单选中
// 根据当前路由路径获取对应的菜单索引
const getActiveMenuFromPath = (path: string) => {
  if (path === '/') return 'dashboard'
  if (path.startsWith('/settings')) return 'settings'
  if (path.startsWith('/repositories')) return 'repos'
  if (path.startsWith('/analysis/trend')) return 'analysis-trend'
  if (path.startsWith('/analysis/risk')) return 'analysis-risk'
  if (path.startsWith('/daily-update')) return 'daily-update'
  return 'dashboard'
}

// 当前激活菜单
const activeMenu = ref('dashboard')

// 监听路由变化，更新高亮菜单
watch(() => route.path, (newPath) => {
  activeMenu.value = getActiveMenuFromPath(newPath)
}, { immediate: true })

// 导航菜单点击处理
const handleMenuSelect = (index: string) => {
  activeMenu.value = index
  switch (index) {
    case 'dashboard':
      router.push('/dashboard')
      break
    case 'analysis-trend':
      router.push('/analysis/trend')
      break
    case 'analysis-risk':
      router.push('/analysis/risk')
      break
    case 'daily-update':
      router.push('/daily-update')
      break
    case 'repos':
      router.push('/repositories')
      break
  }
}

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 过滤仓库（用于抽屉搜索）
const filteredRepos = computed(() => {
  if (!searchQuery.value) return repositories.value
  const query = searchQuery.value.toLowerCase()
  return repositories.value.filter(repo => repo.name.toLowerCase().includes(query))
})

const openDrawer = () => {
  if (!props.disableRepoSelection) {
    showRepoDrawer.value = true
  }
}
</script>


<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
      <div class="sidebar-header">
        <el-icon class="logo-icon" :size="28"><Monitor /></el-icon>
        <span v-show="!isCollapse" class="logo-text">漏洞预警平台</span>
        <el-button
            v-show="!isCollapse"
            class="collapse-btn"
            link
            @click="toggleCollapse"
        >
          <el-icon><Fold /></el-icon>
        </el-button>
        <el-button
            v-show="isCollapse"
            class="expand-btn"
            link
            @click="toggleCollapse"
        >
          <el-icon><Expand /></el-icon>
        </el-button>
      </div>

      <!-- 当前仓库选择区 -->
      <template v-if="!disableRepoSelection">
      <div v-show="!isCollapse" class="repo-section">
        <el-card class="repo-card" shadow="hover" @click="showRepoDrawer = true">
          <div class="repo-info">
            <el-icon :size="20" class="repo-icon"><Collection /></el-icon>
            <div class="repo-details">
              <div class="repo-name">{{ currentRepoName }}</div>
              <div class="repo-label">当前仓库</div>
            </div>
            <el-icon class="switch-icon"><ArrowDown /></el-icon>
          </div>
        </el-card>
      </div>

      <div v-show="isCollapse" class="repo-section-collapsed">
        <el-tooltip effect="dark" :content="currentRepoName" placement="right">
          <el-button type="primary" circle @click="showRepoDrawer = true">
            <el-icon><Collection /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
      </template>
      <!-- 导航菜单（可滚动区域） -->
      <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="true"
          class="sidebar-menu"
          @select="handleMenuSelect"
      >
        <el-menu-item index="dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>


        <el-sub-menu index="analysis">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>分析统计</span>
          </template>
          <el-menu-item index="analysis-trend">趋势分析</el-menu-item>
          <el-menu-item index="analysis-risk">风险评估</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="daily-update">
          <el-icon><Calendar /></el-icon>
          <template #title>每日漏洞更新</template>
        </el-menu-item>

        <el-menu-item index="repos">
          <el-icon><Management /></el-icon>
          <template #title>仓库管理</template>
        </el-menu-item>
      </el-menu>

      <!-- 底部操作区-->
      <div v-show="isCollapse" class="sidebar-footer-collapsed">
        <div class="collapse-footer-buttons">
          <el-tooltip effect="dark" content="展开侧边栏" placement="right">
            <el-button type="default" circle @click="toggleCollapse">
              <el-icon><Expand /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="main-container">
      <el-header class="main-header">
        <div class="header-content">
          <h2 class="page-title">
            <slot name="title">漏洞预警系统</slot>
          </h2>
          <!-- 用户信息 -->
          <div class="user-section">
            <el-dropdown trigger="click" @command="handleLogout">
              <div class="user-info">
                <el-avatar :size="32" :icon="UserFilled" class="user-avatar" />
                <span class="user-email">{{ userStore.userEmail }}</span>
                <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
              </div>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </el-header>

      <el-main class="main-content">
        <slot></slot>
      </el-main>
    </el-container>

    <!-- 仓库选择抽屉 -->
    <el-drawer
        v-if="!disableRepoSelection"
        v-model="showRepoDrawer"
        title="选择仓库"
        size="400px"
        :with-header="true"
    >
      <div class="repo-drawer-content">
        <el-input
            v-model="searchQuery"
            placeholder="搜索仓库..."
            prefix-icon="Search"
            clearable
            class="repo-search"
        />

        <div class="repo-list">
          <el-card
              v-for="repo in filteredRepos"
              :key="repo.id"
              class="repo-item"
              :class="{ 'repo-item-active': repo.is_active }"
              shadow="hover"
              @click="selectRepo(repo)"
          >
            <div class="repo-item-content">
              <div class="repo-item-header">
                <el-icon :size="18" class="repo-item-icon"><Collection /></el-icon>
                <span class="repo-item-name">{{ repo.name }}</span>
                <el-tag v-if="repo.id == selectedRepo.id" type="success" size="small">当前</el-tag>
              </div>
              <p class="repo-item-desc">上次扫描时间:{{ repo.last_fetched_at }}</p>
              <a :href="repo.repo_url" target="_blank" class="repo-item-url" @click.stop>
                <el-icon><Link /></el-icon>
                {{ repo.repo_url }}
              </a>
            </div>
          </el-card>
        </div>

        <el-divider />
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.layout-container {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #f5f7fa;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.sidebar {
  background: linear-gradient(180deg, #1a237e 0%, #283593 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  /* 保证侧边栏本身不滚动，滚动由内部菜单区域负责 */
  overflow: hidden;
}

.sidebar-header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0; /* 防止被压缩 */
}

.logo-icon {
  color: #fff;
  margin-right: 12px;
}

.logo-text {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  flex: 1;
}

.collapse-btn,
.expand-btn {
  color: rgba(255, 255, 255, 0.7);
  padding: 8px;
}

.collapse-btn:hover,
.expand-btn:hover {
  color: #fff;
}

.repo-section {
  padding: 16px;
  flex-shrink: 0;
}

.repo-card {
  cursor: pointer;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.repo-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

:deep(.repo-card .el-card__body) {
  padding: 12px;
}

.repo-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.repo-icon {
  color: #fff;
}

.repo-details {
  flex: 1;
}

.repo-name {
  color: #fff;
  font-weight: 500;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 120px;
}

.repo-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.switch-icon {
  color: rgba(255, 255, 255, 0.6);
}

.repo-section-collapsed {
  padding: 16px 0;
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  background: transparent;
  overflow-y: auto; /* 菜单区域独立滚动，不影响头部和底部 */
}

:deep(.el-menu) {
  background: transparent;
}

:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

:deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-right: 3px solid #fff;
}

:deep(.el-sub-menu .el-menu-item) {
  background: rgba(0, 0, 0, 0.1);
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.manage-repo-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
}

.manage-repo-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: #fff;
}

.sidebar-footer-collapsed {
  padding: 16px 0;
  display: flex;
  justify-content: center;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.collapse-footer-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  width: 100%;           /* 占满父容器宽度，便于居中 */
}
.collapse-footer-buttons .el-button {
  margin: 0;
}
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

.main-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  padding: 0 24px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a237e;
}

/* 用户信息样式 */
.user-section {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.user-info:hover {
  background: rgba(26, 35, 126, 0.05);
}

.user-avatar {
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
  color: white;
}

.user-email {
  font-size: 14px;
  color: #606266;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-icon {
  color: #909399;
  font-size: 12px;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 仓库抽屉样式 */
.repo-drawer-content {
  padding: 20px;
}

.repo-search {
  margin-bottom: 20px;
}

.repo-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.repo-item {
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.repo-item:hover {
  transform: translateX(4px);
  border-color: #dcdfe6;
}

.repo-item-active {
  border-color: #67c23a;
  background: #f0f9eb;
}

.repo-item-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.repo-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.repo-item-icon {
  color: #1a237e;
}

.repo-item-name {
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.repo-item-desc {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.repo-item-url {
  font-size: 12px;
  color: #409eff;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
}

.repo-item-url:hover {
  color: #66b1ff;
}

.add-repo-btn {
  width: 100%;
  margin-top: 16px;
}
</style>