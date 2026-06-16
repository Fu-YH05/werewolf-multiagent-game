<template>
  <div class="player-card-wrapper">
    <!-- 玩家卡片 -->
    <div
      class="player-card glass-card rounded-xl p-2 text-center transition-all duration-300"
      :class="{
        'opacity-50': !player.is_alive,
        'speech-available': speeches.length > 0,
        'speaking-now': isSpeaking,
        'glow-border-green': player.is_alive && canSeeRole && isRole(player, '狼人'),
        'glow-border-purple': player.is_alive && canSeeRole && isRole(player, '平民'),
        'glow-border-blue': player.is_alive && canSeeRole && isRole(player, '预言家'),
        'glow-border-pink': player.is_alive && canSeeRole && isRole(player, '女巫'),
        'glow-border-red': player.is_alive && canSeeRole && isRole(player, '猎人'),
        'glow-border-human': player.is_alive && !canSeeRole
      }"
      @click.stop="toggleSpeech"
    >
      <div
        class="player-avatar mx-auto mb-1.5"
        :class="{
          'alive': player.is_alive,
          'dead': !player.is_alive,
          'pulse-glow': player.is_alive && canSeeRole
        }"
      >
        {{ player.id.replace('P', '') }}
      </div>

      <div class="text-sm font-medium text-white mb-0.5">
        {{ player.name }}
        <span v-if="player.is_human" class="text-xs text-accent-gold ml-0.5">[真人]</span>
      </div>

      <div class="text-xs text-gray-400 mb-1">{{ player.id }}</div>

      <!-- 身份：游戏结束全局可见，真人模式下自己可见 -->
      <div v-if="canSeeRole" class="role-badge" :class="getRoleClass(player)">
        {{ player.role }}
      </div>
      <div v-else class="role-badge role-unknown">
        ?
      </div>

      <!-- 标注身份：仅真人模式且未全局展示时可用 -->
      <div v-if="isHumanMode && !showRole" class="mt-1">
        <button
          class="annotation-btn"
          @click.stop="toggleAnnotation"
          :class="{ active: player.annotation }"
          title="为该玩家标注你认为的身份"
        >
          {{ player.annotation ? '🏷️' : '📝' }}
        </button>
        <div v-if="annotationOpen" class="annotation-dropdown" @click.stop>
          <div
            v-for="role in roleOptions"
            :key="role"
            class="annotation-option"
            :class="{ selected: player.annotation === role }"
            @click.stop="selectAnnotation(role)"
          >
            {{ role }}
          </div>
        </div>
      </div>

      <!-- 标注结果显示 -->
      <div v-if="player.annotation && !showRole" class="annotation-badge">
        {{ player.annotation }}
      </div>

      <div v-if="!player.is_alive" class="mt-1 text-xs text-red-400">
        💀 已淘汰
      </div>

      <!-- 猎人觉醒：仅自己可见或游戏结束 -->
      <div v-if="canSeeRole && player.is_hunter_revealed && player.is_alive" class="mt-1 text-xs text-orange-400">
        🔫 猎人已觉醒
      </div>

      <!-- 特殊技能：仅自己可见或游戏结束 -->
      <div v-if="canSeeRole && player.is_alive && hasSpecialAbility(player)" class="mt-1 text-xs text-blue-400">
        {{ getAbilityText(player) }}
      </div>
    </div>

    <!-- 发言气泡 - 悬浮于玩家卡片下方，与语音同步 -->
    <Transition name="bubble-fade">
      <div v-if="isSpeaking && currentSpeech" class="speech-bubble">
        <div class="speech-bubble-tail"></div>
        <div class="speech-bubble-content">
          {{ currentSpeech }}
        </div>
      </div>
    </Transition>

    <!-- 发言弹窗 -->
    <Teleport to="body">
      <div v-if="showSpeech" class="speech-overlay" @click="closeSpeech"></div>
      <div v-if="showSpeech" class="speech-popup" :style="popupStyle">
        <div class="speech-popup-header">
          <span class="speech-popup-name">{{ player.name }}</span>
          <span class="speech-popup-id">{{ player.id }}</span>
          <button class="speech-popup-close" @click="closeSpeech">&times;</button>
        </div>
        <div class="speech-popup-body">
          <div v-if="speeches.length === 0" class="speech-empty">
            暂无发言记录
          </div>
          <div
            v-for="(s, i) in speeches"
            :key="i"
            class="speech-item"
          >
            <div class="speech-meta">第{{ s.day }}天 · {{ s.phase }}</div>
            <div class="speech-content">{{ s.content }}</div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  player: {
    type: Object,
    required: true
  },
  showRole: {
    type: Boolean,
    default: false
  },
  isHumanMode: {
    type: Boolean,
    default: false
  },
  speeches: {
    type: Array,
    default: () => []
  },
  isSpeaking: {
    type: Boolean,
    default: false
  },
  currentSpeech: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['annotate'])

