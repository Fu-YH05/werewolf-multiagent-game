<template>
  <div class="logs-panel" :class="{ daytime: isDaytime }" :style="{ height: panelHeight + 'px' }">
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
    <div ref="logsContainer" class="logs-scroll-viewport" :class="{ daytime: isDaytime }">
      <div v-if="displayLogs.length === 0" class="empty-logs">
        {{ emptyMessage }}
      </div>
      <template v-for="(entry, displayIdx) in displayLogsWithOrigIdx" :key="displayIdx">
        <LogEntry
          :ref="el => registerLogEntry(el, displayIdx)"
          :log="entry.log"
          :highlighted="entry.originalIndex === highlightLogIndex"
        />
      </template>
    </div>
    <div class="notes-header" @click="toggleNotes">
      <span class="notes-title">📝 {{ notesOpen ? '收起笔记' : '展开笔记' }}</span>
      <span class="notes-toggle">{{ notesOpen ? '▼' : '▲' }}</span>
    </div>
    <div
      v-if="notesOpen"
      class="divider-bar divider-bar-top"
      @mousedown="startResize('note', $event)"
    ></div>
    <textarea
      v-if="notesOpen"
      v-model="noteContent"
      class="notes-textarea"
      :class="{ daytime: isDaytime }"
      :style="{ height: noteHeight + 'px' }"
      placeholder="在此记录你的推理、怀疑和策略..."
    ></textarea>
    <div
      v-if="notesOpen"
      class="divider-bar divider-bar-bottom"
      @mousedown="startResize('panel', $event)"
    ></div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import LogEntry from './LogEntry.vue'

let props = defineProps({
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
  },
  isDaytime: {
    type: Boolean,
    default: false
  },
  gameId: {
    type: String,
    default: ''
  },
  highlightLogIndex: {
    type: Number,
    default: -1
  }
})

const logsContainer = ref(null)
const notesOpen = ref(false)
const noteContent = ref('')
const noteHeight = ref(160)
const panelHeight = ref(520)
const isResizing = ref(false)
const resizeStartY = ref(0)
const resizeTarget = ref('')
const resizeStartVal = ref(0)

// 从 localStorage 加载笔记数据和高度
const NOTE_KEY = computed(() => `werewolf_notes_${props.gameId || 'default'}`)
const savedNotes = localStorage.getItem(NOTE_KEY.value)
if (savedNotes) {
  noteContent.value = savedNotes
  notesOpen.value = true
}
const savedNoteH = localStorage.getItem('werewolf_notes_height')
if (savedNoteH) noteHeight.value = parseInt(savedNoteH, 10) || 160
const savedPanelH = localStorage.getItem('werewolf_panel_height')
if (savedPanelH) panelHeight.value = parseInt(savedPanelH, 10) || 520

// 切换 gameId 时切换笔记
watch(() => props.gameId, (newId) => {
  const key = `werewolf_notes_${newId || 'default'}`
  noteContent.value = localStorage.getItem(key) || ''
})

// 自动保存笔记到 localStorage
watch(noteContent, (val) => {
  localStorage.setItem(NOTE_KEY.value, val)
})

function toggleNotes() {
  notesOpen.value = !notesOpen.value
}

