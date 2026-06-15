import asyncio
import json
import os
import sys
import threading
import re
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 修复 Windows GBK 编码问题
if sys.stdout.encoding and sys.stdout.encoding.lower() in ('gbk', 'gb2312', 'cp936'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from typing import Optional, Dict, List
from flask import Flask, render_template, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.game_engine import WerewolfEngine, GameState, Role
from engine.tts_manager import TTSManager

app = Flask(__name__, static_folder=None)
CORS(app)

# 前端静态文件路径
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'dist')
# 项目根目录（基于 server.py 自身位置推导，不依赖 CWD）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# 音频文件目录
AUDIO_DIR = os.path.join(BASE_DIR, 'audio')

# TTS 管理器（全局单例，edge-tts 无需模型加载）
tts_manager = TTSManager(audio_dir=AUDIO_DIR)

# TTS 结果存储: {game_id: {log_id: audio_url}}
# 后台线程按 log_id 回填，API 端点按 log_id 合并，彻底消除索引错位
tts_results: Dict[str, Dict[str, str]] = {}
tts_results_lock = threading.Lock()

# TTS 线程池（限制并发 3，防止被微软边缘节点风控）
tts_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="TTS")

# 游戏活跃标志（TTS 线程检查此标志，游戏停止后丢弃结果）
game_active = False
game_active_lock = threading.Lock()

# 游戏状态存储
current_game: Optional[WerewolfEngine] = None
game_states: Dict[str, GameState] = {}
game_logs_queue: queue.Queue = queue.Queue()
game_running = False
game_init_error: Optional[str] = None
game_initialized = threading.Event()  # 用于通知游戏初始化完成
game_lock = threading.Lock()  # 用于保护共享变量的线程锁


def run_async_game(api_key: str = None, human_player_index: int = -1, step_delay: float = 1.5):
    """在后台线程中运行游戏"""
    global current_game, game_running, game_logs_queue, game_init_error, game_initialized
    
    async def _run():
        global game_running, game_init_error, game_initialized, current_game, game_states, game_logs_queue
        
        try:
            game_init_error = None
            game_running = True
            global game_active
            with game_active_lock:
                game_active = True
            game_initialized.clear()  # 重置事件
            
            print("[游戏引擎] 开始创建游戏...")
            
            # 创建新游戏引擎
            player_names = ["小刚", "小红", "小明", "小李", "张三", "李四", "王五", "赵六", "孙七"]
            config = {"step_delay": step_delay, "log_dir": LOG_DIR, "tts_manager": tts_manager}
            with game_lock:
                current_game = WerewolfEngine(player_names, config=config, human_player_index=human_player_index)
            print(f"[游戏引擎] 游戏已创建，ID: {current_game.state.game_id}, 真人玩家: {human_player_index}")
            
            # 配置 LLM 客户端
            if api_key:
                print(f"[游戏引擎] 配置 LLM 客户端，API Key: {api_key[:10]}...")
                from openai import AsyncOpenAI
                current_game.llm_client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            else:
                print("[游戏引擎] 未提供 API Key，将使用 Mock 模式")
            
            # 状态变化回调
            def on_state_change(state: GameState):
                game_states[state.game_id] = state
                # 将日志放入队列
                for log in state.logs:
                    game_logs_queue.put(log)
            
            current_game.on_state_change = on_state_change
            
            # 标记游戏已初始化
            game_initialized.set()
            print("[游戏引擎] 游戏初始化完成，开始运行游戏循环...")
            
            # 运行游戏
            await current_game.run_game_loop()
            print("[游戏引擎] 游戏结束")
            
        except Exception as e:
            import traceback
            print(f"[游戏引擎] 错误：{e}")
            print(traceback.format_exc())
            game_init_error = str(e)
            game_initialized.set()  # 即使出错也触发事件
        finally:
            game_running = False
            with game_active_lock:
                game_active = False
    
    # 在新的事件循环中运行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run())
    loop.close()


@app.route('/')
def index():
    """提供前端首页"""
    if os.path.exists(os.path.join(FRONTEND_DIST, 'index.html')):
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return jsonify({"message": "前端文件未构建，请先运行 npm run build", "status": "no_frontend"})


