/**
 * 发言情绪分析工具（关键词字典方案 A）
 *
 * 从发言文本中提取情绪 arousal 分数（0-100）
 * 基于语气词、强调词、反问等语言特征
 */

// 语气词（激动倾向）
const EXCLAMATION_WORDS = [
  '啊', '呀', '吧', '呢', '啦', '哦', '噢', '嘛',
  '我去', '天哪', '我的天', '完了', '不是吧', '真的假的',
  '哇', '哎哟', '哟', '啧啧',
]

// 强调/强情绪词
const INTENSE_WORDS = [
  '绝对', '一定', '肯定', '必须', '完全', '根本',
  '太', '超级', '非常', '极其', '特别', '十分',
  '最', '极', '彻底', '实在', '真是', '居然', '竟然',
]

// 反问/质疑词
const QUESTIONING_WORDS = [
  '为什么', '怎么', '凭什么', '难道', '哪里',
  '怎么可能', '是吗', '真的吗', '不会吧',
]

// 负面情绪词
const NEGATIVE_WORDS = [
  '可恶', '该死', '讨厌', '气死', '烦',
  '受不了', '过分', '无耻', '卑鄙',
  '郁闷', '糟糕', '坏了',
]

// 冷静/犹豫词（负向分数）
const CALM_WORDS = [
  '嗯', '呃', '可能', '也许', '大概', '好像',
  '我觉得', '我想', '估计', '似乎', '应该',
]

/**
 * 计算一段发言的情绪 arousal 分数
 * @param {string} text - 发言文本
 * @returns {{ score: number, level: string, details: object }}
 */
export function analyzeArousal(text) {
  if (!text) return { score: 0, level: '冷静', details: { signals: 0, exclamationCount: 0, questionCount: 0 } }

  const cleaned = text.replace(/[：:]\s*/, '') // 去掉 "发言:" 前缀
  const length = cleaned.length
  if (length < 2) return { score: 0, level: '冷静', details: { signals: 0, exclamationCount: 0, questionCount: 0 } }

  let signals = 0

  // 1. 语气词：+2/个
  let exclamationWordCount = 0
  for (const word of EXCLAMATION_WORDS) {
    let idx = 0
    while ((idx = cleaned.indexOf(word, idx)) !== -1) {
      exclamationWordCount++
      idx += word.length
    }
  }
  signals += exclamationWordCount * 2

  // 2. 强调词：+3/个
  let intenseWordCount = 0
  for (const word of INTENSE_WORDS) {
    let idx = 0
    while ((idx = cleaned.indexOf(word, idx)) !== -1) {
      intenseWordCount++
      idx += word.length
    }
  }
  signals += intenseWordCount * 3

  // 3. 反问词：+2/个
  let questionWordCount = 0
  for (const word of QUESTIONING_WORDS) {
    let idx = 0
    while ((idx = cleaned.indexOf(word, idx)) !== -1) {
      questionWordCount++
      idx += word.length
    }
  }
  signals += questionWordCount * 2

  // 4. 感叹号：+1/个
  const exclamationCount = (cleaned.match(/！/g) || []).length + (cleaned.match(/!/g) || []).length
  signals += exclamationCount

  // 5. 问号：+1/个（超过1个才算激动）
  const questionCount = (cleaned.match(/？/g) || []).length + (cleaned.match(/\?/g) || []).length
  if (questionCount > 1) signals += questionCount

  // 6. 负面词：+2/个
  let negativeWordCount = 0
  for (const word of NEGATIVE_WORDS) {
    let idx = 0
    while ((idx = cleaned.indexOf(word, idx)) !== -1) {
      negativeWordCount++
      idx += word.length
    }
  }
  signals += negativeWordCount * 2

  // 7. 冷静词：-1/个（衰减器）
  let calmWordCount = 0
  for (const word of CALM_WORDS) {
    let idx = 0
    while ((idx = cleaned.indexOf(word, idx)) !== -1) {
      calmWordCount++
      idx += word.length
    }
  }
  signals = Math.max(0, signals - calmWordCount)

  // 8. 长度因子：过长或过短的发言都有自然的抑制
  // 短发言（<10字）倾向冷静，长发言（>50字）情绪更容易累积
  const lengthFactor = length < 10 ? 0.6 : length > 50 ? 1.2 : 1.0

  // 归一化到 0-100
  const raw = (signals / Math.max(1, length)) * 100 * lengthFactor
  const score = Math.min(100, Math.round(raw * 5))

  let level
  if (score < 20) level = '冷静'
  else if (score < 45) level = '正常'
  else if (score < 70) level = '激动'
  else level = '非常激动'

  return {
    score,
    level,
    details: {
      signals,
      exclamationWordCount,
      intenseWordCount,
      questionWordCount,
      negativeWordCount,
      calmWordCount,
      exclamationCount,
      questionCount,
    }
  }
}

/**
 * 分析一局游戏中所有玩家的情绪数据
 * @param {Array} logs - 游戏日志
 * @param {Array} players - 玩家列表
 * @returns {Object} { playerDayMap: { playerId: { day: { count, score, texts } } }, dayRange: number }
 */
export function analyzeAllSpeeches(logs, players) {
  const speechLogs = logs.filter(l => l.type === 'SPEECH' && l.player_id && l.content)
  const playerMap = {}

  // 初始化玩家数据
  for (const p of players) {
    playerMap[p.id] = {}
  }

  for (const log of speechLogs) {
    const pid = log.player_id
    const day = log.day || 1
    if (!playerMap[pid]) playerMap[pid] = {}

    if (!playerMap[pid][day]) {
      playerMap[pid][day] = { count: 0, totalScore: 0, texts: [], maxScore: 0 }
    }

    const result = analyzeArousal(log.content)
    playerMap[pid][day].count++
    playerMap[pid][day].totalScore += result.score
    playerMap[pid][day].texts.push({
      text: log.content,
      score: result.score,
      level: result.level,
    })
    playerMap[pid][day].maxScore = Math.max(playerMap[pid][day].maxScore, result.score)
  }

  // 计算 dayRange
  let maxDay = 0
  for (const pid of Object.keys(playerMap)) {
    for (const d of Object.keys(playerMap[pid])) {
      maxDay = Math.max(maxDay, parseInt(d, 10))
    }
  }

  return { playerDayMap: playerMap, dayRange: maxDay }
}
