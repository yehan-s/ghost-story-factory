# Intent Mapping - 设计说明 (Design Rationale)

**文档用途：** 本说明阐明"意图识别与映射"系统的核心设计原则。它解释了在选项交互式游戏中，Intent Mapping 的角色和功能。

---

## 游戏交互模式说明

**本项目采用：选项交互式**
- 玩家从预设的2-4个选项中选择（A/B/C/D）
- Intent Mapping 的主要职责**不是**解析自由文本
- Intent Mapping 的主要职责**是**：
  1. 辅助 Choice Points 生成合理的选项
  2. 将玩家的选择（A/B/C/D）映射到后果树
  3. 处理极少数的自由文本补充（如输入NPC名字）

---

## 设计挑战（选项式游戏）

**核心问题：** 选项式游戏中，Intent Mapping 不需要处理"千变万化的自然语言"，而是需要确保：
1. 每个选项都能准确映射到游戏逻辑
2. 选项的后果清晰、可预测
3. 选项与后果树的关联明确

**举例：**
```
Choice Points 生成的选项：
A) 躲进监控室 → HIDE + location:监控室
B) 冲向楼梯 → FLEE + direction:楼梯
C) 使用念佛机 → USE_ITEM + item:念佛机

Intent Mapping 的工作：
- 将选项A映射到 {intent: "HIDE", target: "监控室", consequence: "主线分支A"}
- 将选项B映射到 {intent: "FLEE", target: "楼梯", consequence: "主线分支B"}
- 将选项C映射到 {intent: "USE_ITEM", target: "念佛机", consequence: "特殊分支"}
```

**设计目标：** 建立清晰的"选项→意图→后果"映射表，确保游戏逻辑的一致性和可预测性。

---

## Intent Mapping 在自由输入式游戏中的角色（可选）

**注：** 如果未来需要支持自由文本输入（酒馆式），Intent Mapping 也可以扩展为：

**核心问题：** 酒馆式游戏允许玩家用自然语言输入任何行为，但后端的《世界书》和《GDD》是基于"结构化意图"设计的。

**举例：**
```
玩家可能的自由输入：
- "我躲起来"
- "我藏在桌子下面"
- "我装死"
- "我蹲下不动"

这些都应该映射到同一个意图：HIDE（躲藏）
```

但在当前的选项式设计中，这种复杂性被 Choice Points 模块承担了。

---

## 核心原则一：分层意图架构 (Hierarchical Intent)

**设计说明：** 意图不是"扁平"的，而是**分层嵌套**的。

**实现方式：**

```
顶层意图（Top-Level Intent）
├── 探索 (EXPLORE)
│   ├── 移动 (MOVE)
│   │   ├── 换楼层 (CHANGE_FLOOR)
│   │   └── 同楼层移动 (SAME_FLOOR)
│   ├── 调查 (INVESTIGATE)
│   │   ├── 检查物体 (EXAMINE_OBJECT)
│   │   ├── 搜索区域 (SEARCH_AREA)
│   │   └── 触摸/拿取 (TOUCH/TAKE)
│   └── 观察 (OBSERVE)
│       ├── 看 (LOOK)
│       └── 听 (LISTEN)
│
├── 交互 (INTERACT)
│   ├── 对话 (TALK)
│   │   ├── 询问 (ASK)
│   │   └── 回答 (ANSWER)
│   ├── 使用道具 (USE_ITEM)
│   │   ├── 念佛机 (USE_BUDDHA_MACHINE)
│   │   ├── 手电筒 (USE_FLASHLIGHT)
│   │   └── 对讲机 (USE_WALKIE_TALKIE)
│   └── 干预 (INTERVENE)
│       ├── 物理接触 (PHYSICAL_CONTACT)
│       ├── 呼喊 (SHOUT)
│       └── 投掷物品 (THROW)
│
├── 防御 (DEFEND)
│   ├── 躲藏 (HIDE)
│   │   ├── 进入房间 (ENTER_ROOM)
│   │   ├── 躲在物体后 (BEHIND_OBJECT)
│   │   └── 装死 (PLAY_DEAD)
│   ├── 逃跑 (FLEE)
│   │   ├── 跑向楼梯 (RUN_TO_STAIRS)
│   │   └── 使用电梯 (USE_ELEVATOR)
│   └── 对抗 (CONFRONT)
│       ├── 攻击 (ATTACK)
│       └── 威胁 (THREATEN)
│
└── 等待 (WAIT)
    ├── 观察等待 (WAIT_AND_WATCH)
    └── 静止不动 (STAY_STILL)
```

