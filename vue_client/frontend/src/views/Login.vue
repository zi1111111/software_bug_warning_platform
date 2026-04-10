<template>
  <div class="login-page">
    <!-- 动态渐变背景层 -->
    <div class="gradient-bg">
      <div class="gradient-sphere sphere-1"></div>
      <div class="gradient-sphere sphere-2"></div>
      <div class="gradient-sphere sphere-3"></div>
      <div class="gradient-sphere sphere-4"></div>
    </div>

    <!-- 网格背景 -->
    <div class="grid-overlay"></div>

    <!-- 粒子效果 -->
    <div class="particles">
      <span v-for="n in 30" :key="n" class="particle"></span>
    </div>

    <!-- 脉冲光环 -->
    <div class="pulse-rings">
      <div class="ring"></div>
      <div class="ring"></div>
      <div class="ring"></div>
    </div>

    <!-- 主内容区 - 融合式设计 -->
    <div class="content-wrapper">
      <div class="fusion-card">
        <!-- 顶部品牌区 -->
        <div class="brand-header">
          <div class="logo-glow">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
          </div>
          <h1 class="title">
            <span class="gradient-text">开源软件预警漏洞平台</span>
          </h1>
          <p class="subtitle">智能漏洞分析平台</p>
        </div>

        <!-- 模型展示 - 浮动标签 -->
        <div class="model-float-tags">
          <span class="float-tag" style="--delay: 0s">DeepSeek</span>
          <span class="float-tag" style="--delay: 0.5s">GLM-5</span>
          <span class="float-tag" style="--delay: 1s">Qwen</span>
          <span class="float-tag" style="--delay: 1.5s">Hunyuan</span>
        </div>

        <!-- 登录表单 -->
        <div class="login-section">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="rules"
            class="login-form"
            @keyup.enter="handleLogin"
          >
            <el-form-item prop="email">
              <el-input
                v-model="loginForm.email"
                placeholder="邮箱地址"
                size="large"
                :prefix-icon="User"
                class="custom-input"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                size="large"
                :prefix-icon="Lock"
                show-password
                class="custom-input"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="login-btn"
                :loading="isLoading"
                @click="handleLogin"
              >
                <el-icon v-if="isLoading" class="is-loading"><Loading /></el-icon>
                <span v-else>登 录</span>
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 底部链接 -->
          <div class="card-footer">
            <p>还没有账号？ <router-link to="/register" class="link">立即注册</router-link></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Loading } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { storeToRefs } from 'pinia'

const router = useRouter()
const userStore = useUserStore()
const { isLoading } = storeToRefs(userStore)

const loginForm = reactive({
  email: '',
  password: ''
})

const loginFormRef = ref()

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await loginFormRef.value?.validate().catch(() => false)
  if (!valid) return

  const success = await userStore.login({
    email: loginForm.email,
    password: loginForm.password
  })

  if (success) {
    router.push('/dashboard')
  }
}
</script>

<style scoped>
/* 页面基础布局 */
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  height: 100vh;
  height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

/* 动态渐变背景 */
.gradient-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.gradient-sphere {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.6;
  animation: float 25s infinite ease-in-out;
}

.sphere-1 {
  width: 700px;
  height: 700px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  top: -300px;
  left: -200px;
  animation-delay: 0s;
}

.sphere-2 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  bottom: -200px;
  right: -200px;
  animation-delay: -8s;
}

.sphere-3 {
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  top: 40%;
  left: 60%;
  animation-delay: -15s;
}

.sphere-4 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  bottom: 30%;
  left: 20%;
  animation-delay: -5s;
  opacity: 0.4;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1) rotate(0deg);
  }
  25% {
    transform: translate(80px, -60px) scale(1.15) rotate(90deg);
  }
  50% {
    transform: translate(-40px, 40px) scale(0.9) rotate(180deg);
  }
  75% {
    transform: translate(60px, 20px) scale(1.1) rotate(270deg);
  }
}

