"""狼人策略模块"""

class WolfStrategy:
    """狼人策略类"""
    
    def __init__(self, player, game_state):
        self.player = player
        self.game_state = game_state
    
    def select_kill_target(self):
        """选择击杀目标"""
        alive_players = [p for p in self.game_state.players.values() if p.is_alive]
        wolves = [p.id for p in alive_players if p.role.value == "狼人"]
        
        # 优先击杀神职
        priority_targets = []
        for player in alive_players:
            if player.id == self.player.id:
                continue
            if player.id in wolves:
                continue
            # 优先级：预言家 > 女巫 > 猎人 > 平民
            if player.role.value == "预言家":
                priority_targets.append((3, player.id))
            elif player.role.value == "女巫":
                priority_targets.append((2, player.id))
            elif player.role.value == "猎人":
                priority_targets.append((1, player.id))
            else:
                priority_targets.append((0, player.id))
        
        # 按优先级排序
        priority_targets.sort(key=lambda x: -x[0])
        
        if priority_targets:
            return priority_targets[0][1]
        return None
    
    def select_vote_target(self, speech_analysis):
        """选择投票目标"""
        alive_players = [p for p in self.game_state.players.values() if p.is_alive]
        wolves = [p.id for p in alive_players if p.role.value == "狼人"]
        
        valid_targets = [p.id for p in alive_players if p.id not in wolves and p.id != self.player.id]
        
        if not valid_targets:
            return None
        
        # 根据发言分析选择最可疑的目标
        if speech_analysis:
            # 选择被怀疑最多的玩家
            suspicion_scores = {}
            for player_id in valid_targets:
                suspicion_scores[player_id] = speech_analysis.get(player_id, 0)
            
            if suspicion_scores:
                return max(suspicion_scores, key=suspicion_scores.get)
        
        # 默认选择发言最多的玩家
        return valid_targets[0]

def get_strategy_prompt() -> str:
    """获取狼人策略prompt"""
    return """【狼人核心策略】
身份：狼人（3人）
目标：消灭所有好人，屠边获胜

【夜间策略】
1. 优先击杀预言家，阻止其查验
2. 其次击杀女巫，阻止其用药
3. 最后击杀猎人和平民
4. 保持击杀目标一致，避免分歧

【白天策略】
1. 伪装成好人，参与讨论
2. 寻找发言漏洞，攻击好人
3. 煽动好人互投，转移注意力
4. 必要时悍跳预言家，混淆视听

【发言技巧】
1. 模仿平民发言风格
2. 分析其他玩家的逻辑漏洞
3. 提出合理的怀疑对象
4. 避免被怀疑，保持低调

【投票策略】
1. 跟随队友投票，保持一致
2. 优先投票给被怀疑的好人
3. 避免暴露狼队友

【胜利条件】
- 神职全灭 或 平民全灭 或 狼人数量 >= 存活人数一半

【禁忌】
- 绝对不能投票或击杀狼队友
- 避免在发言中暴露狼队信息
- 不要过早暴露身份"""