**目的：**
1. 顶层意图决定"玩家的大方向"（探索/交互/防御）
2. 中层意图决定"具体方式"（躲藏/逃跑/对抗）
3. 底层意图决定"细节实现"（躲在桌子下/装死）

---

## 核心原则二：模式匹配引擎 (Pattern Matching Engine)

**设计说明：** 使用**多层模式匹配**而非单一关键词匹配。

**实现方式：**

### Layer 1: 关键词匹配

```python
intent_keywords = {
    "HIDE": ["躲", "藏", "隐蔽", "装死", "趴下", "蹲下", "不动"],
    "FLEE": ["跑", "逃", "冲", "离开", "撤退"],
    "INVESTIGATE": ["检查", "调查", "看看", "搜索", "翻找"],
    "USE_BUDDHA_MACHINE": ["念佛机", "佛经", "打开念佛"],
    "PHYSICAL_CONTACT": ["抓", "拉", "推", "触碰", "接触", "摸"],
}
```

### Layer 2: 短语匹配

```python
intent_phrases = {
    "HIDE_BEHIND": [
        "躲在.*后面",
        "藏在.*下面",
        "钻进.*里面"
    ],
    "MOVE_TO": [
        "去.*",
        "走向.*",
        "前往.*"
    ],
    "USE_ON": [
        "用.*对着.*",
        "拿.*照.*"
    ]
}
```

### Layer 3: 语义理解

```python
# 使用 LLM 进行语义理解
ambiguous_inputs = [
    "我靠在墙边不动",  # 是 HIDE 还是 WAIT?
    "我站在原地观察他",  # 是 OBSERVE 还是 WAIT?
]

# LLM 判断标准：
# - 上下文（玩家是否在危险中）
# - 之前的行为序列
# - 环境状态（是否有威胁实体）
```

**目的：** 三层过滤确保准确性，同时保持灵活性。

---

## 核心原则三：上下文敏感映射 (Context-Sensitive Mapping)

**设计说明：** 同样的输入，在不同场景下应映射到不同的意图。

**示例问题：**
```
玩家输入: "我看着他"

场景A（场景1：交接班）
- 上下文：正在与老保安张叔对话
- 映射：INTERACT → TALK → LISTEN（倾听对话）

场景B（场景4：五楼危机）
- 上下文：失魂者正在走向围栏
- 映射：DEFEND → WAIT → OBSERVE（观察等待）

场景C（场景5：清洁工出现）
- 上下文：清洁工正在拖地
- 映射：EXPLORE → OBSERVE（危险观察，增加共鸣度）
```

**实现方式：**

```python
def map_intent(player_input, game_state):
    # 提取上下文
    current_scene = game_state["current_scene"]
    resonance = game_state["resonance"]
    nearby_entities = game_state["entities"]

    # 基础意图识别
    base_intent = keyword_match(player_input)

    # 上下文修正
    if base_intent == "OBSERVE":
        if resonance > 60 and nearby_entities["清洁工"]["level"] >= 2:
            return "OBSERVE_DANGER"  # 危险观察
        else:
            return "OBSERVE_SAFE"    # 安全观察

    return base_intent
```

**目的：** 让AI理解"看着老保安"和"看着清洁工"是完全不同的行为。

