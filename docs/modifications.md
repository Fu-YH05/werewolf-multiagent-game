# 项目修改记录

> 记录自仓库同步后所有代码改动，按修改时间排序。

---

## 1. 环境修复

### 1.1 httpx / openai 版本冲突

- **问题**: `httpx` 版本过高导致 `AsyncClient` 的 `proxies` 参数不兼容
- **修复**: `requirements.txt` 指定 `openai>=2.0.0`，其依赖的 `httpx` 版本兼容

### 1.2 前端构建指向错误

- **问题**: Flask 服务器指向 `frontend-react/dist/`（静态 Mock 页面），实际使用 Vue 项目位于 `frontend/`
- **修复**: `server.py` 中 `FRONTEND_DIST` 路径改为指向 `frontend/dist/`

### 1.3 Windows GBK 编码崩溃

- **问题**: Flask 终端输出含 Emoji 和中文，Windows GBK 编码无法处理，服务器启动崩溃 `UnicodeEncodeError`
- **修复**: 启动时设置环境变量 `PYTHONIOENCODING=utf-8`

---

## 2. 新增功能

### 2.1 结束游戏按钮 🛑

**涉及文件**:
- `engine/game_engine.py`
- `frontend/server.py`
- `frontend/src/services/api.js`
- `frontend/src/components/ControlPanel.vue`
- `frontend/src/App.vue`

**改动详情**:

| 文件 | 改动 |
|------|------|
| `engine/game_engine.py` | 新增 `_stop_requested` 标志位、`request_stop()` 方法；`run_game_loop()` 循环中检查标志位及时中断；`request_agent_decision()` 入口快速返回 `PASS`；`request_stop()` 同时解除人类玩家 Future 等待 |
| `frontend/server.py` | 新增 `POST /api/game/stop` 路由，发送停止信号后等待线程退出（最多 5 秒） |
| `frontend/src/services/api.js` | 新增 `stopGame()` 方法 |
| `frontend/src/components/ControlPanel.vue` | 新增红色 🛑 结束游戏按钮，绑定 `@stop` 事件；新增 `.btn-danger` CSS 样式 |
| `frontend/src/App.vue` | 新增 `stopGame()` 处理函数，调用 API 后执行 `stopPolling()` |

### 2.2 自动结束旧局再开始新游戏

**涉及文件**: `frontend/src/components/ControlPanel.vue`、`frontend/src/App.vue`

**改动**:
- `ControlPanel.vue`: 移除开始按钮的 `:disabled="isRunning"` 绑定，按钮始终可点击
- `App.vue`: `startGame()` 开头检测 `isRunning`，如为 true 则先调 `stopGame()` 再继续创建新游戏

### 2.3 直播/回放状态分离

**涉及文件**: `frontend/src/App.vue`

**改动**:
- 新增 `viewingReplay` / `savedLiveState` 两个响应式变量
- `loadReplay()`: 加载回放前将当前游戏状态（gameId, gameState, players, logs, voteResults, isRunning, gameStartTime）保存到 `savedLiveState`，再停止轮询、加载回放数据
- 新增 `returnToLive()`: 从 `savedLiveState` 恢复所有直播状态，如有仍在运行的直播则恢复轮询
- 模板新增黄色横幅: `v-if="viewingReplay"`，显示当前回放 ID 和「返回直播」按钮
- `startGame()` 开头清除 `viewingReplay` 和 `savedLiveState`
- 回放模式下（`savedLiveState` 有值）停止按钮依然可用

### 2.4 刷新后自动恢复游戏

**涉及文件**: `frontend/server.py`、`frontend/src/App.vue`

**改动**:
- `server.py`: `/api/health` 响应新增 `game_id` 字段
- `App.vue` `onMounted`: 调用 `/api/health` 检查是否有游戏在运行，若有则自动设置 `currentGameId`、`isRunning`，拉取当前状态，恢复轮询和计时器

