import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,  // 增加到 60 秒，给游戏初始化足够时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response:`, response.data)
    return response
  },
  (error) => {
    console.error('[API] Response error:', error)
    return Promise.reject(error)
  }
)

export const gameApi = {
  // 健康检查
  checkHealth: () => api.get('/health'),
  
  // 开始新游戏 (支持真人玩家参数、延迟配置、豆包语音)
  startGame: (apiKey = '', humanPlayerIndex = -1, stepDelay = 1.5, useDoubaoTTS = false, doubaoAppid = '', doubaoApiKey = '') => api.post('/game/start', { 
    api_key: apiKey,
    human_player_index: humanPlayerIndex,
    step_delay: stepDelay,
    use_doubao_tts: useDoubaoTTS,
    doubao_appid: doubaoAppid,
    doubao_api_key: doubaoApiKey
  }),
  
  // 获取游戏状态
  getGameState: (gameId) => api.get(`/game/${gameId}/state`),
  
  // 获取新日志
  getNewLogs: (gameId) => api.get(`/game/${gameId}/logs/new`),
  
  // 获取游戏状态
  getStatus: () => api.get('/game/status'),
  
  // 人类玩家：获取待处理操作
  getHumanPrompt: (gameId) => api.get(`/game/${gameId}/human/prompt`),
  
  // 人类玩家：提交操作
  submitHumanAction: (gameId, decision) => api.post(`/game/${gameId}/human/action`, { decision }),
  
  // 获取历史记录
  getHistory: () => api.get('/game/history'),
  
  // 获取回放
  getReplay: (filename) => api.get(`/game/replay/${filename}`),
  
  // 获取排行榜
  getLeaderboard: () => api.get('/leaderboard'),
  
  // 停止当前游戏
  stopGame: () => api.post('/game/stop'),

  // 获取角色信息
  getRolesInfo: () => api.get('/roles/info')
}

export default api
