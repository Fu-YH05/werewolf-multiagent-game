import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from engine.game_engine import WerewolfEngine, GameState
from evaluation.evaluator import GameEvaluator, ReplayAnalyzer
from leaderboard.leaderboard import Leaderboard
from agents.role_agents import ExperiencePool


class EvolutionManager:
    def __init__(self, player_names: List[str], iterations: int = 5):
        self.player_names = player_names
        self.iterations = iterations
        self.experience_pool = ExperiencePool()
        self.leaderboard = Leaderboard()
        self.evolution_history = []

    async def run_evolution_cycle(self):
        """执行完整的进化循环：对局→分析→优化→再对局"""
        print("="*70)
        print("🦾 狼人杀 Agent 自进化系统启动")
        print(f"迭代次数: {self.iterations}")
        print("="*70)

        for iteration in range(1, self.iterations + 1):
            print(f"\n\n====== 第 {iteration} 轮迭代 ======")
            
            # 1. 运行一局游戏
            print("\n[Step 1] 运行游戏对局...")
            engine = WerewolfEngine(self.player_names)
            game_state = await engine.run_game_loop()
            
            # 2. 评测与分析
            print("\n[Step 2] 执行游戏评测...")
            evaluator = GameEvaluator(game_state, engine.action_records)
            evaluation = evaluator.evaluate()
            self._print_evaluation(evaluation)
            
            # 3. 经验提取与优化
            print("\n[Step 3] 提取经验并优化策略...")
            await self._extract_and_update_experiences(game_state, evaluation)
            
            # 4. 更新排行榜
            print("\n[Step 4] 更新排行榜...")
            self._update_leaderboard(game_state, evaluation)
            
            # 5. 记录进化历史
            self.evolution_history.append({
                "iteration": iteration,
                "game_id": game_state.game_id,
                "winner": game_state.winner,
                "evaluation": evaluation
            })
            
            print(f"\n第 {iteration} 轮迭代完成！")

        # 输出最终报告
        self._generate_final_report()

    async def _extract_and_update_experiences(self, game_state: GameState, evaluation: Dict):
        """从游戏结果中提取经验并更新经验池"""
        for player_id, player_eval in evaluation["player_evaluations"].items():
            role = player_eval["role"]
            analysis = player_eval["analysis"]
            
            if "获胜" in analysis:
                experience = self._generate_positive_experience(player_eval)
            else:
                experience = self._generate_negative_experience(player_eval)
            
            if experience:
                self.experience_pool.add_experience(role, experience)
                print(f"  [{role}] 新增经验: {experience}")

    def _generate_positive_experience(self, player_eval: Dict) -> str:
        """生成正向经验"""
        role = player_eval["role"]
        scores = player_eval["detailed_scores"]
        
        if role == "狼人" and scores["accuracy"] > 0.7:
            return f"作为狼人，精准击杀好人目标是获胜关键，本轮击杀准确率{scores['accuracy']*100:.0f}%"
        
        if role == "预言家" and scores["communication_quality"] > 0.8:
            return "作为预言家，清晰报出查验信息并带领好人投票能有效提高胜率"
        
        if role == "女巫" and scores["skill_usage"] > 0.7:
            return "作为女巫，合理使用解药和毒药能左右游戏走向"
        
        if role == "平民" and scores["accuracy"] > 0.6:
            return "作为平民，认真分析发言并投出正确票至关重要"
        
        return ""

    def _generate_negative_experience(self, player_eval: Dict) -> str:
        """生成负向经验（教训）"""
        role = player_eval["role"]
        scores = player_eval["detailed_scores"]
        
        if scores["accuracy"] < 0.4:
            return f"作为{role}，决策准确率太低，需要提高分析能力"
        
        if scores["communication_quality"] < 0.5:
            return f"作为{role}，发言不够清晰有力，需要改进表达方式"
        
        return ""

    def _update_leaderboard(self, game_state: GameState, evaluation: Dict):
        """更新排行榜数据"""
        winner_team = game_state.winner
        
        for player_id, player_eval in evaluation["player_evaluations"].items():
            player = game_state.players[player_id]
            is_winner = (player.role.value == "狼人" and winner_team == "狼人阵营") or \
                        (player.role.value != "狼人" and winner_team == "好人阵营")
            
            self.leaderboard.add_or_update_entry(
                player_id=player_id,
                name=player.name,
                role=player.role.value,
                version="v1.0",
                model="deepseek-chat",
                won=is_winner,
                score=player_eval["score"],
                stats=player_eval["detailed_scores"]
            )

    def _print_evaluation(self, evaluation: Dict):
        """打印评测结果"""
        print(f"  游戏ID: {evaluation['game_id']}")
        print(f"  胜利者: {evaluation['winner']}")
        print(f"  总回合: {evaluation['metrics']['total_turns']}")
        print(f"  综合评分: {evaluation['overall_rating']}")
        
        print("\n  玩家评分:")
        for pid, eval_data in evaluation["player_evaluations"].items():
            print(f"    {eval_data['name']}({eval_data['role']}): {eval_data['score']:.2f}分")

    def _generate_final_report(self):
        """生成最终进化报告"""
        print("\n" + "="*70)
        print("📊 自进化循环最终报告")
        print("="*70)
        
        print("\n【进化历史】")
        for record in self.evolution_history:
            print(f"  第{record['iteration']}轮: {record['winner']} - 评分:{record['evaluation']['overall_rating']}")
        
        print("\n【各角色经验积累】")
        for role, exps in self.experience_pool.pool.items():
            if exps:
                print(f"  {role}: {len(exps)}条经验")
                for i, exp in enumerate(exps[-3:], 1):
                    print(f"    {i}. {exp}")
        
        print("\n【排行榜】")
        print(self.leaderboard.generate_report())

        # 保存报告
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "iterations": self.iterations,
            "evolution_history": self.evolution_history,
            "experience_pool": self.experience_pool.pool,
            "leaderboard": {k: v.to_dict() for k, v in self.leaderboard.entries.items()}
        }
        
        with open(f"logs/evolution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print("\n报告已保存！")