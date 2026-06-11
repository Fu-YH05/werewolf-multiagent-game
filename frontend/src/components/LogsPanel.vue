<template>
  <div class="logs-panel">
    <div class="logs-header">
      <div class="section-title">游戏日志</div>
      <div class="logs-filter">
        <button
          v-for="filter in filters"
          :key="filter.value"
          :class="['filter-btn', currentFilter === filter.value ? 'active' : '']"
          @click="$emit('filterChange', filter.value)"
        >
          {{ filter.label }}
        </button>
      </div>
    </div>
    <div ref="logsContainer" class="logs-scroll-viewport">
      <div v-if="displayLogs.length === 0" class="empty-logs">
        {{ emptyMessage }}
      </div>
      <LogEntry
        v-for="(log, index) in displayLogs"
        :key="index"
        :log="log"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import LogEntry from './LogEntry.vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  },
  currentFilter: {
    type: String,
    default: 'all'
  },
  emptyMessage: {
    type: String,
    default: '点击"开始游戏"按钮开始新的对局'
  },
  isHumanMode: {
    type: Boolean,
    default: false
  }
})

defineEmits(['filterChange'])

const logsContainer = ref(null)

const filters = [
  { label: '全部', value: 'all' },
  { label: '发言', value: 'speak' },
  { label: '投票', value: 'vote' },
  { label: '公告', value: 'announce' }
]

const displayLogs = computed(() => {
  // 真人模式下先过滤隐藏日志
  let result = props.logs
  if (props.isHumanMode) {
    result = result.filter(log => !log.hidden)
  }
  
  // 再按类型筛选
  if (props.currentFilter === 'all') {
    return result
  }
  
  return result.filter(log => {
    const type = (log.type || '').toLowerCase()
    if (props.currentFilter === 'speak') {
      return type.includes('speech') || type.includes('发言')
    }
    if (props.currentFilter === 'vote') {
      return type.includes('vote') || type.includes('投票')
    }
    if (props.currentFilter === 'announce') {
      return type.includes('announce') || type.includes('game_start') || 
             type.includes('game_over') || type.includes('night_start') ||
             type.includes('day_start') || type.includes('lynch')
    }
    return true
  })
})

// 自动滚动到底部
watch(() => props.logs.length, async () => {
  await nextTick()
  if (logsContainer.value) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
})
</script>

<style scoped>
.logs-panel {
  @apply flex flex-col p-3 bg-bg-primary;
}

.logs-header {
  @apply flex justify-between items-center mb-2 flex-shrink-0;
}

.logs-filter {
  @apply flex gap-1.5;
}

.filter-btn {
  @apply px-3 py-1 rounded-full border-none text-xs cursor-pointer transition-all;
  @apply bg-bg-card text-gray-400;
}

.filter-btn:hover {
  @apply bg-white/10 text-white;
}

.filter-btn.active {
  @apply bg-accent-green/20 text-accent-green;
}

.logs-scroll-viewport {
  @apply overflow-y-auto overflow-x-hidden rounded-lg p-2;
  height: 320px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  scroll-behavior: smooth;
}

.logs-scroll-viewport::-webkit-scrollbar {
  width: 5px;
}

.logs-scroll-viewport::-webkit-scrollbar-track {
  background: transparent;
}

.logs-scroll-viewport::-webkit-scrollbar-thumb {
  @apply rounded-full;
  background: rgba(255, 255, 255, 0.15);
}

.logs-scroll-viewport::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.empty-logs {
  @apply flex items-center justify-center text-gray-400 text-sm;
  height: 280px;
}
</style>
