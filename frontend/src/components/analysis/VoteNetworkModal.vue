<template>
  <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title">🗳️ 投票关系网络图</h3>
        <div class="modal-header-right">
          <span class="hint-text">节点=玩家，箭头=投票，粗细=次数</span>
          <button class="modal-close" @click="$emit('close')">&times;</button>
        </div>
      </div>
      <div class="network-container" ref="containerRef"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  visible: { type: Boolean, default: false },
  logs: { type: Array, default: () => [] },
  players: { type: Array, default: () => [] },
})

defineEmits(['close'])

const containerRef = ref(null)
let simulation = null

// 从日志中提取投票关系
function extractVoteEdges(logs) {
  const voteCount = {} // key: "voter->target" -> count

  for (const log of logs) {
    const type = (log.type || '').toLowerCase()
    if (!type.includes('vote') && !type.includes('lynch')) continue

    const content = log.content || ''
    // 解析格式: "P1(小刚) 投票给 P9" 或 "P1投票给P9"
    const voteMatch = content.match(/P(\d+)[^投]*投票给\s*P(\d+)/)
    if (voteMatch) {
      const voter = 'P' + voteMatch[1]
      const target = 'P' + voteMatch[2]
      if (voter && target && voter !== target) {
        const key = `${voter}->${target}`
        voteCount[key] = (voteCount[key] || 0) + 1
      }
      continue
    }

    // 解析格式: "P1 放逐投票 P9"
    const lynchMatch = content.match(/P(\d+)[^可被]*放逐投票\s*P(\d+)/)
    if (lynchMatch) {
      const voter = 'P' + lynchMatch[1]
      const target = 'P' + lynchMatch[2]
      if (voter && target && voter !== target) {
        const key = `${voter}->${target}`
        voteCount[key] = (voteCount[key] || 0) + 1
      }
    }
  }

  return voteCount
}

// 构建节点和边
function buildGraph(logs, players) {
  const voteEdges = extractVoteEdges(logs)

  // 创建玩家查找表
  const playerMap = {}
  for (const p of players) {
    playerMap[p.id] = p
  }
  // 从日志中查找所有出现在投票中的玩家
  const nodeSet = new Set()
  for (const key of Object.keys(voteEdges)) {
    const [voter, target] = key.split('->')
    nodeSet.add(voter)
    nodeSet.add(target)
  }
  // 如果没有任何投票关系，使用所有玩家
  if (nodeSet.size === 0) {
    for (const p of players) nodeSet.add(p.id)
  }

  const nodes = Array.from(nodeSet).map(id => {
    const p = playerMap[id]
    return {
      id,
      name: p?.name || id,
      role: p?.role || 'unknown',
      isAlive: p?.is_alive !== false,
    }
  })

  const edges = Object.entries(voteEdges).map(([key, count]) => {
    const [source, target] = key.split('->')
    return { source, target, count }
  })

  return { nodes, edges }
}

// 角色颜色
function getRoleColor(role) {
  const colors = {
    werewolf: '#ef4444',
    seer: '#3b82f6',
    witch: '#a855f7',
    hunter: '#f59e0b',
    villager: '#22c55e',
    unknown: '#6b7280',
  }
  return colors[role?.toLowerCase()] || colors.unknown
}

function renderGraph() {
  if (!containerRef.value) return
  const { nodes, edges } = buildGraph(props.logs, props.players)
  if (nodes.length === 0) return

  const width = containerRef.value.clientWidth || 700
  const height = containerRef.value.clientHeight || 460

  // 清空
  d3.select(containerRef.value).selectAll('*').remove()

  const svg = d3.select(containerRef.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .style('background', 'transparent')

  // 箭头标记
  svg.append('defs').selectAll('marker')
    .data(['arrow'])
    .join('marker')
    .attr('id', 'arrow')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 22)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('fill', 'rgba(255,255,255,0.4)')
    .attr('d', 'M0,-5L10,0L0,5')

  // 边
  const link = svg.append('g')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('stroke', 'rgba(255,255,255,0.3)')
    .attr('stroke-width', d => Math.max(1, Math.min(d.count * 2, 6)))
    .attr('stroke-opacity', d => Math.min(0.3 + d.count * 0.15, 0.8))
    .attr('marker-end', 'url(#arrow)')

  // 边的标注重叠（hover提示用title）
  link.append('title').text(d => `${d.source} → ${d.target} (${d.count}次)`)

  // 节点组
  const node = svg.append('g')
    .selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', 18)
    .attr('fill', d => getRoleColor(d.role))
    .attr('stroke', d => d.isAlive ? '#fff' : '#666')
    .attr('stroke-width', 2)
    .attr('opacity', d => d.isAlive ? 1 : 0.5)
    .style('cursor', 'pointer')
    .call(drag(simulation))

  // 节点标题
  node.append('title').text(d => `${d.name} (${d.role})`)

  // 玩家名称标签
  const label = svg.append('g')
    .selectAll('text')
    .data(nodes)
    .join('text')
    .text(d => d.name)
    .attr('font-size', 10)
    .attr('fill', '#ddd')
    .attr('text-anchor', 'middle')
    .attr('dy', 30)
    .style('pointer-events', 'none')

  // 角色标识小标签
  const roleLabel = svg.append('g')
    .selectAll('text')
    .data(nodes)
    .join('text')
    .text(d => {
      const r = d.role?.toLowerCase()
      if (r === 'werewolf') return '🐺'
      if (r === 'seer') return '🔮'
      if (r === 'witch') return '🧪'
      if (r === 'hunter') return '🏹'
      if (r === 'villager') return '👤'
      return '?'
    })
    .attr('font-size', 13)
    .attr('text-anchor', 'middle')
    .attr('dy', 4.5)
    .style('pointer-events', 'none')

  // 力模拟
  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(100))
    .force('charge', d3.forceManyBody().strength(-280))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide(35))
    .on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)
      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)
      label
        .attr('x', d => d.x)
        .attr('y', d => d.y)
      roleLabel
        .attr('x', d => d.x)
        .attr('y', d => d.y)
    })
}

function drag(sim) {
  function dragstarted(event, d) {
    if (!event.active) sim.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }
  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }
  function dragended(event, d) {
    if (!event.active) sim.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
  return d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended)
}

watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => renderGraph())
  } else if (simulation) {
    simulation.stop()
    simulation = null
  }
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
    simulation = null
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: rgba(30, 30, 40, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 20px;
  width: 780px;
  max-width: 92vw;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.modal-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-title {
  font-size: 1.1rem;
  color: #f59e0b;
}

.hint-text {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.35);
}

.modal-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.modal-close:hover {
  color: white;
}

.network-container {
  width: 100%;
  height: 460px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.3);
  overflow: hidden;
}
</style>