@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """提供前端静态资源（JS/CSS等）"""
    assets_dir = os.path.join(FRONTEND_DIST, 'assets')
    return send_from_directory(assets_dir, filename)


@app.route('/api/game/start', methods=['POST'])
def start_game():
    """开始新游戏"""
    global current_game, game_running, game_init_error
    
    print("[API] ====== 进入 start_game 路由 ======")
    
    try:
        print(f"[API] 当前 game_running: {game_running}")
        
        if game_running:
            print("[API] 游戏正在运行中，返回 400")
            return jsonify({"error": "游戏正在运行中", "code": "ALREADY_RUNNING"}), 400
        
        print("[API] 获取请求数据")
        data = request.json or {}
        api_key = data.get('api_key') or os.getenv("DEEPSEEK_API_KEY", "")
        human_player_index = data.get('human_player_index', -1)  # -1 = 无真人, 0-8 = 真人位置
        step_delay = float(data.get('step_delay', 1.5))  # 步骤间延迟秒数
        game_init_error = None
        
        # 重置状态
        print("[API] 重置状态")
        current_game = None
        game_logs_queue.queue.clear()
        game_states.clear()
        game_initialized.clear()
        with tts_results_lock:
            tts_results.clear()

        print(f"[API] 收到开始游戏请求，API Key: {api_key[:10] if api_key else 'None'}...")

        # edge-tts 无需加载，即时可用

        # 在后台线程启动游戏
        print("[API] 创建游戏线程")
        thread = threading.Thread(target=run_async_game, args=(api_key, human_player_index, step_delay), name="GameThread")
        thread.daemon = True
        print("[API] 启动游戏线程")
        thread.start()
        
        print("[API] 游戏线程已启动，等待初始化...")
        
        # 使用事件等待游戏初始化（最多等待 30 秒）
        print("[API] 开始等待 game_initialized 事件...")
        initialized = game_initialized.wait(timeout=30)
        
        print(f"[API] 初始化等待完成，initialized: {initialized}")
        
        if not initialized:
            print("[API] 等待超时，游戏未初始化")
            return jsonify({
                "error": "游戏初始化超时，请重试",
                "code": "TIMEOUT"
            }), 500
        
        # 检查结果
        if game_init_error:
            print(f"[API] 检测到初始化错误：{game_init_error}")
            return jsonify({
                "error": f"游戏初始化失败：{game_init_error}",
                "code": "INIT_ERROR"
            }), 500
        
        # 使用锁保护访问 current_game
        with game_lock:
            if not current_game:
                print("[API] 游戏对象未创建")
                return jsonify({
                    "error": "游戏创建失败，请重试",
                    "code": "CREATION_ERROR"
                }), 500
            
            if not current_game.state:
                print("[API] 游戏状态未初始化")
                return jsonify({
                    "error": "游戏状态未初始化",
                    "code": "STATE_ERROR"
                }), 500
        
        # 使用锁保护访问 current_game 数据
        with game_lock:
            players_data = [{
                "id": p.id,
                "name": p.name,
                "role": p.role.value if hasattr(p, 'role') and p.role else None,
                "is_alive": p.is_alive,
                "is_human": p.is_human if hasattr(p, 'is_human') else False
            } for p in current_game.state.players.values()]

            game_id = current_game.state.game_id
            day = current_game.state.day
            phase = current_game.state.phase.value
            start_time = current_game.state.start_time

        print(f"[API] 游戏初始化成功，返回数据：{game_id}")

        return jsonify({
            "success": True,
            "game_id": game_id,
            "players": players_data,
            "day": day,
            "phase": phase,
            "start_time": start_time.isoformat() if start_time else None
        })
    
    except Exception as e:
        import traceback
        print(f"[API] start_game 路由异常：{e}")
        print(traceback.format_exc())
        return jsonify({
            "error": f"服务器内部错误：{str(e)}",
            "code": "INTERNAL_ERROR"
        }), 500


