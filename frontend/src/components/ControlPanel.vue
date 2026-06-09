<template>
  <div class="control-panel">
    <div class="section-title">游戏控制</div>
    
    <input
      v-model="apiKey"
      type="text"
      placeholder="输入 DeepSeek API Key (可选)"
      class="api-input"
    />
    
    <button
      class="btn btn-primary"
      :disabled="isRunning"
      @click="$emit('start')"
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
      class="btn btn-secondary"
      @click="$emit('showReplay')"
    >
      📺 观看回放
    </button>
    
    <div class="status-card mt-4">
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
  isPaused: Boolean
})

const emit = defineEmits(['start', 'togglePause', 'showReplay'])

const apiKey = ref('')

defineExpose({
  apiKey
})

watch(apiKey, (newVal) => {
  console.log('API Key changed:', newVal ? `${newVal.substring(0, 10)}...` : 'None')
})
</script>

<style scoped>
.control-panel {
  @apply bg-bg-secondary p-6 border-r border-white/5 overflow-y-auto;
}

.api-input {
  @apply w-full bg-bg-card border border-white/10 rounded-lg p-3 text-white text-sm mb-3;
}

.api-input::placeholder {
  @apply text-gray-400;
}

.status-item {
  @apply flex justify-between py-2 border-b border-white/5;
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
</style>
