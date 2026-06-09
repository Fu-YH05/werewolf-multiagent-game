import asyncio
import random
import json
import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable


class Role(Enum):
    VILLAGER = "平民"
    WEREWOLF = "狼人"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER = "猎人"


class GamePhase(Enum):
    INIT = "初始化"
    NIGHT_START = "天黑请闭眼"
    WOLF_KILL = "狼人杀人"
    WITCH_ACT = "女巫行动"
    SEER_ACT = "预言家验人"
    HUNTER_CHECK = "猎人觉醒"
    DAY_START = "天亮请睁眼"
    DISCUSS = "自由发言"
    VOTE = "放逐投票"
    GAME_OVER = "游戏结束"


@dataclass
class Player:
    id: str
    name: str
    role: Optional[Role] = None
    is_alive: bool = True
    has_antidote: bool = True
    has_poison: bool = True
    is_hunter_revealed: bool = False
    agent_version: str = "v1.0"
    model_name: str = "deepseek-chat"
    is_human: bool = False  # 是否为人类玩家


@dataclass
class GameState:
    game_id: str
    day: int = 1
    phase: GamePhase = GamePhase.INIT
    players: Dict[str, Player] = field(default_factory=dict)
    night_killed: Optional[str] = None
    witch_saved: bool = False
    witch_poisoned: Optional[str] = None
    seer_check_result: Optional[Dict[str, str]] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    winner: Optional[str] = None
    vote_results: List[Dict[str, Any]] = field(default_factory=list)  # 投票结果记录
    first_day_random_start: bool = False  # 是否是首轮随机发言


@dataclass
class ActionRecord:
    player_id: str
    action_type: str
    target: Optional[str]
    timestamp: datetime
    reasoning: str = ""


