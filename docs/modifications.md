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

- **文件**: `frontend/server.py`、`frontend/src/App.vue`
- **根因**: 计时器基于客户端 `Date.now() - gameStartTime`，刷新后 `gameStartTime` 重置为当前时间
- **修复**:
  - `server.py`: `/api/game/<id>/state` 和 `/api/game/start` 返回 `start_time` 字段（游戏实际开始时间 ISO 格式）
  - `App.vue`: `startGame()` 和 `onMounted` 中的重连逻辑从 `data.start_time` / `state.start_time` 解析时间戳赋值给 `gameStartTime`

---

## 4. 文件变更汇总

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `engine/game_engine.py` | ✅ 修改 | 停止标志、`request_stop()`、`log_dir` 支持、stop 检查 |
| `frontend/server.py` | ✅ 修改 | 停止路由、排行榜重写、路径修复、`start_time` 返回、编码修复 |
| `frontend/src/services/api.js` | ✅ 修改 | 新增 `stopGame()` |
| `frontend/src/components/ControlPanel.vue` | ✅ 修改 | 停止按钮、开始按钮禁用移除、新增 props |
| `frontend/src/App.vue` | ✅ 修改 | 回放分离、刷新恢复、自动停止、计时器修复 |
| `frontend/dist/` | ✅ 自动 | 前端构建产物（更新 3 次） |
| `docs/modifications.md` | 🆕 新增 | 本文件 |
| `requirements.txt` | ✅ 修改 | openai 版本兼容 |
