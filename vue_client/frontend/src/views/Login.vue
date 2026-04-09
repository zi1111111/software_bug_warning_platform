<template>
  <div class="login-page">
    <!-- 背景动画 -->
    <div class="animated-background">
      <div class="gradient-sphere sphere-1"></div>
      <div class="gradient-sphere sphere-2"></div>
      <div class="gradient-sphere sphere-3"></div>
    </div>

    <div class="login-container">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <el-icon :size="64"><CircleCheckFilled /></el-icon>
          </div>
          <h1 class="brand-title">安全漏洞预警平台</h1>
          <p class="brand-subtitle">智能化开源软件安全分析系统</p>
          <div class="brand-features">
            <div class="feature-item">
              <el-icon><CircleCheckFilled /></el-icon>
              <span>AI 驱动的漏洞检测</span>
            </div>
            <div class="feature-item">
              <el-icon><CircleCheckFilled /></el-icon>
              <span>实时监控与预警</span>
            </div>
            <div class="feature-item">
              <el-icon><CircleCheckFilled /></el-icon>
              <span>多维度风险评估</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <h2 class="form-title">欢迎回来</h2>
            <p class="form-subtitle">请登录您的账户以继续</p>
          </div>

          <!-- 登录方式切换 -->
          <div class="login-tabs">
            <button
              :class="['tab-btn', { active: loginMethod === 'password' }]"
              @click="loginMethod = 'password'"
            >
              密码登录
            </button>
            <button
              :class="['tab-btn', { active: loginMethod === 'code' }]"
              @click="loginMethod = 'code'"
            >
              验证码登录
            </button>
          </div>

          <!-- 密码登录表单 -->
          <el-form
            v-if="loginMethod === 'password'"
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            class="login-form"
          >
            <el-form-item prop="email">
              <el-input
                v-model="passwordForm.email"
                placeholder="请输入邮箱"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="passwordForm.password"
                type="password"
                placeholder="请输入密码"
                size="large"
                show-password
                :prefix-icon="Lock"
                @keyup.enter="handlePasswordLogin"
              />
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="userStore.isLoading"
              @click="handlePasswordLogin"
            >
              登录
            </el-button>
          </el-form>

          <!-- 验证码登录表单 -->
          <el-form
            v-else
            ref="codeFormRef"
            :model="codeForm"
            :rules="codeRules"
            class="login-form"
          >
            <el-form-item prop="email">
              <el-input
                v-model="codeForm.email"
                placeholder="请输入邮箱"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="verification_code">
              <div class="code-input-row">
                <el-input
                  v-model="codeForm.verification_code"
                  placeholder="请输入验证码"
                  size="large"
                  :prefix-icon="Message"
                  maxlength="6"
                  @keyup.enter="handleCodeLogin"
                />
                <el-button
                  size="large"
                  :disabled="codeCountdown > 0"
                  @click="handleSendLoginCode"
                >
                  {{ codeCountdown > 0 ? `${codeCountdown}s` : '获取验证码' }}
                </el-button>
              </div>
            </el-form-item>
            <el-button
              type="primary"
              size="large"
              class="login-btn"
              :loading="userStore.isLoading"
              @click="handleCodeLogin"
            >
              登录
            </el-button>
          </el-form>

          <div class="form-footer">
            <p>还没有账户？ <router-link to="/register" class="link">立即注册</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, CircleCheckFilled } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

// 登录方式
const loginMethod = ref<'password' | 'code'>('password')

// 表单引用
const passwordFormRef = ref<FormInstance>()
const codeFormRef = ref<FormInstance>()

// 密码登录表单
const passwordForm = reactive({
  email: '',
  password: ''
})

// 验证码登录表单
const codeForm = reactive({
  email: '',
  verification_code: ''
})

// 验证码倒计时
const codeCountdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

// 验证规则
const passwordRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

const codeRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  verification_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ]
}

