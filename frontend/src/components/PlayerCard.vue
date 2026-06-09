<template>
  <div
    class="player-card glass-card rounded-xl p-4 text-center transition-all duration-300"
    :class="{ 
      'opacity-50': !player.is_alive,
      'glow-border-green': player.is_alive && isRole(player, '狼人'),
      'glow-border-purple': player.is_alive && isRole(player, '平民'),
      'glow-border-blue': player.is_alive && isRole(player, '预言家'),
      'glow-border-pink': player.is_alive && isRole(player, '女巫'),
      'glow-border-red': player.is_alive && isRole(player, '猎人')
    }"
  >
    <div 
      class="player-avatar mx-auto mb-3"
      :class="{ 
        'alive': player.is_alive,
        'dead': !player.is_alive,
        'pulse-glow': player.is_alive
      }"
    >
      {{ player.id.replace('P', '') }}
    </div>
    
    <div class="text-sm font-medium text-white mb-1">
      {{ player.name }}
      <span v-if="player.is_human" class="text-xs text-accent-gold ml-1">[真人]</span>
    </div>
    
    <div class="text-xs text-gray-400 mb-2">{{ player.id }}</div>
    
    <div v-if="showRole" class="role-badge" :class="getRoleClass(player)">
      {{ player.role }}
    </div>
    
    <div v-else class="role-badge role-unknown">
      ?
    </div>
    
    <div v-if="!player.is_alive" class="mt-2 text-xs text-red-400">
      💀 已淘汰
    </div>
    
    <div v-if="player.is_hunter_revealed && player.is_alive" class="mt-2 text-xs text-orange-400">
      🔫 猎人已觉醒
    </div>
    
    <div v-if="player.is_alive && hasSpecialAbility(player)" class="mt-2 text-xs text-blue-400">
      {{ getAbilityText(player) }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  player: {
    type: Object,
    required: true
  },
  showRole: {
    type: Boolean,
    default: false
  }
})

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
    return `药剂: ${abilities.join('/')}`
  }
  if (player.role === '猎人') {
    return '🔫 可开枪'
  }
  return ''
}
</script>

<style scoped>
.player-card {
  min-width: 80px;
  max-width: 100px;
}

.player-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.player-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  font-weight: bold;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4);
}

.player-avatar.alive {
  box-shadow: 0 0 15px rgba(34, 197, 94, 0.5), 0 4px 15px rgba(79, 70, 229, 0.4);
}

.player-avatar.dead {
  filter: grayscale(100%) brightness(50%);
  box-shadow: none;
}

.role-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
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
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.3), inset 0 0 10px rgba(34, 197, 94, 0.1);
}

.glow-border-purple {
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.3), inset 0 0 10px rgba(139, 92, 246, 0.1);
}

.glow-border-blue {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3), inset 0 0 10px rgba(59, 130, 246, 0.1);
}

.glow-border-pink {
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.3), inset 0 0 10px rgba(236, 72, 153, 0.1);
}

.glow-border-red {
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3), inset 0 0 10px rgba(239, 68, 68, 0.1);
}

@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 15px rgba(34, 197, 94, 0.5); }
  50% { box-shadow: 0 0 30px rgba(34, 197, 94, 0.8), 0 0 45px rgba(34, 197, 94, 0.4); }
}

.pulse-glow {
  animation: pulse-glow 2s infinite;
}
</style>
