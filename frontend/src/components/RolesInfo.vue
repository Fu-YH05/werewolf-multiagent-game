<template>
  <div class="roles-section">
    <div class="section-title">📖 角色说明</div>
    <div class="roles-grid">
      <div
        v-for="role in roles"
        :key="role.id"
        :class="['role-card', `role-${role.id}`]"
      >
        <div class="role-icon">{{ role.icon }}</div>
        <div class="role-info">
          <h4>{{ role.name }}</h4>
          <p>{{ role.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  roles: {
    type: Array,
    default: () => [
      { id: 'werewolf', name: '狼人', icon: '🐺', description: '夜晚可以杀死一名玩家' },
      { id: 'seer', name: '预言家', icon: '🔮', description: '夜晚可以查验身份' },
      { id: 'witch', name: '女巫', icon: '🧪', description: '拥有解药和毒药' },
      { id: 'hunter', name: '猎人', icon: '🏹', description: '死亡时可带走一人' },
      { id: 'villager', name: '平民', icon: '👤', description: '通过投票找出狼人' }
    ]
  }
})
</script>

<style scoped>
.roles-section {
  @apply mt-6;
}

.roles-grid {
  @apply space-y-2;
}

.role-card {
  @apply flex items-center p-3 bg-bg-card rounded-lg border-l-4;
}

.role-card.role-werewolf {
  @apply border-l-accent-red;
}

.role-card.role-seer {
  @apply border-l-accent-blue;
}

.role-card.role-witch {
  @apply border-l-accent-purple;
}

.role-card.role-hunter {
  @apply border-l-accent-orange;
}

.role-card.role-villager {
  @apply border-l-accent-green;
}

.role-icon {
  @apply w-10 h-10 rounded-lg flex items-center justify-center text-xl mr-3;
}

.role-card.role-werewolf .role-icon {
  @apply bg-red-500/20;
}

.role-card.role-seer .role-icon {
  @apply bg-blue-500/20;
}

.role-card.role-witch .role-icon {
  @apply bg-purple-500/20;
}

.role-card.role-hunter .role-icon {
  @apply bg-orange-500/20;
}

.role-card.role-villager .role-icon {
  @apply bg-green-500/20;
}

.role-info h4 {
  @apply text-sm font-semibold mb-1;
}

.role-info p {
  @apply text-xs text-gray-400;
}
</style>
