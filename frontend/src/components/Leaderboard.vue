<template>
  <div class="leaderboard-section">
    <div class="section-title">🏆 排行榜</div>
    <div v-if="leaderboard.length > 0">
      <div
        v-for="(player, index) in leaderboard"
        :key="player.name"
        class="leaderboard-item"
      >
        <div :class="['leaderboard-rank', getRankClass(index)]">
          {{ index + 1 }}
        </div>
        <div class="leaderboard-info">
          <div class="leaderboard-name">{{ player.name }}</div>
          <div class="leaderboard-role">{{ player.role }}</div>
        </div>
        <div class="leaderboard-stats text-right">
          <div class="leaderboard-winrate">{{ player.win_rate.toFixed(1) }}%</div>
          <div class="leaderboard-games">{{ player.total_games }}场</div>
        </div>
      </div>
    </div>
    <div v-else class="text-center text-gray-400 text-sm py-4">
      暂无排行数据
    </div>
  </div>
</template>

<script setup>
defineProps({
  leaderboard: {
    type: Array,
    default: () => []
  }
})

const getRankClass = (index) => {
  if (index === 0) return 'gold'
  if (index === 1) return 'silver'
  if (index === 2) return 'bronze'
  return 'normal'
}
</script>

<style scoped>
.leaderboard-section {
  @apply mb-6;
}

.leaderboard-item {
  @apply flex items-center p-3 bg-bg-card rounded-lg mb-2 transition-all;
}

.leaderboard-item:hover {
  @apply -translate-x-1;
}

.leaderboard-rank {
  @apply w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm mr-3;
}

.leaderboard-rank.gold {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  @apply text-bg-primary;
}

.leaderboard-rank.silver {
  background: linear-gradient(135deg, #9ca3af, #6b7280);
  @apply text-white;
}

.leaderboard-rank.bronze {
  background: linear-gradient(135deg, #f97316, #ea580c);
  @apply text-white;
}

.leaderboard-rank.normal {
  @apply bg-bg-secondary text-gray-400;
}

.leaderboard-info {
  @apply flex-1;
}

.leaderboard-name {
  @apply text-sm font-semibold;
}

.leaderboard-role {
  @apply text-xs text-gray-400;
}

.leaderboard-winrate {
  @apply text-lg font-bold text-accent-green;
}

.leaderboard-games {
  @apply text-xs text-gray-400;
}
</style>