# ---------------------------------------------------------------------------
# 文本清洗：去除 Markdown、XML 标签、URL 等不适宜 TTS 朗读的内容
# ---------------------------------------------------------------------------
def sanitize_tts_text(text: str) -> str:
    """清理文本中的 Markdown/XML/code/URL，保留口语化内容"""
    if not text:
        return ""
    # 移除 XML/HTML 标签（LLM 输出的 <VOTE> 等）
    text = re.sub(r'<[^>]+>', '', text)
    # 移除 markdown 代码块
    text = re.sub(r'```[\w]*\n?.*?```', '', text, flags=re.DOTALL)
    # 移除行内代码
    text = re.sub(r'`[^`]+`', '', text)
    # 移除 URL
    text = re.sub(r'https?://[^\s]+', '', text)
    # 移除邮箱
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    # 移除 markdown 符号和特殊括号（# * _ ~ 【】等）
    text = re.sub(r'[#*_~`\[\]()>|【】「」]', '', text)
    # 压缩空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_speech_text(content: str) -> str:
    """从日志内容中提取发言文本（去除 '发言:' 前缀）"""
    m = re.search(r"发言[:：]\s*(.*)", content)
    text = m.group(1) if m else content
    return sanitize_tts_text(text)


def split_long_speech(text: str, max_chars: int = 120) -> list:
    """长文本按句号拆分，防止 edge-tts 合成超时"""
    if len(text) <= max_chars:
        return [text]
    # 按句号/问号/叹号切割，每段不超过 max_chars
    parts = []
    sentences = re.split(r'([。！？!?])', text)
    buf = ""
    for i in range(0, len(sentences), 2):
        seg = sentences[i]
        punct = sentences[i + 1] if i + 1 < len(sentences) else ""
        chunk = seg + punct
        if len(buf) + len(chunk) <= max_chars:
            buf += chunk
        else:
            if buf:
                parts.append(buf.strip())
            buf = chunk
    if buf:
        parts.append(buf.strip())
    return parts if parts else [text]


# ---------------------------------------------------------------------------
# TTS 后台生成：按 log_id 回填，支持线程池和长文本拆分
# ---------------------------------------------------------------------------
def _tts_gen_for_game(gid, logs):
    """为指定游戏的 SPEECH 日志逐个生成 TTS（在后台线程池调度）"""
    if not tts_manager.is_loaded:
        return

    tasks = []
    for log in logs:
        if log.get("type") != "SPEECH" or not log.get("player_id"):
            continue
        # 游戏引擎同步生成时已设置 audio_url，无需再生成
        if log.get("audio_url"):
            continue
        log_id = log.get("log_id")
        if not log_id:
            continue
        with tts_results_lock:
            if gid in tts_results and log_id in tts_results[gid]:
                continue

        player_id = log["player_id"]
        speech_text = extract_speech_text(log.get("content", ""))
        if len(speech_text) < 3:
            with tts_results_lock:
                tts_results.setdefault(gid, {})[log_id] = ""
            continue

        try:
            idx = max(0, min(int(player_id.replace("P", "")) - 1, 8))
        except ValueError:
            idx = 0

        tasks.append((log_id, player_id, speech_text, idx))

    if not tasks:
        return

    def gen_one(log_id, player_id, text, idx):
        """单个 TTS 生成任务（在 ThreadPoolExecutor 中运行）"""
        # 长文本拆分为多段
        segments = split_long_speech(text)
        urls = []
        for seg_text in segments:
            with game_active_lock:
                if not game_active:
                    print(f"[TTS] 🛑 [{player_id}] 游戏已停止，丢弃")
                    return None
            print(f"[TTS] ⏳ [{player_id}] {len(seg_text)}字: {seg_text[:40]}...")
            result = tts_manager.generate(seg_text, player_id, idx)
            if result:
                urls.append(f"/api/audio/{os.path.basename(result['filepath'])}")
            # 生成后不再检查 game_active：已生成的音频总是保存
            # （即使游戏结束，回放时仍可用）

        if urls:
            # 多段音频用逗号拼接（前端按逗号拆开依次播放）
            combined = ",".join(urls)
            with tts_results_lock:
                tts_results.setdefault(gid, {})[log_id] = combined
            print(f"[TTS] ✅ [{player_id}] {len(urls)}段音频 -> {combined[:60]}...")
        else:
            with tts_results_lock:
                tts_results.setdefault(gid, {})[log_id] = ""
            print(f"[TTS] ❌ [{player_id}] 生成失败")

    # 提交到线程池（限制并发3）
    for task in tasks:
        tts_pool.submit(gen_one, *task)


