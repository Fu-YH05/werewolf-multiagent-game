import re
import random
import sys
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from engine.game_engine import Role, Player, GameState

# 导入人格系统
from .personalities import (
    get_random_personality,
    get_personality_prompt,
    get_personality_description,
    get_personality_icon,
    apply_personality_modifier
)

sys.stdout.reconfigure(encoding='utf-8')


class MemoryRetrieval:
    """RAG精检索系统 - 语义检索top-K相关记忆"""
    
    def __init__(self):
        self.memory_store = []
    
    def add_memory(self, day: int, phase: str, speaker: str, content: str, speaker_role: Optional[str] = None):
        self.memory_store.append({
            "day": day,
            "phase": phase,
            "speaker": speaker,
            "content": content,
            "speaker_role": speaker_role,
            "timestamp": len(self.memory_store)
        })
    
    def retrieve_top_k(self, query: str, k: int = 5) -> List[Dict]:
        if not self.memory_store:
            return []
        
        scores = []
        for mem in self.memory_store:
            score = self._calculate_relevance(query, mem)
            scores.append((score, mem))
        
        scores.sort(key=lambda x: -x[0])
        return [mem for _, mem in scores[:k]]
    
    def _calculate_relevance(self, query: str, memory: Dict) -> float:
        score = 0.0
        
        query_lower = query.lower()
        content_lower = memory["content"].lower()
        
        keywords = query_lower.split()
        for keyword in keywords:
            if keyword in content_lower:
                score += 1.0
        
        if memory["speaker"] in query_lower:
            score += 2.0
        
        if memory["phase"] in ["自由发言", "放逐投票"]:
            score += 0.5
        
        return score


class BeliefAuditor:
    """信念审计系统 - 新证据出现时重新评估旧信念"""
    
    def __init__(self):
        self.beliefs = {}
    
    def update_belief(self, player_id: str, belief_type: str, confidence: float, reason: str):
        if player_id not in self.beliefs:
            self.beliefs[player_id] = {}
        self.beliefs[player_id][belief_type] = {
            "confidence": confidence,
            "reason": reason,
            "updated_at": len(self.beliefs)
        }
    
    def audit_beliefs(self, new_evidence: Dict):
        decayed_beliefs = []
        
        for player_id, beliefs in self.beliefs.items():
            for belief_type, data in beliefs.items():
                data["confidence"] *= 0.8
                if data["confidence"] < 0.2:
                    decayed_beliefs.append((player_id, belief_type))
        
        for player_id, belief_type in decayed_beliefs:
            del self.beliefs[player_id][belief_type]
            if not self.beliefs[player_id]:
                del self.beliefs[player_id]
        
        return self.beliefs
    
    def get_belief_summary(self) -> str:
        summary = []
        for player_id, beliefs in self.beliefs.items():
            for belief_type, data in beliefs.items():
                summary.append(f"{player_id}: {belief_type} (置信度:{data['confidence']:.2f})")
        return "\n".join(summary) if summary else "暂无信念记录"


