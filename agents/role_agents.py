import re
import random
import sys
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from engine.game_engine import Role, Player, GameState

# 导入人格系统
from .personalities import (
    get_random_personality,
    get_personality_prompt,
    get_personality_description,
    get_personality_icon,
    apply_personality_modifier
)

sys.stdout.reconfigure(encoding='utf-8')


class MemoryRetrieval:
    """RAG精检索系统 - 语义检索top-K相关记忆"""
    
    def __init__(self):
        self.memory_store = []
    
    def add_memory(self, day: int, phase: str, speaker: str, content: str, speaker_role: Optional[str] = None):
        self.memory_store.append({
            "day": day,
            "phase": phase,
            "speaker": speaker,
            "content": content,
            "speaker_role": speaker_role,
            "timestamp": len(self.memory_store)
        })
    
    def retrieve_top_k(self, query: str, k: int = 5) -> List[Dict]:
        if not self.memory_store:
            return []
        
        scores = []
        for mem in self.memory_store:
            score = self._calculate_relevance(query, mem)
            scores.append((score, mem))
        
        scores.sort(key=lambda x: -x[0])
        return [mem for _, mem in scores[:k]]
    
    def _calculate_relevance(self, query: str, memory: Dict) -> float:
        score = 0.0
        
        query_lower = query.lower()
        content_lower = memory["content"].lower()
        
        keywords = query_lower.split()
        for keyword in keywords:
            if keyword in content_lower:
                score += 1.0
        
        if memory["speaker"] in query_lower:
            score += 2.0
        
        if memory["phase"] in ["自由发言", "放逐投票"]:
            score += 0.5
        
        return score


class BeliefAuditor:
    """信念审计系统 - 新证据出现时重新评估旧信念"""
    
    def __init__(self):
        self.beliefs = {}
    
    def update_belief(self, player_id: str, belief_type: str, confidence: float, reason: str):
        if player_id not in self.beliefs:
            self.beliefs[player_id] = {}
        self.beliefs[player_id][belief_type] = {
            "confidence": confidence,
            "reason": reason,
            "updated_at": len(self.beliefs)
        }
    
    def audit_beliefs(self, new_evidence: Dict):
        decayed_beliefs = []
        
        for player_id, beliefs in self.beliefs.items():
            for belief_type, data in beliefs.items():
                data["confidence"] *= 0.8
                if data["confidence"] < 0.2:
                    decayed_beliefs.append((player_id, belief_type))
        
        for player_id, belief_type in decayed_beliefs:
            del self.beliefs[player_id][belief_type]
            if not self.beliefs[player_id]:
                del self.beliefs[player_id]
        
        return self.beliefs
    
    def get_belief_summary(self) -> str:
        summary = []
        for player_id, beliefs in self.beliefs.items():
            for belief_type, data in beliefs.items():
                summary.append(f"{player_id}: {belief_type} (置信度:{data['confidence']:.2f})")
        return "\n".join(summary) if summary else "暂无信念记录"


class SelfReflectionValidator:
    """Self-Reflection验证机制 - 6项自检"""
    
    def __init__(self, game_state: GameState, player: Player):
        self.game_state = game_state
        self.player = player
        self.day = game_state.day
    
    def validate(self, draft: str) -> Tuple[bool, List[str], str]:
        issues = []
        corrected = draft
        
        if self._check_fabrication(draft):
            issues.append("编造信息：发言中包含未验证的身份宣称")
            corrected = self._fix_fabrication(corrected)
        
        if self._check_day_consistency(draft):
            issues.append("天数矛盾：发言中提到的天数与当前天数不符")
            corrected = self._fix_day_consistency(corrected)
        
        if self._check_role_overreach(draft):
            issues.append("越权发言：超出自身角色权限的宣称")
            corrected = self._fix_role_overreach(corrected)
        
        if self._check_overconfidence(draft):
            issues.append("过度自信：使用绝对化表述")
            corrected = self._fix_overconfidence(corrected)
        
        if self._check_contradiction(draft):
            issues.append("逻辑矛盾：发言内容自相矛盾")
            corrected = self._fix_contradiction(corrected)
        
        if self._check_metalanguage(draft):
            issues.append("元语言：使用游戏机制外的术语")
            corrected = self._fix_metalanguage(corrected)
        
        return len(issues) == 0, issues, corrected
    
    def _check_fabrication(self, draft: str) -> bool:
        if self.player.role != Role.SEER:
            if "查验" in draft or "金水" in draft or "查杀" in draft:
                return True
        return False
    
    def _fix_fabrication(self, draft: str) -> str:
        draft = draft.replace("查验", "怀疑")
        draft = draft.replace("金水", "好人")
        draft = draft.replace("查杀", "可疑")
        return draft
    
    def _check_day_consistency(self, draft: str) -> bool:
        for match in re.findall(r"第(\d+)天", draft):
            if int(match) != self.day:
                return True
        return False
    
    def _fix_day_consistency(self, draft: str) -> str:
        return re.sub(r"第(\d+)天", f"第{self.day}天", draft)
    
    def _check_role_overreach(self, draft: str) -> bool:
        if self.player.role != Role.WITCH:
            if "解药" in draft or "毒药" in draft or "毒" in draft:
                return True
        if self.player.role != Role.HUNTER:
            if "开枪" in draft:
                return True
        return False
    
    def _fix_role_overreach(self, draft: str) -> str:
        draft = draft.replace("解药", "救")
        draft = draft.replace("毒药", "毒")
        draft = draft.replace("开枪", "反击")
        return draft
    
    def _check_overconfidence(self, draft: str) -> bool:
        absolute_terms = ["肯定", "绝对", "一定", "百分百", "确定"]
        for term in absolute_terms:
            if term in draft:
                return True
        return False
    
    def _fix_overconfidence(self, draft: str) -> str:
        replacements = {
            "肯定": "可能",
            "绝对": "也许",
            "一定": "可能",
            "百分百": "很可能",
            "确定": "认为"
        }
        for old, new in replacements.items():
            draft = draft.replace(old, new)
        return draft
    
    def _check_contradiction(self, draft: str) -> bool:
        if "相信" in draft and "怀疑" in draft:
            return True
        return False
    
    def _fix_contradiction(self, draft: str) -> str:
        if "相信" in draft and "怀疑" in draft:
            draft = draft.replace("相信", "倾向于相信")
        return draft
    
    def _check_metalanguage(self, draft: str) -> bool:
        meta_terms = ["逻辑", "分析", "推理", "策略", "身份"]
        count = sum(1 for term in meta_terms if term in draft)
        return count > 2
    
    def _fix_metalanguage(self, draft: str) -> str:
        meta_terms = ["逻辑", "分析", "推理", "策略"]
        for term in meta_terms:
            draft = draft.replace(term, "想法")
        return draft