### 2.5 暂停同步计时器

**涉及文件**: `frontend/src/App.vue`

**改动**:
- `togglePause()`: 暂停时同时清除 `durationInterval`，恢复时重新调用 `startDurationTimer()`

### 2.6 排行榜从历史记录统计

**涉及文件**: `frontend/server.py`

**改动**:
- `/api/leaderboard` 路由重写：直接遍历 `logs/*.json` 文件，统计每位玩家的总场次、胜利次数、主要角色，按胜率排序返回 Top 10
- 不再依赖 `leaderboard.json` 文件

---

## 3. Bug 修复

### 3.1 排行榜 win_rate 崩溃

- **文件**: `frontend/server.py`
- **问题**: `entry.win_rate` 是方法调用，被当作属性访问 → `AttributeError`
- **修复**: `entry.win_rate` → `entry.get_win_rate()`

### 3.2 历史记录不显示

- **文件**: `frontend/server.py`、`engine/game_engine.py`
- **根因**: `logs/` 路径使用相对路径，依赖启动时的当前工作目录（CWD）。服务器从 `frontend/` 启动时找不到项目根目录下的 `logs/`
- **修复**:
  - `server.py`: 新增 `BASE_DIR` 和 `LOG_DIR` 全局常量，从 `__file__` 文件位置推导项目根路径，不依赖 CWD
  - `server.py`: `get_game_history()` 和 `get_game_replay()` 使用 `LOG_DIR`
  - `server.py`: `get_game_history()` 中修正一处残留的 `log_dir`（小写）→ `LOG_DIR`（大写）
  - `engine/game_engine.py`: `__init__` 从 `config` 接受 `log_dir` 参数；`save_game_log()` 使用 `os.path.join(self.log_dir, ...)` 并自动 `os.makedirs`
  - `server.py`: `run_async_game()` 向 config 传入 `log_dir: LOG_DIR`

### 3.3 游戏结束/停止后未保存回放

- **根因**: 同上路径问题，`logs/` 目录不存在导致 `save_game_log()` 写文件失败
- **修复**: 同 3.2 修复，路径正确 + `os.makedirs` 自动创建目录

### 3.4 刷新后计时器归零

**涉及文件**: `frontend/server.py`、`frontend/src/App.vue`

**根因**: 计时器基于客户端 `Date.now() - gameStartTime`，刷新后 `gameStartTime` 重置为当前时间

**修复**:
- `server.py`: `/api/game/<id>/state` 和 `/api/game/start` 返回 `start_time` 字段（游戏实际开始时间 ISO 格式）
- `App.vue`: `startGame()` 和 `onMounted` 中的重连逻辑从 `data.start_time` / `state.start_time` 解析时间戳赋值给 `gameStartTime`

### 3.5 异常崩溃未保存游戏日志

**涉及文件**: `engine/game_engine.py`

**根因**: LLM 调用抛异常时直接从 `run_game_loop()` 跳出到 `_run()` 的 `except`，中间的 `save_game_log()` 执行不到。手动停止因 `request_agent_decision()` 中 `if _stop_requested: return "PASS"` 跳过了 LLM 调用，所以不受影响。

**修复**: `run_game_loop()` 的 while 循环外加 `try/except`，捕获异常后仍调用 `save_game_log()` 保存当前进度再返回。

---

## 4. 后续新增功能

### 4.1 点击玩家查看发言 💬

**涉及文件**: `frontend/src/components/PlayerCard.vue`、`frontend/src/App.vue`、`engine/game_engine.py`

**改动**:
- `PlayerCard.vue`: 卡片新增点击事件，点击后弹出浮窗（`Teleport` 到 body），显示该玩家最近 5 条发言；新增 `speech-available` 高亮样式提示可点击
- `App.vue`: 新增 `playerSpeeches` 计算属性，从 `logs` 中按玩家分拣发言传递给每个卡片
- `game_engine.py`: 修复 `log_event("SPEECH")` 未传 `player_id` 的问题，加 `player_id=p.id`

