<template>
  <transition name="panel-slide">
    <div v-if="visible" class="human-action-panel">
      <div class="action-card">
        <!-- 头部：角色和阶段信息 -->
        <div class="card-header">
          <div class="role-badge">
            <span class="role-icon">{{ roleIcon }}</span>
            <span class="role-name">{{ action?.role || '???' }}</span>
          </div>
          <div class="phase-info">
            <span>第 {{ action?.day || '?' }} 天</span>
            <span class="mx-2">·</span>
            <span>{{ phaseLabel }}</span>
          </div>
        </div>

        <!-- 标题 -->
        <h2 class="action-title">{{ action?.options?.title || '请等待...' }}</h2>
        <p v-if="action?.options?.hint" class="action-hint">{{ action.options.hint }}</p>

        <!-- 狼队夜间讨论 -->
        <div v-if="action?.options?.wolf_chat && action.options.wolf_chat.length > 0" class="wolf-chat-section">
          <div class="wolf-chat-header">🐺 狼队友讨论</div>
          <div
            v-for="msg in action.options.wolf_chat"
            :key="msg.player_id + msg.timestamp"
            class="wolf-chat-msg"
          >
            <span class="wolf-chat-name">{{ msg.player_name }}</span>
            <span class="wolf-chat-text">{{ msg.message }}</span>
          </div>
        </div>

        <!-- 玩家选择模式 (kill/seer/vote) -->
        <div v-if="action?.options?.type === 'player_select'" class="player-grid">
          <button
            v-for="player in action.options.players"
            :key="player.id"
            :disabled="submitting"
            class="player-option-btn"
            @click="submitDecision(player.id)"
          >
            <span class="player-avatar-sm">{{ player.name.charAt(0) }}</span>
            <span class="player-name-sm">{{ player.name }}</span>
            <span class="player-id-sm">{{ player.id }}</span>
            <span v-if="player.id === 'PASS'" class="skip-badge">弃权</span>
          </button>
        </div>

        <!-- 行动选择模式 (witch) -->
        <div v-if="action?.options?.type === 'action_select'" class="action-grid">
          <button
            v-for="opt in action.options.actions"
            :key="opt.id"
            :disabled="submitting"
            class="action-option-btn"
            :class="{ 'action-danger': opt.id.startsWith('poison_') }"
            @click="submitDecision(opt.id)"
          >
            {{ opt.name }}
          </button>
          <button
            v-if="action?.options?.can_skip"
            :disabled="submitting"
            class="action-option-btn skip-btn"
            @click="submitDecision('skip')"
          >
            ⏭️ 跳过
          </button>
        </div>

        <!-- 自由文本模式 (speak) -->
        <div v-if="action?.options?.type === 'free_text'" class="text-input-area">
          <div class="speech-input-row">
            <textarea
              v-model="textInput"
              :placeholder="action?.options?.placeholder || '输入你的发言...'"
              :disabled="submitting"
              class="speech-textarea"
              rows="3"
              @keydown.ctrl.enter="submitDecision(textInput)"
            ></textarea>
            <button
              class="mic-btn"
              :class="{ recording: isRecording }"
              :title="isRecording ? '点击停止' : '点击开始语音输入'"
              @mousedown.prevent="startRecording"
              @mouseup.prevent="stopRecording"
              @mouseleave.prevent="stopRecording"
              @touchstart.prevent="startRecording"
              @touchend.prevent="stopRecording"
            >
              <span v-if="isRecording" class="mic-pulse"></span>
              <span class="mic-icon">{{ isRecording ? '🔴' : '🎤' }}</span>
            </button>
          </div>
          <div v-if="recognitionError" class="mic-error">{{ recognitionError }}</div>
          <div v-if="isRecording" class="mic-status">🎙️ 录音中，请说话...</div>
          <button
            :disabled="submitting || !textInput.trim()"
            class="submit-speech-btn"
            @click="submitDecision(textInput)"
          >
            {{ submitting ? '提交中...' : '发送发言 (Ctrl+Enter)' }}
          </button>
        </div>

        <!-- 提交中状态 -->
        <div v-if="submitting" class="submitted-badge">
          <div class="loading-spinner"></div>
          <span>已提交，等待其他玩家...</span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { gameApi } from '../services/api'

