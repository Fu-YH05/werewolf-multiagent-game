import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class LeaderboardEntry:
    def __init__(self, player_id: str, name: str, role: str, version: str, model: str):
        self.player_id = player_id
        self.name = name
        self.role = role
        self.version = version
        self.model = model
        self.total_games = 0
        self.wins = 0
        self.losses = 0
        self.avg_score = 0.0
        self.total_score = 0.0
        self.last_played = None
        self.skill_stats = {
            "accuracy": [],
            "strategic_value": [],
            "communication_quality": [],
            "skill_usage": []
        }

    def update(self, won: bool, score: float, stats: Optional[Dict] = None):
        self.total_games += 1
        if won:
            self.wins += 1
        else:
            self.losses += 1
        self.total_score += score
        self.avg_score = self.total_score / self.total_games
        self.last_played = datetime.now()
        
        if stats:
            for key in self.skill_stats:
                if key in stats:
                    self.skill_stats[key].append(stats[key])

    def get_win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "role": self.role,
            "version": self.version,
            "model": self.model,
            "total_games": self.total_games,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.get_win_rate(),
            "avg_score": self.avg_score,
            "total_score": self.total_score,
            "last_played": self.last_played.isoformat() if self.last_played else None,
            "skill_stats": {k: sum(v)/len(v) if v else 0 for k, v in self.skill_stats.items()}
        }


class Leaderboard:
    def __init__(self, file_path: str = "leaderboard/leaderboard.json"):
        self.file_path = file_path
        self.entries: Dict[str, LeaderboardEntry] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for player_id, entry_data in data.items():
                        entry = LeaderboardEntry(
                            player_id=entry_data["player_id"],
                            name=entry_data["name"],
                            role=entry_data["role"],
                            version=entry_data["version"],
                            model=entry_data["model"]
                        )
                        entry.total_games = entry_data["total_games"]
                        entry.wins = entry_data["wins"]
                        entry.losses = entry_data["losses"]
                        entry.avg_score = entry_data["avg_score"]
                        entry.total_score = entry_data["total_score"]
                        if entry_data["last_played"]:
                            entry.last_played = datetime.fromisoformat(entry_data["last_played"])
                        entry.skill_stats = entry_data.get("skill_stats", {
                            "accuracy": [],
                            "strategic_value": [],
                            "communication_quality": [],
                            "skill_usage": []
                        })
                        self.entries[player_id] = entry
            except Exception as e:
                print(f"加载排行榜失败: {e}")

    def _save(self):
        data = {pid: entry.to_dict() for pid, entry in self.entries.items()}
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_or_update_entry(self, player_id: str, name: str, role: str, version: str, model: str, 
                           won: bool, score: float, stats: Optional[Dict] = None):
        if player_id not in self.entries:
            self.entries[player_id] = LeaderboardEntry(player_id, name, role, version, model)
        
        self.entries[player_id].update(won, score, stats)
        self._save()

    def get_top_players(self, limit: int = 10, role_filter: Optional[str] = None) -> List[LeaderboardEntry]:
        filtered = [e for e in self.entries.values() if role_filter is None or e.role == role_filter]
        sorted_entries = sorted(filtered, key=lambda x: x.get_win_rate(), reverse=True)
        return sorted_entries[:limit]

    def get_player_stats(self, player_id: str) -> Optional[LeaderboardEntry]:
        return self.entries.get(player_id)

    def get_role_leaderboard(self, role: str) -> List[LeaderboardEntry]:
        return self.get_top_players(limit=10, role_filter=role)

    def get_overall_leaderboard(self) -> List[LeaderboardEntry]:
        return self.get_top_players(limit=10)

    def get_version_comparison(self, versions: List[str]) -> Dict[str, Dict[str, float]]:
        version_stats = {}
        
        for entry in self.entries.values():
            if entry.version in versions:
                if entry.version not in version_stats:
                    version_stats[entry.version] = {
                        "total_games": 0,
                        "wins": 0,
                        "avg_score": 0.0,
                        "count": 0
                    }
                version_stats[entry.version]["total_games"] += entry.total_games
                version_stats[entry.version]["wins"] += entry.wins
                version_stats[entry.version]["avg_score"] += entry.avg_score
                version_stats[entry.version]["count"] += 1
        
        for version, stats in version_stats.items():
            if stats["count"] > 0:
                stats["avg_score"] /= stats["count"]
            stats["win_rate"] = (stats["wins"] / stats["total_games"]) * 100 if stats["total_games"] > 0 else 0
        
        return version_stats

    def reset(self):
        self.entries = {}
        self._save()

    def generate_report(self) -> str:
        report = ["="*60]
        report.append("狼人杀 Agent Leaderboard 报告")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"总玩家数: {len(self.entries)}")
        report.append(f"总局数: {sum(e.total_games for e in self.entries.values())}")
        report.append("="*60)
        report.append("\n【综合排行榜 Top 10】")
        
        for i, entry in enumerate(self.get_overall_leaderboard(), 1):
            report.append(f"{i}. {entry.name} ({entry.role}) - 胜率: {entry.get_win_rate():.1f}% | 平均分: {entry.avg_score:.1f} | 局数: {entry.total_games}")
        
        report.append("\n【各角色排行榜】")
        for role in ["狼人", "预言家", "女巫", "猎人", "平民"]:
            report.append(f"\n{role}:")
            for i, entry in enumerate(self.get_role_leaderboard(role), 1):
                report.append(f"  {i}. {entry.name} - 胜率: {entry.get_win_rate():.1f}% | 局数: {entry.total_games}")
        
        report.append("\n" + "="*60)
        return "\n".join(report)