import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from engine.game_engine import Role, GameState, ActionRecord, Player


class GameEvaluator:
    def __init__(self, game_state: GameState, action_records: List[ActionRecord]):
        self.game_state = game_state
        self.action_records = action_records
        self.evaluation_results = {}

    def evaluate(self) -> Dict[str, Any]:
        """执行完整的多维度评测"""
        results = {
            "game_id": self.game_state.game_id,
            "winner": self.game_state.winner,
            "duration": self._calculate_duration(),
            "overall_rating": 0,
            "player_evaluations": {},
            "team_evaluations": {},
            "metrics": {}
        }
        
        results["player_evaluations"] = self._evaluate_players()
        results["team_evaluations"] = self._evaluate_teams()
        results["metrics"] = self._calculate_metrics()
        results["overall_rating"] = self._calculate_overall_rating(results)
        
        return results

    def _calculate_duration(self) -> float:
        if self.game_state.start_time and self.game_state.end_time:
            return (self.game_state.end_time - self.game_state.start_time).total_seconds()
        return 0.0

    def _evaluate_players(self) -> Dict[str, Dict[str, Any]]:
        evaluations = {}
        
        for pid, player in self.game_state.players.items():
            evaluations[pid] = {
                "name": player.name,
                "role": player.role.value,
                "is_alive": player.is_alive,
                "team": "狼人阵营" if player.role == Role.WEREWOLF else "好人阵营",
                "score": 0,
                "detailed_scores": {},
                "analysis": ""
            }
            
            player_actions = [ar for ar in self.action_records if ar.player_id == pid]
            evaluations[pid]["detailed_scores"] = self._score_player_actions(player, player_actions)
            evaluations[pid]["score"] = sum(evaluations[pid]["detailed_scores"].values())
            evaluations[pid]["analysis"] = self._analyze_player_performance(player, player_actions)
        
        return evaluations

    def _score_player_actions(self, player: Player, actions: List[ActionRecord]) -> Dict[str, float]:
        scores = {
            "accuracy": 0.0,
            "strategic_value": 0.0,
            "communication_quality": 0.0,
            "skill_usage": 0.0,
            "survival": 1.0 if player.is_alive else 0.5
        }
        
        if not actions:
            return scores
        
        role = player.role.value
        wolf_actions = [ar for ar in actions if ar.action_type in ["kill", "vote", "speak"]]
        good_actions = [ar for ar in actions if ar.action_type in ["vote", "speak", "save", "poison", "check"]]
        
        if role == "狼人":
            scores["accuracy"] = self._score_wolf_accuracy(player, wolf_actions)
            scores["strategic_value"] = self._score_wolf_strategy(wolf_actions)
            scores["communication_quality"] = self._score_wolf_speaking(actions)
        else:
            scores["accuracy"] = self._score_good_accuracy(player, good_actions)
            scores["strategic_value"] = self._score_good_strategy(player, good_actions)
            scores["communication_quality"] = self._score_good_speaking(player, actions)
            
            if role == "女巫":
                scores["skill_usage"] = self._score_witch_skill(player, actions)
            elif role == "预言家":
                scores["skill_usage"] = self._score_seer_skill(player, actions)
        
        return scores

    def _score_wolf_accuracy(self, player: Player, actions: List[ActionRecord]) -> float:
        kills = [ar for ar in actions if ar.action_type == "kill" and ar.target]
        votes = [ar for ar in actions if ar.action_type == "vote" and ar.target != "PASS"]
        
        if not kills and not votes:
            return 0.5
        
        hit_count = 0
        total_actions = 0
        
        for action in kills:
            total_actions += 1
            if action.target and self.game_state.players[action.target].role != Role.WEREWOLF:
                hit_count += 1
        
        for action in votes:
            total_actions += 1
            if action.target and self.game_state.players[action.target].role != Role.WEREWOLF:
                hit_count += 1
        
        return hit_count / total_actions if total_actions > 0 else 0.5

    def _score_wolf_strategy(self, actions: List[ActionRecord]) -> float:
        return 0.7

    def _score_wolf_speaking(self, actions: List[ActionRecord]) -> float:
        speeches = [ar for ar in actions if ar.action_type == "speak"]
        if not speeches:
            return 0.5
        avg_length = sum(len(ar.reasoning) for ar in speeches) / len(speeches)
        return min(avg_length / 100, 1.0)

    def _score_good_accuracy(self, player: Player, actions: List[ActionRecord]) -> float:
        votes = [ar for ar in actions if ar.action_type == "vote" and ar.target != "PASS"]
        
        if not votes:
            return 0.5
        
        correct_votes = 0
        for vote in votes:
            if vote.target and self.game_state.players[vote.target].role == Role.WEREWOLF:
                correct_votes += 1
        
        return correct_votes / len(votes)

    def _score_good_strategy(self, player: Player, actions: List[ActionRecord]) -> float:
        return 0.6

    def _score_good_speaking(self, player: Player, actions: List[ActionRecord]) -> float:
        speeches = [ar for ar in actions if ar.action_type == "speak"]
        if not speeches:
            return 0.5
        
        if player.role == Role.SEER:
            avg_length = sum(len(ar.reasoning) for ar in speeches) / len(speeches)
            has_check_info = any("查验" in ar.reasoning or "验人" in ar.reasoning for ar in speeches)
            return min(avg_length / 100, 1.0) * (1.2 if has_check_info else 1.0)
        
        avg_length = sum(len(ar.reasoning) for ar in speeches) / len(speeches)
        return min(avg_length / 80, 1.0)

    def _score_witch_skill(self, player: Player, actions: List[ActionRecord]) -> float:
        saves = [ar for ar in actions if ar.action_type == "save"]
        poisons = [ar for ar in actions if ar.action_type == "poison" and ar.target]
        
        score = 0.5
        
        for save in saves:
            if save.target and self.game_state.players[save.target].role != Role.WEREWOLF:
                score += 0.3
        
        for poison in poisons:
            if poison.target and self.game_state.players[poison.target].role == Role.WEREWOLF:
                score += 0.3
        
        return min(score, 1.0)

    def _score_seer_skill(self, player: Player, actions: List[ActionRecord]) -> float:
        checks = [ar for ar in actions if ar.action_type == "check" and ar.target]
        speeches = [ar for ar in actions if ar.action_type == "speak"]
        
        score = 0.5
        
        if checks:
            score += 0.2
        
        if any("查验" in ar.reasoning or "验人" in ar.reasoning for ar in speeches):
            score += 0.3
        
        return min(score, 1.0)

    def _analyze_player_performance(self, player: Player, actions: List[ActionRecord]) -> str:
        role = player.role.value
        team = "狼人阵营" if player.role == Role.WEREWOLF else "好人阵营"
        winner = self.game_state.winner
        
        if team == winner:
            return f"{player.name}({role})所在阵营获胜！"
        else:
            return f"{player.name}({role})所在阵营失败。"

    def _evaluate_teams(self) -> Dict[str, Dict[str, Any]]:
        wolf_team = [p for p in self.game_state.players.values() if p.role == Role.WEREWOLF]
        good_team = [p for p in self.game_state.players.values() if p.role != Role.WEREWOLF]
        
        wolf_alive = sum(1 for p in wolf_team if p.is_alive)
        good_alive = sum(1 for p in good_team if p.is_alive)
        
        return {
            "狼人阵营": {
                "members": [p.name for p in wolf_team],
                "survivors": wolf_alive,
                "total": len(wolf_team),
                "won": self.game_state.winner == "狼人阵营",
                "efficiency": wolf_alive / len(wolf_team) if wolf_team else 0
            },
            "好人阵营": {
                "members": [p.name for p in good_team],
                "survivors": good_alive,
                "total": len(good_team),
                "won": self.game_state.winner == "好人阵营",
                "efficiency": good_alive / len(good_team) if good_team else 0
            }
        }

    def _calculate_metrics(self) -> Dict[str, Any]:
        total_actions = len(self.action_records)
        speech_actions = len([ar for ar in self.action_records if ar.action_type == "speak"])
        vote_actions = len([ar for ar in self.action_records if ar.action_type == "vote"])
        skill_actions = len([ar for ar in self.action_records if ar.action_type in ["kill", "save", "poison", "check"]])
        
        return {
            "total_turns": self.game_state.day,
            "total_actions": total_actions,
            "speech_count": speech_actions,
            "vote_count": vote_actions,
            "skill_usage_count": skill_actions,
            "action_density": total_actions / self.game_state.day if self.game_state.day > 0 else 0
        }

    def _calculate_overall_rating(self, results: Dict[str, Any]) -> float:
        player_scores = [p["score"] for p in results["player_evaluations"].values()]
        avg_player_score = sum(player_scores) / len(player_scores) if player_scores else 0
        return round(avg_player_score * 100, 1)