### 4.2 白天/黑夜日志背景切换 🌗

**涉及文件**: `frontend/src/components/LogsPanel.vue`、`frontend/src/App.vue`

**改动**:
- `App.vue`: 新增 `isDaytime` 计算属性，检测当前阶段（天亮/发言/投票/结束为白天）
- `LogsPanel.vue`: 接收 `isDaytime` prop，白天时日志面板背景变为暖色调 `rgba(255, 240, 210, 0.06)`，滚动区域变暖 `rgba(255, 235, 200, 0.12)`

### 4.3 侧栏折叠 ↔

**涉及文件**: `frontend/src/App.vue`

**改动**:
- 左右侧栏各新增折叠按钮（`collapse-left` / `collapse-right`），点击切换
- 折叠时侧栏宽度缩至 40px（仅显示按钮），中央游戏区域 `1fr` 自动填充
- 使用 `grid-template-columns` 过渡动画（0.35s）

### 4.4 AI 发言自然化 🗣️

**涉及文件**: `agents/role_agents.py`

**改动**:
- `system_base` 提示第 299 行末尾增加限制："直接参与游戏，不要自我介绍，不要固定句式，发言的首部不要用固定的短语，像普通人聊天一样说话。"
- `speak` action 提示增加禁止固定句式指令

### 4.5 笔记区域 📝

**涉及文件**: `frontend/src/components/LogsPanel.vue`、`frontend/src/App.vue`

**改动**:
- `LogsPanel.vue` 日志面板底部新增笔记输入框
- 笔记内容按 `gameId` 存入 `localStorage`，不同对局自动切换
- 点击表头展开/收起

### 4.6 可拖拽分割条 📏

**涉及文件**: `frontend/src/components/LogsPanel.vue`

**改动**:
- 新增两个拖拽分割条：
  - **顶部分割条**（日志与笔记之间）：控制日志/笔记的分配比例，总面板高度不变
  - **底部分割条**（笔记下方）：控制整个面板的总高度
- 面板总高度默认 520px，笔记高度默认 160px，均存入 `localStorage` 持久化
- 移除 CSS 过渡延迟，确保拖拽实时响应

### 4.7 语音输入 🎤

**涉及文件**: `frontend/src/components/HumanActionPanel.vue`

**改动**:
- 发言输入框右侧新增话筒按钮
- 按住 🎤 按钮录音，松开自动语音转文字填入输入框
- 录音时按钮变红 + 脉冲动画 + 状态提示
- 基于浏览器 Web Speech API（`webkitSpeechRecognition`），无需外部服务
- 错误处理（权限拒绝、未检测到语音等）

---

## 5. 文件变更汇总（第一阶段）

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `engine/game_engine.py` | ✅ 修改 | 停止标志、`request_stop()`、`log_dir` 支持、异常时保存日志、`player_id` 修复 |
| `frontend/server.py` | ✅ 修改 | 停止路由、排行榜从日志统计、路径修复、`start_time` 返回 |
| `frontend/src/services/api.js` | ✅ 修改 | 新增 `stopGame()` |
| `frontend/src/components/ControlPanel.vue` | ✅ 修改 | 结束按钮、开始按钮始终可用 |
| `frontend/src/App.vue` | ✅ 修改 | 回放分离、刷新恢复、自动停止、侧栏折叠、昼夜检测、speeches 传参 |
| `frontend/src/components/PlayerCard.vue` | ✅ 修改 | 点击查看发言、speech 弹窗 |
| `frontend/src/components/LogsPanel.vue` | ✅ 修改 | 昼夜背景、笔记区域、可拖拽分割条 |
| `frontend/src/components/HumanActionPanel.vue` | ✅ 修改 | 语音输入（🎤 按钮 + Web Speech API）|
| `agents/role_agents.py` | ✅ 修改 | AI 发言自然化提示词 |
| `.gitignore` | 🆕 新增 | 排除 `__pycache__`、`dist` |
| `docs/modifications.md` | 🆕 新增 | 本文件 |

