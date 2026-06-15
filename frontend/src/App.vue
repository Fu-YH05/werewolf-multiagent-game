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

    <!-- 白天暖光叠加层 -->
    <div v-if="isDaytime" class="daytime-overlay"></div>
    
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
    <div class="main-container" :style="{
      gridTemplateColumns: `${leftCollapsed ? '40px' : '260px'} 1fr ${rightCollapsed ? '40px' : '280px'}`
    }">
      <!-- 左侧控制面板 -->
      <aside class="sidebar-left" :class="{ collapsed: leftCollapsed }">
        <div class="sidebar-inner" v-show="!leftCollapsed">
          <ControlPanel
            ref="controlPanelRef"
            :game-id="currentGameId"
            :phase="phase"
            :alive-count="alivePlayers.length"
            :total-players="9"
            :duration="duration"
            :is-running="isRunning"
            :is-paused="isPaused"
            :viewing-replay="viewingReplay"
            :has-live-game="!!savedLiveState"
            @start="startGame"
            @toggle-pause="togglePause"
            @stop="stopGame"
            @show-replay="showReplayModal = true"
          />

          <HistoryList
            :history="history"
            @select="loadReplay"
          />
        </div>
        <button class="collapse-btn collapse-left" @click="leftCollapsed = !leftCollapsed" :title="leftCollapsed ? '展开左侧' : '收起左侧'">
          {{ leftCollapsed ? '▶' : '◀' }}
        </button>
      </aside>
      
      <!-- 中间游戏区域 -->
      <main class="game-area">
        <div class="game-area-layout">
          <!-- 游戏时间线（侧边竖条） -->
          <TimelineStrip
            v-if="logs.length > 0"
            :logs="logs"
            :current-day="day"
            :active-index="highlightLogIndex"
            @scroll-to-log="onTimelineScroll"
          />
          <div class="game-area-content">
        <div v-if="viewingReplay" class="replay-banner">
          <span>📽️ 观看回放 — {{ currentGameId }}</span>
          <span v-if="savedLiveState" class="replay-banner-actions">
            <span class="separator">|</span>
            <button class="replay-return-btn" @click="returnToLive">🔙 返回直播</button>
          </span>
        </div>

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
              :is-human-mode="isHumanMode"
              :speeches="playerSpeeches[player.id] || []"
              :is-speaking="speakingPlayerId === player.id"
              @annotate="handleAnnotate"
            />
          </div>
        </div>
        
        <!-- 投票面板按钮 -->
        <div v-if="voteResults.length > 0" class="vote-toggle-area">
          <button
            class="vote-toggle-btn"
            @click="showVotePanel = !showVotePanel"
          >
            <span>🗳️ 投票记录 (第{{ voteResults[voteResults.length - 1]?.day }}天)</span>
            <span class="ml-2 text-xs">{{ showVotePanel ? '🔽 收起' : '🔼 展开' }}</span>
          </button>
          <button
            class="vote-network-btn"
            @click="showVoteNetwork = !showVoteNetwork"
            title="投票关系网络图"
          >
            <span>{{ showVoteNetwork ? '✕ 关闭' : '🔗 关系网络' }}</span>
          </button>
        </div>
        <VotePanel v-if="showVotePanel && voteResults.length > 0" :vote-results="voteResults" />

        <!-- 分析工具按钮 -->
        <div v-if="logs.length > 0" class="analysis-btn-area">
          <button
            class="analysis-btn"
            @click="showEliminationModal = !showEliminationModal"
            title="玩家存活淘汰树"
          >
            <span>{{ showEliminationModal ? '✕' : '🌳' }} 存活树</span>
          </button>
          <button
            class="analysis-btn"
            @click="showEmotionModal = !showEmotionModal"
            title="发言情绪热力图"
          >
            <span>{{ showEmotionModal ? '✕' : '🔥' }} 情绪图</span>
          </button>
        </div>
        
        <!-- 日志面板 -->
        <LogsPanel
          ref="logsPanelRef"
          :logs="logs"
          :current-filter="currentFilter"
          :empty-message="emptyMessage"
          :is-human-mode="isHumanMode"
          :is-daytime="isDaytime"
          :game-id="currentGameId"
          :highlight-log-index="highlightLogIndex"
          @filter-change="currentFilter = $event"
        />
          </div><!-- .game-area-content -->
        </div><!-- .game-area-layout -->
      </main>

      <!-- 右侧信息面板 -->
      <aside class="sidebar-right" :class="{ collapsed: rightCollapsed }">
        <button class="collapse-btn collapse-right" @click="rightCollapsed = !rightCollapsed" :title="rightCollapsed ? '展开右侧' : '收起右侧'">
          {{ rightCollapsed ? '◀' : '▶' }}
        </button>
        <div class="sidebar-inner" v-show="!rightCollapsed">
          <Leaderboard :leaderboard="leaderboard" />
          <RolesInfo />
        </div>
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
    
    <!-- 投票关系网络图弹窗 -->
    <VoteNetworkModal
      :visible="showVoteNetwork"
      :logs="logs"
      :players="players"
      @close="showVoteNetwork = false"
    />

    <!-- 玩家存活淘汰树弹窗 -->
    <div v-if="showEliminationModal" class="modal-overlay" @click.self="showEliminationModal = false">
      <div class="modal-content modal-compact">
        <div class="modal-header">
          <h3 class="modal-title">🌳 玩家存活淘汰树</h3>
          <button class="modal-close" @click="showEliminationModal = false">&times;</button>
        </div>
        <div class="modal-body-analysis">
          <EliminationTree :logs="logs" :players="players" :expanded="true" />
        </div>
      </div>
    </div>

    <!-- 发言情绪热力图弹窗 -->
    <div v-if="showEmotionModal" class="modal-overlay" @click.self="showEmotionModal = false">
      <div class="modal-content modal-compact">
        <div class="modal-header">
          <h3 class="modal-title">🔥 发言情绪热力图</h3>
          <button class="modal-close" @click="showEmotionModal = false">&times;</button>
        </div>
        <div class="modal-body-analysis">
          <EmotionHeatmap :logs="logs" :players="players" :expanded="true" />
        </div>
      </div>
    </div>

    <!-- 人类玩家操作面板 -->
    <HumanActionPanel
      :visible="!!humanPendingAction"
      :action="humanPendingAction"
      :game-id="currentGameId"
      @submitted="onHumanSubmitted"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { gameApi } from './services/api'
