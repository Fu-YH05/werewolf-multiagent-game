<template>
  <div class="vote-panel glass-card rounded-xl p-6">
    <h3 class="text-lg font-bold text-accent-green mb-4 flex items-center gap-2">
      <span>🗳️</span> 投票记录
    </h3>
    
    <div class="space-y-6">
      <div
        v-for="(voteResult, index) in voteResults"
        :key="index"
        class="vote-round fade-in"
      >
        <div class="flex items-center gap-2 mb-3">
          <span class="text-accent-gold font-medium">第{{ voteResult.day }}天</span>
          <span class="text-gray-400 text-sm">投票</span>
        </div>
        
        <!-- 投票Chips -->
        <div class="flex flex-wrap gap-2 mb-4">
          <div
            v-for="(count, target) in voteResult.votes"
            :key="target"
            class="vote-chip"
            :class="{ 'highlight': count === maxVotes(voteResult.votes) }"
          >
            {{ target }}: {{ count }}票
          </div>
        </div>
        
        <!-- 柱状图 -->
        <div class="bar-chart-container">
          <div
            v-for="(count, target) in voteResult.votes"
            :key="target"
            class="bar-item flex flex-col items-center"
            :class="{ 'highlight': count === maxVotes(voteResult.votes) }"
            :style="{ height: getBarHeight(count, voteResult.votes) + '%' }"
          >
            <span class="text-xs mt-1">{{ count }}</span>
          </div>
        </div>
        
        <!-- 投票详情 -->
        <div class="mt-3 text-sm text-gray-400">
          <span class="font-medium text-gray-300">投票详情:</span>
          <div class="flex flex-wrap gap-2 mt-1">
            <span
              v-for="detail in voteResult.details"
              :key="detail.voter"
              class="text-xs bg-white/5 px-2 py-1 rounded"
            >
              {{ detail.voter }} → {{ detail.target }}
            </span>
          </div>
        </div>
        
        <!-- PK轮次 -->
        <div v-if="voteResult.pk_1" class="mt-4 pt-4 border-t border-white/10">
          <div class="text-sm text-accent-gold mb-2">🔄 PK第1轮</div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(count, target) in voteResult.pk_1.votes"
              :key="target"
              class="vote-chip"
            >
              {{ target }}: {{ count }}票
            </span>
          </div>
        </div>
        
        <div v-if="voteResult.pk_2" class="mt-2">
          <div class="text-sm text-accent-gold mb-2">🔄 PK第2轮</div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(count, target) in voteResult.pk_2.votes"
              :key="target"
              class="vote-chip"
            >
              {{ target }}: {{ count }}票
            </span>
          </div>
        </div>
        
        <div v-if="voteResult.pk_3" class="mt-2">
          <div class="text-sm text-accent-gold mb-2">🔄 PK第3轮</div>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="(count, target) in voteResult.pk_3.votes"
              :key="target"
              class="vote-chip"
            >
              {{ target }}: {{ count }}票
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  voteResults: {
    type: Array,
    required: true
  }
})

function maxVotes(votes) {
  if (!votes || Object.keys(votes).length === 0) return 0
  return Math.max(...Object.values(votes))
}

function getBarHeight(count, votes) {
  const max = maxVotes(votes)
  if (max === 0) return 0
  return (count / max) * 100
}
</script>

<style scoped>
.vote-panel {
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.vote-round {
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.vote-chip {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #22c55e;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  transition: all 0.3s ease;
}

.vote-chip:hover {
  background: rgba(34, 197, 94, 0.25);
  transform: translateY(-2px);
}

.vote-chip.highlight {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.3), rgba(245, 158, 11, 0.1));
  border-color: #f59e0b;
  color: #f59e0b;
}

.bar-chart-container {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 80px;
  padding: 8px 0;
}

.bar-item {
  flex: 1;
  background: linear-gradient(180deg, #22c55e 0%, rgba(34, 197, 94, 0.3) 100%);
  border-radius: 4px 4px 0 0;
  min-height: 4px;
  transition: height 0.5s ease-out;
}

.bar-item.highlight {
  background: linear-gradient(180deg, #f59e0b 0%, rgba(245, 158, 11, 0.3) 100%);
}
</style>
