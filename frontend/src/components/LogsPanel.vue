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
    <div ref="logsContainer" class="logs-container">
      <LogEntry
        v-for="(log, index) in filteredLogs"
        :key="index"
        :log="log"
      />
      <div v-if="logs.length === 0" class="text-center text-gray-400 py-10">
        {{ emptyMessage }}
      </div>
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
  }
})

defineEmits(['filterChange'])

const logsContainer = ref(null)

const filters = [
  { label: '全部', value: 'all' },
  { label: '行动', value: 'action' },
  { label: '发言', value: 'speak' },
  { label: '投票', value: 'vote' }
]

const filteredLogs = computed(() => {
  if (props.currentFilter === 'all') {
    return props.logs
  }
  
  return props.logs.filter(log => {
    const type = log.type || ''
    if (props.currentFilter === 'action') {
      return type.includes('ACTION') || type.includes('KILL') || type.includes('SEER') ||
             type.includes('save') || type.includes('check')
    }
    if (props.currentFilter === 'speak') {
      return type.includes('SPEECH') || type.includes('发言')
    }
    if (props.currentFilter === 'vote') {
      return type.includes('VOTE') || type.includes('投票')
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
  @apply flex-1 p-5 bg-bg-primary overflow-y-auto;
}

.logs-header {
  @apply flex justify-between items-center mb-4;
}

.logs-filter {
  @apply flex gap-2;
}

.filter-btn {
  @apply px-3 py-1 rounded-full border-none text-xs cursor-pointer transition-all;
  @apply bg-bg-card text-gray-400;
}

.filter-btn.active {
  @apply bg-accent-gold text-bg-primary;
}

.logs-container {
  @apply bg-bg-secondary rounded-xl p-4 h-[calc(100%-50px)] overflow-y-auto;
}
</style>