/* 网格覆盖层 - 更透明 */
.grid-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
  background-size: 60px 60px;
  z-index: 1;
  pointer-events: none;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: perspective(500px) rotateX(60deg) translateY(0); }
  100% { transform: perspective(500px) rotateX(60deg) translateY(60px); }
}

/* 粒子效果 - 增加到30个 */
.particles {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  pointer-events: none;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 50%;
  animation: particle-float 12s infinite linear;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
}

.particle:nth-child(1) { left: 5%; animation-delay: 0s; }
.particle:nth-child(2) { left: 10%; animation-delay: 0.4s; }
.particle:nth-child(3) { left: 15%; animation-delay: 0.8s; }
.particle:nth-child(4) { left: 20%; animation-delay: 1.2s; }
.particle:nth-child(5) { left: 25%; animation-delay: 1.6s; }
.particle:nth-child(6) { left: 30%; animation-delay: 2s; }
.particle:nth-child(7) { left: 35%; animation-delay: 2.4s; }
.particle:nth-child(8) { left: 40%; animation-delay: 2.8s; }
.particle:nth-child(9) { left: 45%; animation-delay: 3.2s; }
.particle:nth-child(10) { left: 50%; animation-delay: 3.6s; }
.particle:nth-child(11) { left: 55%; animation-delay: 4s; }
.particle:nth-child(12) { left: 60%; animation-delay: 4.4s; }
.particle:nth-child(13) { left: 65%; animation-delay: 4.8s; }
.particle:nth-child(14) { left: 70%; animation-delay: 5.2s; }
.particle:nth-child(15) { left: 75%; animation-delay: 5.6s; }
.particle:nth-child(16) { left: 80%; animation-delay: 6s; }
.particle:nth-child(17) { left: 85%; animation-delay: 6.4s; }
.particle:nth-child(18) { left: 90%; animation-delay: 6.8s; }
.particle:nth-child(19) { left: 95%; animation-delay: 7.2s; }
.particle:nth-child(20) { left: 8%; animation-delay: 7.6s; }
.particle:nth-child(21) { left: 18%; animation-delay: 8s; }
.particle:nth-child(22) { left: 28%; animation-delay: 8.4s; }
.particle:nth-child(23) { left: 38%; animation-delay: 8.8s; }
.particle:nth-child(24) { left: 48%; animation-delay: 9.2s; }
.particle:nth-child(25) { left: 58%; animation-delay: 9.6s; }
.particle:nth-child(26) { left: 68%; animation-delay: 10s; }
.particle:nth-child(27) { left: 78%; animation-delay: 10.4s; }
.particle:nth-child(28) { left: 88%; animation-delay: 10.8s; }
.particle:nth-child(29) { left: 3%; animation-delay: 11.2s; }
.particle:nth-child(30) { left: 93%; animation-delay: 11.6s; }

@keyframes particle-float {
  0% {
    transform: translateY(100vh) scale(0);
    opacity: 0;
  }
  5% {
    opacity: 0.8;
  }
  95% {
    opacity: 0.8;
  }
  100% {
    transform: translateY(-100vh) scale(2);
    opacity: 0;
  }
}

/* 脉冲光环效果 */
.pulse-rings {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
  pointer-events: none;
}

.ring {
  position: absolute;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: pulse-ring 4s ease-out infinite;
}

.ring:nth-child(1) {
  width: 300px;
  height: 300px;
  animation-delay: 0s;
}

.ring:nth-child(2) {
  width: 500px;
  height: 500px;
  animation-delay: 1.3s;
}

.ring:nth-child(3) {
  width: 700px;
  height: 700px;
  animation-delay: 2.6s;
}

@keyframes pulse-ring {
  0% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 0.6;
    border-color: rgba(102, 126, 234, 0.3);
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
    border-color: rgba(102, 126, 234, 0);
  }
}

/* 内容包装器 - 居中融合设计 */
.content-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  padding: 20px;
  width: 100%;
}