// 密码登录
const handlePasswordLogin = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    const success = await userStore.login({
      email: passwordForm.email,
      password: passwordForm.password
    })
    if (success) {
      router.push('/')
    }
  } catch (e) {
    // 表单验证失败
  }
}

// 验证码登录
const handleCodeLogin = async () => {
  if (!codeFormRef.value) return
  
  try {
    await codeFormRef.value.validate()
    const success = await userStore.loginWithCode({
      email: codeForm.email,
      verification_code: codeForm.verification_code
    })
    if (success) {
      router.push('/')
    }
  } catch (e) {
    // 表单验证失败
  }
}

// 发送登录验证码
const handleSendLoginCode = async () => {
  if (!codeForm.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(codeForm.email)) {
    ElMessage.warning('邮箱格式不正确')
    return
  }
  
  const success = await userStore.sendLoginCode(codeForm.email)
  if (success) {
    codeCountdown.value = 60
    countdownTimer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0 && countdownTimer) {
        clearInterval(countdownTimer)
      }
    }, 1000)
  }
}

// 组件卸载时清除定时器
onMounted(() => {
  // 检查是否已登录
  if (userStore.isLoggedIn) {
    router.push('/')
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 动画背景 */
.animated-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;
}

.gradient-sphere {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 20s infinite ease-in-out;
}

.sphere-1 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  top: -200px;
  left: -100px;
  animation-delay: 0s;
}

.sphere-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  bottom: -100px;
  right: -100px;
  animation-delay: -5s;
}

.sphere-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  top: 50%;
  left: 50%;
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(50px, -50px) scale(1.1);
  }
  50% {
    transform: translate(-30px, 30px) scale(0.9);
  }
  75% {
    transform: translate(30px, 50px) scale(1.05);
  }
}

/* 登录容器 */
.login-container {
  display: flex;
  width: 1000px;
  min-height: 600px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
}

/* 品牌区域 */
.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: white;
  position: relative;
  overflow: hidden;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
}

.brand-content {
  text-align: center;
  position: relative;
  z-index: 1;
}

.logo {
  margin-bottom: 24px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

.brand-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 12px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 40px;
}

.brand-features {
  text-align: left;
  display: inline-block;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 14px;
  opacity: 0.9;
}

.feature-item .el-icon {
  color: #4caf50;
  font-size: 18px;
}

/* 表单区域 */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  background: white;
}

.form-card {
  width: 100%;
  max-width: 360px;
}

.form-header {
  text-align: center;
  margin-bottom: 32px;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: #1a237e;
  margin-bottom: 8px;
}

.form-subtitle {
  font-size: 14px;
  color: #6b7280;
}

/* 登录方式切换 */
.login-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 10px;
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.tab-btn.active {
  background: white;
  color: #1a237e;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 登录表单 */
.login-form {
  margin-bottom: 24px;
}

:deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.code-input-row {
  display: flex;
  gap: 12px;
}

.code-input-row .el-input {
  flex: 1;
}

.code-input-row .el-button {
  width: 120px;
}

.login-btn {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
  border: none;
  font-weight: 600;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(26, 35, 126, 0.3);
}

/* 表单底部 */
.form-footer {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.link {
  color: #1a237e;
  font-weight: 600;
  text-decoration: none;
  transition: color 0.3s ease;
}

.link:hover {
  color: #3949ab;
  text-decoration: underline;
}

/* 响应式适配 */
@media (max-width: 1024px) {
  .login-container {
    width: 90%;
    max-width: 400px;
    flex-direction: column;
  }

  .brand-section {
    padding: 40px;
    min-height: 200px;
  }

  .brand-title {
    font-size: 22px;
  }

  .brand-features {
    display: none;
  }

  .form-section {
    padding: 40px;
  }
}

@media (max-width: 480px) {
  .login-page {
    padding: 20px;
  }

  .login-container {
    border-radius: 16px;
  }

  .brand-section,
  .form-section {
    padding: 30px 20px;
  }
}
</style>