---

## 6. TTS v2：ChatTTS → edge-tts 迁移

### 6.1 背景

ChatTTS 本地生成质量极佳，但在 CPU 上推理耗时 10-180 秒/条，完全无法满足实时游戏需求。Azure TTS 注册受阻，因此选用 edge-tts（调用微软 Edge 免费云服务，与 Azure TTS 相同神经语音品质）。

### 6.2 迁移内容

- `engine/tts_manager.py`：重写为 edge-tts 封装，无模型加载、无注册要求
- 9 种中文神经语音对应 9 个玩家角色
- 语速/音高微调（VOICE_STYLES）增加个性区分
- 返回值从 `str`（文件路径）改为 `Dict{"filepath","duration"}`，支持游戏引擎同步等待
- 新增 `_get_wav_duration()`：从 WAV 头读取时长
- 新增 `generate_batch()` 批量接口

### 6.3 相关清理

- `chattts_models/` 目录（1.2GB）已删除
- `frontend-react/` 目录（82MB）已删除
- `requirements.txt`：移除 `ChatTTS`、`torch`、`soundfile`，添加 `edge-tts`

---

## 7. 日志索引重构：log_id 唯一标识

### 7.1 痛点

TTS 线程按日志列表的 `index` 回填 `audio_url`，但前端/后端经过过滤（人类模式隐藏日志）后索引偏移，导致音频匹配错位。

### 7.2 修复

- `engine/game_engine.py`：`log_event()` 中用 `uuid.uuid4().hex[:12]` 为每条日志生成 `log_id`
- `frontend/server.py`：`tts_results` 存储键从 `int`（索引）改为 `str`（log_id）
- 状态端点按 `log_id` 精确合并，不再依赖 `ol is log` 对象身份比较
- 前端 `enqueueSpeechLog()` 用 `log_id` 去重

---

## 8. 前端音频队列状态机

### 8.1 旧方案问题

- 数组 `audioQueue` + `isPlaying` 布尔，时序竞争频繁
- 对象身份 `ol is log` 匹配易错位
- 15 秒超时（ChatTTS 遗留）太长
- 降级播放后 edge-tts 音频到达会重复播放

### 8.2 新方案

- 状态机：`PENDING → PLAYING → DONE`，每个 `log_id` 仅处理一次
- `playedLogIds` / `fallbackLogIds` Set 双重去重
- 3 秒降级超时（匹配 edge-tts 生成速度）
- 音频 URL 到达后自动取消降级定时器
- 降级播放后丢弃后续到达的 edge-tts 音频

### 8.3 Freshness 保鲜检查

- 队列处理器检查 `item.day < day.value`，过时发言自动跳过
- 防止 mock 模式下游戏跑完、音频才到达的"阴魂不散"问题

### 8.4 标签清洗

- 前端 `cleanSpeechText()` 增加 `replace(/<[^>]+>/g, '')` 和 Markdown 过滤
- 后端 `sanitize_tts_text()` 同步增加 `【】` 过滤
- 解决浏览器 SpeechSynthesis 降级时读出 `<VOTE>`、`【发言】` 等乱码

---

## 9. 游戏引擎同步 TTS

### 9.1 改造前

```python
# 异步：server.py 后台线程生成，游戏引擎不等待
audio_url = ""  # 占位
self.log_event("SPEECH", ..., audio_url=audio_url)
await asyncio.sleep(self.step_delay * 0.6)
```

### 9.2 改造后

```python
# 同步：游戏引擎等 TTS 生成完成再继续
loop = asyncio.get_event_loop()
tts_result = await loop.run_in_executor(None, self._generate_tts, speech, p.id)
if tts_result:
    audio_url = self.tts_manager.get_audio_url(tts_result["filepath"])
    wait_time = float(tts_result.get("duration", 0))
self.log_event("SPEECH", ..., audio_url=audio_url)
await asyncio.sleep(max(2.0, wait_time + 0.5))  # 等音频播完
```