const annotationOpen = ref(false)
const showSpeech = ref(false)
const popupStyle = ref({})

const roleOptions = ['狼人', '预言家', '女巫', '猎人', '平民']

function toggleSpeech(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  popupStyle.value = {
    top: Math.min(rect.bottom + 8, window.innerHeight - 300) + 'px',
    left: Math.max(8, Math.min(rect.left + rect.width / 2 - 140, window.innerWidth - 288)) + 'px'
  }
  showSpeech.value = !showSpeech.value
}

function closeSpeech() {
  showSpeech.value = false
}

// 真人模式：真人自己可见、狼队友可见；全局展示模式下所有人可见
const canSeeRole = computed(() => {
  return props.showRole || (props.isHumanMode && (props.player.is_human || props.player.is_wolf_teammate))
})

function toggleAnnotation() {
  annotationOpen.value = !annotationOpen.value
}

function selectAnnotation(role) {
  emit('annotate', { playerId: props.player.id, role })
  annotationOpen.value = false
}

function isRole(player, roleName) {
  return player.role === roleName
}

function getRoleClass(player) {
  const roleMap = {
    '狼人': 'role-wolf',
    '平民': 'role-villager',
    '预言家': 'role-seer',
    '女巫': 'role-witch',
    '猎人': 'role-hunter'
  }
  return roleMap[player.role] || 'role-unknown'
}

function hasSpecialAbility(player) {
  return (player.role === '女巫' && (player.has_antidote || player.has_poison)) ||
         (player.role === '猎人' && !player.is_hunter_revealed)
}

function getAbilityText(player) {
  if (player.role === '女巫') {
    const abilities = []
    if (player.has_antidote) abilities.push('解药')
    if (player.has_poison) abilities.push('毒药')
    return `🧪 ${abilities.join(' / ')}`
  }
  if (player.role === '猎人') {
    return '🔫 可开枪'
  }
  return ''
}
</script>

<style scoped>
.player-card {
  min-width: 60px;
  max-width: 80px;
}

.player-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.player-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: bold;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
  position: relative;
}

.player-avatar.alive {
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.4), 0 4px 15px rgba(79, 70, 229, 0.3);
}

.player-avatar.dead {
  filter: grayscale(100%) brightness(50%);
  box-shadow: none;
}

.role-badge {
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: medium;
}

.role-unknown {
  background: rgba(107, 114, 128, 0.3);
  color: #9ca3af;
}

