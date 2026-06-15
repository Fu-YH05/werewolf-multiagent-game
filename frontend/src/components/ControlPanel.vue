<template>
  <div class="control-panel">
    <div class="section-title">游戏控制</div>
    
    <input
      v-model="apiKey"
      type="text"
      placeholder="输入 DeepSeek API Key (可选)"
      class="api-input"
    />
    
    <!-- 真人玩家模式 -->
    <div class="human-mode-toggle">
      <label class="toggle-label">
        <input type="checkbox" v-model="isHumanMode" class="toggle-checkbox" />
        <span class="toggle-text">👤 真人玩家模式</span>
      </label>
      <p v-if="isHumanMode" class="toggle-hint">
        你将扮演第 {{ humanPlayerIndex + 1 }} 位玩家，其他 8 位由 AI 控制
      </p>
    </div>

    <!-- 豆包语音模式 -->
    <div class="doubao-toggle">
      <label class="toggle-label">
        <input type="checkbox" v-model="useDoubaoTTS" class="toggle-checkbox" />
        <span class="toggle-text">🎵 豆包语音 (全部AI使用豆包TTS)</span>
      </label>
      <div v-if="useDoubaoTTS" class="mt-2">
        <input
          v-model="doubaoAppid"
          type="text"
          placeholder="输入豆包 AppID (控制台获取)"
          class="api-input mb-1"
        />
        <input
          v-model="doubaoApiKey"
          type="text"
          placeholder="输入豆包 Token (控制台获取)"
          class="api-input"
        />
        <p class="toggle-hint">需在豆包语音控制台获取 AppID 和 Token</p>
      </div>
    </div>
    
    <!-- 游戏速度控制 -->
    <div class="speed-control mb-2">
      <div class="flex items-center justify-between mb-1">
        <span class="speed-label">⏱️ 游戏速度</span>
        <span class="speed-value">{{ stepDelay.toFixed(1) }}s/步</span>
      </div>
      <input
        type="range"
        :min="0.2"
        :max="3.0"
        :step="0.1"
        v-model.number="stepDelay"
        class="speed-slider"
      />
      <div class="flex justify-between text-xs text-gray-500 mt-1">
        <span>⚡快</span>
        <span>🐢慢</span>
      </div>
    </div>
    
    <button
      class="btn btn-primary"
      @click="$emit('start', isHumanMode ? (humanPlayerIndex) : -1, stepDelay)"
    >
      🚀 开始新游戏
    </button>
    
    <button
      class="btn btn-secondary"
      :disabled="!isRunning"
      @click="$emit('togglePause')"
    >
      {{ isPaused ? '▶️ 继续' : '⏸️ 暂停' }}
    </button>

    <button
      class="btn btn-danger"
      :disabled="!isRunning && !(viewingReplay && hasLiveGame)"
      @click="$emit('stop')"
    >
      🛑 结束游戏
    </button>

    <button
      class="btn btn-secondary"
      @click="$emit('showReplay')"
    >
      📺 观看回放
    </button>
    
    <div class="status-card mt-3">
      <div class="section-title">游戏状态</div>
      <div class="status-item">
        <span class="status-label">游戏ID</span>
        <span class="status-value">{{ gameId || '-' }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">当前阶段</span>
        <span class="status-value">{{ phase || '等待开始' }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">存活人数</span>
        <span class="status-value">{{ aliveCount }}/{{ totalPlayers }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">游戏时长</span>
        <span class="status-value">{{ duration }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  gameId: String,
  phase: String,
  aliveCount: {
    type: Number,
    default: 7
  },
  totalPlayers: {
    type: Number,
    default: 7
  },
  duration: {
    type: String,
    default: '0:00'
  },
  isRunning: Boolean,
  isPaused: Boolean,
  viewingReplay: {
    type: Boolean,
    default: false
  },
  hasLiveGame: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['start', 'togglePause', 'stop', 'showReplay'])

const apiKey = ref('')
const isHumanMode = ref(false)
const humanPlayerIndex = ref(0)  // 默认真人坐在第1个位置
const stepDelay = ref(1.5)  // 默认1.5秒/步
const useDoubaoTTS = ref(false)  // 豆包语音开关
const doubaoAppid = ref('4605841871')  // 豆包应用ID
const doubaoApiKey = ref('ZCrTMDsGLAFQg_Y5QiPX5SldET-Sfg8_')  // 豆包语音 Token

defineExpose({
  apiKey,
  isHumanMode,
  humanPlayerIndex,
  stepDelay,
  useDoubaoTTS,
  doubaoAppid,
  doubaoApiKey
})

watch(apiKey, (newVal) => {
  console.log('API Key changed:', newVal ? `${newVal.substring(0, 10)}...` : 'None')
})
</script>

<style scoped>
.control-panel {
  @apply bg-bg-secondary p-3 border-r border-white/5 overflow-y-auto;
}

.api-input {
  @apply w-full bg-bg-card border border-white/10 rounded-lg p-2 text-white text-sm mb-2;
}

.api-input::placeholder {
  @apply text-gray-400;
}

.status-item {
  @apply flex justify-between py-1 border-b border-white/5;
}

.status-item:last-child {
  @apply border-b-0;
}

.status-label {
  @apply text-sm text-gray-400;
}

.status-value {
  @apply font-semibold text-accent-gold;
}

.human-mode-toggle {
  @apply mb-2 p-2 rounded-lg;
  background: rgba(34, 197, 94, 0.05);
  border: 1px solid rgba(34, 197, 94, 0.15);
}

.toggle-label {
  @apply flex items-center gap-2 cursor-pointer;
}

.toggle-checkbox {
  @apply w-4 h-4 accent-green-500 cursor-pointer;
}

.toggle-text {
  @apply text-sm text-white font-medium;
}

.toggle-hint {
  @apply text-xs text-gray-400 mt-1 ml-6;
}

.speed-control {
  @apply p-2 rounded-lg;
  background: rgba(99, 102, 241, 0.05);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.speed-label {
  @apply text-sm text-white font-medium;
}

.speed-value {
  @apply text-xs text-accent-purple font-mono;
}

.speed-slider {
  @apply w-full h-2 rounded-lg appearance-none cursor-pointer;
  background: rgba(99, 102, 241, 0.2);
  accent-color: #818cf8;
}

.speed-slider::-webkit-slider-thumb {
  @apply appearance-none w-4 h-4 rounded-full;
  background: #818cf8;
  cursor: pointer;
}

.btn-danger {
  @apply w-full py-2 rounded-lg text-sm font-medium transition-all duration-200 disabled:opacity-40;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(220, 38, 38, 0.35));
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  cursor: pointer;
}

.btn-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.4), rgba(220, 38, 38, 0.5));
  border-color: rgba(239, 68, 68, 0.5);
  color: #fecaca;
}
</style>
