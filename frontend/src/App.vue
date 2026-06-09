<template>
  <div class="app">
    <!-- 星空背景 -->
    <div class="starfield">
      <div
        v-for="star in stars"
        :key="star.id"
        class="star"
        :style="{
          left: star.x + '%',
          top: star.y + '%',
          width: star.size + 'px',
          height: star.size + 'px',
          animationDelay: star.delay + 's',
          opacity: star.opacity
        }"
      ></div>
    </div>
    
    <!-- 头部 -->
    <header class="header">
      <div class="logo">
        <span class="logo-icon">🐺</span>
        <div>
          <h1>狼人杀多Agent对战平台</h1>
          <div class="subtitle">Multi-Agent Werewolf Game</div>
        </div>
      </div>
    </header>
    
    <!-- 主容器 -->
    <div class="main-container">
      <!-- 左侧控制面板 -->
      <aside class="sidebar-left">
        <ControlPanel
          ref="controlPanelRef"
          :game-id="currentGameId"
          :phase="phase"
          :alive-count="alivePlayers.length"
          :total-players="9"
          :duration="duration"
          :is-running="isRunning"
          :is-paused="isPaused"
          @start="startGame"
          @toggle-pause="togglePause"
          @show-replay="showReplayModal = true"
        />
        
        <HistoryList
          :history="history"
          @select="loadReplay"
        />
      </aside>
      
      <!-- 中间游戏区域 -->
      <main class="game-area">
        <GameInfoBar
          :phase="phase"
          :day="day"
          :winner="winner"
        />
        
        <!-- 玩家面板 -->
        <div class="players-panel">
          <div class="players-grid">
            <PlayerCard
              v-for="player in players"
              :key="player.id"
              :player="player"
              :show-role="isGameOver"
            />
          </div>
        </div>
        
        <!-- 投票面板 -->
        <VotePanel v-if="voteResults.length > 0" :vote-results="voteResults" />
        
        <!-- 日志面板 -->
        <LogsPanel
          :logs="logs"
          :current-filter="currentFilter"
          :empty-message="emptyMessage"
          @filter-change="currentFilter = $event"
        />
      </main>
      
      <!-- 右侧信息面板 -->
      <aside class="sidebar-right">
        <Leaderboard :leaderboard="leaderboard" />
        <RolesInfo />
      </aside>
    </div>
    
    <!-- 回放模态框 -->
    <div v-if="showReplayModal" class="modal-overlay" @click="showReplayModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">📺 选择回放</h3>
          <button class="modal-close" @click="showReplayModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div
            v-for="item in history"
            :key="item.filename"
            class="history-item"
            @click="loadReplay(item)"
          >
            <div class="game-id">{{ item.game_id }}</div>
            <div class="game-result">{{ item.winner }} · {{ item.days }}天</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 加载遮罩 -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-spinner"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { gameApi } from './services/api'
import ControlPanel from './components/ControlPanel.vue'
import GameInfoBar from './components/GameInfoBar.vue'
import PlayerCard from './components/PlayerCard.vue'
import LogsPanel from './components/LogsPanel.vue'
import Leaderboard from './components/Leaderboard.vue'
import HistoryList from './components/HistoryList.vue'
import RolesInfo from './components/RolesInfo.vue'
import VotePanel from './components/VotePanel.vue'

// 生成星空
const stars = ref([])

function generateStars() {
  const starCount = 150
  stars.value = Array.from({ length: starCount }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 2 + 1,
    delay: Math.random() * 3,
    opacity: Math.random() * 0.5 + 0.3
  }))
}

// 响应式状态
const controlPanelRef = ref(null)
const currentGameId = ref(null)
const players = ref([])
const logs = ref([])
const history = ref([])
const leaderboard = ref([])
const isRunning = ref(false)
const isPaused = ref(false)
const isLoading = ref(false)
const showReplayModal = ref(false)
const currentFilter = ref('all')
const gameStartTime = ref(null)
const durationInterval = ref(null)
const pollInterval = ref(null)
const duration = ref('0:00')
const voteResults = ref([])

const emptyMessage = computed(() => {
  return isRunning.value 
    ? '等待游戏进行中...' 
    : '点击"开始游戏"按钮开始新的对局'
})

// 计算属性
const alivePlayers = computed(() => {
  return players.value.filter(p => p.is_alive)
})

const phase = computed(() => {
  return gameState.value?.phase || '等待开始'
})

const day = computed(() => {
  return gameState.value?.day || 1
})

const winner = computed(() => {
  return gameState.value?.winner
})

const isGameOver = computed(() => {
  return gameState.value?.phase === '游戏结束' || gameState.value?.winner
})

const gameState = ref(null)

// 方法
async function checkHealth() {
  try {
    const response = await gameApi.checkHealth()
    console.log('Server health:', response.data)
  } catch (error) {
    console.error('Health check failed:', error)
  }
}

async function loadHistory() {
  try {
    const response = await gameApi.getHistory()
    history.value = response.data
  } catch (error) {
    console.error('Failed to load history:', error)
  }
}

async function loadLeaderboard() {
  try {
    const response = await gameApi.getLeaderboard()
    leaderboard.value = response.data
  } catch (error) {
    console.error('Failed to load leaderboard:', error)
  }
}