.role-wolf {
  background: linear-gradient(135deg, #7c3aed, #5b21b6);
  color: white;
}

.role-villager {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
}

.role-seer {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.role-witch {
  background: linear-gradient(135deg, #ec4899, #db2777);
  color: white;
}

.role-hunter {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.glow-border-green {
  box-shadow: 0 0 12px rgba(34, 197, 94, 0.25), inset 0 0 6px rgba(34, 197, 94, 0.08);
}

.glow-border-purple {
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.25), inset 0 0 6px rgba(139, 92, 246, 0.08);
}

.glow-border-blue {
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.25), inset 0 0 6px rgba(59, 130, 246, 0.08);
}

.glow-border-pink {
  box-shadow: 0 0 12px rgba(236, 72, 153, 0.25), inset 0 0 6px rgba(236, 72, 153, 0.08);
}

.glow-border-red {
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.25), inset 0 0 6px rgba(239, 68, 68, 0.08);
}

.glow-border-human {
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.06), inset 0 0 4px rgba(255, 255, 255, 0.03);
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 10px rgba(34, 197, 94, 0.35); }
  50% { box-shadow: 0 0 20px rgba(34, 197, 94, 0.6), 0 0 30px rgba(34, 197, 94, 0.3); }
}

.pulse-glow {
  animation: pulse-glow 2s infinite;
}

/* 标注按钮 */
.annotation-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 0 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  line-height: 1.5;
}
.annotation-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
}
.annotation-btn.active {
  background: rgba(234, 179, 8, 0.2);
  border-color: rgba(234, 179, 8, 0.4);
}

/* 标注下拉 */
.annotation-dropdown {
  position: absolute;
  background: #1e1b4b;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  padding: 2px 0;
  z-index: 50;
  min-width: 64px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  margin-top: 2px;
}
.annotation-option {
  padding: 3px 10px;
  font-size: 11px;
  color: #d1d5db;
  cursor: pointer;
  transition: background 0.15s;
}
.annotation-option:hover {
  background: rgba(255, 255, 255, 0.08);
  color: white;
}
.annotation-option.selected {
  background: rgba(234, 179, 8, 0.15);
  color: #fbbf24;
}