const props = defineProps({
  visible: Boolean,
  action: Object,
  gameId: String,
})

const emit = defineEmits(['submitted'])

const textInput = ref('')
const submitting = ref(false)
const isRecording = ref(false)
const recognitionError = ref('')
let recognition = null

function initRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    recognitionError.value = '当前浏览器不支持语音输入，请使用 Chrome 或 Edge'
    return null
  }
  const r = new SpeechRecognition()
  r.lang = 'zh-CN'
  r.continuous = true
  r.interimResults = true
  r.maxAlternatives = 1
  r.onresult = (e) => {
    let finalText = ''
    let interimText = ''
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        finalText += e.results[i][0].transcript
      } else {
        interimText += e.results[i][0].transcript
      }
    }
    if (finalText) {
      textInput.value = (textInput.value + finalText).trim()
    }
  }
  r.onerror = (e) => {
    console.error('语音识别错误:', e.error)
    if (e.error === 'not-allowed') {
      recognitionError.value = '麦克风权限被拒绝，请在浏览器设置中允许'
    } else if (e.error === 'no-speech') {
      recognitionError.value = '未检测到语音，请重试'
    } else {
      recognitionError.value = `语音识别错误: ${e.error}`
    }
    isRecording.value = false
  }
  r.onend = () => {
    isRecording.value = false
  }
  return r
}

function startRecording() {
  recognitionError.value = ''
  if (!recognition) {
    recognition = initRecognition()
  }
  if (!recognition) return
  try {
    recognition.start()
    isRecording.value = true
  } catch (e) {
    // 可能已经在运行
    if (e.name !== 'InvalidStateError') {
      console.error('启动录音失败:', e)
    }
  }
}

function stopRecording() {
  if (recognition && isRecording.value) {
    recognition.stop()
    isRecording.value = false
  }
}

const roleIcon = computed(() => {
  const map = { '狼人': '🐺', '平民': '👤', '预言家': '🔮', '女巫': '🧪', '猎人': '🏹' }
  return map[props.action?.role] || '❓'
})

const phaseLabel = computed(() => {
  const map = {
    'NIGHT_START': '🌙 天黑请闭眼',
    'WOLF_KILL': '🐺 狼人刀人',
    'WITCH_ACT': '🧪 女巫行动',
    'SEER_ACT': '🔮 预言家查验',
    'HUNTER_CHECK': '🏹 猎人觉醒',
    'DAY_START': '☀️ 天亮了',
    'DISCUSS': '💬 自由发言',
    'VOTE': '🗳️ 放逐投票',
  }
  return map[props.action?.phase] || props.action?.phase || ''
})

// 重置输入
watch(() => props.action?.options?.type, () => {
  textInput.value = ''
  submitting.value = false
})

async function submitDecision(decision) {
  if (submitting.value || !props.gameId) return
  submitting.value = true

  try {
    await gameApi.submitHumanAction(props.gameId, decision)
    emit('submitted', decision)
    // 不重置 submitting，后端处理完会自动下发新状态
  } catch (error) {
    console.error('提交失败:', error)
    alert('操作提交失败，请重试')
    submitting.value = false
  }
}
</script>

<style scoped>
/* 底部浮动面板 — 不遮挡游戏界面 */
.human-action-panel {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 60;
  pointer-events: auto;
}

.action-card {
  width: 520px;
  max-height: 55vh;
  overflow-y: auto;
  padding: 1.5rem;
  background: rgba(15, 23, 42, 0.97);
  border: 1px solid rgba(34, 197, 94, 0.35);
  border-radius: 16px;
  box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.6), 0 0 40px rgba(34, 197, 94, 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.role-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.4);
  border-radius: 999px;
  padding: 0.2rem 0.85rem;
}

