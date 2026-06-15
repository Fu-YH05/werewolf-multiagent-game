<template>
  <div class="elimination-tree" :class="{ collapsed: isCollapsed }">
    <div class="tree-header" @click="isCollapsed = !isCollapsed">
      <span class="tree-icon">🌳</span>
      <span class="tree-title">玩家存活树</span>
      <span class="tree-toggle">{{ isCollapsed ? '▶' : '▼' }}</span>
    </div>
    <div v-show="!isCollapsed" class="tree-body">
      <!-- 空状态 -->
      <div v-if="treeData.length === 0" class="tree-empty">
        暂无淘汰数据
      </div>
      <!-- 树 -->
      <div v-for="(dayNode, di) in treeData" :key="di" class="day-node">
        <div class="day-label">第 {{ dayNode.day }} 天</div>
        <div class="day-players">
          <span
            v-for="p in dayNode.alive"
            :key="p.id"
            :class="['player-chip', 'alive', { dead: !p.isAlive }]"
          >
            {{ p.name || p.id }}
          </span>
        </div>
        <!-- 淘汰事件 -->
        <div v-for="(evt, ei) in dayNode.events" :key="ei" class="death-event">
          <span class="death-icon">{{ evt.icon }}</span>
          <span class="death-cause">{{ evt.label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  players: { type: Array, default: () => [] },
  expanded: { type: Boolean, default: false },
})

const isCollapsed = ref(!props.expanded)

// 解析淘汰树
const treeData = computed(() => {
  const playerMap = {}
  for (const p of props.players) {
    playerMap[p.id] = p
  }

  const dayEvents = {}
  let maxDay = 0

  for (const log of props.logs) {
    const day = log.day || 1
    if (!dayEvents[day]) dayEvents[day] = { events: [], killedThisDay: new Set() }
    maxDay = Math.max(maxDay, day)

    const type = (log.type || '').toLowerCase()
    const content = log.content || ''

    // 1. 平安夜 / 无人死亡
    if (type.includes('announce')) {
      const isPeaceful =
        content.includes('平安夜') ||
        content.includes('无人死亡') ||
        /昨晚死亡[：:]\s*无/.test(content) ||
        /昨晚死亡[：:]\s*没人/.test(content) ||
        /无人伤亡/.test(content)

      if (isPeaceful) {
        dayEvents[day].events.push({ icon: '🌙', label: '平安夜', playerName: '' })
        continue  // 跳过后面的死亡解析
      }
    }

    // 2. 夜晚死亡 (ANNOUNCE)
    if (type.includes('announce') && content.includes('昨晚死亡')) {
      const match = content.match(/死亡[：:]\s*(\S+)/)
      if (match) {
        const name = match[1]
        dayEvents[day].events.push({
          icon: '🌙',
          label: `夜晚: ${name} 死亡`,
          playerName: name,
        })
        dayEvents[day].killedThisDay.add(name)
      } else {
        // 可能包含多个死者：用逗号/空格分隔
        const multiMatch = content.match(/死亡[：:]\s*(.+)/)
        if (multiMatch) {
          const names = multiMatch[1].split(/[,，、\s]+/).filter(Boolean)
          for (const name of names) {
            dayEvents[day].events.push({
              icon: '🌙',
              label: `夜晚: ${name} 死亡`,
              playerName: name,
            })
            dayEvents[day].killedThisDay.add(name)
          }
        }
      }
    }

    // 3. 放逐 (LYNCH)
    if (type.includes('lynch') || (type.includes('vote') && content.includes('放逐'))) {
      const match = content.match(/P(\d+)\s*[被]/)
      const nameMatch = content.match(/[（(]\s*(\S+?)\s*[)）]/)
      if (match) {
        const pid = 'P' + match[1]
        const p = playerMap[pid]
        const name = p?.name || (nameMatch ? nameMatch[1] : pid)
        dayEvents[day].events.push({
          icon: '☀️',
          label: `放逐: ${name}`,
          playerName: name,
        })
        dayEvents[day].killedThisDay.add(name)
      }
    }

    // 4. 毒药/枪杀 (ACTION)
    if (type.includes('action')) {
      if (content.includes('毒')) {
        const match = content.match(/毒[死杀]\s*P?(\d+)/)
        if (match) {
          const pid = 'P' + match[1]
          const p = playerMap[pid]
          const name = p?.name || pid
          dayEvents[day].events.push({
            icon: '🧪',
            label: `女巫毒杀: ${name}`,
            playerName: name,
          })
          dayEvents[day].killedThisDay.add(name)
        }
      }
      if (content.includes('猎') || content.includes('枪')) {
        const match = content.match(/猎[人]?\s*带[走杀]\s*P?(\d+)/)
        if (match) {
          const pid = 'P' + match[1]
          const p = playerMap[pid]
          const name = p?.name || pid
          dayEvents[day].events.push({
            icon: '🏹',
            label: `猎人带走: ${name}`,
            playerName: name,
          })
          dayEvents[day].killedThisDay.add(name)
        }
      }
    }
  }

  // 构建树：按天显示存活和淘汰情况
  const tree = []
  let currentAlive = [...props.players]

  for (let d = 1; d <= maxDay; d++) {
    const evt = dayEvents[d]
    const killedNames = evt ? evt.killedThisDay : new Set()

    tree.push({
      day: d,
      alive: currentAlive.map(p => ({
        id: p.id,
        name: p.name,
        isAlive: !killedNames.has(p.name) && !killedNames.has(p.id),
      })),
      events: evt ? evt.events : [],
    })

    // 更新下一轮的存活列表
    currentAlive = currentAlive.filter(p => !killedNames.has(p.name) && !killedNames.has(p.id))
  }

  return tree
})
</script>

<style scoped>
.elimination-tree {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  overflow: hidden;
}

.tree-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.tree-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.tree-icon {
  font-size: 0.85rem;
}

.tree-title {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.8);
  flex: 1;
}

.tree-toggle {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.3);
}

.tree-body {
  padding: 0 10px 8px;
  max-height: 200px;
  overflow-y: auto;
}

.tree-empty {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.3);
  text-align: center;
  padding: 8px 0;
}

.day-node {
  margin-bottom: 6px;
  padding-left: 8px;
  border-left: 1px solid rgba(255, 255, 255, 0.1);
}

.day-node:last-child {
  margin-bottom: 0;
}

.day-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 2px;
}

.day-players {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-bottom: 3px;
}

.player-chip {
  font-size: 0.6rem;
  padding: 1px 5px;
  border-radius: 8px;
}

.player-chip.alive {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.player-chip.dead {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  text-decoration: line-through;
}

.death-event {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 1px 0;
  font-size: 0.65rem;
  color: rgba(255, 255, 255, 0.6);
}

.death-icon {
  font-size: 0.7rem;
}

.death-cause {
  color: rgba(255, 255, 255, 0.55);
}
</style>
