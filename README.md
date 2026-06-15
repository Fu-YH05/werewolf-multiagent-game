# 🐺 狼人杀多 Agent 对战平台

> Multi-Agent Werewolf Game — 基于 DeepSeek LLM 的 AI 狼人杀游戏平台

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Vue](https://img.shields.io/badge/Vue-3-brightgreen)
![Flask](https://img.shields.io/badge/Flask-2.3-lightgrey)
![TTS](https://img.shields.io/badge/TTS-edge--tts-orange)

---

## ✨ 功能特色

- **🤖 AI 玩家决策**：每个角色由 DeepSeek LLM 驱动，具备人格、记忆、信念系统和自我反思
- **🎭 9 人标准局**：2 狼人 + 1 预言家 + 1 女巫 + 1 猎人 + 4 平民
- **🎤 AI 语音播报**：每位玩家发言自动生成语音（edge-tts 神经语音，9 种不同声线）
- **👤 人类玩家模式**：真人可加入扮演任一角色
- **🎙️ 语音输入**：人类玩家发言支持语音转文字
- **📜 完整日志**：昼夜背景切换、笔记、拖拽分割、点击查看发言
- **📊 排行榜**：自动统计胜率
- **📽️ 回放系统**：保存游戏记录，支持回放与直播切换

---

## 🚀 快速启动

### 环境要求

- Python 3.10+
- Node.js 18+（构建前端）
- 网络连接（用于 edge-tts 云端 TTS 和 DeepSeek API）

### 1. 安装依赖

**后端依赖：**

```bash
pip install -r requirements.txt
```

**前端依赖：**

```bash
cd frontend
npm install
```

### 2. 配置 DeepSeek API Key（可选）

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY = "your-api-key-here"

# 或在启动游戏时在网页上输入
```

> 不配置 API Key 时使用 Mock 模式（AI 使用模板发言，适合测试）

### 3. 构建前端

```bash
cd frontend
npm run build
```

### 4. 启动服务器

```bash
# 在项目根目录
cd frontend
python server.py
```

服务器将在 `http://127.0.0.1:5000` 启动，浏览器打开即可游玩。

---

## 🎮 游戏流程

| 阶段 | 说明 |
|------|------|
| 初始化 | 分配 9 人身份（2狼/1预言家/1女巫/1猎人/4平民） |
| 天黑 | 狼人讨论→杀人→女巫救/毒→预言家查验→猎人觉醒 |
| 天亮 | 公布死讯 |
| 自由发言 | 存活玩家逐个发言，**TTS 语音同步播报** |
| 放逐投票 | 存活玩家投票放逐（平票 PK，最多 3 轮） |
| 游戏结束 | 判定胜负，保存日志 |

---

## 🎤 TTS 语音系统

### 技术方案

- **引擎**：edge-tts（微软 Edge 免费云服务，神经语音品质）
- **无需注册**：直接使用，无需 API Key
- **9 种声线**：对应 9 名玩家，各有语速/音高微调

### 角色声线映射

| 玩家 | 性格 | 语音 | 语速 |
|------|------|------|------|
| P1 | 冷静理性预言家 | 温柔女声 (Xiaoxiao) | 正常 |
| P2 | 活泼开朗少女 | 活泼女声 (Xiaoyi) | +15% |
| P3 | 憨厚老实中年人 | 厚重男声 (Yunyang) | -10% |
| P4 | 温柔体贴女生 | 自然女声 (Xiaochen) | -5% |
| P5 | 粗犷豪爽汉子 | 沉稳男声 (Yunjian) | -5% |
| P6 | 古灵精怪小个子 | 元气女声 (Xiaoshuang) | +20% |
| P7 | 沉默寡言青年 | 阳光男声 (Yunxi) | -10% |
| P8 | 成熟稳重女性 | 柔和女声 (Xiaomo) | 正常 |
| P9 | 淘气顽皮小孩 | 可爱童声 (Xiaoyou) | +25% |

### 同步机制

1. 游戏引擎生成发言文本 → 同步调用 edge-tts 生成音频
2. 日志写入时 `audio_url` 已预置（无需异步回填）
3. 游戏引擎等待音频时长后才继续下一位玩家
4. 前端状态机队列串行播放，过时发言自动跳过
5. edge-tts 失败时降级到浏览器 SpeechSynthesis

---

## 🏗️ 项目架构

```
werewolf-multiagent-game/
├── engine/                    # 游戏引擎
│   ├── game_engine.py         # 核心引擎：9人局、日夜轮回、角色技能
│   ├── tts_manager.py         # edge-tts 语音合成管理器
│   └── evolution.py           # 自对战训练
├── agents/                    # AI 代理
│   ├── role_agents.py         # RoleAgent：LLM 决策、记忆、信念、反思
│   ├── personalities/         # 5种人格
│   └── strategies/            # 各角色策略
├── frontend/                  # Vue 3 + Vite 前端
│   ├── src/
│   │   ├── App.vue            # 主应用（轮询、音频队列、状态管理）
│   │   └── components/        # 10个组件
│   ├── server.py              # Flask 后端（REST API + TTS 线程池）
│   └── dist/                  # 构建产物
├── docs/
│   └── modifications.md       # 完整修改记录
├── requirements.txt
└── README.md
```

### 通信架构

```
浏览器 ← 轮询 1s/次 → Flask 后端 ←→ 游戏引擎线程
                              ↕
                         TTS 线程池 (max 3)
                              ↕
                        edge-tts 云服务
```

---

## 🔧 常见问题

**Q: 没有 DeepSeek API Key 能玩吗？**
A: 能。不填 Key 时会使用 Mock 模式，AI 用模板发言，适合测试 UI 和 TTS。

**Q: TTS 语音没听到？**
A: 检查网络连接（edge-tts 需要访问微软云服务）。网络不佳时会自动降级到浏览器语音合成。

**Q: 语音不同步？**
A: 游戏引擎会在每个发言前等待 TTS 生成 + 音频播放完毕，节奏是自动适配的。如果感觉太快，可以增加 `step_delay` 参数。

**Q: 能改玩家人数吗？**
A: 目前固定为 9 人标准局（2狼 + 3神 + 4平民）。

---

## 📝 修改记录

详见 [docs/modifications.md](docs/modifications.md)