.role-icon { font-size: 1.3rem; }
.role-name { color: #22c55e; font-weight: 700; font-size: 1rem; }

.phase-info {
  color: #94a3b8;
  font-size: 0.8rem;
}

.action-title {
  color: white;
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 0.35rem;
  text-align: center;
}

.action-hint {
  color: #94a3b8;
  font-size: 0.8rem;
  text-align: center;
  margin-bottom: 1rem;
}

/* 玩家选择网格 */
.player-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.6rem;
}

.player-option-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  padding: 0.6rem 0.4rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}
.player-option-btn:hover:not(:disabled) {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.5);
  transform: translateY(-2px);
}
.player-option-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.player-avatar-sm {
  width: 36px; height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; font-weight: 700;
}
.player-name-sm { font-size: 0.8rem; font-weight: 600; }
.player-id-sm { font-size: 0.65rem; color: #94a3b8; }
.skip-badge {
  font-size: 0.65rem; padding: 0.1rem 0.4rem;
  background: rgba(148, 163, 184, 0.2); border-radius: 999px;
  color: #94a3b8;
}

/* 行动选择 */
.action-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.action-option-btn {
  padding: 0.7rem 0.85rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: white;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}
.action-option-btn:hover:not(:disabled) {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.4);
}
.action-option-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.action-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.4);
}
.skip-btn {
  background: rgba(148, 163, 184, 0.08);
  color: #94a3b8;
  text-align: center;
}

/* 狼队讨论 */
.wolf-chat-section {
  margin-bottom: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.18);
  border-radius: 10px;
}
.wolf-chat-header {
  font-size: 0.75rem;
  font-weight: 600;
  color: #a78bfa;
  margin-bottom: 0.4rem;
}
.wolf-chat-msg {
  padding: 0.25rem 0;
  border-bottom: 1px solid rgba(139, 92, 246, 0.08);
  font-size: 0.78rem;
  line-height: 1.4;
}
.wolf-chat-msg:last-child { border-bottom: none; }
.wolf-chat-name {
  color: #a78bfa;
  font-weight: 600;
  margin-right: 0.35rem;
}
.wolf-chat-text { color: #d1d5db; }

/* 文本输入 */
.text-input-area {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.speech-input-row {
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.speech-textarea {
  flex: 1;
  padding: 0.7rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: white;
  font-size: 0.85rem;
  resize: vertical;
  outline: none;
  transition: border-color 0.2s;
}
.speech-textarea:focus { border-color: rgba(34, 197, 94, 0.5); }
.speech-textarea::placeholder { color: #64748b; }

/* 话筒按钮 */
.mic-btn {
  width: 44px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  user-select: none;
}
.mic-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}
.mic-btn.recording {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
}
.mic-icon {
  font-size: 1.2rem;
  line-height: 1;
}
.mic-pulse {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  border: 2px solid rgba(239, 68, 68, 0.4);
  animation: mic-pulse 1.2s ease-out infinite;
}
@keyframes mic-pulse {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.4); opacity: 0; }
}

.mic-error {
  color: #ef4444;
  font-size: 0.75rem;
  text-align: center;
}
.mic-status {
  color: #ef4444;
  font-size: 0.8rem;
  text-align: center;
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% { opacity: 0.5; }
}

.submit-speech-btn {
  padding: 0.65rem;
  background: linear-gradient(135deg, #22c55e, #16a34a);
  border: none; border-radius: 8px;
  color: white; font-weight: 600; font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}
.submit-speech-btn:hover:not(:disabled) { opacity: 0.9; }
.submit-speech-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* 提交中状态 */
.submitted-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding: 0.5rem;
  border-radius: 8px;
  background: rgba(34, 197, 94, 0.08);
  color: #94a3b8;
  font-size: 0.8rem;
}

.loading-spinner {
  width: 18px; height: 18px;
  border: 2px solid rgba(34, 197, 94, 0.2);
  border-top-color: #22c55e;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 进出动画 */
.panel-slide-enter-active { transition: all 0.35s ease-out; }
.panel-slide-leave-active { transition: all 0.25s ease-in; }
.panel-slide-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(30px);
}
.panel-slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