import ControlPanel from './components/ControlPanel.vue'
import GameInfoBar from './components/GameInfoBar.vue'
import PlayerCard from './components/PlayerCard.vue'
import LogsPanel from './components/LogsPanel.vue'
import Leaderboard from './components/Leaderboard.vue'
import HistoryList from './components/HistoryList.vue'
import RolesInfo from './components/RolesInfo.vue'
import VotePanel from './components/VotePanel.vue'
import HumanActionPanel from './components/HumanActionPanel.vue'

// 分析看板组件
import TimelineStrip from './components/analysis/TimelineStrip.vue'
import VoteNetworkModal from './components/analysis/VoteNetworkModal.vue'
import EliminationTree from './components/analysis/EliminationTree.vue'
import EmotionHeatmap from './components/analysis/EmotionHeatmap.vue'

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
const humanPendingAction = ref(null)
const isHumanMode = ref(false)
const showVotePanel = ref(false)
const annotations = ref({})
const showVoteNetwork = ref(false)
const showEliminationModal = ref(false)
const showEmotionModal = ref(false)
const highlightLogIndex = ref(-1)
const logsPanelRef = ref(null)

/** 时间线点击：跳转到对应日志并高亮 */
function onTimelineScroll(logIndex) {
  highlightLogIndex.value = logIndex
  // 用 setTimeout 重置高亮，触发动画重播
  setTimeout(() => { highlightLogIndex.value = -1 }, 1500)
  // 让 LogsPanel 滚动到对应位置
  if (logsPanelRef.value?.scrollToLog) {
    logsPanelRef.value.scrollToLog(logIndex)
  }
}

// 回放/直播分离状态
const viewingReplay = ref(false)
const savedLiveState = ref(null)

// 侧栏折叠状态
const leftCollapsed = ref(false)
const rightCollapsed = ref(false)

// 白天阶段检测
const dayPhases = ['天亮请睁眼', '自由发言', '放逐投票', '游戏结束']
const isDaytime = computed(() => dayPhases.includes(phase.value))

