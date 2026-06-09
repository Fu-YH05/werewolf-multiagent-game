"""策略系统 - 为各角色提供专业的决策策略"""

from typing import Dict, Any

def get_strategy(role: str):
    """获取指定角色的策略类"""
    from . import wolf, villager, seer, witch, hunter
    
    strategy_map = {
        "狼人": wolf.WolfStrategy,
        "平民": villager.VillagerStrategy,
        "预言家": seer.SeerStrategy,
        "女巫": witch.WitchStrategy,
        "猎人": hunter.HunterStrategy
    }
    
    return strategy_map.get(role)

def get_strategy_prompt(role: str) -> str:
    """获取指定角色的策略prompt"""
    from . import wolf, villager, seer, witch, hunter
    
    prompt_map = {
        "狼人": wolf.get_strategy_prompt(),
        "平民": villager.get_strategy_prompt(),
        "预言家": seer.get_strategy_prompt(),
        "女巫": witch.get_strategy_prompt(),
        "猎人": hunter.get_strategy_prompt()
    }
    
    return prompt_map.get(role, "")
