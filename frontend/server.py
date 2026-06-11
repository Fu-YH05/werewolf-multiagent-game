import asyncio
import json
import os
import sys
import threading
from datetime import datetime
from typing import Optional, Dict, List
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.game_engine import WerewolfEngine, GameState, Role

app = Flask(__name__, static_folder=None)
CORS(app)

# 前端静态文件路径
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend', 'dist')

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
            game_initialized.clear()  # 重置事件
            
            print("[游戏引擎] 开始创建游戏...")
            
            # 创建新游戏引擎
            player_names = ["小刚", "小红", "小明", "小李", "张三", "李四", "王五", "赵六", "孙七"]
            config = {"step_delay": step_delay}
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
        
        print(f"[API] 收到开始游戏请求，API Key: {api_key[:10] if api_key else 'None'}...")
        
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
        
        print(f"[API] 游戏初始化成功，返回数据：{game_id}")
        
        return jsonify({
            "success": True,
            "game_id": game_id,
            "players": players_data,
            "day": day,
            "phase": phase
        })
    
    except Exception as e:
        import traceback
        print(f"[API] start_game 路由异常：{e}")
        print(traceback.format_exc())
        return jsonify({
            "error": f"服务器内部错误：{str(e)}",
            "code": "INTERNAL_ERROR"
        }), 500


@app.route('/api/game/<game_id>/state')
def get_game_state(game_id: str):
    """获取游戏状态"""
    if game_id in game_states:
        state = game_states[game_id]
        print(f"[API] 获取游戏状态：{game_id}, 阶段：{state.phase.value}")
        
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
                    pi["is_wolf_teammate"] = True  # 前端据此显示身份
                else:
                    pi["role"] = None  # 非狼队友仍然隐藏身份
        
        # 人类玩家模式下，过滤掉上帝视角日志（但保留真人玩家自己的行动）
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
            "is_over": state.phase.value == "GAME_OVER",
            "human_pending_action": human_pending
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


@app.route('/api/health')
def health_check():
    """健康检查端点"""
    global game_running, current_game, game_init_error
    
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "game": {
            "running": game_running,
            "has_game": current_game is not None,
            "has_state": current_game.state is not None if current_game else False,
            "error": game_init_error
        }
    })


@app.route('/api/game/history')
def get_game_history():
    """获取游戏历史记录"""
    history = []
    log_dir = 'logs'
    if os.path.exists(log_dir):
        for filename in sorted(os.listdir(log_dir), reverse=True)[:20]:
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(log_dir, filename), 'r', encoding='utf-8') as f:
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
    log_path = os.path.join('logs', filename)
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return jsonify(data)
    return jsonify({"error": "File not found"}), 404


@app.route('/api/leaderboard')
def get_leaderboard():
    """获取排行榜"""
    try:
        from leaderboard.leaderboard import Leaderboard
        lb = Leaderboard()
        top_players = lb.get_overall_leaderboard()
        return jsonify([{
            "rank": i+1,
            "name": entry.name,
            "role": entry.role,
            "total_games": entry.total_games,
            "wins": entry.wins,
            "win_rate": entry.win_rate
        } for i, entry in enumerate(top_players[:10])])
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
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
