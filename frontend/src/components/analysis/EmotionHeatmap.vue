<template>
  <div class="emotion-heatmap" :class="{ collapsed: isCollapsed }">
    <div class="heatmap-header" @click="isCollapsed = !isCollapsed">
      <span class="heatmap-icon">🔥</span>
      <span class="heatmap-title">情绪热力图</span>
      <span class="heatmap-toggle">{{ isCollapsed ? '▶' : '▼' }}</span>
    </div>
    <div v-show="!isCollapsed" class="heatmap-body">
      <div v-if="heatData.length === 0" class="heatmap-empty">
        暂无发言数据
      </div>
      <div v-else class="heatmap-grid-wrapper">
        <!-- 图例 -->
        <div class="heatmap-legend">
          <span class="legend-label">冷静</span>
          <span class="legend-bar">
            <span class="legend-stop" style="background: #1a5276"></span>
            <span class="legend-stop" style="background: #2e86c1"></span>
            <span class="legend-stop" style="background: #f39c12"></span>
            <span class="legend-stop" style="background: #e74c3c"></span>
            <span class="legend-stop" style="background: #922b21"></span>
          </span>
          <span class="legend-label">激动</span>
        </div>
        <!-- 网格 -->
        <table class="heatmap-table">
          <thead>
            <tr>
              <th class="corner-cell"></th>
              <th v-for="d in dayRange" :key="d" class="day-header">D{{ d }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in heatData" :key="row.playerId">
              <td class="player-cell" :title="row.playerName">{{ row.shortName }}</td>
              <td
                v-for="(cell, ci) in row.cells"
                :key="ci"
                :class="['emotion-cell', { 'has-data': cell.hasData }]"
                :style="cell.hasData ? { background: cell.color } : {}"
                :title="cell.tooltip"
              >
                <span v-if="cell.hasData" class="cell-level">{{ cell.level }}</span>
                <span v-else class="cell-empty"></span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { analyzeAllSpeeches } from '../../utils/emotionAnalysis.js'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  players: { type: Array, default: () => [] },
  expanded: { type: Boolean, default: false },
})

const isCollapsed = ref(!props.expanded)

// 情绪色阶
function getHeatColor(score) {
  if (score < 15) return '#1a5276'    // 深蓝-冷静
  if (score < 30) return '#2e86c1'    // 蓝-平和
  if (score < 50) return '#f39c12'    // 橙黄-正常
  if (score < 70) return '#e74c3c'    // 红-激动
  return '#922b21'                     // 深红-非常激动
}

function getLevelLabel(score) {
  if (score < 15) return '静'
  if (score < 30) return '平'
  if (score < 50) return '常'
  if (score < 70) return '激'
  return '🔥'
}

const analysis = computed(() => analyzeAllSpeeches(props.logs, props.players))

const dayRange = computed(() => {
  const range = analysis.value.dayRange
  return range > 0 ? range : 1
})

const heatData = computed(() => {
  const map = analysis.value.playerDayMap
  const maxDay = dayRange.value

  return props.players.map(p => {
    const cells = []
    for (let d = 1; d <= maxDay; d++) {
      const dayData = map[p.id]?.[d]
      if (dayData && dayData.count > 0) {
        const avgScore = Math.round(dayData.totalScore / dayData.count)
        cells.push({
          hasData: true,
          score: avgScore,
          color: getHeatColor(avgScore),
          level: getLevelLabel(avgScore),
          tooltip: `${p.name} 第${d}天: ${dayData.count}次发言, 平均情绪${avgScore}分`,
        })
      } else {
        cells.push({ hasData: false, score: 0, color: 'transparent', level: '', tooltip: `${p.name} 第${d}天: 无发言` })
      }
    }
    return {
      playerId: p.id,
      playerName: p.name || p.id,
      shortName: (p.name || p.id).slice(0, 2),
      cells,
    }
  })
})
</script>

<style scoped>
.emotion-heatmap {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  overflow: hidden;
}

.heatmap-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.heatmap-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.heatmap-icon {
  font-size: 0.85rem;
}

.heatmap-title {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  flex: 1;
}

.heatmap-toggle {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.3);
}

.heatmap-body {
  padding: 0 10px 8px;
}

.heatmap-empty {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.3);
  text-align: center;
  padding: 8px 0;
}

.heatmap-grid-wrapper {
  overflow-x: auto;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  justify-content: center;
}

.legend-label {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.4);
}

.legend-bar {
  display: flex;
  gap: 2px;
  border-radius: 4px;
  overflow: hidden;
}

.legend-stop {
  width: 16px;
  height: 8px;
}

.heatmap-table {
  width: 100%;
  border-collapse: collapse;
}

.corner-cell {
  width: 24px;
}

.day-header {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
  padding: 2px 4px;
  font-weight: normal;
}

.player-cell {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.6);
  padding: 2px 4px 2px 0;
  white-space: nowrap;
  width: 20px;
}

.emotion-cell {
  width: 28px;
  height: 22px;
  text-align: center;
  border-radius: 3px;
  transition: transform 0.15s;
}

.emotion-cell.has-data:hover {
  transform: scale(1.3);
  z-index: 2;
  box-shadow: 0 0 8px rgba(255,255,255,0.2);
}

.cell-level {
  font-size: 0.55rem;
  color: rgba(255, 255, 255, 0.8);
}

.cell-empty {
  display: inline-block;
  width: 100%;
  height: 100%;
}
</style>
