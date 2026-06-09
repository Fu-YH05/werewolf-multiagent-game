import { ref, computed } from 'vue'

// 响应式状态
const currentGameId = ref(null)
const gameState = ref(null)
const logs = ref([])
const isRunning = ref(false)
const isPaused = ref(false)
const error = ref(null)
const gameStartTime = ref(null)

// 计算属性
const alivePlayers = computed(() => {
  if (!gameState.value?.players) return []
  return gameState.value.players.filter(p => p.is_alive)
})

const phase = computed(() => {
  return gameState.value?.phase || '等待开始'
})

const day = computed(() => {
  return gameState.value?.day || 1
})

const isGameOver = computed(() => {
  return gameState.value?.is_over || false
})

const winner = computed(() => {
  return gameState.value?.winner
})

// 方法
function updateGameState(state) {
  gameState.value = state
  if (state?.logs) {
    logs.value = state.logs
  }
}

function updateLogs(newLogs) {
  logs.value = newLogs
}

function setError(err) {
  error.value = err
}

function clearError() {
  error.value = null
}

function reset() {
  currentGameId.value = null
  gameState.value = null
  logs.value = []
  isRunning.value = false
  isPaused.value = false
  error.value = null
  gameStartTime.value = null
}

export function useGameStore() {
  return {
    // 状态
    currentGameId,
    gameState,
    logs,
    isRunning,
    isPaused,
    error,
    gameStartTime,
    
    // 计算属性
    alivePlayers,
    phase,
    day,
    isGameOver,
    winner,
    
    // 方法
    updateGameState,
    updateLogs,
    setError,
    clearError,
    reset
  }
}
