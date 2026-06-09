<template>
  <div :class="['log-entry', logClass]">
    <span class="log-time">{{ formattedTime }}</span>
    <span class="log-phase">{{ log?.phase || '' }}</span>
    <div class="log-content">{{ log?.content }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  log: {
    type: Object,
    default: () => ({})
  }
})

const formattedTime = computed(() => {
  if (!props.log?.timestamp) return ''
  return new Date(props.log.timestamp).toLocaleTimeString()
})

const logClass = computed(() => {
  if (props.log?.hidden) return 'hidden-info'
  
  const type = (props.log?.type || '').toLowerCase()
  if (type.includes('kill')) return 'action-kill'
  if (type.includes('save')) return 'action-save'
  if (type.includes('check') || type.includes('seer')) return 'action-check'
  if (type.includes('vote')) return 'action-vote'
  if (type.includes('speak') || type.includes('发言')) return 'action-speak'
  if (type.includes('game')) return 'action-game'
  return ''
})
</script>

<style scoped>
.log-time {
  @apply text-xs text-gray-400 mr-2;
}

.log-phase {
  @apply text-xs px-2 py-0.5 rounded-full bg-white/10 mr-2;
}

.log-content {
  @apply mt-1;
}

.hidden-info {
  @apply opacity-60 border-l-gray-400;
}

.action-kill {
  @apply border-l-accent-red;
}

.action-save {
  @apply border-l-accent-green;
}

.action-check {
  @apply border-l-accent-blue;
}

.action-vote {
  @apply border-l-accent-orange;
}

.action-speak {
  @apply border-l-accent-purple;
}

.action-game {
  @apply border-l-accent-gold bg-accent-gold/10;
}
</style>