// ====================================================================
// 音频播报系统：状态机驱动的串行语音队列
// ====================================================================
// 每一条 SPEECH 日志经历：
//   日志出现 → audioPlayQueue.push({log_id, urls:[], text, ...})
//      ├─ 有 audio_url？→ urls 填好 → 轮到队列头部时播放
//      └─ 无 audio_url？→ 启动 3 秒超时
//            ├─ 3 秒内 audio_url 到达 → 更新 urls → 正常播放 edge-tts
//            └─ 3 秒超时 → fallback=true → 播放浏览器 TTS（且 edge-tts 后来到的丢弃）
// 队列处理器（processAudioQueue）：串行，一次只播一个，播完才处理下一个
// ====================================================================
const speakingPlayerId = ref(null)
const audioPlayQueue = []             // 音频队列（FIFO，元素带状态）
let isAudioPlaying = false
let currentAudio = null               // 当前正在播放的 Audio 元素
const playedLogIds = new Set()        // 已播完的 log_id（任何方式）
const fallbackLogIds = new Set()      // 已降级到浏览器 TTS 的 log_id
const pendingTimers = {}              // {log_id: setTimeoutId} - 降级超时

/** 重置音频队列：停止播放、清空队列、取消所有定时器 */
function resetAudioQueue() {
  // 停止当前播放的音频
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }
  // 停止浏览器 TTS
  if (window.speechSynthesis) {
    window.speechSynthesis.cancel()
  }
  // 清空队列
  audioPlayQueue.length = 0
  isAudioPlaying = false
  speakingPlayerId.value = null
  // 清空状态集合
  playedLogIds.clear()
  fallbackLogIds.clear()
  // 取消所有降级定时器
  for (const key of Object.keys(pendingTimers)) {
    clearTimeout(pendingTimers[key])
    delete pendingTimers[key]
  }
}

/** 向队列中添加或更新一条语音条目 */
function enqueueSpeechLog(log) {
  const logId = log.log_id
  if (!logId || playedLogIds.has(logId) || fallbackLogIds.has(logId)) return

  // 提取发言文本
  const text = cleanSpeechText(log.content || '')
  if (!text) return

  const audioUrls = log.audio_url ? log.audio_url.split(',').filter(Boolean) : []

  // 查找是否已在队列中
  let item = audioPlayQueue.find(i => i.logId === logId)
  if (item) {
    // 更新 urls（可能刚被后台线程回填）
    if (audioUrls.length && !item.audioUrls.length) {
      item.audioUrls = audioUrls
      // 有音频了，取消降级定时器
      if (pendingTimers[logId]) {
        clearTimeout(pendingTimers[logId])
        delete pendingTimers[logId]
      }
    }
    return
  }

  // 新条目，推入队尾
  item = {
    logId,
    playerId: log.player_id,
    audioUrls: [...audioUrls],
    text,
    day: log.day || 0,
    phase: log.phase || '',
    fallbackReady: false,   // 3秒超时后设为 true
  }

  // 检查发言是否已过时（游戏已进入下一天）
  if (day.value && item.day < day.value) {
    playedLogIds.add(logId)
    return
  }

  audioPlayQueue.push(item)

  // 如果没有音频，设 3 秒降级超时
  if (!audioUrls.length && !pendingTimers[logId]) {
    pendingTimers[logId] = setTimeout(() => {
      // 超时触发降级
      const queued = audioPlayQueue.find(i => i.logId === logId)
      if (queued && !playedLogIds.has(logId) && !queued.audioUrls.length) {
        queued.fallbackReady = true
        delete pendingTimers[logId]
        processAudioQueue()  // 触发队列处理（可能当前正在播别的，但播完这条会被处理）
      }
    }, 3000)
  }

  processAudioQueue()
}