function startResize(target, event) {
  isResizing.value = true
  resizeTarget.value = target
  resizeStartY.value = event.clientY
  resizeStartVal.value = target === 'note' ? noteHeight.value : panelHeight.value
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

function onResize(e) {
  if (!isResizing.value) return
  const delta = resizeStartY.value - e.clientY
  if (resizeTarget.value === 'note') {
    // 顶部分割：调整日志/笔记划分，总大小不变
    const minNote = 60
    const maxNote = panelHeight.value - 120
    noteHeight.value = Math.max(minNote, Math.min(maxNote, resizeStartVal.value + delta))
  } else {
    // 底部分割：调整总面板大小
    panelHeight.value = Math.max(300, Math.min(1200, resizeStartVal.value - delta))
  }
}

function stopResize() {
  isResizing.value = false
  localStorage.setItem('werewolf_notes_height', noteHeight.value.toString())
  localStorage.setItem('werewolf_panel_height', panelHeight.value.toString())
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
}

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

// 带原始索引的展示日志（用于时间线跳转）
const displayLogsWithOrigIdx = computed(() => {
  return displayLogs.value.map(log => ({
    log,
    originalIndex: props.logs.indexOf(log),
  }))
})

// LogEntry 元素引用（用于跳转时计算滚动位置）
const logEntryRefs = {}
function registerLogEntry(el, displayIdx) {
  if (el) logEntryRefs[displayIdx] = el
}

/**
 * 滚动到指定原始日志索引位置并高亮
 * @param {number} originalIndex - 在完整 logs 数组中的索引
 */
function scrollToLog(originalIndex) {
  if (!logsContainer.value) return
  // 找到该日志对应的展示索引
  for (let i = 0; i < displayLogsWithOrigIdx.value.length; i++) {
    if (displayLogsWithOrigIdx.value[i].originalIndex === originalIndex) {
      const el = logEntryRefs[i]?.$el || logEntryRefs[i]
      if (el && el.scrollIntoView) {
        el.scrollIntoView({ block: 'center', behavior: 'smooth' })
      }
      break
    }
  }
}

defineExpose({ scrollToLog })

// 自动滚动到底部（未被高亮打断时）
watch(() => props.logs.length, async () => {
  await nextTick()
  if (logsContainer.value && props.highlightLogIndex < 0) {
    logsContainer.value.scrollTop = logsContainer.value.scrollHeight
  }
})

// 高亮索引变化时自动跳转
watch(() => props.highlightLogIndex, (idx) => {
  if (idx >= 0) scrollToLog(idx)
})
</script>

<style scoped>
.logs-panel {
  @apply flex flex-col p-3 bg-bg-primary;
  transition: background 0.5s ease;
  flex-shrink: 0;
  overflow: hidden;
}
.logs-panel.daytime {
  background: rgba(255, 240, 210, 0.06);
}

.logs-header {
  @apply flex justify-between items-center mb-2;
  flex-shrink: 0;
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
  flex: 1 1 0;
  min-height: 60px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  scroll-behavior: smooth;
}

.logs-scroll-viewport.daytime {
  background: rgba(255, 235, 200, 0.12);
  border-color: rgba(255, 220, 180, 0.15);
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
  height: 100%;
  min-height: 60px;
}

/* 拖拽分割条 */
.divider-bar {
  height: 5px;
  cursor: row-resize;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.04);
  transition: background 0.2s;
  flex-shrink: 0;
  position: relative;
}
.divider-bar:hover,
.divider-bar:active {
  background: rgba(34, 197, 94, 0.25);
}
.divider-bar::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 30px;
  height: 2px;
  border-radius: 1px;
  background: rgba(255, 255, 255, 0.15);
}
.divider-bar:hover::after {
  background: rgba(34, 197, 94, 0.5);
}
.divider-bar-top {
  margin: 4px 0;
}
.divider-bar-bottom {
  margin-top: 4px;
}

.notes-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
  flex-shrink: 0;
  margin-top: 4px;
}
.notes-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.notes-title {
  font-size: 12px;
  color: #94a3b8;
}

.notes-toggle {
  font-size: 10px;
  color: #64748b;
}

.notes-textarea {
  width: 100%;
  flex-shrink: 0;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 12px;
  line-height: 1.5;
  color: #cbd5e1;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.08);
  outline: none;
  transition: all 0.2s;
  font-family: inherit;
  box-sizing: border-box;
  resize: vertical;
}
.notes-textarea:focus {
  border-color: rgba(34, 197, 94, 0.3);
  background: rgba(0, 0, 0, 0.35);
}
.notes-textarea::placeholder {
  color: #475569;
}
.notes-textarea.daytime {
  background: rgba(255, 240, 210, 0.08);
  border-color: rgba(255, 220, 180, 0.1);
}
.notes-textarea.daytime:focus {
  border-color: rgba(255, 200, 100, 0.3);
  background: rgba(255, 240, 210, 0.12);
}
</style>
