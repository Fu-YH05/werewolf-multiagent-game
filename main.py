import asyncio
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from engine.game_engine import WerewolfEngine
from engine.evolution import EvolutionManager
from evaluation.evaluator import GameEvaluator, ReplayAnalyzer
from leaderboard.leaderboard import Leaderboard


def get_llm_client(api_key: str = None):
    """获取LLM客户端"""
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
    if api_key:
        from openai import AsyncOpenAI
        return AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    return None


async def run_single_game(player_names: list, llm_client=None):
    """运行单局游戏"""
    print("开始单局狼人杀游戏")
    engine = WerewolfEngine(player_names)
    
    if llm_client:
        engine.llm_client = llm_client
        print("LLM客户端已配置")
    else:
        print("使用Mock模式")
    
    game_state = await engine.run_game_loop()
    
    print("\n游戏评测")
    evaluator = GameEvaluator(game_state, engine.action_records)
    evaluation = evaluator.evaluate()
    
    print(f"游戏ID: {evaluation['game_id']}")
    print(f"胜利者: {evaluation['winner']}")
    print(f"综合评分: {evaluation['overall_rating']}")
    
    return game_state


async def run_evolution(player_names: list, iterations: int, llm_client=None):
    """运行自进化循环"""
    manager = EvolutionManager(player_names, iterations)
    if llm_client:
        manager.llm_client = llm_client
    await manager.run_evolution_cycle()


def show_leaderboard():
    """显示排行榜"""
    lb = Leaderboard()
    print(lb.generate_report())


def analyze_replay(log_file: str):
    """分析复盘日志"""
    print(f"分析复盘日志: {log_file}")
    analyzer = ReplayAnalyzer()
    log_data = analyzer.load_game_log(log_file)
    analysis = analyzer.analyze_game(log_data)
    
    print(f"\n游戏ID: {analysis['game_id']}")
    print(f"胜利者: {analysis['winner']}")
    
    print("\n关键时刻:")
    for moment in analysis["key_moments"]:
        print(f"  第{moment['day']}天 {moment['phase']}: {moment['content']}")
    
    print("\n建议:")
    for suggestion in analysis["suggestions"]:
        print(f"  - {suggestion}")


def main():
    parser = argparse.ArgumentParser(description="狼人杀多Agent对战系统")
    parser.add_argument('--mode', choices=['game', 'evolution', 'leaderboard', 'analyze'], 
                        default='game', help='运行模式')
    parser.add_argument('--iterations', type=int, default=5, help='进化迭代次数')
    parser.add_argument('--players', nargs='+', default=["小刚", "小红", "小明", "小李", "张三", "李四", "王五"],
                        help='玩家名称列表')
    parser.add_argument('--logfile', type=str, help='复盘日志文件路径')
    parser.add_argument('--api-key', type=str, help='DeepSeek API Key (也可通过环境变量 DEEPSEEK_API_KEY 设置)')
    
    args = parser.parse_args()
    
    llm_client = get_llm_client(args.api_key)
    
    if args.mode == 'game':
        asyncio.run(run_single_game(args.players, llm_client))
    elif args.mode == 'evolution':
        asyncio.run(run_evolution(args.players, args.iterations, llm_client))
    elif args.mode == 'leaderboard':
        show_leaderboard()
    elif args.mode == 'analyze':
        if args.logfile:
            analyze_replay(args.logfile)
        else:
            print("请指定复盘日志文件: --logfile <path>")


if __name__ == "__main__":
    main()