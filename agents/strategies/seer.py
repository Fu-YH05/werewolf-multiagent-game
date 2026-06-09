"""预言家策略模块"""

class SeerStrategy:
    """预言家策略类"""
    
    def __init__(self, player, game_state):
        self.player = player
        self.game_state = game_state
    
    def select_check_target(self, day):
        """选择查验目标"""
        alive_players = [p for p in self.game_state.players.values() if p.is_alive]
        
        # 第一天优先查边缘玩家
        if day == 1:
            # 选择发言最少或最沉默的玩家
            return alive_players[0].id if alive_players else None
        
        # 后续优先查可疑玩家
        suspicious_players = self._identify_suspicious_players()
        if suspicious_players:
            return suspicious_players[0]
        
        # 默认选择未查验过的玩家
        for player in alive_players:
            if player.id != self.player.id:
                return player.id
        
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
            if hasattr(player, 'speech_count') and player.speech_count > 5:
                suspicious.append(player.id)
        
        return suspicious
    
    def generate_report(self, target, result):
        """生成查验报告"""
        report = f"昨晚我查验了{target}，结果是"
        if result == "狼人":
            report += "查杀！"
        else:
            report += "金水，是好人。"
        return report

def get_strategy_prompt() -> str:
    """获取预言家策略prompt"""
    return """【预言家核心策略】
身份：预言家（1人）
目标：带领好人阵营胜利，查验狼人身份

【查验策略】
1. 第一天：优先查验边缘玩家或发言少的玩家
2. 第二天：查验发言可疑的玩家
3. 第三天及以后：查验关键人物或有争议的玩家
4. 避免查验明显的好人

【发言策略】
1. 必须起跳，报出查验结果
2. 清晰说明查验目标和结果
3. 分析局势，给出投票建议
4. 建立逻辑链，获取好人信任

【报验技巧】
1. 明确说出"金水"或"查杀"
2. 解释查验理由
3. 给出接下来的查验计划
4. 要求其他玩家表立场

【投票策略】
1. 投票给查验出的狼人
2. 带领好人投票给可疑玩家
3. 要求其他玩家跟随自己

【注意事项】
- 必须尽快起跳，避免被狼人悍跳
- 保持发言连贯，逻辑清晰
- 不要查验狼人队友（不存在）
- 注意保护自己，避免被狼人击杀

【胜利条件】
- 所有狼人被投票出局

【禁忌】
- 不要不报查验结果
- 不要查验自己
- 不要犹豫不决"""
