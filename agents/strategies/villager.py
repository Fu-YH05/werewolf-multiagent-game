"""平民策略模块"""

class VillagerStrategy:
    """平民策略类"""
    
    def __init__(self, player, game_state):
        self.player = player
        self.game_state = game_state
    
    def analyze_speeches(self, recent_speeches):
        """分析发言，找出可疑玩家"""
        suspicion_scores = {}
        
        for speaker, speech in recent_speeches.items():
            score = 0
            
            # 检查是否有矛盾发言
            if "我是预言家" in speech and "我是女巫" in speech:
                score += 3
            
            # 检查是否过度攻击
            if speech.count("怀疑") > 3:
                score += 2
            
            # 检查是否划水
            if len(speech) < 20:
                score += 1
            
            # 检查是否有逻辑漏洞
            if "绝对" in speech or "肯定" in speech:
                score += 1
            
            suspicion_scores[speaker] = score
        
        return suspicion_scores
    
    def select_vote_target(self, suspicion_scores):
        """选择投票目标"""
        alive_players = [p.id for p in self.game_state.players.values() if p.is_alive]
        
        if not suspicion_scores:
            # 随机选择一个非自己的玩家
            valid_targets = [p for p in alive_players if p != self.player.id]
            return valid_targets[0] if valid_targets else None
        
        # 选择怀疑度最高的玩家
        max_suspicion = max(suspicion_scores.values())
        suspects = [p for p, score in suspicion_scores.items() if score == max_suspicion]
        
        return suspects[0]

def get_strategy_prompt() -> str:
    """获取平民策略prompt"""
    return """【平民核心策略】
身份：平民（3人）
目标：找出狼人并投票放逐

【发言策略】
1. 表明平民身份，获取信任
2. 分析其他玩家的发言
3. 提出合理的怀疑对象
4. 避免被误认为狼人

【分析技巧】
1. 关注发言中的矛盾点
2. 注意过度攻击他人的玩家
3. 留意划水、发言简短的玩家
4. 分析投票行为是否合理

【投票策略】
1. 投票给发言最可疑的玩家
2. 跟随有逻辑的玩家投票
3. 避免盲目跟风
4. 关键时刻可以弃票

【注意事项】
- 不要轻易暴露自己的平民身份
- 不要攻击太多玩家，避免被怀疑
- 保持冷静分析，不情绪化

【胜利条件】
- 所有狼人被投票出局

【禁忌】
- 不要乱投好人
- 不要不发言或划水过多
- 不要冒充神职身份"""
