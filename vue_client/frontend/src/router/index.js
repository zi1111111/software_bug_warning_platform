import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import RepositoryManagement from '../views/RepositoryManagement.vue'

import TrendAnalysis from '../views/TrendAnalysis.vue'
import RiskAssessment from '../views/RiskAssessment.vue'
import DailyVulnUpdate from '../views/DailyVulnUpdate.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/repositories',
    name: 'RepositoryManagement',
    component: RepositoryManagement
  },
  {
    path: '/analysis/trend',
    name: 'TrendAnalysis',
    component: TrendAnalysis
  },
  {
    path: '/analysis/risk',
    name: 'RiskAssessment',
    component: RiskAssessment
  },
  {
    path: '/daily-update',
    name: 'DailyVulnUpdate',
    component: DailyVulnUpdate
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Dashboard.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
