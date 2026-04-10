<template>
  <div class="register-page">
    <!-- 背景动画 -->
    <div class="animated-background">
      <div class="gradient-sphere sphere-1"></div>
      <div class="gradient-sphere sphere-2"></div>
      <div class="gradient-sphere sphere-3"></div>
    </div>

    <div class="register-container">
      <!-- 左侧表单区域 -->
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <h2 class="form-title">创建账户</h2>
            <p class="form-subtitle">加入我们，开启智能安全分析之旅</p>
          </div>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            class="register-form"
          >
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                placeholder="请输入邮箱"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>

            <el-form-item prop="verification_code">
              <div class="code-input-row">
                <el-input
                  v-model="form.verification_code"
                  placeholder="请输入验证码"
                  size="large"
                  :prefix-icon="Message"
                  maxlength="6"
                />
                <el-button
                  size="large"
                  :disabled="codeCountdown > 0"
                  :loading="isSendingCode"
                  @click="handleSendCode"
                >
                  {{ codeCountdown > 0 ? `${codeCountdown}s` : '获取验证码' }}
                </el-button>
              </div>
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请设置密码（至少6位）"
                size="large"
                show-password
                :prefix-icon="Lock"
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="请确认密码"
                size="large"
                show-password
                :prefix-icon="Lock"
                @keyup.enter="handleRegister"
              />
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="agreedTerms">
                我已阅读并同意 <a href="#" class="terms-link">服务条款</a> 和 <a href="#" class="terms-link">隐私政策</a>
              </el-checkbox>
            </el-form-item>

            <el-button
              type="primary"
              size="large"
              class="register-btn"
              :loading="userStore.isLoading"
              :disabled="!agreedTerms"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form>

          <div class="form-footer">
            <p>已有账户？ <router-link to="/login" class="link">立即登录</router-link></p>
          </div>
        </div>
      </div>

      <!-- 右侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <el-icon :size="64"><CircleCheckFilled /></el-icon>
          </div>
          <h1 class="brand-title">安全漏洞预警平台</h1>
          <p class="brand-subtitle">智能化开源软件安全分析系统</p>
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

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const form = reactive({
  email: '',
  password: '',
  confirmPassword: '',
  verification_code: ''
})

// 协议同意
const agreedTerms = ref(false)

// 验证码倒计时
const codeCountdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null
const isSendingCode = ref(false)

// 自定义密码确认验证
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 验证规则
const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  verification_code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 发送验证码
const handleSendCode = async () => {
  if (!form.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(form.email)) {
    ElMessage.warning('邮箱格式不正确')
    return
  }

  isSendingCode.value = true
  try {
    const success = await userStore.sendVerificationCode(form.email)
    if (success) {
      codeCountdown.value = 60
      countdownTimer = setInterval(() => {
        codeCountdown.value--
        if (codeCountdown.value <= 0 && countdownTimer) {
          clearInterval(countdownTimer)
        }
      }, 1000)
    }
  } finally {
    isSendingCode.value = false
  }
}

// 注册
const handleRegister = async () => {
  if (!formRef.value) return

  if (!agreedTerms.value) {
    ElMessage.warning('请先同意服务条款和隐私政策')
    return
  }

  try {
    await formRef.value.validate()
    const success = await userStore.register({
      email: form.email,
      password: form.password,
      verification_code: form.verification_code
    })
    if (success) {
     router.push('/')
    }
  } catch (e) {
    // 表单验证失败
  }
}

// 组件挂载时检查登录状态
onMounted(() => {
  if (userStore.isLoggedIn) {
    router.push('/')
  }
})
</script>

<style scoped>
.register-page {
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
  right: -100px;
  animation-delay: 0s;
}

.sphere-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  bottom: -100px;
  left: -100px;
  animation-delay: -5s;
}

.sphere-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  top: 50%;
  right: 30%;
  animation-delay: -10s;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  25% {
    transform: translate(-50px, 50px) scale(1.1);
  }
  50% {
    transform: translate(30px, -30px) scale(0.9);
  }
  75% {
    transform: translate(-30px, -50px) scale(1.05);
  }
}

/* 注册容器 */
.register-container {
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

/* 注册表单 */
.register-form {
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

.register-btn {
  width: 100%;
  border-radius: 10px;
  background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
  border: none;
  font-weight: 600;
  transition: all 0.3s ease;
  margin-top: 8px;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(26, 35, 126, 0.3);
}

.register-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.terms-link {
  color: #1a237e;
  text-decoration: none;
}

.terms-link:hover {
  text-decoration: underline;
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

.brand-stats {
  display: flex;
  gap: 32px;
  justify-content: center;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 12px;
  opacity: 0.8;
}

/* 响应式适配 */
@media (max-width: 1024px) {
  .register-container {
    width: 90%;
    max-width: 400px;
    flex-direction: column-reverse;
  }

  .brand-section {
    padding: 40px;
    min-height: 180px;
  }

  .brand-title {
    font-size: 22px;
  }

  .brand-stats {
    display: none;
  }

  .form-section {
    padding: 40px;
  }
}

@media (max-width: 480px) {
  .register-page {
    padding: 20px;
  }

  .register-container {
    border-radius: 16px;
  }

  .brand-section,
  .form-section {
    padding: 30px 20px;
  }
}
</style>