---

## 核心原则四：后果树绑定 (Consequence Tree Binding)

**设计说明：** 意图识别的最终目标是**触发后果树的正确分支**。

**实现方式：**

```python
# GDD 中定义的后果树
consequence_tree = {
    "场景4_失魂者": {
        "INTERVENE + PHYSICAL_CONTACT": "后果A：失衡",
        "INTERVENE + USE_BUDDHA_MACHINE": "后果B：存活",
        "INTERVENE + SHOUT": "后果B：存活（如果知道名字）",
        "OBSERVE": "后果C：观察（失魂者坠落）"
    },
    "场景5_清洁工": {
        "HIDE": "主线分支A：标记",
        "FLEE": "主线分支B：追猎",
        "INTERVENE": "主线分支B：追猎（立即触发）",
        "USE_BUDDHA_MACHINE": "特殊分支：激怒"
    }
}

# 意图 → 后果的映射
def get_consequence(scene, intent, game_state):
    key = f"{intent.top_level} + {intent.sub_level}"
    return consequence_tree[scene].get(key, "默认后果")
```

**目的：** 确保玩家的每个行为都能精准触发《GDD》中设计的剧情分支。

---

## 核心原则五：模糊输入的优雅降级 (Graceful Degradation)

**设计说明：** 当无法准确识别意图时，不应"报错"，而应**智能猜测 + 确认**。

**实现方式：**

### 情况A：完全无法理解

```
玩家输入: "我施展魔法"

AI响应:
[系统: 意图识别失败]

你试图...施展魔法？
但你只是一个普通的保安，没有超自然能力。

[智能引导]
你的手里有：手电筒、对讲机、念佛机。
你想用哪个？或者你想做点别的？
（请重新描述你的行动）
```

### 情况B：意图模糊（多义）

```
玩家输入: "我靠近他"

AI响应:
[系统: 检测到多义输入]

你想靠近那个失魂者。但你的目的是：
A) 拉住他，防止他跳下去 [物理接触 - 危险]
B) 靠近观察，但不触碰他 [观察 - 较安全]
C) 靠近后大声呼喊唤醒他 [干预 - 需要名字]

请选择 A/B/C 或重新描述。
```

### 情况C：意图合理但目标不明

```
玩家输入: "我躲起来"

AI响应:
[系统: 意图明确，目标模糊]

你想找地方躲起来。你看到：
- 左侧的监控室（门虚掩着）
- 右侧的楼梯间（门紧闭）
- 前方的柱子（可以躲在后面）

你要躲在哪里？
```

**目的：** 将"无法理解"转化为"引导对话"，保持游戏流畅性。

---

## 核心原则六：行为序列记忆 (Action Sequence Memory)

**设计说明：** 玩家的当前意图应该考虑**之前的行为序列**。

**示例问题：**
```
行为序列A：
1. "我检查监控" -> INVESTIGATE
2. "我看到五楼有黑影" -> OBSERVE
3. "我去五楼" -> MOVE
4. "我靠近黑影" -> INVESTIGATE（合理延续）

行为序列B：
1. "我听到脚步声" -> OBSERVE
2. "我很害怕" -> [情绪状态]
3. "我靠近" -> ??? （矛盾！害怕还靠近？）
```

**实现方式：**

```python
action_history = [
    {"intent": "OBSERVE", "target": "五楼黑影"},
    {"intent": "MOVE", "target": "五楼"},
    {"intent": "INVESTIGATE", "target": "黑影"}
]

def validate_intent(new_intent, history, game_state):
    # 检查意图连贯性
    if history[-1]["intent"] == "OBSERVE" and \
       history[-1]["emotion"] == "FEAR" and \
       new_intent == "INVESTIGATE":
        return {
            "valid": True,
            "note": "玩家克服恐惧进行调查（勇敢行为，-5共鸣度）"
        }
```

