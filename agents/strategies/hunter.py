"""猎人策略模块"""

class HunterStrategy:
    """猎人策略类"""
    
    def __init__(self, player, game_state):
        self.player = player
        self.game_state = game_state
    
    def decide_shoot(self, voted_out):
        """决定是否开枪"""
        # 如果是被投票出局，必须开枪
        if voted_out == self.player.id:
            return self._select_shoot_target()
        return None
    
    def _select_shoot_target(self):
        """选择开枪目标"""
        alive_players = [p for p in self.game_state.players.values() if p.is_alive]
        wolves = [p.id for p in alive_players if p.role.value == "狼人"]
        
        # 如果知道狼人的身份，直接带走
        if wolves:
            return wolves[0]
        
        # 否则带走最可疑的玩家
        suspicious_players = self._identify_suspicious_players()
        if suspicious_players:
            return suspicious_players[0]
        
        # 默认选择投票给自己的玩家
        if hasattr(self.player, 'voters') and self.player.voters:
            return self.player.voters[0]
        
        return None
    
    def _identify_suspicious_players(self):
        """识别可疑玩家"""
        suspicious = []
        
        for player in self.game_state.players.values():
            if not player.is_alive:
                continue
            if player.id == self.player.id:
                continue
            
            # 检查发言记录
            if hasattr(player, 'suspicion_score') and player.suspicion_score > 5:
                suspicious.append(player.id)
        
        return suspicious

def get_strategy_prompt() -> str:
    """获取猎人策略prompt"""
    return """【猎人核心策略】
身份：猎人（1人）
技能：被投票出局时可以开枪带走一名玩家
目标：带领好人阵营胜利

【发言策略】
1. 隐藏身份，不要暴露猎人身份
2. 伪装成平民或其他身份
3. 分析局势，引导投票
4. 必要时可以亮身份带队

【隐藏策略】
1. 不要表现出有技能的样子
2. 避免被狼人优先击杀
3. 在合适的时机亮身份

【开枪策略】
1. 如果被投票出局，必须开枪
2. 优先带走确认的狼人
3. 其次带走发言最可疑的玩家
4. 可以带走投票给自己的玩家

【亮身份时机】
1. 当自己被怀疑时
2. 当局势混乱时
3. 当需要带队时

【注意事项】
- 不要过早暴露猎人身份
- 被狼人击杀时无法开枪
- 只有被投票出局时才能开枪
- 开枪前要确认目标身份

【胜利条件】
- 所有狼人被投票出局

【禁忌】
- 不要在被击杀时试图开枪
- 不要误杀好人
- 不要在第一天就亮身份"""