async function startGame() {
  isLoading.value = true
  
  try {
    const apiKey = controlPanelRef.value?.apiKey || ''
    console.log('Starting game with API key:', apiKey ? `${apiKey.substring(0, 10)}...` : 'None')
    
    const response = await gameApi.startGame(apiKey)
    const data = response.data
    
    if (data.error) {
      alert(`游戏启动失败: ${data.error}`)
      return
    }
    
    currentGameId.value = data.game_id
    gameState.value = data
    players.value = data.players || []
    logs.value = []
    voteResults.value = []
    isRunning.value = true
    gameStartTime.value = Date.now()
    
    // 开始轮询
    startPolling()
    startDurationTimer()
    
    console.log('Game started:', data)
  } catch (error) {
    console.error('Failed to start game:', error)
    alert(`游戏启动失败: ${error.message}`)
  } finally {
    isLoading.value = false
  }
}

function startPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
  }
  
  pollInterval.value = setInterval(async () => {
    if (!currentGameId.value || isPaused.value) return
    
    try {
      const response = await gameApi.getGameState(currentGameId.value)
      const data = response.data
      
      if (data.error) return
      
      gameState.value = data
      players.value = data.players || []
      logs.value = data.logs || []
      voteResults.value = data.vote_results || []
      
      if (data.is_over) {
        stopPolling()
      }
    } catch (error) {
      console.error('Poll error:', error)
    }
  }, 1000)
}

function stopPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value)
    pollInterval.value = null
  }
  if (durationInterval.value) {
    clearInterval(durationInterval.value)
    durationInterval.value = null
  }
  isRunning.value = false
}

function startDurationTimer() {
  if (durationInterval.value) {
    clearInterval(durationInterval.value)
  }
  
  durationInterval.value = setInterval(() => {
    if (!gameStartTime.value) return
    
    const elapsed = Math.floor((Date.now() - gameStartTime.value) / 1000)
    const minutes = Math.floor(elapsed / 60)
    const seconds = elapsed % 60
    duration.value = `${minutes}:${seconds.toString().padStart(2, '0')}`
  }, 1000)
}

function togglePause() {
  isPaused.value = !isPaused.value
}

async function loadReplay(item) {
  showReplayModal.value = false
  isLoading.value = true
  
  try {
    const response = await gameApi.getReplay(item.filename)
    const data = response.data
    
    currentGameId.value = data.game_id
    gameState.value = data
    
    // 转换players数据格式（后端返回的是字典）
    if (data.players && typeof data.players === 'object') {
      players.value = Object.entries(data.players).map(([id, p]) => ({
        id: id,
        name: p.name,
        role: p.role,
        is_alive: p.is_alive
      }))
    } else {
      players.value = data.players || []
    }
    
    logs.value = data.logs || []
    voteResults.value = data.vote_results || []
    isRunning.value = false
    
    console.log('Replay loaded:', data)
  } catch (error) {
    console.error('Failed to load replay:', error)
    alert('加载回放失败')
  } finally {
    isLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  generateStars()
  checkHealth()
  loadHistory()
  loadLeaderboard()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.app {
  @apply min-h-screen relative text-white;
}

.header {
  @apply mx-4 mt-4 rounded-xl p-5 flex justify-between items-center;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.logo {
  @apply flex items-center gap-4;
}

.logo-icon {
  @apply text-5xl;
  animation: wolf-pulse 2s infinite;
}

@keyframes wolf-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.logo h1 {
  @apply text-2xl font-bold;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  @apply text-xs text-gray-400 mt-1;
}

.main-container {
  @apply grid h-[calc(100vh-120px)] px-4 pb-4;
  grid-template-columns: 300px 1fr 320px;
  gap: 16px;
}

.sidebar-left {
  @apply rounded-xl p-6 overflow-y-auto;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.game-area {
  @apply flex flex-col gap-4;
}

.players-panel {
  @apply rounded-xl p-6;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.players-grid {
  @apply grid gap-4;
  grid-template-columns: repeat(9, 1fr);
}

.sidebar-right {
  @apply rounded-xl p-6 overflow-y-auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.modal-overlay {
  @apply fixed inset-0 bg-black/80 z-50 flex items-center justify-center backdrop-blur-sm;
}

.modal-content {
  @apply rounded-2xl p-8 max-w-2xl w-[90%] max-h-[80vh] overflow-y-auto;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.modal-header {
  @apply flex justify-between items-center mb-5;
}

.modal-title {
  @apply text-xl text-accent-green;
}

.modal-close {
  @apply bg-none border-none text-gray-400 text-3xl cursor-pointer hover:text-white;
}

.history-item {
  @apply bg-white/5 rounded-lg p-4 mb-3 cursor-pointer transition-all border border-transparent hover:border-accent-green/50;
}

.history-item:hover {
  @apply bg-white/10;
}

.loading-overlay {
  @apply fixed inset-0 bg-black/80 z-50 flex items-center justify-center backdrop-blur-sm;
}

.loading-spinner {
  @apply w-16 h-16 border-4 border-accent-green border-t-transparent rounded-full animate-spin;
}

@media (max-width: 1200px) {
  .main-container {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
  }
  
  .sidebar-left,
  .sidebar-right {
    @apply hidden;
  }
  
  .players-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
