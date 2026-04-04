import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import RepositoryManagement from '../views/RepositoryManagement.vue'

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
    path: '/warnings',
    name: 'Warnings',
    component: () => import('../views/Dashboard.vue') // 暂时复用仪表盘
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Dashboard.vue') // 暂时复用仪表盘
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
