"""语音合成管理器：支持 edge-tts（免费）和豆包语音（火山引擎 TTS）"""
import os
import time
import logging
import asyncio
import wave
import requests
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# 多角色声线映射到 edge-tts 的不同语音
# edge-tts 使用微软 Edge 的免费 TTS 服务，与 Azure TTS 相同神经语音品质
VOICE_MAP = [
    "zh-CN-XiaoxiaoNeural",    # P1 冷静理性预言家 → 温柔女声
    "zh-CN-XiaoyiNeural",      # P2 活泼开朗少女 → 活泼女声
    "zh-CN-YunyangNeural",     # P3 憨厚老实中年人 → 厚重男声
    "zh-CN-XiaochenNeural",    # P4 温柔体贴女生 → 自然女声
    "zh-CN-YunjianNeural",     # P5 粗犷豪爽汉子 → 沉稳男声
    "zh-CN-XiaoshuangNeural",  # P6 古灵精怪小个子 → 元气女声
    "zh-CN-YunxiNeural",       # P7 沉默寡言青年 → 阳光男声
    "zh-CN-XiaomoNeural",      # P8 成熟稳重女性 → 柔和知性女声
    "zh-CN-XiaoyouNeural",     # P9 淘气顽皮小孩 → 可爱儿童音
]

# 语速/音高偏移（可微调角色个性）
# 值范围: rate -50% ~ +50%, pitch -50Hz ~ +50Hz
VOICE_STYLES = [
    {},                                                     # P1 默认
    {"rate": "+15%"},                                       # P2 语速偏快
    {"rate": "-10%", "pitch": "-5Hz"},                      # P3 语速偏慢，音高偏低
    {"rate": "-5%"},                                        # P4 略慢
    {"rate": "-5%", "pitch": "-10Hz"},                      # P5 低沉
    {"rate": "+20%", "pitch": "+10Hz"},                     # P6 快语速高音
    {"rate": "-10%"},                                       # P7 慢语速平淡
    {"rate": "0%"},                                         # P8 默认
    {"rate": "+25%", "pitch": "+20Hz"},                     # P9 快语速尖细
]


# 豆包语音（火山引擎）TTS API 配置
# 官方文档: https://www.volcengine.com/docs/6561/79820
DOUBAO_API_URL = "https://openspeech.bytedance.com/api/v1/tts"
# 豆包语音可选音色（全部AI使用同一音色时从这里随机选取）
DOUBAO_VOICES = [
    "BV001_streaming",   # 免费女声-通用
    "BV002_streaming",   # 免费男声-通用
    "BV005_streaming",   #
    "BV007_streaming",   #
    "BV019_streaming",   #
    "BV021_streaming",   #
    "BV033_streaming",   #
    "BV034_streaming",   #
    "BV051_streaming",   #
    "BV056_streaming",   #
    "BV112_streaming",   #
    "BV113_streaming",   #
    "BV115_streaming",   #
    "BV119_streaming",   #
    "BV700_streaming",   # 女声-温柔
    "BV701_streaming",   # 男声-沉稳
    "BV705_streaming",   #
]
# 旁白专用音色：豆包标准女声本音
DOUBAO_NARRATOR_VOICE = "BV001_streaming"


