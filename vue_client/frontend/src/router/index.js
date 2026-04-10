import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import RepositoryManagement from '../views/RepositoryManagement.vue'
import TrendAnalysis from '../views/TrendAnalysis.vue'
import RiskAssessment from '../views/RiskAssessment.vue'
import DailyVulnUpdate from '../views/DailyVulnUpdate.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { public: true }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/repositories',
    name: 'RepositoryManagement',
    component: RepositoryManagement,
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis/trend',
    name: 'TrendAnalysis',
    component: TrendAnalysis,
    meta: { requiresAuth: true }
  },
  {
    path: '/analysis/risk',
    name: 'RiskAssessment',
    component: RiskAssessment,
    meta: { requiresAuth: true }
  },
  {
    path: '/daily-update',
    name: 'DailyVulnUpdate',
    component: DailyVulnUpdate,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫 - 验证登录状态
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 如果路由需要认证且用户未登录
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  }
  // 如果用户已登录且访问登录/注册页面，重定向到首页
  else if (to.meta.public && userStore.isLoggedIn) {
    next('/')
  }
  else {
    next()
  }
})

export default router