/** 串行队列处理器：一次只播一条 */
function processAudioQueue() {
  if (isAudioPlaying || audioPlayQueue.length === 0) return

  const item = audioPlayQueue[0]  // peek

  // 检查是否过时（游戏已进入下一天），过时则跳过
  if (day.value && item.day < day.value) {
    finishAudioItem(item.logId)
    return
  }

  isAudioPlaying = true
  speakingPlayerId.value = item.playerId

  // 情况 A：有 edge-tts 音频 → 播 URL 序列
  if (item.audioUrls.length > 0) {
    playUrlSequence([...item.audioUrls], () => finishAudioItem(item.logId))
    return
  }

  // 情况 B：降级超时已到 → 浏览器 TTS
  if (item.fallbackReady || fallbackLogIds.has(item.logId)) {
    fallbackLogIds.add(item.logId)
    playBrowserFallback(item)
    // 浏览器 TTS 播放结束由 onend 回调触发 finishAudioItem
    return
  }

  // 情况 C：音频还没到、降级还没触发 → 等 200ms 再检查
  isAudioPlaying = false
  speakingPlayerId.value = null
  setTimeout(processAudioQueue, 200)
}

/** 播放 URL 序列（多段音频依次播完） */
function playUrlSequence(urls, onDone) {
  if (urls.length === 0) { onDone(); return }
  const url = urls.shift()
  const audio = new Audio(url)
  currentAudio = audio
  audio.onended = () => { if (currentAudio === audio) currentAudio = null; playUrlSequence(urls, onDone) }
  audio.onerror = () => { if (currentAudio === audio) currentAudio = null; playUrlSequence(urls, onDone) }
  audio.play().catch(() => { if (currentAudio === audio) currentAudio = null; playUrlSequence(urls, onDone) })
}

/** 完成一条语音（无论何种方式） */
function finishAudioItem(logId) {
  playedLogIds.add(logId)
  if (pendingTimers[logId]) {
    clearTimeout(pendingTimers[logId])
    delete pendingTimers[logId]
  }
  audioPlayQueue.shift()  // 出队
  isAudioPlaying = false
  speakingPlayerId.value = null
  processAudioQueue()
}

/** 监听日志变化：新发言入队 */
watch(() => logs.value, (newLogs) => {
  if (viewingReplay.value) return
  for (const log of newLogs) {
    // SPEECH 类型：玩家发言
    if (log?.type === 'SPEECH' && log.player_id) {
      enqueueSpeechLog(log)
    }
    // 旁白类型（有 audio_url 且无 player_id 的系统广播）
    const narratorTypes = ['GAME_START', 'NIGHT_START', 'WOLF_TURN', 'WITCH_TURN', 'SEER_TURN', 'ANNOUNCE', 'DISCUSS_START', 'VOTE_START', 'GAME_OVER']
    if (narratorTypes.includes(log?.type) && log.audio_url) {
      enqueueSpeechLog({ ...log, player_id: 'NARRATOR' })
    }
  }
})

// ====================================================================
// 浏览器语音合成（降级方案）
// ====================================================================
const synth = window.speechSynthesis
let playerVoices = {}
function initVoices() {
  const voices = synth.getVoices()
  const zhVoices = voices.filter(v => v.lang.startsWith('zh'))
  if (zhVoices.length === 0) return
  const players = ['P1','P2','P3','P4','P5','P6','P7','P8','P9']
  players.forEach((pid, i) => {
    playerVoices[pid] = zhVoices[i % zhVoices.length]
  })
}
if (synth) {
  initVoices()
  synth.onvoiceschanged = initVoices
}

function playBrowserFallback(item) {
  if (!synth || !item.text) return
  const utterance = new SpeechSynthesisUtterance(item.text)
  utterance.lang = 'zh-CN'
  utterance.rate = 1.0
  utterance.pitch = 1.0
  if (playerVoices[item.playerId]) {
    utterance.voice = playerVoices[item.playerId]
  }
  utterance.onstart = () => { speakingPlayerId.value = item.playerId }
  utterance.onend = () => { finishAudioItem(item.logId) }
  utterance.onerror = () => { finishAudioItem(item.logId) }
  synth.speak(utterance)
}

