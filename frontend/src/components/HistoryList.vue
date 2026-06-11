<template>
  <div class="history-section">
    <div class="section-title">历史记录</div>
    <div class="history-list">
      <div
        v-for="item in history"
        :key="item.filename"
        class="history-item"
        @click="$emit('select', item)"
      >
        <div class="game-id">{{ item.game_id }}</div>
        <div class="game-result">
          <span :class="item.winner.includes('狼人') ? 'winner-wolf' : 'winner-good'">
            {{ item.winner }}
          </span>
          · {{ item.days }}天 · {{ item.players }}人
        </div>
      </div>
      <div v-if="history.length === 0" class="text-center text-gray-400 text-sm py-4">
        暂无历史记录
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  history: {
    type: Array,
    default: () => []
  }
})

defineEmits(['select'])
</script>

<style scoped>
.history-section {
  @apply mt-3;
}

.history-list {
  @apply max-h-48 overflow-y-auto;
}

.history-item {
  @apply bg-bg-card rounded-lg p-2 mb-1.5 cursor-pointer transition-all border border-transparent;
}

.history-item:hover {
  @apply border-accent-gold;
  transform: translateX(5px);
}

.game-id {
  @apply text-xs text-gray-400;
}

.game-result {
  @apply text-sm mt-1;
}

.winner-wolf {
  @apply text-accent-red;
}

.winner-good {
  @apply text-accent-green;
}
</style>