def try_generate_tts(game_id):
    """检查游戏是否有未处理的 SPEECH 日志，有则启动 TTS 生成"""
    if not tts_manager.is_loaded:
        return
    with game_lock:
        if game_id not in game_states:
            return
        logs = list(game_states[game_id].logs)

    # 按 log_id 检查是否有需要 TTS 但尚未生成的
    # （新游戏由 game_engine 同步生成并已携带 audio_url，跳过）
    pending = False
    for log in logs:
        if log.get("type") == "SPEECH" and log.get("player_id"):
            # 如果日志已有 audio_url（由 game_engine 同步生成），跳过
            if log.get("audio_url"):
                continue
            log_id = log.get("log_id")
            if not log_id:
                continue
            with tts_results_lock:
                if game_id not in tts_results or log_id not in tts_results[game_id]:
                    pending = True
                    break
    if not pending:
        return

    # 后台提交（由 ThreadPoolExecutor 管理线程，不再手动 new Thread）
    tts_pool.submit(_tts_gen_for_game, game_id, logs)
    print(f"[TTS] 📤 提交 {game_id[:12]} 的 TTS 任务至线程池")


@app.route('/api/game/<game_id>/state')
def get_game_state(game_id: str):
    """获取游戏状态"""
    if game_id in game_states:
        state = game_states[game_id]

        # 触发后台 TTS 生成（不阻塞响应）
        try_generate_tts(game_id)

        players_data = []
        is_human_mode = False
        human_player_id = None
        human_is_wolf = False
        for p in state.players.values():
            player_info = {
                "id": p.id,
                "name": p.name,
                "role": p.role.value if hasattr(p, 'role') and p.role else None,
                "is_alive": p.is_alive,
                "is_human": p.is_human if hasattr(p, 'is_human') else False,
                "has_antidote": p.has_antidote if hasattr(p, 'has_antidote') else False,
                "has_poison": p.has_poison if hasattr(p, 'has_poison') else False,
                "is_hunter_revealed": p.is_hunter_revealed if hasattr(p, 'is_hunter_revealed') else False,
            }
            if player_info["is_human"]:
                is_human_mode = True
                human_player_id = p.id
                if p.role and p.role.value == "狼人":
                    human_is_wolf = True
            players_data.append(player_info)

        # 真人狼人模式下：标记狼队友并显示其身份
        if is_human_mode and human_is_wolf:
            for pi in players_data:
                if pi["role"] == "狼人":
                    pi["is_wolf_teammate"] = True
                else:
                    pi["role"] = None

        # 人类玩家模式下，过滤掉上帝视角日志
        raw_logs = state.logs[-100:]
        if is_human_mode:
            human_player_id = next(
                (p.id for p in state.players.values()
                 if hasattr(p, 'is_human') and p.is_human),
                None
            )
            logs = [
                log for log in raw_logs
                if not log.get("hidden", False)
                or log.get("player_id") == human_player_id
            ]
        else:
            logs = raw_logs

        # 合并后台 TTS 结果到日志中（按 log_id 匹配，绝对精确）
        with tts_results_lock:
            if game_id in tts_results:
                game_tts = tts_results[game_id]
                for log in logs:
                    lid = log.get("log_id")
                    if lid and lid in game_tts:
                        url = game_tts[lid]
                        if url:  # 非空才设置
                            log["audio_url"] = url

        # 人类玩家待处理操作
        human_pending = None
        if current_game and hasattr(current_game, 'get_human_prompt'):
            human_pending = current_game.get_human_prompt()

        return jsonify({
            "game_id": state.game_id,
            "day": state.day,
            "phase": state.phase.value,
            "winner": state.winner,
            "players": players_data,
            "logs": logs,
            "vote_results": getattr(state, 'vote_results', []),
            "is_over": state.phase.value == "游戏结束",
            "human_pending_action": human_pending,
            "start_time": state.start_time.isoformat() if state.start_time else None
        })

    print(f"[API] 游戏状态未找到：{game_id}")
    return jsonify({"error": "Game not found", "code": "NOT_FOUND"}), 404