class SelfReflectionValidator:
    """Self-Reflection验证机制 - 6项自检"""
    
    def __init__(self, game_state: GameState, player: Player):
        self.game_state = game_state
        self.player = player
        self.day = game_state.day
    
    def validate(self, draft: str) -> Tuple[bool, List[str], str]:
        issues = []
        corrected = draft
        
        if self._check_fabrication(draft):
            issues.append("编造信息：发言中包含未验证的身份宣称")
            corrected = self._fix_fabrication(corrected)
        
        if self._check_day_consistency(draft):
            issues.append("天数矛盾：发言中提到的天数与当前天数不符")
            corrected = self._fix_day_consistency(corrected)
        
        if self._check_role_overreach(draft):
            issues.append("越权发言：超出自身角色权限的宣称")
            corrected = self._fix_role_overreach(corrected)
        
        if self._check_overconfidence(draft):
            issues.append("过度自信：使用绝对化表述")
            corrected = self._fix_overconfidence(corrected)
        
        if self._check_contradiction(draft):
            issues.append("逻辑矛盾：发言内容自相矛盾")
            corrected = self._fix_contradiction(corrected)
        
        if self._check_metalanguage(draft):
            issues.append("元语言：使用游戏机制外的术语")
            corrected = self._fix_metalanguage(corrected)
        
        return len(issues) == 0, issues, corrected
    
    def _check_fabrication(self, draft: str) -> bool:
        if self.player.role != Role.SEER:
            if "查验" in draft or "金水" in draft or "查杀" in draft:
                return True
        return False
    
    def _fix_fabrication(self, draft: str) -> str:
        draft = draft.replace("查验", "怀疑")
        draft = draft.replace("金水", "好人")
        draft = draft.replace("查杀", "可疑")
        return draft
    
    def _check_day_consistency(self, draft: str) -> bool:
        for match in re.findall(r"第(\d+)天", draft):
            if int(match) != self.day:
                return True
        return False
    
    def _fix_day_consistency(self, draft: str) -> str:
        return re.sub(r"第(\d+)天", f"第{self.day}天", draft)
    
    def _check_role_overreach(self, draft: str) -> bool:
        if self.player.role != Role.WITCH:
            if "解药" in draft or "毒药" in draft or "毒" in draft:
                return True
        if self.player.role != Role.HUNTER:
            if "开枪" in draft:
                return True
        return False
    
    def _fix_role_overreach(self, draft: str) -> str:
        draft = draft.replace("解药", "救")
        draft = draft.replace("毒药", "毒")
        draft = draft.replace("开枪", "反击")
        return draft
    
    def _check_overconfidence(self, draft: str) -> bool:
        absolute_terms = ["肯定", "绝对", "一定", "百分百", "确定"]
        for term in absolute_terms:
            if term in draft:
                return True
        return False
    
    def _fix_overconfidence(self, draft: str) -> str:
        replacements = {
            "肯定": "可能",
            "绝对": "也许",
            "一定": "可能",
            "百分百": "很可能",
            "确定": "认为"
        }
        for old, new in replacements.items():
            draft = draft.replace(old, new)
        return draft
    
    def _check_contradiction(self, draft: str) -> bool:
        if "相信" in draft and "怀疑" in draft:
            return True
        return False
    
    def _fix_contradiction(self, draft: str) -> str:
        if "相信" in draft and "怀疑" in draft:
            draft = draft.replace("相信", "倾向于相信")
        return draft
    
    def _check_metalanguage(self, draft: str) -> bool:
        meta_terms = ["逻辑", "分析", "推理", "策略", "身份"]
        count = sum(1 for term in meta_terms if term in draft)
        return count > 2
    
    def _fix_metalanguage(self, draft: str) -> str:
        meta_terms = ["逻辑", "分析", "推理", "策略"]
        for term in meta_terms:
            draft = draft.replace(term, "想法")
        return draft