**目的：** 让AI理解玩家的"意图轨迹"，而不仅是单次输入。

---

## 数据结构定义

### 输入结构
```json
{
  "player_input": "我躲在桌子下面",
  "game_state": {
    "current_scene": "场景5",
    "location": "五楼中庭",
    "resonance": 75,
    "nearby_objects": ["监控室门", "柱子", "长椅"],
    "nearby_entities": {"清洁工": {"level": 2, "distance": "10米"}}
  },
  "action_history": [
    {"intent": "OBSERVE", "target": "清洁工"}
  ]
}
```

### 输出结构
```json
{
  "top_level_intent": "DEFEND",
  "sub_intent": "HIDE",
  "detailed_intent": "HIDE_BEHIND_OBJECT",
  "target": "长椅",
  "confidence": 0.95,
  "reasoning": "玩家明确提到'躲'和'桌子下'，环境中有长椅可以躲藏",
  "consequence_trigger": "主线分支A：标记",
  "state_impact": {
    "resonance": "保持不变（成功躲藏）",
    "flags": {"玩家_已躲藏": true}
  },
  "alternatives": [
    "如果玩家说的是'柱子'而非'桌子'，则躲在柱子后"
  ]
}
```

---

## 意图优先级规则

当存在多个可能的意图时，按以下优先级排序：

1. **生存类意图** (DEFEND) > 其他
   - 危险情况下，"我看看"应解释为"观察威胁"而非"随便看看"

2. **明确道具使用** (USE_ITEM) > 模糊交互
   - "我打开念佛机"优先于"我用东西"

3. **物理接触** (PHYSICAL_CONTACT) > 语言交互
   - "我拉他"优先于"我跟他说话"

4. **主动行为** (EXPLORE/INTERACT) > 被动行为 (WAIT)
   - "我看着他"在无威胁时 = EXPLORE，有威胁时 = WAIT

---

## 特殊意图处理

### 情绪表达类输入

```
玩家输入: "我好害怕"
映射: EMOTIONAL_STATE (不是行为意图)

AI处理:
1. 记录情绪状态 -> game_state["emotion"] = "FEAR"
2. 共鸣度 +5
3. 引导行为选择: "你感到恐惧，你想怎么办？躲起来？还是逃跑？"
```

### 元游戏类输入

```
玩家输入: "存档" / "查看状态" / "我的道具有什么"
映射: META_GAME

AI处理:
- 不推进游戏时间
- 显示 UI 信息
- 返回玩家继续游戏
```

### 问询类输入

```
玩家输入: "这是哪里？" / "现在几点？"
映射: QUERY

AI处理:
- 回答问题（基于 game_state）
- 不推进时间
- 保持沉浸感（用角色视角回答）
```

---

## 与其他模块的关系

```
┌─────────────────┐
│ 玩家自由输入     │ "我躲在桌子下"
└────────┬────────┘
         ↓
┌─────────────────┐
│ Intent Mapping   │ 识别: DEFEND → HIDE → BEHIND_OBJECT
└────────┬────────┘
         ↓
┌─────────────────┐
│ State Management │ 检查环境中是否有"桌子/长椅"可躲
└────────┬────────┘
         ↓
┌─────────────────┐
│ GDD Check        │ 检查场景5的后果树: HIDE → "标记分支"
└────────┬────────┘
         ↓
┌─────────────────┐
│ Runtime Response │ 生成"你蹲在长椅后..."的响应
└─────────────────┘
```

---

## 设计哲学

**核心理念：** Intent Mapping 是"自然语言"与"游戏逻辑"的翻译器。它让玩家用人类的方式说话，让游戏用机器的方式理解。

**质量标尺：**
- 准确性：95%以上的常见输入能正确映射
- 鲁棒性：即使识别失败也能优雅降级
- 可扩展性：新增意图类别不影响现有逻辑
- 透明性：玩家知道AI理解了什么（通过响应确认）