class WerewolfEngine:
    def __init__(self, player_names: List[str], config: Optional[Dict] = None):
        self.config = config or {}
        self.state = GameState(game_id=self._generate_game_id())
        self.action_records: List[ActionRecord] = []
        self.on_state_change: Optional[Callable[[GameState], None]] = None
        
        for i, name in enumerate(player_names):
            pid = f"P{i+1}"
            self.state.players[pid] = Player(id=pid, name=name)
        
        self.role_config = [
            Role.WEREWOLF, Role.WEREWOLF,                 # 2狼人
            Role.SEER, Role.WITCH, Role.HUNTER,           # 3神职
            Role.VILLAGER, Role.VILLAGER, Role.VILLAGER, Role.VILLAGER    # 4平民
        ]
        
        self.winner = None
        self._initialize_llm_client()

    def _generate_game_id(self) -> str:
        return f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

    def _initialize_llm_client(self):
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if api_key:
            from openai import AsyncOpenAI
            self.llm_client = AsyncOpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        else:
            self.llm_client = None

    def log_event(self, event_type: str, content: str, hidden: bool = False, player_id: Optional[str] = None):
        log_entry = {
            "day": self.state.day,
            "phase": self.state.phase.value,
            "type": event_type,
            "content": content,
            "hidden": hidden,
            "player_id": player_id,
            "timestamp": datetime.now().isoformat()
        }
        self.state.logs.append(log_entry)
        
        prefix = "[上帝视角-私密]" if hidden else "[全局广播]"
        player_tag = f" [{player_id}]" if player_id else ""
        print(f"第{self.state.day}天 | {self.state.phase.value} | {prefix}{player_tag} {content}")
        
        if self.on_state_change:
            self.on_state_change(self.state)

    def record_action(self, player_id: str, action_type: str, target: Optional[str], reasoning: str = ""):
        self.action_records.append(ActionRecord(
            player_id=player_id,
            action_type=action_type,
            target=target,
            timestamp=datetime.now(),
            reasoning=reasoning
        ))

    def assign_roles(self):
        self.state.phase = GamePhase.INIT
        self.state.start_time = datetime.now()
        roles = self.role_config.copy()
        random.shuffle(roles)
        
        for pid, player in self.state.players.items():
            player.role = roles.pop()
            self.log_event("ROLE_ASSIGN", f"{player.id}({player.name}) 底牌: {player.role.value}", hidden=True)

    def get_alive_players(self) -> List[Player]:
        return [p for p in self.state.players.values() if p.is_alive]

    def get_wolves(self) -> List[Player]:
        return [p for p in self.get_alive_players() if p.role == Role.WEREWOLF]

    def get_good_players(self) -> List[Player]:
        return [p for p in self.get_alive_players() if p.role != Role.WEREWOLF]

    def check_victory(self) -> bool:
        alive = self.get_alive_players()
        wolves = [p for p in alive if p.role == Role.WEREWOLF]
        good = [p for p in alive if p.role != Role.WEREWOLF]
        
        if not wolves:
            self.winner = "好人阵营"
            return True
        
        civilians = [p for p in alive if p.role == Role.VILLAGER]
        roles = [p for p in alive if p.role in [Role.SEER, Role.WITCH, Role.HUNTER]]
        
        if not civilians or not roles:
            self.winner = "狼人阵营"
            return True
        
        if len(wolves) >= len(alive) / 2:
            self.winner = "狼人阵营"
            return True
        
        return False

    async def run_game_loop(self):
        self.assign_roles()
        self.log_event("GAME_START", "游戏开始！")
        
        while not self.check_victory():
            await self.run_night_phase()
            if self.check_victory():
                break
            await self.run_day_phase()
        
        self.state.phase = GamePhase.GAME_OVER
        self.state.end_time = datetime.now()
        self.state.winner = self.winner
        self.log_event("GAME_OVER", f"游戏结束！胜利者是: {self.winner}")
        
        self.save_game_log()
        return self.state

    async def run_night_phase(self):
        self.state.phase = GamePhase.NIGHT_START
        self.log_event("NIGHT_START", "天黑请闭眼...")
        
        self.state.night_killed, self.state.witch_saved, self.state.witch_poisoned = None, False, None
        
        wolves = self.get_wolves()
        if wolves:
            self.state.phase = GamePhase.WOLF_KILL
            target = await self.request_agent_decision(wolves[0], "kill", self.get_alive_players())
            self.state.night_killed = target
            self.log_event("ACTION", f"狼人击杀目标: {target}", hidden=True)
            self.record_action(wolves[0].id, "kill", target)
        
        witch = next((p for p in self.get_alive_players() if p.role == Role.WITCH), None)
        if witch:
            self.state.phase = GamePhase.WITCH_ACT
            dec = await self.request_agent_decision(witch, "witch", self.state.night_killed)
            if dec == "save" and witch.has_antidote:
                self.state.witch_saved, witch.has_antidote = True, False
                self.log_event("ACTION", "女巫使用了解药", hidden=True)
                self.record_action(witch.id, "save", self.state.night_killed)
            elif dec.startswith("poison_") and witch.has_poison:
                tgt = dec.split("_")[1]
                self.state.witch_poisoned, witch.has_poison = tgt, False
                self.log_event("ACTION", f"女巫毒杀了 {tgt}", hidden=True)
                self.record_action(witch.id, "poison", tgt)
        
        seer = next((p for p in self.get_alive_players() if p.role == Role.SEER), None)
        if seer:
            self.state.phase = GamePhase.SEER_ACT
            tgt = await self.request_agent_decision(seer, "seer", self.get_alive_players())
            tgt_role = self.state.players[tgt].role
            res = "狼人" if tgt_role == Role.WEREWOLF else "好人"
            self.state.seer_check_result[tgt] = res
            self.log_event("ACTION", f"预言家查验 {tgt} 结果: {res}", hidden=True)
            self.record_action(seer.id, "check", tgt)
        
        hunter = next((p for p in self.get_alive_players() if p.role == Role.HUNTER), None)
        if hunter:
            self.state.phase = GamePhase.HUNTER_CHECK
            hunter.is_hunter_revealed = True
            self.log_event("ACTION", "猎人觉醒", hidden=True)

    async def run_day_phase(self):
        self.state.phase = GamePhase.DAY_START
        deads = []
        
        if self.state.night_killed and not self.state.witch_saved:
            deads.append(self.state.night_killed)
        if self.state.witch_poisoned:
            deads.append(self.state.witch_poisoned)
        
        for d in deads:
            self.state.players[d].is_alive = False
            self._handle_death(d)
        
        dead_names = ",".join([self.state.players[d].name for d in deads]) if deads else "平安夜"
        self.log_event("ANNOUNCE", f"昨晚死亡: {dead_names}")
        
        if self.check_victory():
            return
        
        self.state.phase = GamePhase.DISCUSS
        self.log_event("DISCUSS_START", "进入自由发言阶段")
        
        alive_players = self.get_alive_players()
        
        if self.state.day == 1 and not self.state.first_day_random_start:
            random.shuffle(alive_players)
            self.state.first_day_random_start = True
            self.log_event("INFO", f"首轮发言随机顺序: {','.join([p.id for p in alive_players])}")
        
        for p in alive_players:
            speech = await self.request_agent_decision(p, "speak", None)
            self.log_event("SPEECH", f"{p.id}({p.name}) 发言: {speech}")
            self.record_action(p.id, "speak", None, speech)
        
        self.state.phase = GamePhase.VOTE
        self.log_event("VOTE_START", "进入放逐投票阶段")
        
        votes = {}
        vote_details = []
        
        for p in self.get_alive_players():
            v = await self.request_agent_decision(p, "vote", self.get_alive_players())
            self.log_event("VOTE", f"{p.id}({p.name}) 投票给 {v}")
            self.record_action(p.id, "vote", v)
            vote_details.append({"voter": p.id, "target": v})
            if v != "PASS":
                votes[v] = votes.get(v, 0) + 1
        
        vote_result_entry = {
            "day": self.state.day,
            "votes": votes,
            "details": vote_details,
            "total_voters": len(self.get_alive_players())
        }
        self.state.vote_results.append(vote_result_entry)
        
        if votes:
            max_v = max(votes.values())
            cands = [k for k, v in votes.items() if v == max_v]
            
            pk_round = 0
            max_pk_rounds = 3
            
            while len(cands) > 1 and pk_round < max_pk_rounds:
                pk_round += 1
                self.log_event("PK", f"平票！进入第{pk_round}轮PK: {','.join(cands)}")
                pk_votes = {}
                
                for p in self.get_alive_players():
                    v = await self.request_agent_decision(p, "vote", cands)
                    self.log_event("VOTE", f"{p.id}({p.name}) PK投票给 {v}")
                    self.record_action(p.id, "vote", v)
                    if v in cands:
                        pk_votes[v] = pk_votes.get(v, 0) + 1
                
                vote_result_entry[f"pk_{pk_round}"] = {"votes": pk_votes, "candidates": cands}
                
                if pk_votes:
                    max_pk_v = max(pk_votes.values())
                    cands = [k for k, v in pk_votes.items() if v == max_pk_v]
            
            if len(cands) == 1:
                target = cands[0]
            else:
                sorted_cands = sorted(cands)
                target = sorted_cands[0]
                self.log_event("INFO", f"经过{max_pk_rounds}轮PK仍平票，按姓名顺位淘汰: {target}")
            
            self.log_event("LYNCH", f"{target}({self.state.players[target].name}) 被放逐")
            self.state.players[target].is_alive = False
            self._handle_death(target)
        
        self.state.day += 1

    def _handle_death(self, player_id: str):
        player = self.state.players[player_id]
        if player.role == Role.HUNTER and player.is_alive:
            self.log_event("SKILL", f"猎人{player.id}发动技能！")
            target = random.choice([p.id for p in self.get_alive_players() if p.id != player_id])
            if target:
                self.state.players[target].is_alive = False
                self.log_event("SKILL", f"猎人带走了 {target}")

    async def request_agent_decision(self, agent: Player, action_type: str, context: Any) -> str:
        from agents.role_agents import RoleAgent
        
        print(f"[DEBUG] 请求决策: {agent.id}({agent.name}), 动作: {action_type}")
        role_agent = RoleAgent(agent, self.state, self.llm_client)
        result = await role_agent.make_decision(action_type, context)
        print(f"[DEBUG] 决策结果: {result}")
        return result

    def save_game_log(self):
        log_data = {
            "game_id": self.state.game_id,
            "start_time": self.state.start_time.isoformat() if self.state.start_time else None,
            "end_time": self.state.end_time.isoformat() if self.state.end_time else None,
            "winner": self.state.winner,
            "days": self.state.day,
            "players": {pid: {"name": p.name, "role": p.role.value, "is_alive": p.is_alive} 
                       for pid, p in self.state.players.items()},
            "logs": self.state.logs,
            "action_records": [{
                "player_id": ar.player_id,
                "action_type": ar.action_type,
                "target": ar.target,
                "timestamp": ar.timestamp.isoformat(),
                "reasoning": ar.reasoning
            } for ar in self.action_records]
        }
        
        log_path = f"logs/{self.state.game_id}.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"游戏日志已保存到: {log_path}")