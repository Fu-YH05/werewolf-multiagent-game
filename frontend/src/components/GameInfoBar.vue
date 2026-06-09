<template>
  <div class="game-info-bar">
    <div class="phase-display">
      <div :class="['phase-icon', isNight ? 'phase-icon-night' : 'phase-icon-day']">
        {{ phaseIcon }}
      </div>
      <div class="phase-text">
        <h2 class="text-xl font-bold">{{ phase }}</h2>
        <p class="text-sm text-gray-400 mt-1">第 {{ day }} 天</p>
      </div>
    </div>
    <div v-if="winner" class="winner-badge animate-pulse-gold">
      🎉 {{ winner }}获胜!
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  phase: {
    type: String,
    default: '等待开始'
  },
  day: {
    type: Number,
    default: 1
  },
  winner: {
    type: String,
    default: null
  }
})

const isNight = computed(() => {
  return props.phase.includes('夜晚') || props.phase.includes('NIGHT')
})

const phaseIcon = computed(() => {
  if (props.phase.includes('游戏结束')) return '🏁'
  return isNight.value ? '🌙' : '☀️'
})
</script>

<style scoped>
.game-info-bar {
  @apply flex justify-between items-center p-5 bg-bg-secondary border-b border-white/5;
}

.phase-display {
  @apply flex items-center gap-4;
}

.phase-icon {
  @apply w-12 h-12 rounded-full flex items-center justify-center text-2xl;
}

.phase-icon-night {
  background: linear-gradient(135deg, #1e3a5f, #0f172a);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.phase-icon-day {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.3);
}

.winner-badge {
  @apply px-6 py-3 rounded-full font-bold text-lg text-bg-primary;
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}
</style>
