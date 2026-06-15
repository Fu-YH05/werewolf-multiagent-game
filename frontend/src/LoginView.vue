<template>
  <div class="login-page">
    <!-- 星空背景 -->
    <div class="starfield">
      <div
        v-for="star in stars"
        :key="star.id"
        class="star"
        :style="{
          left: star.x + '%',
          top: star.y + '%',
          width: star.size + 'px',
          height: star.size + 'px',
          animationDelay: star.delay + 's',
          opacity: star.opacity
        }"
      ></div>
    </div>

    <div class="login-container">
      <div class="login-card">
        <div class="login-header">
          <span class="logo-icon">🐺</span>
          <h1>狼人杀多Agent对战平台</h1>
          <div class="subtitle">Multi-Agent Werewolf Game</div>
        </div>

        <div class="login-form">
          <div class="form-section">
            <label class="form-label">DeepSeek API Key</label>
            <input
              v-model="apiKey"
              type="text"
              placeholder="输入 DeepSeek API Key (可选)"
              class="form-input"
            />
            <p class="form-hint">不填则使用默认配置，填入后可自定义 AI 模型</p>
          </div>

          <button class="btn btn-primary btn-large" @click="enterGame">
            🚀 进入游戏
          </button>
        </div>

        <div class="login-footer">
          <p>由 Multi-Agent AI 驱动的狼人杀游戏</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['enter'])

const apiKey = ref(localStorage.getItem('deepseek_api_key') || '')

const stars = ref([])
const STAR_COUNT = 150

function generateStars() {
  stars.value = Array.from({ length: STAR_COUNT }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 2 + 1,
    delay: Math.random() * 3,
    opacity: Math.random() * 0.5 + 0.5
  }))
}

function enterGame() {
  emit('enter', apiKey.value)
}

onMounted(() => {
  generateStars()
})
</script>

<style scoped>
.login-page {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  overflow: hidden;
}

.starfield {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.star {
  position: absolute;
  background: white;
  border-radius: 50%;
  animation: twinkle 3s ease-in-out infinite;
}

@keyframes twinkle {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.login-container {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

.login-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 50px 40px;
  max-width: 480px;
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  font-size: 60px;
  display: block;
  margin-bottom: 15px;
}

.login-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: white;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 2px;
  text-transform: uppercase;
}

.login-form {
  margin-bottom: 30px;
}

.form-section {
  margin-bottom: 25px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 14px 18px;
  font-size: 15px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.form-input:focus {
  outline: none;
  border-color: #4fc3f7;
  background: rgba(255, 255, 255, 0.15);
}

.form-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 8px;
}

.btn-large {
  width: 100%;
  padding: 16px 24px;
  font-size: 18px;
}

.btn-primary {
  background: linear-gradient(135deg, #4fc3f7 0%, #29b6f6 100%);
  color: #1a1a2e;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(79, 195, 247, 0.4);
}

.login-footer {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}
</style>
