"""AI 语音合成管理 - 使用 edge-tts"""

import os
import asyncio
from typing import Optional, Tuple

# 每个玩家固定声线（男女混合）
VOICE_MAP = {
    "P1": "zh-CN-YunxiNeural",      # 男 - 阳光
    "P2": "zh-CN-XiaoxiaoNeural",    # 女 - 亲切
    "P3": "zh-CN-YunjianNeural",     # 男 - 严肃
    "P4": "zh-CN-XiaochenNeural",    # 女 - 冷静
    "P5": "zh-CN-YunyangNeural",     # 男 - 专业
    "P6": "zh-CN-XiaohanNeural",     # 女 - 温暖
    "P7": "zh-CN-XiaomengNeural",    # 女 - 活泼
    "P8": "zh-CN-XiaomoNeural",      # 女 - 柔和
    "P9": "zh-CN-XiaoruiNeural",     # 女 - 可爱
}

def get_voice(player_id: str) -> str:
    """根据玩家 ID 返回固定声线"""
    return VOICE_MAP.get(player_id, "zh-CN-XiaoxiaoNeural")


async def generate_speech(
    text: str,
    player_id: str,
    audio_dir: str,
    filename: str,
) -> Tuple[Optional[str], float]:
    """
    生成语音文件。
    返回 (filename, duration_seconds)，失败返回 (None, 0)
    """
    if not text or not text.strip():
        return None, 0

    # 清理文本：去掉过长的发言，只取前 100 字
    clean_text = text.strip()
    if len(clean_text) > 100:
        clean_text = clean_text[:100] + "……"

    voice = get_voice(player_id)
    filepath = os.path.join(audio_dir, filename)

    try:
        import edge_tts
        communicate = edge_tts.Communicate(clean_text, voice)
        await communicate.save(filepath)

        # 粗略估算时长（中文约 4.5 字/秒）
        duration = max(1.0, len(clean_text) / 4.5)
        return filename, round(duration, 1)
    except Exception as e:
        print(f"[TTS] 生成语音失败 [{player_id}]: {e}")
        # 删除可能的部分文件
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        return None, 0