### 9.3 效果

- 每条发言生成 TTS 后，日志直接带 `audio_url`，无需异步回填
- 游戏引擎等待音频时长 + 0.5 秒缓冲后才继续下一位
- TTS 失败时至少等 2 秒，防止日志刷屏
- 重试机制：edge-tts 云端瞬断时自动重试一次

---

## 10. 其他优化

### 10.1 后端并发控制

- `concurrent.futures.ThreadPoolExecutor(max_workers=3)` 取代原始 `threading.Thread`
- 限制并发请求数，防止被微软边缘节点风控
- `game_active` 生命周期标志：游戏停止后不再启动新 TTS，新游戏清空旧结果

### 10.2 LLM 提示词优化

- 发言提示增加"多用语气词（啊、呢、吧、嘛、哦）"
- "禁止列点、禁止编号、用短句"
- 增加口语化示例

### 10.3 呼吸灯动画

- 3 层 CSS 动画：`breathe-card`（外发光）+ `breathe-avatar`（头像缩放）+ `breathe-ring`（环脉冲）
- 发言时玩家名称变色 + 文字发光
- `.player-avatar` 增加 `position: relative` 支持伪元素

### 10.4 停止/重启修复（仍有问题 ⚠️）

**涉及文件**: `frontend/server.py`、`frontend/src/App.vue`

**改动**:
- `server.py` `stop_game()`: 改为强制设置 `game_running = False`，清空 `game_active`、`tts_results`、`game_states`、`game_logs_queue`，不等线程退出，允许立即开始新局
- `App.vue` `startGame()`: 开始时先调 `stopGame()` 再等待服务器确认停止（最多 5 秒）
- `App.vue` `stopGame()`: 调用 API 后立即 `resetAudioQueue()` + `stopPolling()`
- `App.vue`: 新增 `resetAudioQueue()` 清空音频状态

**⚠️ 已知问题**: 停止后重启仍有概率出现 400 错误（旧 server 进程未完全退出占用端口），需手动 `taskkill /F /IM python.exe` 后重试。

---

## 11. 四维分析看板

新增 4 个可视化分析功能，帮助玩家洞察游戏数据。

### 11.1 投票关系网络图 🔗

**涉及文件**:
- `frontend/src/components/analysis/VoteNetworkModal.vue`

**改动**:
- 基于 D3.js force-directed graph 的力导向图弹窗
- 节点 = 玩家（圆形，按角色着色）
- 有向边 = 投票方向，边粗细 = 投票次数
- 节点可拖拽，鼠标悬停显示详情
- 游戏结束后按阵营着色（狼人红/预言家蓝/女巫紫/猎人橙/平民绿）
- 按钮：「🔗 关系网络」在投票记录旁

### 11.2 游戏时间线侧边条 ⏱

**涉及文件**:
- `frontend/src/components/analysis/TimelineStrip.vue`

**改动**:
- 36px 宽的竖条，嵌在中间游戏区域左侧
- 每条日志对应一个小圆点，按日志类型着色
- **点击圆点 → LogsPanel 自动滚动到对应日志 + 金色高亮闪烁动画**
- 旁有 D1/D2/D3 天数标记

### 11.3 玩家存活淘汰树 🌳

**涉及文件**:
- `frontend/src/components/analysis/EliminationTree.vue`

**改动**:
- 从日志中解析每晚死亡、白天放逐、女巫毒杀、猎人带走事件
- 按天展示存活玩家和淘汰事件
- 平安夜显示「🌙 平安夜」而非错误死亡
- 按钮弹出紧凑模态框

### 11.4 发言情绪热力图 🔥