/** 清理发言文本前缀 */
function cleanSpeechText(content) {
  if (!content) return ''
  // 去掉 "发言:" 前缀
  const match = content.match(/发言[:：]\s*(.*)/)
  let text = match ? match[1].trim() : content.trim()
  // 移除 XML/HTML 标签（<VOTE> <KILL> 等）
  text = text.replace(/<[^>]+>/g, '')
  // 移除 Markdown 符号和括号
  text = text.replace(/[#*_~`\[\]()>|【】]/g, '')
  // 压缩空白
  text = text.replace(/\s+/g, ' ').trim()
  return text
}

const emptyMessage = computed(() => {
  if (viewingReplay.value) return '观看回放中'
  return isRunning.value
    ? '等待游戏进行中...'
    : '点击"开始游戏"按钮开始新的对局'
})

// 计算属性
const alivePlayers = computed(() => {
  return players.value.filter(p => p.is_alive)
})

const playerSpeeches = computed(() => {
  const map = {}
  const speechLogs = logs.value.filter(l => l.type === 'SPEECH')
  // 从后遍历取最近 5 条
  for (let i = speechLogs.length - 1; i >= 0; i--) {
    const log = speechLogs[i]
    const pid = log.player_id
    if (!pid) continue
    if (!map[pid]) map[pid] = []
    if (map[pid].length < 5) {
      map[pid].push({ day: log.day, phase: log.phase, content: log.content })
    }
  }
  return map
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

async function startGame(humanPlayerIndex = -1, stepDelay = 1.5) {
  // 重置音频队列（清除上局残留）
  resetAudioQueue()

  // 如果正在看回放，清除回放状态
  viewingReplay.value = false
  savedLiveState.value = null

  // 停止可能还在运行的上局游戏（前端 isRunning 可能已不同步）
  try {
    await gameApi.stopGame()
  } catch (e) {
    console.error('Failed to stop current game:', e)
  }
  stopPolling()  // 重置 isRunning 为 false
  // 等待服务器确认游戏已完全停止（最多等 5 秒）
  for (let i = 0; i < 25; i++) {
    try {
      const statusResp = await gameApi.getStatus()
      if (!statusResp.data.running) break
    } catch (_) {}
    await new Promise(r => setTimeout(r, 200))
  }

  isLoading.value = true

  try {
    const apiKey = controlPanelRef.value?.apiKey || ''
    const useDoubaoTTS = controlPanelRef.value?.useDoubaoTTS || false
    const doubaoAppid = controlPanelRef.value?.doubaoAppid || ''
    const doubaoApiKey = controlPanelRef.value?.doubaoApiKey || ''
    isHumanMode.value = humanPlayerIndex >= 0
    console.log('Starting game with API key:', apiKey ? `${apiKey.substring(0, 10)}...` : 'None', 'Human:', humanPlayerIndex, 'Delay:', stepDelay, 'DoubaoTTS:', useDoubaoTTS)
    
    const response = await gameApi.startGame(apiKey, humanPlayerIndex, stepDelay, useDoubaoTTS, doubaoAppid, doubaoApiKey)
    const data = response.data
    
    if (data.error) {
      alert(`游戏启动失败: ${data.error}`)
      return
    }
    
    currentGameId.value = data.game_id
    gameState.value = data
    players.value = mergeAnnotations(data.players || [])
    logs.value = []
    voteResults.value = []
    humanPendingAction.value = null
    showVotePanel.value = false
    isRunning.value = true
    gameStartTime.value = data.start_time ? new Date(data.start_time).getTime() : Date.now()

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
      players.value = mergeAnnotations(data.players || [])
      logs.value = data.logs || []
      voteResults.value = data.vote_results || []
      
      // 检查人类玩家待处理操作
      if (data.human_pending_action) {
        humanPendingAction.value = data.human_pending_action
      }
      
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

async function stopGame() {
  isLoading.value = true
  try {
    await gameApi.stopGame()
    console.log('Game stop requested')
  } catch (error) {
    console.error('Failed to stop game:', error)
  } finally {
    isLoading.value = false
  }
  // 立即重置音频队列（停止播放、清空队列、取消定时器）
  resetAudioQueue()
  stopPolling()  // 前端立即停止，不再询问该局
}

function togglePause() {
  isPaused.value = !isPaused.value
  if (isPaused.value) {
    // 暂停时也暂停计时器
    if (durationInterval.value) {
      clearInterval(durationInterval.value)
      durationInterval.value = null
    }
  } else {
    // 恢复时恢复计时器
    startDurationTimer()
  }
}

async function loadReplay(item) {
  showReplayModal.value = false
  isLoading.value = true

  // 保存当前直播状态（如果有），方便返回
  if (!savedLiveState.value && currentGameId.value) {
    savedLiveState.value = {
      gameId: currentGameId.value,
      gameState: gameState.value ? { ...gameState.value } : null,
      players: players.value ? [...players.value] : [],
      logs: logs.value ? [...logs.value] : [],
      voteResults: voteResults.value ? [...voteResults.value] : [],
      isRunning: isRunning.value,
      gameStartTime: gameStartTime.value
    }
  }

  // 停止直播轮询（回放不轮询）
  stopPolling()

  try {
    const response = await gameApi.getReplay(item.filename)
    const data = response.data

    currentGameId.value = data.game_id
    gameState.value = data

    // 转换players数据格式（后端返回的是字典）
    if (data.players && typeof data.players === 'object') {
      players.value = mergeAnnotations(Object.entries(data.players).map(([id, p]) => ({
        id: id,
        name: p.name,
        role: p.role,
        is_alive: p.is_alive
      })))
    } else {
      players.value = mergeAnnotations(data.players || [])
    }

    logs.value = data.logs || []
    voteResults.value = data.vote_results || []
    isRunning.value = false
    viewingReplay.value = true

    console.log('Replay loaded:', data)
  } catch (error) {
    console.error('Failed to load replay:', error)
    alert('加载回放失败')
  } finally {
    isLoading.value = false
  }
}

function returnToLive() {
  if (!savedLiveState.value) return
  const s = savedLiveState.value
  currentGameId.value = s.gameId
  gameState.value = s.gameState
  players.value = s.players
  logs.value = s.logs
  voteResults.value = s.voteResults
  isRunning.value = s.isRunning
  gameStartTime.value = s.gameStartTime || Date.now()
  viewingReplay.value = false
  savedLiveState.value = null

  // 如果直播游戏还在进行，恢复轮询
  if (s.isRunning) {
    startPolling()
    startDurationTimer()
  }

  console.log('Returned to live game:', currentGameId.value)
}

function onHumanSubmitted(decision) {
  console.log('人类玩家操作已提交:', decision)
  humanPendingAction.value = null
}

function handleAnnotate({ playerId, role }) {
  if (annotations.value[playerId] === role) {
    // 取消标注
    delete annotations.value[playerId]
  } else {
    annotations.value[playerId] = role
  }
  // 触发响应式更新
  annotations.value = { ...annotations.value }
  // 将标注合并到 players 中
  players.value = players.value.map(p => ({
    ...p,
    annotation: annotations.value[p.id] || null
  }))
}

function mergeAnnotations(dataPlayers) {
  return (dataPlayers || []).map(p => ({
    ...p,
    annotation: annotations.value[p.id] || null
  }))
}

// 生命周期
onMounted(async () => {
  generateStars()
  loadHistory()
  loadLeaderboard()

  // 刷新恢复：尝试重新连接到服务器上正在运行的游戏
  try {
    const healthResp = await gameApi.checkHealth()
    const health = healthResp.data
    console.log('Server health on mount:', health)
    if (health.game?.running && health.game?.game_id) {
      currentGameId.value = health.game.game_id
      isRunning.value = true
      isPaused.value = false

      // 立即拉取当前状态
      const stateResp = await gameApi.getGameState(health.game.game_id)
      const state = stateResp.data
      if (state && !state.error) {
        gameState.value = state
        players.value = mergeAnnotations(state.players || [])
        logs.value = state.logs || []
        voteResults.value = state.vote_results || []
        // 使用服务端的 start_time 让计时器从游戏实际开始时间算起
        gameStartTime.value = state.start_time ? new Date(state.start_time).getTime() : Date.now()
        console.log('Reattached to running game:', health.game.game_id,
          'start_time:', state.start_time,
          'elapsed:', Math.floor((Date.now() - gameStartTime.value) / 1000) + 's')
      } else {
        gameStartTime.value = Date.now()
      }
      startPolling()
      startDurationTimer()
    }
  } catch (e) {
    console.error('Failed to reattach to running game:', e)
  }
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
  @apply mx-4 mt-2 rounded-xl py-2 px-4 flex justify-between items-center;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.logo {
  @apply flex items-center gap-3;
}

.logo-icon {
  @apply text-3xl;
  animation: wolf-pulse 2s infinite;
}

@keyframes wolf-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.logo h1 {
  @apply text-lg font-bold;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  @apply text-xs text-gray-400;
}

.main-container {
  @apply grid h-[calc(100vh-72px)] px-4 pb-2;
  grid-template-columns: 260px 1fr 280px;
  gap: 10px;
  transition: grid-template-columns 0.35s ease;
}

/* 白天暖光叠加层 */
.daytime-overlay {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: radial-gradient(ellipse at 50% 0%, rgba(255, 200, 100, 0.07) 0%, rgba(255, 180, 50, 0.03) 40%, transparent 70%);
  transition: opacity 0.5s ease;
}

.sidebar-left {
  @apply rounded-xl overflow-y-auto;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: row;
  overflow: hidden;
  transition: all 0.35s ease;
  position: relative;
}
.sidebar-left.collapsed {
  min-width: 0;
}
.sidebar-left .sidebar-inner {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  min-width: 0;
}

.game-area {
  @apply flex flex-col gap-2 overflow-hidden;
}

.players-panel {
  @apply rounded-xl p-3;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.players-grid {
  @apply grid gap-2;
  grid-template-columns: repeat(9, 1fr);
}

.vote-toggle-area {
  @apply flex justify-center flex-shrink-0;
}

.vote-network-btn {
  @apply px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200;
  background: rgba(168, 85, 247, 0.1);
  border: 1px solid rgba(168, 85, 247, 0.2);
  color: #c084fc;
  cursor: pointer;
  margin-left: 8px;
}

.vote-network-btn:hover {
  background: rgba(168, 85, 247, 0.2);
  border-color: rgba(168, 85, 247, 0.4);
  color: #d8b4fe;
}

/* 分析工具按钮 */
.analysis-btn-area {
  display: flex;
  justify-content: center;
  gap: 8px;
  flex-shrink: 0;
}

.analysis-btn {
  @apply px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200;
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.18);
  color: #86efac;
  cursor: pointer;
}

.analysis-btn:hover {
  background: rgba(34, 197, 94, 0.18);
  border-color: rgba(34, 197, 94, 0.35);
  color: #bbf7d0;
}

/* 紧凑模态框 */
.modal-compact {
  max-width: 600px !important;
  padding: 16px 20px !important;
}

.modal-body-analysis {
  max-height: 420px;
  overflow-y: auto;
}

/* 时间线布局 */
.game-area-layout {
  display: flex;
  gap: 4px;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.game-area-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
  min-width: 0;
}

.vote-toggle-btn {
  @apply px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-200;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #94a3b8;
  cursor: pointer;
}

.vote-toggle-btn:hover {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.35);
  color: #22c55e;
}

.sidebar-right {
  @apply rounded-xl overflow-y-auto;
  display: flex;
  flex-direction: row;
  gap: 0;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.35s ease;
  overflow: hidden;
  position: relative;
}
.sidebar-right .sidebar-inner {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 0;
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

.replay-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  background: rgba(250, 204, 21, 0.1);
  border: 1px solid rgba(250, 204, 21, 0.25);
  color: #fde68a;
  flex-shrink: 0;
}

.replay-banner-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.separator {
  opacity: 0.3;
}

.replay-return-btn {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
  padding: 3px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s;
}

.replay-return-btn:hover {
  background: rgba(34, 197, 94, 0.3);
  border-color: rgba(34, 197, 94, 0.5);
  color: #86efac;
}

/* 折叠按钮 */
.collapse-btn {
  flex-shrink: 0;
  width: 40px;
  background: rgba(255, 255, 255, 0.03);
  border: none;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  transition: all 0.2s ease;
  z-index: 2;
}
.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}
.collapse-left {
  border-left: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0 12px 12px 0;
}
.collapse-right {
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px 0 0 12px;
  order: -1;
}

.loading-overlay {
  @apply fixed inset-0 bg-black/80 z-50 flex items-center justify-center backdrop-blur-sm;
}

.loading-spinner {
  @apply w-16 h-16 border-4 border-accent-green border-t-transparent rounded-full animate-spin;
}

@media (max-width: 900px) {
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