/* 标注徽章 */
.annotation-badge {
  margin-top: 2px;
  padding: 0 6px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 500;
  background: rgba(234, 179, 8, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(234, 179, 8, 0.25);
}

/* 有发言可查看的提示 */
.speech-available {
  cursor: pointer;
}
.speech-available:hover .player-avatar {
  box-shadow: 0 0 12px rgba(34, 211, 238, 0.5), 0 4px 15px rgba(79, 70, 229, 0.3);
}

/* TTS 播放中呼吸光晕 */
.speaking-now {
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.5), 0 0 40px rgba(34, 197, 94, 0.2);
  transform: translateY(-3px);
  animation: breathe-card 1.4s ease-in-out infinite;
}
.speaking-now .player-avatar {
  box-shadow: 0 0 16px rgba(34, 197, 94, 0.6), 0 4px 15px rgba(79, 70, 229, 0.3);
  animation: breathe-avatar 1.4s ease-in-out infinite;
}
.speaking-now .player-avatar::after {
  content: '';
  position: absolute;
  inset: -5px;
  border-radius: 50%;
  border: 2.5px solid rgba(34, 197, 94, 0.5);
  animation: breathe-ring 1.4s ease-in-out infinite;
}
.speaking-now .player-name {
  color: #4ade80 !important;
  text-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
}
@keyframes breathe-card {
  0%, 100% { box-shadow: 0 0 12px rgba(34, 197, 94, 0.3), 0 0 25px rgba(34, 197, 94, 0.1); }
  50% { box-shadow: 0 0 30px rgba(34, 197, 94, 0.6), 0 0 50px rgba(34, 197, 94, 0.3); }
}
@keyframes breathe-avatar {
  0%, 100% { transform: scale(1); box-shadow: 0 0 12px rgba(34, 197, 94, 0.4), 0 4px 15px rgba(79, 70, 229, 0.3); }
  50% { transform: scale(1.08); box-shadow: 0 0 24px rgba(34, 197, 94, 0.8), 0 4px 15px rgba(79, 70, 229, 0.5); }
}
@keyframes breathe-ring {
  0%, 100% { opacity: 0.2; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

/* 发言弹窗遮罩 */
.speech-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 999;
  background: transparent;
}

/* 发言弹窗 */
.speech-popup {
  position: fixed;
  z-index: 1000;
  width: 280px;
  max-height: 320px;
  background: #1a1a3e;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.speech-popup-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.speech-popup-name {
  font-size: 14px;
  font-weight: 600;
  color: #e2e8f0;
}

.speech-popup-id {
  font-size: 11px;
  color: #64748b;
  flex: 1;
}

.speech-popup-close {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}
.speech-popup-close:hover {
  color: white;
}

.speech-popup-body {
  padding: 8px 12px;
  overflow-y: auto;
  flex: 1;
}

.speech-empty {
  text-align: center;
  color: #64748b;
  font-size: 13px;
  padding: 20px 0;
}

.speech-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.speech-item:last-child {
  border-bottom: none;
}

.speech-meta {
  font-size: 10px;
  color: #64748b;
  margin-bottom: 3px;
}

.speech-content {
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.4;
  word-break: break-word;
}

/* 玩家卡片包装器 - 设置相对定位，使气泡相对于卡片定位 */
.player-card-wrapper {
  position: relative;
}

/* 发言气泡样式 - 悬浮于玩家卡片下方 */
.speech-bubble {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 12px;
  max-width: 280px;
  min-width: 120px;
  z-index: 100;
}

.speech-bubble-content {
  background: linear-gradient(135deg, #22d3ee, #06b6d4);
  color: #0f172a;
  padding: 10px 14px;
  border-radius: 16px;
  border-top-left-radius: 4px;
  font-size: 13px;
  line-height: 1.5;
  text-align: left;
  word-break: break-word;
  box-shadow: 0 4px 20px rgba(34, 211, 238, 0.4);
  position: relative;
}

/* 气泡三角箭头 - 指向上方 */
.speech-bubble-tail {
  position: absolute;
  top: -8px;
  left: 20px;
  width: 0;
  height: 0;
  border-left: 10px solid transparent;
  border-right: 10px solid transparent;
  border-bottom: 10px solid #06b6d4;
}

/* 气泡出现/消失动画 */
.bubble-fade-enter-active {
  animation: bubble-in 0.3s ease-out;
}

.bubble-fade-leave-active {
  animation: bubble-out 0.2s ease-in;
}

@keyframes bubble-in {
  0% {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
}

@keyframes bubble-out {
  0% {
    opacity: 1;
    transform: translateX(-50%) translateY(0) scale(1);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(5px) scale(0.95);
  }
}

/* 根据角色类型调整气泡颜色 */
.player-card-wrapper:has(.glow-border-green) .speech-bubble-content {
  background: linear-gradient(135deg, #a855f7, #9333ea);
  box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4);
}
.player-card-wrapper:has(.glow-border-green) .speech-bubble-tail {
  border-bottom-color: #9333ea;
}

.player-card-wrapper:has(.glow-border-blue) .speech-bubble-content {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
}
.player-card-wrapper:has(.glow-border-blue) .speech-bubble-tail {
  border-bottom-color: #2563eb;
}

.player-card-wrapper:has(.glow-border-pink) .speech-bubble-content {
  background: linear-gradient(135deg, #ec4899, #db2777);
  box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4);
}
.player-card-wrapper:has(.glow-border-pink) .speech-bubble-tail {
  border-bottom-color: #db2777;
}

.player-card-wrapper:has(.glow-border-red) .speech-bubble-content {
  background: linear-gradient(135deg, #f87171, #ef4444);
  box-shadow: 0 4px 20px rgba(248, 113, 113, 0.4);
}
.player-card-wrapper:has(.glow-border-red) .speech-bubble-tail {
  border-bottom-color: #ef4444;
}

.player-card-wrapper:has(.glow-border-purple) .speech-bubble-content {
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
  color: #1e293b;
  box-shadow: 0 4px 20px rgba(203, 213, 225, 0.4);
}
.player-card-wrapper:has(.glow-border-purple) .speech-bubble-tail {
  border-bottom-color: #cbd5e1;
}
</style>