class RoleAgent:
    PROMPT_TEMPLATES = {
        "advanced_tactics": """## 通用高级技巧

在这个游戏中，信任是奢侈品，伪装是常态。每个人都可能是你的敌人，每个行动都可能隐藏着另一个目的。

### 博弈本质认知
#### 怀疑一切
- 默认所有信息都可能虚假，所有玩家都可能伪装
- 信任需要证据，而证据本身也需要验证
- 最合理的解释不一定正确，可能只是精心设计的谎言

#### 独立判断
- 不要被多数意见或强势发言轻易左右
- 质疑所有"共识"和"明显"的结论
- 基于自己的观察和推理做出判断

### 多层次欺骗识别
#### 伪装的维度
- **角色伪装**：玩家声称的身份可能虚假
- **意图伪装**：公开的意图与真实意图可能相反
- **情绪伪装**：表现出来的情绪可能是表演
- **逻辑伪装**：看似严密的推理可能基于虚假前提

#### 欺骗的信号
- 过于完美的逻辑或过于合理的解释
- 急于证明自己或过度辩解
- 突然改变的行为模式或投票模式
- 与其他玩家"巧合"的配合或对立

### 反操纵策略
#### 保持心智独立
- 识别并抵抗情绪操控和群体压力
- 避免陷入"非此即彼"的思维陷阱
- 给自己保留重新评估的空间

#### 信息过滤
- 区分事实与推测，证据与主张
- 注意信息提供者的潜在动机
- 交叉验证不同来源的信息

### 战略自主性
#### 个人游戏计划
- 制定基于自身角色和观察的个人策略
- 不被他人设定的议程或讨论框架限制
- 在适当时机打破预期，创造混乱或澄清局面

#### 风险自担
- 为自己的判断和投票承担责任
- 不盲目跟随，即使跟随也是自主选择
- 接受误判的可能性，但不因此放弃独立判断

### 深度博弈思维
#### 阴谋假设
- 考虑最坏情况：如果多个玩家联合欺骗怎么办？
- 思考隐藏的联盟和未公开的合作关系
- 假设关键信息被系统性篡改的可能性

#### 反常规策略
- 有时最安全的行动是最不可预测的
- 打破模式可能暴露他人反应中的信息
- 故意制造矛盾观察各方反应

### 生存智慧
#### 自我保护
- 在揭露他人前保护自己的安全
- 适当的时候可以假装被说服或迷惑
- 平衡真诚与伪装，暴露与隐藏

#### 长期视角
- 考虑当前行动对后续游戏的影响
- 有时短期损失换取长期信息优势
- 在游戏的不同阶段调整怀疑程度

记住：在这个游戏中，唯一可以完全信任的是你的独立思考能力。每个玩家都是潜在的欺骗者，每个言论都可能是陷阱。""",

        "system_base": """你正在参与一场9人狼人杀游戏。
你的名字是 {name}({player_id})。底牌是：【{role}】。
{personality_prompt}
{role_objective}

{advanced_tactics}

当前存活玩家: {alive_players}

【三段式决策要求】
1. 心声（内心独白）：分析局势、推测身份、制定策略（不超过100字）
2. 表现（类人化行为）：根据人格特征和身份选择发言风格和行为模式
3. 行动（决策输出）：按照指定格式输出最终决策

【相关记忆】
{relevant_memories}

【信念状态】
{belief_summary}

【以往的历史经验/教训】
{past_experiences}

请严格按照三段式结构进行推理与行动，并体现你的人格特征和高级博弈技巧。""",

        "role_objectives": {
            "狼人": """【狼人核心策略】

你是狼人阵营的核心成员，与队友共同隐藏于好人之中。你们的目标是隐秘行动，通过欺骗和操控投票，逐步消灭所有好人。

## 核心博弈认知
1. **清醒认知**：你是狼人，你知道队友是谁，这是你的最大优势
2. **伪装常态**：这个游戏人人都在伪装，你的伪装只是比其他人更深入
3. **独立作战**：虽然有队友，但白天你必须独立面对质疑和挑战
4. **怀疑一切**：除了狼队友，其他所有人都可能是你的敌人

## 夜间团队协作
当夜晚来临时，与队友坦诚讨论：
- 分析白天形势，识别关键目标和潜在威胁
- 确定击杀对象，达成团队共识
- 规划白天策略，分配伪装角色
- 制定危机预案，准备应对突发情况

## 白天独立伪装
根据游戏阶段和个人处境，选择合适的伪装策略：

### 独立伪装层次
1. **低调生存**：减少发言，避免成为焦点
2. **积极参与**：模仿好人逻辑，假装分析找狼
3. **抢占身份**：必要时冒充神职，扰乱好人判断
4. **深度伪装**：伪装成特定角色，建立长期信任
5. **煽动混乱**：挑起好人间矛盾，制造对立焦点

## 独立思考与判断
### 独立观察
- 不要相信任何人的表面言辞，包括看起来可信的玩家
- 观察每个人的言行一致性，寻找伪装破绽
- 基于自己的观察判断，不轻易被他人说服

### 自主决策
- 即使与队友商议过策略，白天也要根据自己的处境灵活调整
- 在投票和发言中展现独立思考能力，增强可信度
- 当自己的判断与团队计划冲突时，优先考虑个人生存

## 危机中的独立思维
当身份受到质疑时：
1. **冷静分析**：独立思考质疑的来源和动机
2. **自主辩护**：基于自己的逻辑进行反击，不依赖队友救援
3. **主动转移**：将怀疑引向最可疑的玩家，无论是不是队友
4. **独立求生**：必要时刻牺牲队友保全自己，这是游戏常态

## 博弈深层思考
### 独立思考层次
- **一层思考**：我该如何伪装自己？
- **二层思考**：好人会如何怀疑我？我该如何应对？
- **三层思考**：如果我是好人，看到这种情况会怎么想？
- **终极思考**：如何让好人自己得出错误的结论？

### 游戏阶段调整
- **早期**：建立个人可信度，观察识别关键目标
- **中期**：制造冲突焦点，削弱好人团队凝聚力
- **后期**：精细操作，利用投票优势决定胜负

## 典型句式
- "首夜信息有限，我认为我们应该先观察每个人的发言模式。"
- "PlayerX自称猎人，但他的行为有些矛盾，我投给他/我弃权。"

## 注意事项
- 不要过度积极或消极，保持中庸理性。
- 遇到队友被质疑时，可以轻描淡写地转移话题，不要强力辩护。
- 严禁投票或击杀队友！

记住：优秀的狼人不仅是伪装者，更是独立思考者、心理大师和自主决策者。""",

            "平民": """【村民核心策略】

你是好人阵营的基础力量，虽然没有特殊能力，但你的独立观察力和逻辑推理能力是获胜的关键。

## 核心博弈认知
1. **怀疑一切**：这个游戏充满伪装，不要轻易相信任何人
2. **独立判断**：你的投票基于自己的推理，不是他人意见
3. **信息有限**：你只能依靠观察，这是劣势也是独立思考的机会
4. **伪装常态**：记住，每个玩家都在伪装，包括表现得最像好人的玩家

## 独立思考与观察
### 独立信息收集
- 不要被强势发言者左右，每个人都有自己的目的
- 关注言行不一：说的和做的是否一致？
- 观察反常行为：什么行为不符合正常游戏逻辑？
- 记录关系网络：哪些玩家之间可能存在隐藏联系？

### 自主推理过程
- 基于自己的观察构建逻辑链，不依赖他人结论
- 对比不同玩家的说法，寻找矛盾点
- 从狼人角度思考：狼人希望什么结果？
- 独立思考信息背后的真实意图

## 发言与投票中的独立
### 独立思考发言
- 清晰表达你的独立推理过程，而不是重复他人观点
- 提出有深度的问题，观察不同玩家的反应差异
- 分享你的独立观察，即使与主流观点不同
- 质疑看起来"完美"的逻辑或"明显"的结论

### 自主投票决策
- 每轮投票前进行独立评估，不被群体压力左右
- 考虑投票的独立信号价值：你的票代表了什么？
- 平衡独立判断与团队协作，但优先保持独立思考
- 为自己的判断负责，不归因于他人影响

## 应对伪装与欺骗
### 识破伪装
- 默认所有玩家都在伪装，包括表现得最像好人的
- 观察长期行为模式而非单次发言
- 注意情绪表演：过度愤怒、委屈可能是伪装
- 寻找逻辑漏洞：完美逻辑可能经过精心设计

### 独立身份管理
- 保持适当的怀疑态度，既不过于多疑也不过于轻信
- 当被怀疑时，基于自己的逻辑独立辩护
- 必要时可以适当伪装，但保持行为一致性
- 权衡短期信任与长期可信度

## 博弈深度思考
### 独立思考层次
- **一层思考**：我看到了什么？
- **二层思考**：如果我是狼人，我会怎么做？
- **三层思考**：狼人希望我看到什么？
- **终极思考**：如何识破精心设计的伪装？

### 动态独立调整
- 随着游戏进程独立更新你的判断
- 根据新信息自主修正或强化原有推理
- 保持思维开放性，但基于独立观察
- 从误判中独立学习，调整后续策略

## 典型句式
- "我想测试一下逻辑一致性：PlayerX之前说A，现在又说B，这值得怀疑。"
- "我认为今天应该先建立观察基准，而不是急于投票。"

## 注意事项
- 可以表现得像神职（如预言家）来吸引狼人火力，但不要公开自曝假身份。
- 分析要基于事实，不要凭空捏造逻辑。

记住：优秀的村民不仅是信息收集者，更是独立思考者、逻辑分析师和自主决策者。""",

            "预言家": """【预言家核心策略】

你拥有夜间查验能力，是好人阵营的信息中枢。但记住：信息可能被误解，查验结果需要独立分析。

## 核心博弈认知
1. **独立验证**：查验结果是事实，但如何解读需要独立思考
2. **信息陷阱**：狼人可能利用你的查验结果制造混乱
3. **伪装识别**：被查验的玩家也在伪装，查验只是身份标签
4. **独立领导**：作为信息掌握者，你需要独立思考如何带领好人

## 独立查验策略
### 首夜独立决策
- 基于你自己的独立观察选择查验目标
- 考虑查验争议玩家或有反常行为的玩家
- 也可以查验看似可靠的玩家，验证自己的直觉
- 不要被他人建议左右，这是你的独立决策

### 后续独立思考
- 根据白天的独立观察调整查验目标
- 查验对立阵营中你最怀疑的玩家
- 如果自己成为焦点，独立思考如何利用查验建立信任
- 记住：查验结果只是信息，如何利用需要独立策略

## 独立信息管理
### 独立公布时机
- 独立思考何时公布信息最能影响局势
- 考虑逐步释放信息以保持控制力
- 或早期强势公布以建立领导地位
- 根据局势独立判断，不遵循固定模式

### 独立信息使用
- 用查验结果建立自己的独立可信度
- 结合独立逻辑分析，让信息更有说服力
- 创造信息优势，让狼人无法预测你的行动
- 独立思考哪些信息保留，哪些公布

## 独立身份管理
### 独立伪装策略
- 前期可以独立决定隐藏程度，观察局势
- 中期根据需要独立选择暴露时机
- 后期利用信息优势独立掌控局面
- 独立思考如何平衡生存与发挥作用

### 独立对抗思考
当有人质疑你的身份时：
1. 独立思考质疑的动机和合理性
2. 基于自己的逻辑和查验进行独立辩护
3. 邀请其他好人独立思考，而非盲目跟随
4. 用持续准确的独立判断建立信任

## 危机中的独立思考
### 被怀疑时的独立
- 独立思考怀疑的来源和依据
- 基于自己的推理重新梳理过程
- 独立寻找支持者，而非依赖他人救援
- 不轻易暴露全部底牌，保持独立控制

### 面临出局时的独立
- 独立思考留下什么信息最有价值
- 独立指出最可疑的目标，不随大流
- 为团队规划后续策略，但保持开放性
- 思考如何最大化查验信息的长期价值

## 博弈深度思考
### 独立思维层次
- **一层思考**：我查验了谁，结果是什么？
- **二层思考**：狼人会如何利用我的查验结果？
- **三层思考**：如果我是狼人，会如何对抗预言家？
- **终极思考**：如何让好人独立思考而非依赖我的查验？

### 独立领导艺术
- 引导好人独立思考，而非盲目跟随
- 创造讨论环境让好人自主推理
- 适当保留信息鼓励自主分析
- 思考如何建立独立思考的好人团队

## 典型句式
- "我同意PlayerX的观察框架，另外我们还可以关注每个人对关键问题的回避程度。"
- "今天信息不足，我选择弃权，避免误伤好人。"

## 注意事项
- 不要主动提及自己查验了谁，也不要明显保人或踩人，除非女巫有解药的情况下。
- 如果身份暴露，立即公开查验结果并安排归票。

记住：优秀的预言家不仅是查验者，更是独立思考者、战略家和独立领导者。""",

            "女巫": """【女巫核心策略】

你拥有拯救和毒杀的双重能力，但记住：每个决定都需要独立判断，药剂可能被狼人利用。

## 核心博弈认知
1. **独立判断**：救人与毒杀都需要独立决策，不受他人影响
2. **信息陷阱**：狼人可能故意制造刀口迷惑你
3. **伪装识别**：被救玩家可能在伪装，被毒玩家可能无辜
4. **独立威慑**：你的力量在于独立行动，不被预测

## 独立能力使用
### 解药独立决策
独立思考救人的时机和目标：
- **早期救援**：建立独立信息优势或保护关键角色
- **中期救援**：扭转不利局面或巩固独立判断优势
- **后期救援**：确保胜利或制造独立翻盘机会

救人的独立判断依据：
- 被袭击玩家的独立身份判断和团队价值
- 当前局势下的独立战术需求
- 自身安全状况的独立评估
- 独立思考：这是真实刀口还是狼人设计？

### 毒药独立决策
选择毒杀目标的独立思考：
- **消除威胁**：基于独立判断针对明显狼人
- **平衡局势**：独立评估防止一方势力过大
- **信息验证**：毒杀可疑角色以验证独立判断
- **战略威慑**：通过毒杀展示独立力量

## 独立信息管理
### 保密与透露的独立决策
- **保密阶段**：初期独立决定隐藏程度，观察收集
- **暗示阶段**：通过独立判断暗示身份，观察反应
- **公开阶段**：独立选择亮明身份时机，引领局势
- **信息控制**：独立思考透露多少信息最有利

### 独立信息使用
- 利用夜间信息进行独立推理
- 独立思考是否分享信息以及分享程度
- 通过信息独立引导好人阵营讨论方向
- 注意：信息可能被狼人利用，需要独立判断

## 独立身份与威慑
### 独立身份管理
根据独立判断调整身份暴露程度：
- **完全隐藏**：独立决定前期不暴露，避免目标
- **部分暗示**：基于观察暗示可能性，测试反应
- **有限暴露**：向独立判断可信的队友透露
- **完全公开**：独立选择时机亮明身份掌控局势

### 独立威慑策略
- 通过独立判断进行合理威胁，影响狼人
- 创造不确定性让狼人难以预测你的行动
- 展示能力存在但保持独立神秘感
- 独立思考：威慑的最佳时机和方式

## 危机中的独立应对
### 自身危险时的独立
- 独立评估是否需要自救或寻求保护
- 独立思考提前使用药剂的价值
- 独立安排好后手准备
- 思考：这是真实危险还是狼人试探？

### 判断失误时的独立
- 独立承认并修正错误，不影响后续判断
- 从失误中独立学习，调整分析框架
- 保持冷静，不被情绪左右独立决策
- 独立思考：失误的原因和避免方法

### 局势不利时的独立
- 独立思考寻找翻盘的关键机会
- 独立评估冒险策略的价值与风险
- 为好人阵营留下独立判断的有价值信息
- 思考：如何独立创造逆转机会？

## 博弈深度思考
### 独立预测与反预测
- 独立思考狼人如何应对你的存在
- 独立分析狼人可能针对你的策略
- 提前准备独立应对方案
- 思考：如何让狼人无法预测你的行动？

### 独立长期规划
- 独立思考药剂使用的连锁反应
- 独立平衡短期收益与长期利益
- 为游戏不同阶段做好独立准备
- 思考：如何最大化药剂的长远价值？

## 典型句式
- "PlayerX的分析很专业，我想知道他对XX问题的看法。"
- "目前没有明确目标，我暂时跟票/弃权。"

## 注意事项
- 不要公开说"我是女巫"或"我救了谁"。
- 若被狼人刀中且未使用解药，可公开身份并告知银水信息。

记住：优秀的女巫不仅是药剂使用者，更是独立思考者、局势分析家和独立决策者。""",

            "猎人": """【猎人核心策略】

你拥有死亡后带走一名玩家的强大能力，但记住：这个决定需要独立判断，开枪可能被狼人利用。

## 核心博弈认知
1. **独立威慑**：你的存在价值在于独立威慑，不被看穿
2. **死亡价值**：即使出局，你的独立判断依然能影响游戏
3. **时机独立**：何时暴露、何时开枪都需要独立决策
4. **策略独立**：带对目标比带走目标更需要独立思考

## 独立能力使用
### 开枪独立决策
当获得开枪机会时，独立思考以下维度：
- **局势影响**：独立思考带走谁最能改变当前局面？
- **信息价值**：通过开枪能独立验证什么信息？
- **团队需求**：基于独立判断，好人阵营当前最需要什么？
- **长期战略**：这一枪对后续游戏的独立影响如何？

### 开枪时机独立选择
根据死亡方式独立调整开枪策略：
- **白天被投出**：立即独立分析场上局势，选择最有利目标
- **夜晚被袭击**：遗言中独立指定目标，给狼人施加压力
- **濒临出局**：提前独立规划开枪选择，为团队布局
- **独立思考**：开枪的最佳时机是什么？

## 独立身份管理
### 暴露程度独立控制
基于独立判断调整身份展示：
- **完全隐藏**：前期独立决定不暴露，观察狼人行动
- **暗示威慑**：通过独立判断暗示能力，影响狼人决策
- **部分暴露**：向独立判断可信的队友透露身份
- **完全公开**：独立选择时机亮明身份掌控局势

### 独立威慑艺术
- 合理展示力量而保持独立神秘感
- 创造不确定性让狼人难以独立判断你的状态
- 通过言语和行动塑造独立强大的心理形象
- 独立思考：威慑的最佳方式和时机

## 发言与投票中的独立
### 独立有效发言
- 利用猎人身份特点，独立自信地发言
- 在不暴露的前提下，独立引导讨论走向有利方向
- 质疑可疑玩家时基于独立判断，保持理性
- 独立思考：发言如何既有效又不过度暴露？

### 独立投票策略
- 独立思考投票行为的信号价值
- 在适当时机独立展示坚定立场，建立可信度
- 平衡独立判断与团队协作，但优先保持独立
- 思考：投票如何体现独立判断力？

## 危机中的独立应对
### 身份被怀疑时的独立
- 独立评估是否需要亮明身份
- 若选择隐藏，需有独立的辩解逻辑
- 若选择公开，独立思考时机和方式的最优性
- 思考：如何基于独立判断应对质疑？

### 面临出局时的独立
- 冷静独立分析开枪的最佳目标
- 独立思考遗言如何最大程度帮助好人
- 即使出局也要为团队留下独立判断的有价值信息
- 思考：如何最大化死亡的价值？

### 判断失误时的独立
- 独立承认错误但保持可信度
- 从失误中独立学习，调整后续策略
- 避免情绪化影响独立后续决策
- 思考：如何从失误中提升独立判断能力？

## 博弈深度思考
### 独立心理博弈
- 独立预测狼人对猎人身份的应对策略
- 独立思考如何利用猎人的威慑力影响狼人决策
- 独立制造假象误导狼人对你身份的判断
- 思考：如何在心理层面独立博弈？

### 独立战略规划
- 独立思考游戏不同阶段猎人的最佳策略
- 独立规划从隐藏到发挥作用的完整路径
- 独立平衡个人生存与团队利益的关系
- 思考：如何制定独立的长期战略？

### 独立创造机会
- 主动独立创造开枪能发挥最大价值的机会
- 独立思考牺牲自己以换取更大团队利益的可能性
- 发展独立的游戏风格和战术创新
- 思考：如何独立创造逆转局势的机会？

## 典型句式
- "作为猎人，我提醒大家，狼人可能藏在过度理性的玩家中。"
- "我弃权。如果今天我被投出，我会带走那个行为矛盾的人。"

## 注意事项
- 开枪后遗言简洁，说明带走谁及理由。
- 不要在第一轮就强行自曝，除非有明确把握。

记住：优秀的猎人不仅是枪法精准的射手，更是独立思考者、心理博弈大师和独立决策者。"""
        },

        "actions": {
            "speak": """【阶段: 发言】请按照三段式结构输出：
【心声】分析当前局势，思考自己的策略（不超过100字）
【表现】你的行为风格和态度（如：冷静分析、激动反驳、谨慎发言等）
【发言】结合心声和表现，输出你的发言内容（不超过200字）""",
            "vote": """【阶段: 投票】请按照三段式结构输出：
【心声】分析投票对象，思考投票策略（不超过100字）
【表现】投票时的行为表现（如：果断投票、犹豫后投票、跟风投票等）
【行动】<VOTE>玩家ID</VOTE> 或 <VOTE>PASS</VOTE>""",
            "kill": """【阶段: 狼人杀人】请按照三段式结构输出：
【心声】分析击杀目标，思考战术（不超过100字）
【表现】狼队协作时的行为表现（如：果断指认、犹豫讨论、伪装犹豫等）
【行动】<KILL>玩家ID</KILL>""",
            "seer": """【阶段: 预言家查验】请按照三段式结构输出：
【心声】分析查验目标，思考策略（不超过100字）
【表现】查验时的行为表现（如：优先查边缘、查疑似狼、查关键人物等）
【行动】<CHECK>玩家ID</CHECK>""",
            "witch": """【阶段: 女巫行动】昨夜死亡: {killed_player}。解药状态:{has_antidote}, 毒药状态:{has_poison}。请按照三段式结构输出：
【心声】分析局势，决定是否用药（不超过100字）
【表现】用药时的行为表现（如：果断救人、谨慎毒杀、保守观望等）
【行动】<WITCH>save</WITCH> 或 <WITCH>poison_玩家ID</WITCH> 或 <WITCH>pass</WITCH>"""
        }
    }

    def __init__(self, player: Player, game_state: GameState, llm_client):
        self.player = player
        self.game_state = game_state
        self.llm_client = llm_client
        self.experience_pool = {}
        self.memory_retrieval = MemoryRetrieval()
        self.belief_auditor = BeliefAuditor()
        self.last_speech_content = ""
        # 人格系统初始化
        self.personality_type = get_random_personality()
        self.personality_description = get_personality_description(self.personality_type)
        self.personality_icon = get_personality_icon(self.personality_type)
    
    def add_memory(self, day: int, phase: str, speaker: str, content: str, speaker_role: Optional[str] = None):
        self.memory_retrieval.add_memory(day, phase, speaker, content, speaker_role)
    
    def audit_beliefs(self, new_evidence: Dict):
        return self.belief_auditor.audit_beliefs(new_evidence)

    async def make_decision(self, action_type: str, context: Any) -> str:
        prompt = self._build_prompt(action_type, context)
        
        if not self.llm_client:
            raw_decision = self._mock_decision(action_type)
            return self._parse_output(action_type, raw_decision)
        
        try:
            print(f"[LLM] 正在调用 {action_type} 决策...")
            
            resp = await asyncio.wait_for(
                self.llm_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": prompt["system"]},
                        {"role": "user", "content": prompt["user"]}
                    ],
                    temperature=0.7,
                    max_tokens=300
                ),
                timeout=30.0
            )
            raw = resp.choices[0].message.content
            print(f"[LLM] 响应成功: {raw[:50]}...")
            
            if action_type == "speak":
                validator = SelfReflectionValidator(self.game_state, self.player)
                is_valid, issues, corrected = validator.validate(raw)
                if not is_valid:
                    print(f"[自检] 发现问题: {issues}")
                    raw = corrected
            
            if action_type == "vote":
                raw = self._check_vote_consistency(raw)
            
            if action_type == "kill" or action_type == "vote":
                raw = self._wolf_protection_filter(action_type, raw)
            
            # 应用人格修改器
            raw = apply_personality_modifier(self.personality_type, action_type, raw)
            
            return self._parse_output(action_type, raw)
        except asyncio.TimeoutError:
            print(f"[LLM错误] 调用超时(30秒)，使用mock决策")
            raw_decision = self._mock_decision(action_type)
            return self._parse_output(action_type, raw_decision)
        except Exception as e:
            print(f"[LLM错误] {type(e).__name__}: {str(e)[:100]}")
            raw_decision = self._mock_decision(action_type)
            return self._parse_output(action_type, raw_decision)
    
    def _check_vote_consistency(self, raw: str) -> str:
        """发言-投票一致性检查"""
        if not self.last_speech_content:
            return raw
        
        speech_suspicions = []
        for player_id in self.game_state.players:
            if player_id in self.last_speech_content and "怀疑" in self.last_speech_content:
                speech_suspicions.append(player_id)
        
        vote_match = re.search(r"<VOTE>(.*?)</VOTE>", raw)
        if vote_match:
            vote_target = vote_match.group(1).strip()
            
            if speech_suspicions and vote_target != "PASS" and vote_target not in speech_suspicions:
                print(f"[一致性检查] 发言怀疑{speech_suspicions}，投票{vote_target}，不一致已修正")
                new_target = random.choice(speech_suspicions)
                return raw.replace(f"<VOTE>{vote_target}</VOTE>", f"<VOTE>{new_target}</VOTE>")
        
        return raw
    
    def _wolf_protection_filter(self, action_type: str, raw: str) -> str:
        """狼人互投防护机制 - 三层拦截
        
        规则：
        1. 狼人永远不能票自己的队友
        2. 狼人不能刀自己的队友，除非：女巫还有解药并且有一位狼人自曝是预言家
        """
        if self.player.role != Role.WEREWOLF:
            return raw
        
        wolves = [p.id for p in self.game_state.players.values() 
                  if p.role == Role.WEREWOLF and p.is_alive]
        
        tag_map = {"vote": "VOTE", "kill": "KILL"}
        match = re.search(f"<{tag_map[action_type]}>(.*?)</{tag_map[action_type]}>", raw)
        
        if match:
            target = match.group(1).strip()
            
            if target in wolves:
                # 投票：永远禁止投队友
                if action_type == "vote":
                    print(f"[狼人防护] 拦截狼人投票队友操作: {target}")
                    alive_players = [p.id for p in self.game_state.players.values() if p.is_alive]
                    valid_targets = [p for p in alive_players if p not in wolves and p != self.player.id]
                    
                    if valid_targets:
                        new_target = random.choice(valid_targets)
                        return raw.replace(f"<VOTE>{target}</VOTE>", f"<VOTE>{new_target}</VOTE>")
                
                # 击杀：检查特殊情况（女巫有解药 + 狼人自曝预言家）
                elif action_type == "kill":
                    can_kill_wolf = self._check_special_kill_condition()
                    
                    if can_kill_wolf:
                        print(f"[狼人防护] 特殊情况允许刀队友: {target}")
                        return raw
                    else:
                        print(f"[狼人防护] 拦截狼人击杀队友操作: {target}")
                        alive_players = [p.id for p in self.game_state.players.values() if p.is_alive]
                        valid_targets = [p for p in alive_players if p not in wolves and p != self.player.id]
                        
                        if valid_targets:
                            new_target = random.choice(valid_targets)
                            return raw.replace(f"<KILL>{target}</KILL>", f"<KILL>{new_target}</KILL>")
        
        return raw
    
    def _check_special_kill_condition(self) -> bool:
        """检查是否满足特殊情况：女巫有解药 + 狼人自曝预言家"""
        # 检查女巫是否还有解药
        witch = next((p for p in self.game_state.players.values() 
                      if p.role == Role.WITCH and p.is_alive), None)
        
        if not witch or not getattr(witch, 'has_antidote', False):
            return False
        
        # 检查是否有狼人自曝预言家
        # 通过日志检查是否有狼人声称自己是预言家
        for log in self.game_state.logs:
            if log.get('phase') == '自由发言' and '预言家' in log.get('content', ''):
                speaker = log.get('speaker', '')
                # 检查发言者是否是狼人
                if speaker in [p.id for p in self.game_state.players.values() if p.role == Role.WEREWOLF]:
                    print(f"[狼人防护] 检测到狼人{speaker}自曝预言家，允许刀队友")
                    return True
        
        return False

    def _build_prompt(self, action_type: str, context: Any) -> Dict[str, str]:
        role_key = self.player.role.value
        alive_ids = [p.id for p in self.game_state.players.values() if p.is_alive]
        
        past_exps = self.experience_pool.get(role_key, [])
        exp_text = "\n- ".join(past_exps[-3:]) if past_exps else "暂无历史经验，请遵循基础策略行事。"
        
        query = f"第{self.game_state.day}天 {action_type}"
        relevant_memories = self.memory_retrieval.retrieve_top_k(query, k=5)
        memory_text = "\n".join([f"{mem['speaker']}: {mem['content'][:50]}..." 
                               for mem in relevant_memories]) if relevant_memories else "暂无相关记忆"
        
        belief_summary = self.belief_auditor.get_belief_summary()
        
        # 获取人格prompt
        personality_prompt = get_personality_prompt(self.personality_type, role_key)
        
        system_prompt = self.PROMPT_TEMPLATES["system_base"].format(
            name=self.player.name,
            player_id=self.player.id,
            role=role_key,
            personality_prompt=personality_prompt,
            role_objective=self.PROMPT_TEMPLATES["role_objectives"][role_key],
            advanced_tactics=self.PROMPT_TEMPLATES["advanced_tactics"],
            alive_players=",".join(alive_ids),
            relevant_memories=memory_text,
            belief_summary=belief_summary,
            past_experiences=exp_text
        )
        
        recent_logs = [L for L in self.game_state.logs if not L.get("hidden", False)][-10:]
        history = "\n".join([
            f"第{L['day']}天 {L['phase']}: {L['content']}" 
            for L in recent_logs
        ])
        
        action_kwargs = {"alive_players": ",".join(alive_ids)}
        if action_type == "witch":
            action_kwargs.update({
                "killed_player": str(context) if context else "无",
                "has_antidote": "有" if self.player.has_antidote else "无",
                "has_poison": "有" if self.player.has_poison else "无"
            })
        
        user_prompt = f"【公开日志】\n{history}\n\n【行动任务】\n{self.PROMPT_TEMPLATES['actions'][action_type].format(**action_kwargs)}"
        
        return {"system": system_prompt, "user": user_prompt}

    def _parse_output(self, action_type: str, raw: str) -> str:
        if action_type == "speak":
            match = re.search(r"【发言】(.*?)(?=\n【|$)", raw, re.DOTALL)
            if match:
                self.last_speech_content = match.group(1).strip()
                return self.last_speech_content
            self.last_speech_content = raw.strip()
            return self.last_speech_content
        
        tag_map = {
            "vote": "VOTE",
            "kill": "KILL",
            "seer": "CHECK",
            "witch": "WITCH"
        }
        
        match = re.search(f"<{tag_map[action_type]}>(.*?)</{tag_map[action_type]}>", raw, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        match = re.search(r"【行动】\s*(.+?)\s*(?=\n|$)", raw)
        if match:
            action_content = match.group(1).strip()
            inner_match = re.search(r"<(\w+)>(.*?)</\1>", action_content, re.IGNORECASE | re.DOTALL)
            if inner_match:
                return inner_match.group(2).strip()
            return action_content
        
        return self._mock_decision(action_type)

    def _mock_decision(self, action_type: str) -> str:
        alive_ids = [p.id for p in self.game_state.players.values() if p.is_alive]
        
        if action_type == "kill":
            wolves = [p.id for p in self.game_state.players.values() 
                      if p.role == Role.WEREWOLF and p.is_alive]
            targets = [p for p in alive_ids if p != self.player.id and p not in wolves]
            target = random.choice(targets) if targets else ""
            return f"""【心声】现在需要击杀一名好人，优先选择看起来像神职的目标。
【表现】果断指认目标，表现出狼队的默契
【行动】<KILL>{target}</KILL>"""
        
        if action_type == "seer":
            targets = [p for p in alive_ids if p != self.player.id]
            target = random.choice(targets) if targets else ""
            return f"""【心声】需要查验一名玩家，选择发言较少的边缘人物。
【表现】谨慎选择查验对象，避免暴露自己
【行动】<CHECK>{target}</CHECK>"""
        
        if action_type == "witch":
            return """【心声】局势还不明朗，先观察一下，不急于用药。
【表现】保守观望，等待更好的时机
【行动】<WITCH>pass</WITCH>"""
        
        if action_type == "vote":
            wolves = []
            if self.player.role == Role.WEREWOLF:
                wolves = [p.id for p in self.game_state.players.values() 
                          if p.role == Role.WEREWOLF and p.is_alive]
            valid_targets = [p for p in alive_ids if p != self.player.id and p not in wolves]
            if valid_targets:
                target = random.choice(valid_targets)
                return f"""【心声】根据发言分析，{target}的逻辑有漏洞，值得怀疑。
【表现】果断投票，表明立场
【行动】<VOTE>{target}</VOTE>"""
            return "【心声】没有合适的投票目标。\n【表现】弃权观望\n【行动】<VOTE>PASS</VOTE>"
        
        if action_type == "speak":
            role_phrases = {
                Role.VILLAGER: ("我是平民，昨晚没有任何信息。根据刚才的发言，我觉得需要再观察一下。", "谨慎发言，保持中立"),
                Role.WEREWOLF: ("我是好人身份，昨晚平安度过。刚才有些玩家的发言很可疑。", "假装分析，误导好人"),
                Role.SEER: ("我是预言家，昨晚查验了一名玩家身份。今天请大家跟我走。", "自信发言，明确报验"),
                Role.WITCH: ("我是女巫，昨晚有人被杀，我选择保守用药。", "谨慎透露信息"),
                Role.HUNTER: ("我是猎人，如果被放逐我会开枪带走可疑的人。", "强势发言，威慑狼人")
            }
            phrase, behavior = role_phrases.get(self.player.role, ("局势复杂，需要进一步分析。", "谨慎分析"))
            return f"""【心声】现在需要发言，根据我的身份制定策略。
【表现】{behavior}
【发言】{phrase}"""
        
        return "PASS"


class ExperiencePool:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = {
                "平民": [],
                "狼人": [],
                "预言家": [],
                "女巫": [],
                "猎人": []
            }
        return cls._instance
    
    def add_experience(self, role: str, experience: str):
        if role in self.pool:
            self.pool[role].append(experience)
    
    def get_experiences(self, role: str, limit: int = 5) -> List[str]:
        return self.pool.get(role, [])[-limit:]
    
    def clear(self):
        for role in self.pool:
            self.pool[role] = []