class ReplayAnalyzer:
    @staticmethod
    def load_game_log(file_path: str) -> Dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def analyze_game(log_data: Dict[str, Any]) -> Dict[str, Any]:
        analysis = {
            "game_id": log_data["game_id"],
            "winner": log_data["winner"],
            "key_moments": [],
            "role_performance": {},
            "suggestions": []
        }
        
        logs = log_data["logs"]
        actions = log_data.get("action_records", [])
        
        analysis["key_moments"] = ReplayAnalyzer._identify_key_moments(logs, actions)
        analysis["role_performance"] = ReplayAnalyzer._analyze_role_performance(log_data["players"], actions)
        analysis["suggestions"] = ReplayAnalyzer._generate_suggestions(log_data)
        
        return analysis

    @staticmethod
    def _identify_key_moments(logs: List[Dict], actions: List[Dict]) -> List[Dict]:
        key_moments = []
        
        for log in logs:
            if log["type"] in ["LYNCH", "ACTION", "SKILL"] and not log.get("hidden", False):
                key_moments.append({
                    "day": log["day"],
                    "phase": log["phase"],
                    "type": log["type"],
                    "content": log["content"],
                    "timestamp": log.get("timestamp")
                })
        
        return key_moments

    @staticmethod
    def _analyze_role_performance(players: Dict, actions: List[Dict]) -> Dict[str, Any]:
        role_performance = {}
        
        for pid, info in players.items():
            role = info["role"]
            if role not in role_performance:
                role_performance[role] = {"count": 0, "actions": 0, "survivors": 0}
            
            role_performance[role]["count"] += 1
            role_performance[role]["actions"] += len([a for a in actions if a["player_id"] == pid])
            if info["is_alive"]:
                role_performance[role]["survivors"] += 1
        
        return role_performance

    @staticmethod
    def _generate_suggestions(log_data: Dict) -> List[str]:
        suggestions = []
        winner = log_data["winner"]
        days = log_data["days"]
        
        if days <= 2:
            suggestions.append("游戏结束较快，建议增加玩家数量或延长讨论时间。")
        
        if winner == "狼人阵营":
            suggestions.append("狼人阵营获胜，好人阵营需要更好地组织策略和信息共享。")
        else:
            suggestions.append("好人阵营获胜，狼人阵营需要更好地伪装和配合。")
        
        return suggestions