**涉及文件**:
- `frontend/src/utils/emotionAnalysis.js`
- `frontend/src/components/analysis/EmotionHeatmap.vue`

**改动**:
- 关键词字典方案（方案 A）进行情绪分析：
  - 语气词（啊、呀、吧、我去、天哪）：+2/个
  - 强调词（绝对、一定、太、超级）：+3/个
  - 反问词（为什么、怎么、难道）：+2/个
  - 感叹号：+1/个
  - 冷静词（嗯、可能、也许）：-1/个
  - 归一化到 0-100 分
- 矩阵网格：Y 轴=玩家，X 轴=天数
- 色阶：深蓝(冷静) → 橙黄(正常) → 深红(非常激动)
- 悬停显示发言次数和平均情绪分
- 按钮弹出紧凑模态框

### 11.5 日志跳转高亮

**涉及文件**:
- `frontend/src/components/LogsPanel.vue`
- `frontend/src/components/LogEntry.vue`

**改动**:
- LogsPanel 新增 `highlightLogIndex` prop 和 `scrollToLog()` 暴露方法
- LogEntry 新增 `highlighted` prop，金色闪烁动画
- `displayLogsWithOrigIdx` 计算属性维护原始索引映射

### 11.6 新增依赖

- `frontend/package.json`：添加 `d3: ^7.9.0`

---

## 12. 完整文件变更汇总

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `engine/game_engine.py` | ✅ 修改 | 停止标志、`request_stop()`、`log_dir` 支持、异常时保存日志、`player_id` 修复、旁白 TTS |
| `engine/tts_manager.py` | ✅ 重写 | ChatTTS → edge-tts，返回 `{filepath, duration}` 格式，豆包语音支持 |
| `frontend/server.py` | ✅ 修改 | 停止路由、排行榜从日志统计、路径修复、`start_time` 返回、强制停止、豆包语音参数 |
| `frontend/src/services/api.js` | ✅ 修改 | 新增 `stopGame()` |
| `frontend/src/components/ControlPanel.vue` | ✅ 修改 | 结束按钮、开始按钮始终可用、豆包 TTS 开关 |
| `frontend/src/App.vue` | ✅ 重写 | 回放分离、刷新恢复、自动停止、侧栏折叠、昼夜检测、音频队列状态机、四维分析看板集成 |
| `frontend/src/components/PlayerCard.vue` | ✅ 修改 | 点击查看发言、speech 弹窗、呼吸灯动画 |
| `frontend/src/components/LogsPanel.vue` | ✅ 修改 | 昼夜背景、笔记区域、可拖拽分割条、日志跳转高亮、`defineExpose` |
| `frontend/src/components/LogEntry.vue` | ✅ 修改 | 高亮动画 |
| `frontend/src/components/HumanActionPanel.vue` | ✅ 修改 | 语音输入（🎤 按钮 + Web Speech API）|
| `agents/role_agents.py` | ✅ 修改 | AI 发言自然化提示词 |
| `frontend/src/components/analysis/TimelineStrip.vue` | 🆕 新增 | 游戏时间线侧边条 |
| `frontend/src/components/analysis/VoteNetworkModal.vue` | 🆕 新增 | 投票关系网络图弹窗 |
| `frontend/src/components/analysis/EliminationTree.vue` | 🆕 新增 | 玩家存活淘汰树 |
| `frontend/src/components/analysis/EmotionHeatmap.vue` | 🆕 新增 | 发言情绪热力图 |
| `frontend/src/utils/emotionAnalysis.js` | 🆕 新增 | 关键词情绪分析引擎 |
| `frontend/package.json` | ✅ 修改 | 添加 `d3: ^7.9.0` |
| `.gitignore` | 🆕 新增 | 排除 `__pycache__`、`dist` |
| `docs/modifications.md` | 🆕 新增 | 本文件 |
| `requirements.txt` | ✅ 修改 | 移除 ChatTTS/torch/soundfile，添加 edge-tts |
