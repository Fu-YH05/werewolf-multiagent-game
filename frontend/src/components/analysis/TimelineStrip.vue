<template>
  <div class="timeline-strip">
    <div class="timeline-line"></div>
    <div class="timeline-dots" ref="dotContainer">
      <div
        v-for="(entry, i) in dotEntries"
        :key="i"
        :class="['timeline-dot-wrapper', { active: i === activeIndex }]"
        :style="{ top: entry.top + 'px' }"
        :title="entry.label"
        @click="$emit('scrollToLog', entry.logIndex)"
      >
        <div class="timeline-dot" :style="{ background: entry.color }"></div>
      </div>
      <!-- Day markers -->
      <div
        v-for="m in dayMarkers"
        :key="'day-' + m.day"
        class="day-marker"
        :style="{ top: m.top + 'px' }"
      >
        <span class="day-label">D{{ m.day }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  activeIndex: { type: Number, default: -1 },
  currentDay: { type: Number, default: 1 },
})

defineEmits(['scrollToLog'])

const dotContainer = ref(null)
const DOT_GAP = 6  // px gap between dots

// Color map matching LogEntry.vue
const TYPE_COLORS = {
  kill: '#ef4444',
  save: '#22c55e',
  check: '#3b82f6',
  vote: '#f59e0b',
  speech: '#a855f7',
  game: '#fbbf24',
  default: '#6b7280',
}

function getDotColor(log) {
  const type = (log.type || '').toLowerCase()
  if (type.includes('kill') || type.includes('death')) return TYPE_COLORS.kill
  if (type.includes('save')) return TYPE_COLORS.save
  if (type.includes('check') || type.includes('seer')) return TYPE_COLORS.check
  if (type.includes('vote') || type.includes('lynch')) return TYPE_COLORS.vote
  if (type.includes('speech') || type.includes('发言')) return TYPE_COLORS.speech
  if (type.includes('game') || type.includes('start') || type.includes('over')) return TYPE_COLORS.game
  return TYPE_COLORS.default
}

function getLabel(log) {
  const t = (log.type || '').toLowerCase()
  if (t.includes('speech')) return '发言: ' + (log.content || '').slice(0, 12)
  if (t.includes('vote')) return '投票: ' + (log.content || '').slice(0, 12)
  if (t.includes('lynch')) return '放逐: ' + (log.content || '').slice(0, 12)
  if (t.includes('kill')) return '击杀'
  if (t.includes('save')) return '救活'
  if (t.includes('check')) return '查验'
  if (t.includes('announce')) return (log.content || '').slice(0, 16)
  return (log.content || '').slice(0, 16)
}

const dayMarkers = computed(() => {
  const days = new Set()
  const markers = []
  let top = 0
  for (let i = 0; i < props.logs.length; i++) {
    const log = props.logs[i]
    const d = log.day || 1
    if (!days.has(d)) {
      days.add(d)
      markers.push({ day: d, top })
    }
    top += DOT_GAP
  }
  // plus some offset for last dot
  return markers
})

const dotEntries = computed(() => {
  let top = 0
  return props.logs.map((log, i) => {
    const entry = {
      logIndex: i,
      top,
      color: getDotColor(log),
      label: getLabel(log),
      day: log.day || 1,
    }
    top += DOT_GAP
    return entry
  })
})
</script>

<style scoped>
.timeline-strip {
  width: 36px;
  flex-shrink: 0;
  position: relative;
  margin-right: 2px;
}

.timeline-line {
  position: absolute;
  left: 17px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: linear-gradient(to bottom, rgba(255,255,255,0.08), rgba(255,255,255,0.2), rgba(255,255,255,0.08));
  border-radius: 1px;
}

.timeline-dots {
  position: relative;
  padding: 8px 0;
}

.timeline-dot-wrapper {
  position: absolute;
  left: 11px;
  width: 14px;
  height: 14px;
  cursor: pointer;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease;
}

.timeline-dot-wrapper:hover {
  transform: scale(1.5);
  z-index: 5;
}

.timeline-dot-wrapper.active .timeline-dot {
  box-shadow: 0 0 6px 2px rgba(255, 255, 255, 0.5);
}

.timeline-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  transition: all 0.15s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.timeline-dot-wrapper:hover .timeline-dot {
  width: 10px;
  height: 10px;
  box-shadow: 0 0 8px currentColor;
}

.day-marker {
  position: absolute;
  left: 0;
  z-index: 3;
  pointer-events: none;
}

.day-label {
  font-size: 7px;
  color: rgba(255, 255, 255, 0.3);
  background: rgba(0, 0, 0, 0.5);
  border-radius: 3px;
  padding: 1px 3px;
  white-space: nowrap;
  letter-spacing: 0.5px;
}
</style>
