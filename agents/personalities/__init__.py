"""人格系统 - 为智能体分配不同的人格特质"""

import random
from typing import Dict, Any

# 人格类型枚举
PERSONALITY_TYPES = [
    "rational",    # 理性型
    "aggressive",  # 煽动型
    "hesitant",    # 保守型
    "follower",    # 冲动型
    "slacker"      # 划水型
]

def get_random_personality() -> str:
    """随机获取一个人格类型"""
    return random.choice(PERSONALITY_TYPES)

def get_personality_prompt(personality_type: str, role: str) -> str:
    """获取指定人格类型的prompt模板"""
    from . import rational, aggressive, hesitant, follower, slacker
    
    personality_modules = {
        "rational": rational,
        "aggressive": aggressive,
        "hesitant": hesitant,
        "follower": follower,
        "slacker": slacker
    }
    
    module = personality_modules.get(personality_type)
    if module:
        return module.get_prompt(role)
    return ""

def get_personality_description(personality_type: str) -> str:
    """获取人格类型的描述"""
    descriptions = {
        "rational": "理性分析，逻辑严密",
        "aggressive": "积极煽动，强势发言",
        "hesitant": "保守谨慎，三思而后行",
        "follower": "冲动跟风，容易被影响",
        "slacker": "划水敷衍，不愿深入思考"
    }
    return descriptions.get(personality_type, "")

def get_personality_icon(personality_type: str) -> str:
    """获取人格类型的图标"""
    icons = {
        "rational": "🧠",
        "aggressive": "🔥",
        "hesitant": "🐢",
        "follower": "🐑",
        "slacker": "😴"
    }
    return icons.get(personality_type, "👤")

def apply_personality_modifier(personality_type: str, action_type: str, decision: str) -> str:
    """根据人格类型修改决策输出"""
    from . import rational, aggressive, hesitant, follower, slacker
    
    personality_modules = {
        "rational": rational,
        "aggressive": aggressive,
        "hesitant": hesitant,
        "follower": follower,
        "slacker": slacker
    }
    
    module = personality_modules.get(personality_type)
    if module and hasattr(module, 'modify_decision'):
        return module.modify_decision(action_type, decision)
    return decision
