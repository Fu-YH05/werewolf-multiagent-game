"""女巫策略模块"""

class WitchStrategy:
    """女巫策略类"""
    
    def __init__(self, player, game_state):
        self.player = player
        self.game_state = game_state
    
    def decide_heal(self, killed_player):
        """决定是否使用解药"""
        if not self.player.has_antidote:
            return False
        
        # 如果被击杀的是明显的好人或神职，优先救
        if killed_player:
            # 救预言家优先级最高
            if killed_player.role.value == "预言家":
                return True
            # 其次救女巫自己
            if killed_player.id == self.player.id:
                return True
            # 救猎人
            if killed_player.role.value == "猎人":
                return True
        
        # 第一天通常不救，除非是关键人物
        if self.game_state.current_day == 1:
            return False
        
        return False
    
    def decide_poison(self):
        """决定是否使用毒药"""
        if not self.player.has_poison:
            return None
        
        alive_players = [p for p in self.game_state.players.values() if p.is_alive]
        wolves = [p.id for p in alive_players if p.role.value == "狼人"]
        
        # 如果知道狼人的身份，直接毒杀
        if wolves:
            return wolves[0]
        
        # 否则毒杀最可疑的玩家
        suspicious_players = self._identify_suspicious_players()
        if suspicious_players:
            return suspicious_players[0]
        
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
    """获取女巫策略prompt"""
    return """【女巫核心策略】
身份：女巫（1人）
物品：解药×1，毒药×1
目标：保护好人阵营，使用药水帮助好人获胜

【解药策略】
1. 第一天：通常不救，保留解药
2. 如果被击杀的是预言家，必须救
3. 如果被击杀的是自己，可以救
4. 如果被击杀的是猎人，可以考虑救
5. 如果局势不明，谨慎使用

【毒药策略】
1. 确认狼人的身份后再使用
2. 优先毒杀明确的狼人
3. 其次毒杀发言最可疑的玩家
4. 不要轻易毒杀平民
5. 毒杀前要深思熟虑

【发言策略】
1. 隐藏身份，不要暴露女巫身份
2. 伪装成平民或其他身份
3. 分析局势，引导投票
4. 必要时可以亮身份带队

【用药原则】
- 解药和毒药不能在同一晚使用
- 解药可以救被狼人击杀的玩家
- 毒药可以毒杀任意存活玩家
- 自己被击杀时可以使用解药自救

【注意事项】
- 不要过早暴露女巫身份
- 解药和毒药都很珍贵，谨慎使用
- 注意保护自己，避免被狼人击杀

【胜利条件】
- 所有狼人被投票出局

【禁忌】
- 不要浪费解药
- 不要误毒好人
- 不要在第一天就亮身份"""