@app.route('/api/game/<game_id>/logs/new')
def get_new_logs(game_id: str):
    """获取新日志（轮询方式）"""
    logs = []
    try:
        while True:
            log = game_logs_queue.get_nowait()
            logs.append(log)
    except queue.Empty:
        pass
    
    # 人类玩家模式下，过滤掉上帝视角日志（但保留真人玩家自己的行动）
    if current_game and hasattr(current_game, 'state'):
        human_player_id = None
        has_human = False
        for p in current_game.state.players.values():
            if hasattr(p, 'is_human') and p.is_human:
                has_human = True
                human_player_id = p.id
                break
        if has_human:
            logs = [
                log for log in logs 
                if not log.get("hidden", False) 
                or log.get("player_id") == human_player_id
            ]
    
    return jsonify({"logs": logs})


@app.route('/api/game/status')
def game_status():
    """获取游戏运行状态"""
    global game_running, current_game, game_init_error
    
    return jsonify({
        "running": game_running,
        "game_id": current_game.state.game_id if current_game and current_game.state else None,
        "error": game_init_error,
        "current_game_exists": current_game is not None,
        "state_exists": current_game.state is not None if current_game else False
    })


@app.route('/api/game/<game_id>/human/prompt')
def get_human_prompt(game_id: str):
    """获取人类玩家当前需要执行的操作"""
    global current_game
    
    if not current_game or current_game.state.game_id != game_id:
        return jsonify({"error": "Game not found", "code": "NOT_FOUND"}), 404
    
    if not hasattr(current_game, 'get_human_prompt'):
        return jsonify({"error": "Not supported", "code": "NOT_SUPPORTED"}), 400
    
    prompt = current_game.get_human_prompt()
    return jsonify({
        "pending": prompt is not None,
        "action": prompt
    })


@app.route('/api/game/<game_id>/human/action', methods=['POST'])
def submit_human_action(game_id: str):
    """提交人类玩家的操作"""
    global current_game
    
    if not current_game or current_game.state.game_id != game_id:
        return jsonify({"error": "Game not found", "code": "NOT_FOUND"}), 404
    
    if not hasattr(current_game, 'set_human_action'):
        return jsonify({"error": "Not supported", "code": "NOT_SUPPORTED"}), 400
    
    data = request.json or {}
    decision = data.get('decision', '')
    
    print(f"[人类玩家] 收到前端决策: {decision}")
    
    success = current_game.set_human_action({"decision": decision})
    
    if success:
        return jsonify({"success": True, "decision": decision})
    else:
        return jsonify({"error": "No pending human action or game not waiting", "code": "NO_PENDING"}), 400


@app.route('/api/game/stop', methods=['POST'])
def stop_game():
    """停止当前正在运行的游戏的接口"""
    global current_game, game_running

    if not game_running:
        return jsonify({"success": True, "message": "当前没有游戏在运行"})

    with game_lock:
        if current_game and hasattr(current_game, 'request_stop'):
            print("[API] 发送停止请求到游戏引擎...")
            current_game.request_stop()

    # 等待游戏线程结束（最多 5 秒）
    for _ in range(50):
        if not game_running:
            break
        import time
        time.sleep(0.1)

    print(f"[API] 游戏已停止, game_running={game_running}")
    return jsonify({"success": True, "message": "游戏已终止"})


@app.route('/api/health')
def health_check():
    """健康检查端点"""
    global game_running, current_game, game_init_error

    game_id = None
    if current_game and current_game.state:
        game_id = current_game.state.game_id

    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "game": {
            "running": game_running,
            "game_id": game_id,
            "has_game": current_game is not None,
            "has_state": current_game.state is not None if current_game else False,
            "error": game_init_error
        },
        "tts": {
            "type": "edge-tts",
            "ready": True,
            "results_count": sum(len(v) for v in tts_results.values()) if tts_results else 0
        }
    })


@app.route('/api/game/history')
def get_game_history():
    """获取游戏历史记录"""
    history = []
    if os.path.exists(LOG_DIR):
        for filename in sorted(os.listdir(LOG_DIR), reverse=True)[:20]:
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(LOG_DIR, filename), 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history.append({
                            "game_id": data.get("game_id", filename),
                            "winner": data.get("winner", "未知"),
                            "days": data.get("days", 0),
                            "players": len(data.get("players", [])),
                            "start_time": data.get("start_time", ""),
                            "filename": filename
                        })
                except:
                    pass
    return jsonify(history)