class TTSManager:
    """语音合成管理器，支持 edge-tts 和豆包语音两种引擎"""

    def __init__(self, audio_dir: str = "./audio"):
        self.audio_dir = audio_dir
        self._loaded = True
        self.use_doubao = False
        self.doubao_api_key = ""
        self.doubao_appid = ""      # 豆包控制台获取的应用ID
        self.doubao_cluster = "volcano_tts"  # 业务集群
        os.makedirs(audio_dir, exist_ok=True)

    def load(self) -> bool:
        """兼容接口：edge-tts 无需加载"""
        return True

    def warmup(self) -> bool:
        """兼容接口：edge-tts 无需预热"""
        return True

    def generate(
        self,
        text: str,
        player_id: str = "P1",
        speaker_idx: int = 0,
        skip_empty: bool = True,
    ) -> Optional[Dict]:
        """
        生成语音文件

        Args:
            text: 要合成的文本
            player_id: 玩家ID（用于文件名）
            speaker_idx: 角色声线索引 (0-8)
            skip_empty: 跳过空文本

        Returns:
            {"filepath": str, "duration": float} 或 None（失败时）
        """
        if not text or not text.strip():
            return None
        if skip_empty and len(text.strip()) < 3:
            return None

        cleaned = self._clean_text(text)
        if not cleaned:
            return None

        # 豆包语音模式 → 走火山引擎 API
        if self.use_doubao and self.doubao_api_key:
            return self._generate_doubao(cleaned, player_id)

        try:
            voice = VOICE_MAP[speaker_idx % len(VOICE_MAP)]
            style = VOICE_STYLES[speaker_idx % len(VOICE_STYLES)]

            # 构建 edge-tts Communicate
            import edge_tts
            communicate = edge_tts.Communicate(cleaned, voice=voice)

            # 如果设置了语速/音高，使用 SSML
            if style:
                rate = style.get("rate", "0%")
                pitch = style.get("pitch", "0Hz")
                ssml = (
                    f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"'
                    f' xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="zh-CN">'
                    f'<voice name="{voice}">'
                    f'<prosody rate="{rate}" pitch="{pitch}">'
                    f'{cleaned}'
                    f'</prosody>'
                    f'</voice>'
                    f'</speak>'
                )
                communicate = edge_tts.Communicate(ssml, voice=voice)

            # 生成音频文件
            start = time.time()
            safe_id = player_id.replace("/", "_").replace("\\", "_")
            timestamp = int(time.time() * 1000)
            filename = f"{safe_id}_{timestamp}.wav"
            filepath = os.path.join(self.audio_dir, filename)

            # edge_tts 是异步的，在同步包装器中运行
            asyncio.run(communicate.save(filepath))

            gen_time = time.time() - start
            duration = self._get_wav_duration(filepath)
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

            logger.info(
                f"TTS [{player_id}] {gen_time:.1f}s 生成 "
                f"{duration:.1f}s 语音 ({voice}): {cleaned[:30]}..."
            )

            return {"filepath": filepath, "duration": duration}

        except Exception as e:
            logger.error(f"TTS 生成失败 [{player_id}] ({voice}): {e}")
            return None

    @staticmethod
    def _get_wav_duration(filepath: str) -> float:
        """从 WAV 文件头读取音频时长（秒）"""
        try:
            with wave.open(filepath, 'r') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / rate if rate > 0 else 0.0
        except Exception:
            # 回退：根据文件大小估算（16-bit mono 24kHz）
            try:
                size = os.path.getsize(filepath)
                return size / 48000.0  # 24kHz * 2bytes ≈ 48KB/s
            except Exception:
                return 2.0  # 完全无法获取时默认为2秒

    def _generate_doubao(self, text: str, player_id: str) -> Optional[Dict]:
        """通过豆包语音（火山引擎）HTTP 非流式 API 生成语音
        
        官方文档: https://www.volcengine.com/docs/6561/79820
        认证格式: Authorization: Bearer;{token} (分号分隔)
        返回: JSON 中 data 字段为 base64 编码的音频
        """
        import uuid
        import random
        import base64

        safe_id = player_id.replace("/", "_").replace("\\", "_")
        timestamp = int(time.time() * 1000)
        filename = f"{safe_id}_{timestamp}.wav"
        filepath = os.path.join(self.audio_dir, filename)

        # 旁白使用固定本音，AI 玩家随机选音色
        if player_id == "NARRATOR":
            voice = DOUBAO_NARRATOR_VOICE
        else:
            voice = random.choice(DOUBAO_VOICES)
        reqid = uuid.uuid4().hex

        # 认证: Bearer 和 token 之间用分号 ; 分隔
        headers = {
            "Authorization": f"Bearer;{self.doubao_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "app": {
                "appid": self.doubao_appid,
                "token": self.doubao_api_key,
                "cluster": "volcano_tts",   # 标准音色业务集群
            },
            "user": {
                "uid": player_id,
            },
            "audio": {
                "voice_type": voice,
                "encoding": "wav",          # wav 用于非流式
                "rate": 24000,
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": reqid,
                "text": text,
                "text_type": "plain",
                "operation": "query",       # query = 非流式
                "silence_duration": "125",
            },
        }

        start = time.time()
        try:
            resp = requests.post(
                DOUBAO_API_URL,
                json=payload,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()

            code = result.get("code")
            if code != 3000:
                logger.error(
                    f"豆包TTS [{player_id}] 返回错误 code={code}: "
                    f"{result.get('message', '未知')}"
                )
                return None

            # 音频是 base64 编码的
            audio_b64 = result.get("data", "")
            if not audio_b64:
                logger.error(f"豆包TTS [{player_id}] 返回空音频数据")
                return None

            audio_bytes = base64.b64decode(audio_b64)
            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            gen_time = time.time() - start
            duration = self._get_wav_duration(filepath)
            logger.info(
                f"TTS-豆包 [{player_id}] {gen_time:.1f}s 生成 "
                f"{duration:.1f}s 语音 ({voice}): {text[:30]}..."
            )
            return {"filepath": filepath, "duration": duration}

        except requests.exceptions.RequestException as e:
            logger.error(f"豆包TTS 请求失败 [{player_id}]: {e}")
            return None
        except Exception as e:
            logger.error(f"豆包TTS 处理失败 [{player_id}]: {e}")
            return None

    def generate_batch(
        self, items: List[Dict]
    ) -> List[Optional[Dict]]:
        """
        批量生成语音

        Args:
            items: [{"text": str, "player_id": str, "speaker_idx": int}, ...]

        Returns:
            [{"filepath": str, "duration": float}, ...] 列表
        """
        return [self.generate(**item) for item in items]

    def _clean_text(self, text: str) -> str:
        """清理 TTS 文本（移除 URL、代码等不适宜朗读的内容）"""
        import re
        text = re.sub(r'https?://[^\s]+', '', text)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        text = re.sub(r'```[\w]*\n?.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        # 移除 markdown 标记
        text = re.sub(r'\*\*', '', text)
        text = re.sub(r'[#*_~`]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return ""
        return text

    def cleanup_old_files(self, max_age_seconds: int = 3600):
        """清理过期的临时音频文件"""
        now = time.time()
        for f in os.listdir(self.audio_dir):
            fpath = os.path.join(self.audio_dir, f)
            if os.path.isfile(fpath) and (now - os.path.getmtime(fpath)) > max_age_seconds:
                try:
                    os.remove(fpath)
                except OSError:
                    pass

    def get_audio_url(self, filepath: str) -> str:
        """获取音频文件的 URL 路径"""
        if not filepath:
            return ""
        filename = os.path.basename(filepath)
        return f"/api/audio/{filename}"

    @property
    def is_loaded(self) -> bool:
        return self._loaded