class RoleAgent:
    PROMPT_TEMPLATES = {
        "system_base": """你正在参与一场9人狼人杀游戏。
你的名字是 {name}({player_id})。底牌是：【{role}】。
{personality_prompt}
{role_objective}

当前存活玩家: {alive_players}

【三段式决策要求】
1. 心声（内心独白）：分析局势、推测身份、制定策略（不超过100字）
2. 表现（类人化行为）：根据人格特征和身份选择发言风格和行为模式
3. 行动（决策输出）：按照指定格式输出最终决策

【相关记忆】
{relevant_memories}

【信念状态】
{belief_summary}

【以往的历史经验/教训】
{past_experiences}

请严格按照三段式结构进行推理与行动，并体现你的人格特征。""",

        "role_objectives": {
            "平民": "目标：找出狼人并放逐。仔细听取其他玩家发言，寻找逻辑漏洞，投票给最可疑的人。策略：保持中立，分析发言，不轻易站队。",
            "狼人": "目标：消灭所有好人。白天伪装成好人或悍跳神职，晚上击杀关键目标。策略：伪装身份，误导好人，夜晚优先击杀神职。严禁投票或击杀队友！",
            "预言家": "目标：带领好人阵营胜利。每晚查验一人身份，白天必须起跳并报出查验结果。策略：先验边缘人物，及时报查验结果。",
            "女巫": "目标：保护好人阵营。拥有一瓶解药和一瓶毒药。解药可以救被狼人击杀的玩家，毒药可以毒杀任意玩家。策略：谨慎用药，关键时救关键人物。",
            "猎人": "目标：带领好人阵营胜利。被投票放逐时可以开枪带走一名玩家。策略：隐藏身份，关键时刻亮身份带队。"
        },

        "actions": {
            "speak": """【阶段: 发言】请按照三段式结构输出：
【心声】分析当前局势，思考自己的策略（不超过100字）
【表现】你的行为风格和态度（如：冷静分析、激动反驳、谨慎发言等）
【发言】结合心声和表现，输出你的发言内容（不超过200字）""",
            "vote": """【阶段: 投票】请按照三段式结构输出：
【心声】分析投票对象，思考投票策略（不超过100字）
【表现】投票时的行为表现（如：果断投票、犹豫后投票、跟风投票等）
【行动】<VOTE>玩家ID</VOTE> 或 <VOTE>PASS</VOTE>""",
            "kill": """【阶段: 狼人杀人】请按照三段式结构输出：
【心声】分析击杀目标，思考战术（不超过100字）
【表现】狼队协作时的行为表现（如：果断指认、犹豫讨论、伪装犹豫等）
【行动】<KILL>玩家ID</KILL>""",
            "seer": """【阶段: 预言家查验】请按照三段式结构输出：
【心声】分析查验目标，思考策略（不超过100字）
【表现】查验时的行为表现（如：优先查边缘、查疑似狼、查关键人物等）
【行动】<CHECK>玩家ID</CHECK>""",
            "witch": """【阶段: 女巫行动】昨夜死亡: {killed_player}。解药状态:{has_antidote}, 毒药状态:{has_poison}。请按照三段式结构输出：
【心声】分析局势，决定是否用药（不超过100字）
【表现】用药时的行为表现（如：果断救人、谨慎毒杀、保守观望等）
【行动】<WITCH>save</WITCH> 或 <WITCH>poison_玩家ID</WITCH> 或 <WITCH>pass</WITCH>"""
        }
    }

    def __init__(self, player: Player, game_state: GameState, llm_client):
        self.player = player
        self.game_state = game_state
        self.llm_client = llm_client
        self.experience_pool = {}
        self.memory_retrieval = MemoryRetrieval()
        self.belief_auditor = BeliefAuditor()
        self.last_speech_content = ""
        # 人格系统初始化
        self.personality_type = get_random_personality()
        self.personality_description = get_personality_description(self.personality_type)
        self.personality_icon = get_personality_icon(self.personality_type)
    
    def add_memory(self, day: int, phase: str, speaker: str, content: str, speaker_role: Optional[str] = None):
        self.memory_retrieval.add_memory(day, phase, speaker, content, speaker_role)
    
    def audit_beliefs(self, new_evidence: Dict):
        return self.belief_auditor.audit_beliefs(new_evidence)

    async def make_decision(self, action_type: str, context: Any) -> str:
        prompt = self._build_prompt(action_type, context)
        
        if not self.llm_client:
            raw_decision = self._mock_decision(action_type)
            return self._parse_output(action_type, raw_decision)
        
        try:
            print(f"[LLM] 正在调用 {action_type} 决策...")
            
            resp = await asyncio.wait_for(
                self.llm_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": prompt["system"]},
                        {"role": "user", "content": prompt["user"]}
                    ],
                    temperature=0.7,
                    max_tokens=300
                ),
                timeout=30.0
            )
            raw = resp.choices[0].message.content
            print(f"[LLM] 响应成功: {raw[:50]}...")
            
            if action_type == "speak":
                validator = SelfReflectionValidator(self.game_state, self.player)
                is_valid, issues, corrected = validator.validate(raw)
                if not is_valid:
                    print(f"[自检] 发现问题: {issues}")
                    raw = corrected
            
            if action_type == "vote":
                raw = self._check_vote_consistency(raw)
            
            if action_type == "kill" or action_type == "vote":
                raw = self._wolf_protection_filter(action_type, raw)
            
            # 应用人格修改器
            raw = apply_personality_modifier(self.personality_type, action_type, raw)
            
            return self._parse_output(action_type, raw)
        except asyncio.TimeoutError:
            print(f"[LLM错误] 调用超时(30秒)，使用mock决策")
            raw_decision = self._mock_decision(action_type)
            return self._parse_output(action_type, raw_decision)
        except Exception as e:
            print(f"[LLM错误] {type(e).__name__}: {str(e)[:100]}")
            raw_decision = self._mock_decision(action_type)
            return self._parse_output(action_type, raw_decision)
    
    def _check_vote_consistency(self, raw: str) -> str:
        """发言-投票一致性检查"""
        if not self.last_speech_content:
            return raw
        
        speech_suspicions = []
        for player_id in self.game_state.players:
            if player_id in self.last_speech_content and "怀疑" in self.last_speech_content:
                speech_suspicions.append(player_id)
        
        vote_match = re.search(r"<VOTE>(.*?)</VOTE>", raw)
        if vote_match:
            vote_target = vote_match.group(1).strip()
            
            if speech_suspicions and vote_target != "PASS" and vote_target not in speech_suspicions:
                print(f"[一致性检查] 发言怀疑{speech_suspicions}，投票{vote_target}，不一致已修正")
                new_target = random.choice(speech_suspicions)
                return raw.replace(f"<VOTE>{vote_target}</VOTE>", f"<VOTE>{new_target}</VOTE>")
        
        return raw
    
    def _wolf_protection_filter(self, action_type: str, raw: str) -> str:
        """狼人互投防护机制 - 三层拦截
        
        规则：
        1. 狼人永远不能票自己的队友
        2. 狼人不能刀自己的队友，除非：女巫还有解药并且有一位狼人自曝是预言家
        """
        if self.player.role != Role.WEREWOLF:
            return raw
        
        wolves = [p.id for p in self.game_state.players.values() 
                  if p.role == Role.WEREWOLF and p.is_alive]
        
        tag_map = {"vote": "VOTE", "kill": "KILL"}
        match = re.search(f"<{tag_map[action_type]}>(.*?)</{tag_map[action_type]}>", raw)
        
        if match:
            target = match.group(1).strip()
            
            if target in wolves:
                # 投票：永远禁止投队友
                if action_type == "vote":
                    print(f"[狼人防护] 拦截狼人投票队友操作: {target}")
                    alive_players = [p.id for p in self.game_state.players.values() if p.is_alive]
                    valid_targets = [p for p in alive_players if p not in wolves and p != self.player.id]
                    
                    if valid_targets:
                        new_target = random.choice(valid_targets)
                        return raw.replace(f"<VOTE>{target}</VOTE>", f"<VOTE>{new_target}</VOTE>")
                
                # 击杀：检查特殊情况（女巫有解药 + 狼人自曝预言家）
                elif action_type == "kill":
                    can_kill_wolf = self._check_special_kill_condition()
                    
                    if can_kill_wolf:
                        print(f"[狼人防护] 特殊情况允许刀队友: {target}")
                        return raw
                    else:
                        print(f"[狼人防护] 拦截狼人击杀队友操作: {target}")
                        alive_players = [p.id for p in self.game_state.players.values() if p.is_alive]
                        valid_targets = [p for p in alive_players if p not in wolves and p != self.player.id]
                        
                        if valid_targets:
                            new_target = random.choice(valid_targets)
                            return raw.replace(f"<KILL>{target}</KILL>", f"<KILL>{new_target}</KILL>")
        
        return raw
    
    def _check_special_kill_condition(self) -> bool:
        """检查是否满足特殊情况：女巫有解药 + 狼人自曝预言家"""
        # 检查女巫是否还有解药
        witch = next((p for p in self.game_state.players.values() 
                      if p.role == Role.WITCH and p.is_alive), None)
        
        if not witch or not getattr(witch, 'has_antidote', False):
            return False
        
        # 检查是否有狼人自曝预言家
        # 通过日志检查是否有狼人声称自己是预言家
        for log in self.game_state.logs:
            if log.get('phase') == '自由发言' and '预言家' in log.get('content', ''):
                speaker = log.get('speaker', '')
                # 检查发言者是否是狼人
                if speaker in [p.id for p in self.game_state.players.values() if p.role == Role.WEREWOLF]:
                    print(f"[狼人防护] 检测到狼人{speaker}自曝预言家，允许刀队友")
                    return True
        
        return False

    def _build_prompt(self, action_type: str, context: Any) -> Dict[str, str]:
        role_key = self.player.role.value
        alive_ids = [p.id for p in self.game_state.players.values() if p.is_alive]
        
        past_exps = self.experience_pool.get(role_key, [])
        exp_text = "\n- ".join(past_exps[-3:]) if past_exps else "暂无历史经验，请遵循基础策略行事。"
        
        query = f"第{self.game_state.day}天 {action_type}"
        relevant_memories = self.memory_retrieval.retrieve_top_k(query, k=5)
        memory_text = "\n".join([f"{mem['speaker']}: {mem['content'][:50]}..." 
                               for mem in relevant_memories]) if relevant_memories else "暂无相关记忆"
        
        belief_summary = self.belief_auditor.get_belief_summary()
        
        # 获取人格prompt
        personality_prompt = get_personality_prompt(self.personality_type, role_key)
        
        system_prompt = self.PROMPT_TEMPLATES["system_base"].format(
            name=self.player.name,
            player_id=self.player.id,
            role=role_key,
            personality_prompt=personality_prompt,
            role_objective=self.PROMPT_TEMPLATES["role_objectives"][role_key],
            alive_players=",".join(alive_ids),
            relevant_memories=memory_text,
            belief_summary=belief_summary,
            past_experiences=exp_text
        )
        
        recent_logs = [L for L in self.game_state.logs if not L.get("hidden", False)][-10:]
        history = "\n".join([
            f"第{L['day']}天 {L['phase']}: {L['content']}" 
            for L in recent_logs
        ])
        
        action_kwargs = {"alive_players": ",".join(alive_ids)}
        if action_type == "witch":
            action_kwargs.update({
                "killed_player": str(context) if context else "无",
                "has_antidote": "有" if self.player.has_antidote else "无",
                "has_poison": "有" if self.player.has_poison else "无"
            })
        
        user_prompt = f"【公开日志】\n{history}\n\n【行动任务】\n{self.PROMPT_TEMPLATES['actions'][action_type].format(**action_kwargs)}"
        
        return {"system": system_prompt, "user": user_prompt}

    def _parse_output(self, action_type: str, raw: str) -> str:
        if action_type == "speak":
            match = re.search(r"【发言】(.*?)(?=\n【|$)", raw, re.DOTALL)
            if match:
                self.last_speech_content = match.group(1).strip()
                return self.last_speech_content
            self.last_speech_content = raw.strip()
            return self.last_speech_content
        
        tag_map = {
            "vote": "VOTE",
            "kill": "KILL",
            "seer": "CHECK",
            "witch": "WITCH"
        }
        
        match = re.search(f"<{tag_map[action_type]}>(.*?)</{tag_map[action_type]}>", raw, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        match = re.search(r"【行动】\s*(.+?)\s*(?=\n|$)", raw)
        if match:
            action_content = match.group(1).strip()
            inner_match = re.search(r"<(\w+)>(.*?)</\1>", action_content, re.IGNORECASE | re.DOTALL)
            if inner_match:
                return inner_match.group(2).strip()
            return action_content
        
        return self._mock_decision(action_type)

    def _mock_decision(self, action_type: str) -> str:
        alive_ids = [p.id for p in self.game_state.players.values() if p.is_alive]
        
        if action_type == "kill":
            wolves = [p.id for p in self.game_state.players.values() 
                      if p.role == Role.WEREWOLF and p.is_alive]
            targets = [p for p in alive_ids if p != self.player.id and p not in wolves]
            target = random.choice(targets) if targets else ""
            return f"""【心声】现在需要击杀一名好人，优先选择看起来像神职的目标。
【表现】果断指认目标，表现出狼队的默契
【行动】<KILL>{target}</KILL>"""
        
        if action_type == "seer":
            targets = [p for p in alive_ids if p != self.player.id]
            target = random.choice(targets) if targets else ""
            return f"""【心声】需要查验一名玩家，选择发言较少的边缘人物。
【表现】谨慎选择查验对象，避免暴露自己
【行动】<CHECK>{target}</CHECK>"""
        
        if action_type == "witch":
            return """【心声】局势还不明朗，先观察一下，不急于用药。
【表现】保守观望，等待更好的时机
【行动】<WITCH>pass</WITCH>"""
        
        if action_type == "vote":
            wolves = []
            if self.player.role == Role.WEREWOLF:
                wolves = [p.id for p in self.game_state.players.values() 
                          if p.role == Role.WEREWOLF and p.is_alive]
            valid_targets = [p for p in alive_ids if p != self.player.id and p not in wolves]
            if valid_targets:
                target = random.choice(valid_targets)
                return f"""【心声】根据发言分析，{target}的逻辑有漏洞，值得怀疑。
【表现】果断投票，表明立场
【行动】<VOTE>{target}</VOTE>"""
            return "【心声】没有合适的投票目标。\n【表现】弃权观望\n【行动】<VOTE>PASS</VOTE>"
        
        if action_type == "speak":
            role_phrases = {
                Role.VILLAGER: ("我是平民，昨晚没有任何信息。根据刚才的发言，我觉得需要再观察一下。", "谨慎发言，保持中立"),
                Role.WEREWOLF: ("我是好人身份，昨晚平安度过。刚才有些玩家的发言很可疑。", "假装分析，误导好人"),
                Role.SEER: ("我是预言家，昨晚查验了一名玩家身份。今天请大家跟我走。", "自信发言，明确报验"),
                Role.WITCH: ("我是女巫，昨晚有人被杀，我选择保守用药。", "谨慎透露信息"),
                Role.HUNTER: ("我是猎人，如果被放逐我会开枪带走可疑的人。", "强势发言，威慑狼人")
            }
            phrase, behavior = role_phrases.get(self.player.role, ("局势复杂，需要进一步分析。", "谨慎分析"))
            return f"""【心声】现在需要发言，根据我的身份制定策略。
【表现】{behavior}
【发言】{phrase}"""
        
        return "PASS"


class ExperiencePool:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = {
                "平民": [],
                "狼人": [],
                "预言家": [],
                "女巫": [],
                "猎人": []
            }
        return cls._instance
    
    def add_experience(self, role: str, experience: str):
        if role in self.pool:
            self.pool[role].append(experience)
    
    def get_experiences(self, role: str, limit: int = 5) -> List[str]:
        return self.pool.get(role, [])[-limit:]
    
    def clear(self):
        for role in self.pool:
            self.pool[role] = []