@app.route('/api/game/replay/<filename>')
def get_game_replay(filename: str):
    """获取游戏回放数据"""
    log_path = os.path.join(LOG_DIR, filename)
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify(data)
    return jsonify({"error": "File not found"}), 404


@app.route('/api/leaderboard')
def get_leaderboard():
    """获取排行榜 - 从历史游戏记录中统计"""
    try:
        player_stats = {}

        if not os.path.exists(LOG_DIR):
            return jsonify([])

        for filename in os.listdir(LOG_DIR):
            if not filename.endswith('.json'):
                continue
            try:
                with open(os.path.join(LOG_DIR, filename), 'r', encoding='utf-8') as f:
                    game = json.load(f)
            except:
                continue

            winner = game.get('winner')
            players = game.get('players', {})

            for pid, pdata in players.items():
                name = pdata.get('name', pid)
                role = pdata.get('role', '未知')

                if name not in player_stats:
                    player_stats[name] = {'total_games': 0, 'wins': 0, 'roles': {}}

                player_stats[name]['total_games'] += 1
                player_stats[name]['roles'][role] = player_stats[name]['roles'].get(role, 0) + 1

                is_wolf = (role == '狼人')
                if (is_wolf and winner == '狼人阵营') or (not is_wolf and winner == '好人阵营'):
                    player_stats[name]['wins'] += 1

        leaderboard = []
        for name, stats in player_stats.items():
            main_role = max(stats['roles'], key=stats['roles'].get)
            win_rate = (stats['wins'] / stats['total_games']) * 100 if stats['total_games'] > 0 else 0
            leaderboard.append({
                'name': name,
                'role': main_role,
                'total_games': stats['total_games'],
                'wins': stats['wins'],
                'win_rate': round(win_rate, 1)
            })

        # 按胜率排序
        leaderboard.sort(key=lambda x: x['win_rate'], reverse=True)
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1

        return jsonify(leaderboard[:10])

    except Exception as e:
        print(f"[Leaderboard] Error: {e}")
        return jsonify([])


@app.route('/api/roles/info')
def get_roles_info():
    """获取角色信息"""
    roles = [
        {"id": "werewolf", "name": "狼人", "icon": "🐺", "description": "夜晚可以杀死一名玩家"},
        {"id": "seer", "name": "预言家", "icon": "🔮", "description": "夜晚可以查验身份"},
        {"id": "witch", "name": "女巫", "icon": "🧪", "description": "拥有解药和毒药"},
        {"id": "hunter", "name": "猎人", "icon": "🏹", "description": "死亡时可带走一人"},
        {"id": "villager", "name": "平民", "icon": "👤", "description": "通过投票找出狼人"}
    ]
    return jsonify(roles)


@app.route('/api/audio/<path:filename>')
def serve_audio(filename):
    """提供 TTS 生成的音频文件"""
    safe_path = os.path.normpath(os.path.join(AUDIO_DIR, filename))
    if not safe_path.startswith(os.path.normpath(AUDIO_DIR)):
        return jsonify({"error": "Invalid path"}), 403
    if os.path.exists(safe_path):
        return send_file(safe_path, mimetype='audio/wav')
    return jsonify({"error": "Audio not found"}), 404


@app.route('/<path:filename>')
def serve_static(filename):
    """SPA catch-all：未匹配路由返回前端页面"""
    file_path = os.path.join(FRONTEND_DIST, filename)
    if os.path.exists(file_path) and not os.path.isdir(file_path):
        return send_from_directory(FRONTEND_DIST, filename)
    if os.path.exists(os.path.join(FRONTEND_DIST, 'index.html')):
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return jsonify({"error": "Not found"}), 404


if __name__ == '__main__':
    print("=" * 60)
    print("🎮 狼人杀多 Agent 对战平台 - 前端服务器")
    print("=" * 60)
    print(f"📍 本地访问：http://localhost:5000")
    print(f"📍 外部访问：http://127.0.0.1:5000")
    print(f"📍 健康检查：http://localhost:5000/api/health")
    print("=" * 60)
    print("🎤 TTS: edge-tts (即时可用，无需注册)")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