/* 融合式卡片 - 极高透明度 */
.fusion-card {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 32px;
  padding: 60px 50px;
  backdrop-filter: blur(40px);
  box-shadow:
    0 25px 80px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 0 100px rgba(102, 126, 234, 0.1);
  max-width: 480px;
  width: 100%;
  text-align: center;
  position: relative;
  overflow: hidden;
  animation: card-breathe 6s ease-in-out infinite;
}

.fusion-card::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  animation: card-rotate 15s linear infinite;
  pointer-events: none;
}

@keyframes card-breathe {
  0%, 100% {
    box-shadow:
      0 25px 80px rgba(0, 0, 0, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.2),
      0 0 100px rgba(102, 126, 234, 0.1);
  }
  50% {
    box-shadow:
      0 35px 100px rgba(0, 0, 0, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.25),
      0 0 120px rgba(102, 126, 234, 0.2);
  }
}

@keyframes card-rotate {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 品牌头部 - 融合在卡片内 */
.brand-header {
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
}

.logo-glow {
  display: inline-block;
  position: relative;
  margin-bottom: 20px;
}

.logo-glow::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  filter: blur(30px);
  opacity: 0.6;
  animation: logo-pulse 3s ease-in-out infinite;
}

@keyframes logo-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.6; }
  50% { transform: translate(-50%, -50%) scale(1.3); opacity: 0.8; }
}

.logo-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  position: relative;
  z-index: 1;
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
  animation: logo-float 4s ease-in-out infinite;
}

@keyframes logo-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.logo-icon svg {
  width: 32px;
  height: 32px;
  color: white;
}

.title {
  font-size: 36px;
  font-weight: 800;
  margin-bottom: 8px;
  line-height: 1.2;
}

.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 30%, #f093fb 60%, #4facfe 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  background-size: 300% 300%;
  animation: gradient-shift 4s ease infinite;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 2px;
  text-transform: uppercase;
}

/* 浮动模型标签 */
.model-float-tags {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 35px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}

.float-tag {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  animation: tag-float 3s ease-in-out infinite;
  animation-delay: var(--delay);
  transition: all 0.3s ease;
}

.float-tag:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

@keyframes tag-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* 登录区域 */
.login-section {
  position: relative;
  z-index: 1;
}

/* 表单样式 - 更透明 */
.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
  margin-top: 28px;
}

.custom-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  border-radius: 16px !important;
  box-shadow: none !important;
  padding: 8px 20px !important;
  transition: all 0.3s ease;
}

.custom-input :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.15) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
}

.custom-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.2) !important;
  border-color: #667eea !important;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.3) !important;
}

.custom-input :deep(.el-input__inner) {
  color: white !important;
  font-size: 16px;
  height: 52px;
}

.custom-input :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.4) !important;
}

.custom-input :deep(.el-input__icon) {
  color: rgba(255, 255, 255, 0.5) !important;
  font-size: 20px;
}

/* 登录按钮 - 动态发光 */
.login-btn {
  width: 100%;
  height: 56px;
  font-size: 17px;
  font-weight: 600;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.login-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.5s ease;
}

.login-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 40px rgba(102, 126, 234, 0.5);
}

.login-btn:hover::before {
  left: 100%;
}

.login-btn:active {
  transform: translateY(-1px);
}

/* 底部链接 */
.card-footer {
  margin-top: 28px;
  position: relative;
  z-index: 1;
}

.card-footer p {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
}

.link {
  color: #a78bfa;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
  position: relative;
}

.link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 1px;
  background: linear-gradient(90deg, #667eea, #a78bfa);
  transition: width 0.3s ease;
}

.link:hover {
  color: #c4b5fd;
}

.link:hover::after {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 600px) {
  .fusion-card {
    padding: 40px 30px;
    margin: 20px;
  }

  .title {
    font-size: 28px;
  }

  .model-float-tags {
    gap: 8px;
  }

  .float-tag {
    font-size: 11px;
    padding: 5px 10px;
  }
}

@media (max-width: 400px) {
  .fusion-card {
    padding: 35px 25px;
  }

  .title {
    font-size: 24px;
  }
}
</style>
