import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { http } from '../request/request'
import { ElMessage } from 'element-plus'

export interface User {
  id: number
  email: string
  created_at?: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  password: string
  verification_code: string
}

export interface LoginWithCodeCredentials {
  email: string
  verification_code: string
}

// Token响应接口
interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

// 消息响应接口
interface MessageResponse {
  code: number
  message: string
}

// 用户信息响应接口
interface UserResponse {
  code: number
  user: User
}

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)
  const isLoading = ref(false)

  // Getters
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userEmail = computed(() => user.value?.email || '')

  // Actions
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  const setUser = (userData: User) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  // 初始化时从localStorage恢复用户数据
  const initUserFromStorage = () => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    
    if (storedToken) {
      token.value = storedToken
    }
    
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        user.value = null
      }
    }
  }

  // 登录（密码）
  const login = async (credentials: LoginCredentials): Promise<boolean> => {
    isLoading.value = true
    try {
      const res = await http.post<TokenResponse>('/api/user/login', credentials)
      if (res.data && res.data.access_token) {
        setToken(res.data.access_token)
        if (res.data.user) {
          setUser(res.data.user)
        }
        ElMessage.success('登录成功')
        return true
      }
      return false
    } catch (error: any) {
      const msg = error.response?.data?.detail || '登录失败'
      ElMessage.error(msg)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 登录（验证码）
  const loginWithCode = async (credentials: LoginWithCodeCredentials): Promise<boolean> => {
    isLoading.value = true
    try {
      const res = await http.post<TokenResponse>('/api/user/login-with-code', credentials)
      if (res.data && res.data.access_token) {
        setToken(res.data.access_token)
        if (res.data.user) {
          setUser(res.data.user)
        }
        ElMessage.success('登录成功')
        return true
      }
      return false
    } catch (error: any) {
      const msg = error.response?.data?.detail || '登录失败'
      ElMessage.error(msg)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 注册
  const register = async (credentials: RegisterCredentials): Promise<boolean> => {
    isLoading.value = true
    try {
      const res = await http.post<TokenResponse>('/api/user/register', credentials)
      if (res.data && res.data.access_token) {
        setToken(res.data.access_token)
        if (res.data.user) {
          setUser(res.data.user)
        }
        ElMessage.success('注册成功')
        return true
      }
      return false
    } catch (error: any) {
      const msg = error.response?.data?.detail || '注册失败'
      ElMessage.error(msg)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 发送验证码（注册用）
  const sendVerificationCode = async (email: string): Promise<boolean> => {
    try {
      const res = await http.post<MessageResponse>('/api/user/send-verification-code', { email })
      if (res.data && res.data.code === 200) {
        ElMessage.success('验证码已发送')
        return true
      }
      return false
    } catch (error: any) {
      const msg = error.response?.data?.detail || '发送失败'
      ElMessage.error(msg)
      return false
    }
  }

  // 发送验证码（登录用）
  const sendLoginCode = async (email: string): Promise<boolean> => {
    try {
      const res = await http.post<MessageResponse>('/api/user/send-login-code', { email })
      if (res.data && res.data.code === 200) {
        ElMessage.success('验证码已发送')
        return true
      }
      return false
    } catch (error: any) {
      const msg = error.response?.data?.detail || '发送失败'
      ElMessage.error(msg)
      return false
    }
  }

  // 获取当前用户信息
  const fetchCurrentUser = async (): Promise<boolean> => {
    if (!token.value) return false
    
    try {
      const res = await http.get<UserResponse>('/api/user/me')
      if (res.data && res.data.code === 200 && res.data.user) {
        setUser(res.data.user)
        return true
      }
      return false
    } catch (error: any) {
      if (error.response?.status === 401) {
        // Token过期或无效，清除登录状态
        clearToken()
      }
      return false
    }
  }

  // 退出登录
  const logout = async () => {
    try {
      await http.post('/api/user/logout')
    } catch (e) {
      // 忽略错误
    }
    clearToken()
    ElMessage.success('已退出登录')
  }

  // 初始化
  initUserFromStorage()

  return {
    token,
    user,
    isLoading,
    isLoggedIn,
    userEmail,
    login,
    loginWithCode,
    register,
    sendVerificationCode,
    sendLoginCode,
    fetchCurrentUser,
    logout,
    setToken,
    clearToken
  }
})
