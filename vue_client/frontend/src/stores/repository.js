import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useRepoStore = defineStore('repository', () => {
  // State
  const repositories = ref([
    {
      id: 1,
      name: 'vuejs/vue',
      url: 'https://github.com/vuejs/vue',
      description: 'Vue.js 渐进式 JavaScript 框架',
      status: 'active',
      active: true,
      last_scan: '2024-01-15 10:30:00',
      vuln_count: 2,
      auto_scan: true,
      scan_frequency: 'daily',
      notify_email: 'admin@example.com'
    },
    {
      id: 2,
      name: 'facebook/react',
      url: 'https://github.com/facebook/react',
      description: '用于构建用户界面的 JavaScript 库',
      status: 'active',
      active: false,
      last_scan: '2024-01-14 15:20:00',
      vuln_count: 5,
      auto_scan: true,
      scan_frequency: 'weekly',
      notify_email: 'admin@example.com'
    }
  ])

  const currentRepoId = ref(1)

  // Getters
  const currentRepo = computed(() => {
    return repositories.value.find(r => r.id === currentRepoId.value) || repositories.value[0]
  })

  const activeRepos = computed(() => {
    return repositories.value.filter(r => r.status === 'active')
  })

  const totalVulns = computed(() => {
    return repositories.value.reduce((sum, r) => sum + r.vuln_count, 0)
  })

  // Actions
  const setCurrentRepo = (repoId) => {
    currentRepoId.value = repoId
    // 更新所有仓库的 active 状态
    repositories.value.forEach(r => {
      r.active = (r.id === repoId)
    })
  }

  const addRepository = (repo) => {
    const newRepo = {
      id: Date.now(),
      ...repo,
      status: 'active',
      active: false,
      last_scan: '-',
      vuln_count: 0
    }
    repositories.value.push(newRepo)
  }

  const updateRepository = (repoId, updates) => {
    const index = repositories.value.findIndex(r => r.id === repoId)
    if (index !== -1) {
      repositories.value[index] = { ...repositories.value[index], ...updates }
    }
  }

  const deleteRepository = (repoId) => {
    const index = repositories.value.findIndex(r => r.id === repoId)
    if (index !== -1) {
      repositories.value.splice(index, 1)
      // 如果删除的是当前选中的仓库，切换到第一个
      if (currentRepoId.value === repoId && repositories.value.length > 0) {
        setCurrentRepo(repositories.value[0].id)
      }
    }
  }

  const toggleRepoStatus = (repoId) => {
    const repo = repositories.value.find(r => r.id === repoId)
    if (repo) {
      repo.status = repo.status === 'active' ? 'inactive' : 'active'
    }
  }

  return {
    repositories,
    currentRepoId,
    currentRepo,
    activeRepos,
    totalVulns,
    setCurrentRepo,
    addRepository,
    updateRepository,
    deleteRepository,
    toggleRepoStatus
  }
})
