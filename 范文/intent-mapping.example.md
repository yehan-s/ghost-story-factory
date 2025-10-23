# Intent Mapping - 实战范例 (Examples)

**文档用途：** 提供真实的意图识别示例，展示如何将各种自然语言输入映射到标准意图类别，以及如何处理模糊、矛盾、无效的输入。

---

## 类别 1：探索类意图 (EXPLORE)

### 示例 1.1：移动意图 - 明确目标

**玩家输入：** `"我去五楼"`

**识别结果：**
```json
{
  "top_level_intent": "EXPLORE",
  "sub_intent": "MOVE",
  "detailed_intent": "CHANGE_FLOOR",
  "target": "五楼",
  "confidence": 0.98,
  "reasoning": "明确的移动动词'去' + 明确的目标'五楼'",
  "time_cost": "+5分钟（乘电梯或爬楼梯）",
  "state_impact": {
    "location": "五楼",
    "resonance": "+5（五楼是高危区域）"
  }
}
```

---

### 示例 1.2：移动意图 - 模糊表达

**玩家输入：** `"我想看看楼上"`

**识别结果：**
```json
{
  "top_level_intent": "EXPLORE",
  "sub_intent": "MOVE",
  "detailed_intent": "CHANGE_FLOOR",
  "target": "当前楼层+1",
  "confidence": 0.75,
  "reasoning": "'楼上'是相对位置，需要基于game_state['location']计算",
  "need_confirmation": true
}
```

**AI响应：**
```
[系统: 意图识别成功，但目标模糊]

你想去楼上看看。
你现在在四楼，楼上是五楼（中庭）。

[软确认]
你要上五楼吗？那里...土腥味会更浓。
```

---

### 示例 1.3：调查意图 - 物体检查

**玩家输入：** `"我检查监控屏幕"`

**识别结果：**
```json
{
  "top_level_intent": "EXPLORE",
  "sub_intent": "INVESTIGATE",
  "detailed_intent": "EXAMINE_OBJECT",
  "target": "监控屏幕",
  "confidence": 0.95,
  "reasoning": "动词'检查' + 可交互物体'监控屏幕'",
  "time_cost": "+3分钟",
  "state_impact": {
    "flags": {"监控_已检查": true},
    "unlock": ["五楼_发现异常"]
  }
}
```

---

### 示例 1.4：调查意图 - 多义输入

**玩家输入：** `"我看看那个东西"`

**识别结果：**
```json
{
  "top_level_intent": "EXPLORE",
  "sub_intent": "INVESTIGATE",
  "detailed_intent": "EXAMINE_OBJECT",
  "target": "UNKNOWN",
  "confidence": 0.40,
  "reasoning": "'那个东西'指代不明，需要基于上下文推断",
  "need_clarification": true
}
```

**AI处理：**
```python
# 检查上文提到的物体
if last_mentioned_object:
    target = last_mentioned_object  # 如"皮球"
else:
    # 检查当前环境的显著物体
    target = get_salient_object(location)  # 如"清洁工"
```

**AI响应：**
```
[系统: 指代消解]

你走近那个皮球（你之前看到的那个红白色皮球）。
它还静静地躺在地上，散发着土腥味...
```

---

## 类别 2：交互类意图 (INTERACT)

### 示例 2.1：对话意图

**玩家输入：** `"我问张叔：五楼到底有什么？"`

**识别结果：**
```json
{
  "top_level_intent": "INTERACT",
  "sub_intent": "TALK",
  "detailed_intent": "ASK",
  "target": "张叔（老保安）",
  "content": "五楼到底有什么？",
  "confidence": 0.98,
  "reasoning": "明确的对话动词'问' + NPC名称 + 问题内容",
  "time_cost": "+2分钟",
  "state_impact": {
    "resonance": "-5（与正常人类对话降低恐惧）"
  }
}
```

---

### 示例 2.2：道具使用 - 明确指定

**玩家输入：** `"我打开念佛机"`

**识别结果：**
```json
{
  "top_level_intent": "INTERACT",
  "sub_intent": "USE_ITEM",
  "detailed_intent": "USE_BUDDHA_MACHINE",
  "target": "念佛机",
  "confidence": 1.0,
  "reasoning": "明确的道具名称 + 使用动词",
  "precondition": {
    "check": "inventory.includes('念佛机')",
    "battery": ">0%"
  },
  "state_impact": {
    "resonance": "-15",
    "flags": {"念佛机_已使用": true},
    "warning": "可能激怒等级3实体"
  }
}
```

---

### 示例 2.3：道具使用 - 隐含指代

**玩家输入：** `"我用手电筒照他"`

**识别结果：**
```json
{
  "top_level_intent": "INTERACT",
  "sub_intent": "USE_ITEM",
  "detailed_intent": "USE_FLASHLIGHT_ON_TARGET",
  "target": "手电筒",
  "secondary_target": "他（需解析指代）",
  "confidence": 0.85,
  "reasoning": "明确道具 + 动作 + 代词指代",
  "need_resolve": "解析'他'=失魂者/清洁工/张叔？"
}
```

**AI处理：**
```python
# 检查当前场景中的"他"
if nearby_entities["失魂者"]["visible"]:
    secondary_target = "失魂者"
elif nearby_entities["清洁工"]["visible"]:
    secondary_target = "清洁工"
else:
    secondary_target = "张叔"  # 默认最后对话的NPC
```

---

### 示例 2.4：干预意图 - 危险行为

**玩家输入：** `"我冲过去拉住他"`

**识别结果：**
```json
{
  "top_level_intent": "INTERACT",
  "sub_intent": "INTERVENE",
  "detailed_intent": "PHYSICAL_CONTACT",
  "target": "失魂者（基于场景4上下文）",
  "confidence": 0.92,
  "reasoning": "动作'拉'属于物理接触",
  "warning": {
    "level": "HIGH_DANGER",
    "message": "物理接触失魂者将触发'失衡'后果",
    "consequence": "后果A：失衡"
  },
  "state_impact": {
    "resonance": "+25 → 100%（失衡状态）",
    "branch": "后果A：失衡"
  }
}
```

---

## 类别 3：防御类意图 (DEFEND)

### 示例 3.1：躲藏意图 - 基础形式

**玩家输入：** `"我躲起来"`

**识别结果：**
```json
{
  "top_level_intent": "DEFEND",
  "sub_intent": "HIDE",
  "detailed_intent": "HIDE_GENERAL",
  "target": "UNSPECIFIED",
  "confidence": 0.70,
  "reasoning": "明确的躲藏意图，但未指定位置",
  "need_selection": true
}
```

**AI响应：**
```
[系统: 意图明确，目标待定]

你想找地方躲起来。你环顾四周，看到：
- 监控室（门虚掩着，可以进去反锁）
- 柱子（可以躲在后面，但遮挡不够）
- 长椅（可以躲在下面，但空间狭小）

你要躲在哪里？（输入位置名称或重新描述）
```

---

### 示例 3.2：躲藏意图 - 详细描述

**玩家输入：** `"我蹲在长椅下面，屏住呼吸不动"`

**识别结果：**
```json
{
  "top_level_intent": "DEFEND",
  "sub_intent": "HIDE",
  "detailed_intent": "HIDE_BEHIND_OBJECT",
  "target": "长椅",
  "modifiers": ["屏住呼吸", "不动"],
  "confidence": 0.98,
  "reasoning": "详细的躲藏动作描述，显示玩家理解隐蔽机制",
  "quality": "HIGH（修饰词增加成功率）",
  "state_impact": {
    "flags": {"玩家_已躲藏": true, "玩家_高质量隐蔽": true},
    "resonance": "保持不变（成功躲藏）",
    "consequence": "主线分支A：标记"
  }
}
```

---

### 示例 3.3：逃跑意图 - 紧急情况

**玩家输入：** `"我跑！"`

**识别结果：**
```json
{
  "top_level_intent": "DEFEND",
  "sub_intent": "FLEE",
  "detailed_intent": "FLEE_GENERAL",
  "target": "AWAY_FROM_THREAT",
  "confidence": 0.75,
  "reasoning": "紧急情况下的简短输入，方向未明",
  "need_direction": true
}
```

**AI处理：**
```python
# 自动推断逃跑方向（远离威胁）
threat_location = entities["清洁工"]["location"]
player_location = game_state["location"]

# 找最近的安全出口
safe_exits = ["楼梯", "电梯", "监控室"]
best_exit = find_farthest_from_threat(safe_exits, threat_location)
```

**AI响应：**
```
[系统: 自动路径规划]

你转身就跑！
本能驱使你冲向了楼梯口——那是离清洁工最远的出口。
你的脚步声在走廊里回荡...'嗒嗒嗒嗒'！

[音效: 身后传来加速的拖把声]
'啪嗒啪嗒啪嗒'——他也加速了！

[触发: 主线分支B：追猎]
```

---

### 示例 3.4：对抗意图 - 无效行为

**玩家输入：** `"我攻击清洁工"`

**识别结果：**
```json
{
  "top_level_intent": "DEFEND",
  "sub_intent": "CONFRONT",
  "detailed_intent": "ATTACK",
  "target": "清洁工",
  "confidence": 0.95,
  "validity": false,
  "reasoning": "玩家意图明确，但违反世界规则",
  "error": {
    "type": "INVALID_ACTION",
    "reason": "普通人无法伤害超自然实体"
  }
}
```

**AI响应：**
```
[系统: 无效行为]

你握紧巡更棒，想要攻击清洁工！

但你的手臂僵住了。
不是因为恐惧——而是因为你的理智在尖叫：
"他不是人。武器对他没用。"

[强制行为修正]
你必须选择其他方式：
- 使用念佛机（道具对抗）
- 躲起来
- 逃跑

（普通攻击对超自然实体无效）
```

---

## 类别 4：等待/观察类意图 (WAIT/OBSERVE)

### 示例 4.1：主动观察

**玩家输入：** `"我盯着那个清洁工看"`

**识别结果：**
```json
{
  "top_level_intent": "EXPLORE",
  "sub_intent": "OBSERVE",
  "detailed_intent": "OBSERVE_DANGER",
  "target": "清洁工",
  "confidence": 0.90,
  "reasoning": "'盯着'表示持续观察，目标是威胁实体",
  "risk": "HIGH",
  "state_impact": {
    "resonance": "+10（长时间观察会增加共鸣）",
    "time": "+1分钟",
    "trigger": "可能被实体注意到"
  }
}
```

---

### 示例 4.2：被动等待

**玩家输入：** `"我什么都不做"`

**识别结果：**
```json
{
  "top_level_intent": "WAIT",
  "sub_intent": "STAY_STILL",
  "detailed_intent": "PASSIVE_WAIT",
  "confidence": 0.85,
  "reasoning": "明确的消极行为",
  "time_cost": "+5分钟（自动跳过）",
  "state_impact": {
    "resonance": "+5（环境压力累积）",
    "warning": "时间在流逝，威胁可能加剧"
  }
}
```

**AI响应：**
```
[系统: 时间跳过]

你靠在墙边，什么都不做。

时间一分一秒过去。
你的手表显示：03:50 AM → 03:55 AM。

[环境变化]
土腥味越来越浓。
远处传来...拖把拖地的声音。
'啪嗒...啪嗒...啪嗒...'

[系统: 共鸣度 60% → 65%]

你还要继续等吗？还是该做点什么？
```

---

## 特殊情况处理

### 示例 S.1：情绪表达（非行为意图）

**玩家输入：** `"我好怕"`

**识别结果：**
```json
{
  "top_level_intent": "EMOTIONAL_STATE",
  "emotion": "FEAR",
  "confidence": 1.0,
  "reasoning": "纯情绪表达，无具体行为",
  "state_impact": {
    "emotion": "FEAR",
    "resonance": "+5"
  },
  "need_action_prompt": true
}
```

**AI响应：**
```
[系统: 情绪记录]

你感到恐惧。
手心冒着冷汗，心脏狂跳。

[引导行为选择]
但你必须做点什么：
- 逃跑？
- 躲起来？
- 使用念佛机稳定情绪？

你要怎么做？
```

---

### 示例 S.2：元游戏指令

**玩家输入：** `"我有什么道具？"`

**识别结果：**
```json
{
  "top_level_intent": "META_GAME",
  "sub_intent": "QUERY_INVENTORY",
  "confidence": 1.0,
  "no_time_cost": true,
  "no_state_change": true
}
```

**AI响应：**
```
[系统: 物品栏]

你的腰包里有：
- 手电筒（电量：75%）
- 对讲机（信号：无）
- 念佛机（电量：50%，剩余使用次数：2）
- 巡更棒

[返回游戏]
你现在在五楼中庭，土腥味很浓。
你要做什么？
```

---

### 示例 S.3：多意图组合

**玩家输入：** `"我躲进监控室，然后检查监控看他在哪"`

**识别结果：**
```json
{
  "intents": [
    {
      "type": "DEFEND → HIDE",
      "target": "监控室",
      "sequence": 1
    },
    {
      "type": "EXPLORE → INVESTIGATE",
      "target": "监控屏幕",
      "sequence": 2
    }
  ],
  "is_compound": true,
  "confidence": 0.92,
  "reasoning": "两个连续行为，用'然后'连接",
  "execution": "顺序执行"
}
```

**AI响应：**
```
[执行: 意图1]
你猫着腰冲进监控室，反锁了门。
[系统: 共鸣度保持，location="监控室"]

[执行: 意图2]
你立刻凑近监控屏幕，切换到五楼的画面——
清洁工还在中庭，背对着监控室，继续拖地。
'啪嗒...啪嗒...啪嗒...'

[系统: 你暂时安全了]
```

---

### 示例 S.4：矛盾意图（需要确认）

**玩家输入：** `"我躲起来但又想看清他"`

**识别结果：**
```json
{
  "top_level_intent": "DEFEND",
  "sub_intent": "HIDE",
  "contradiction": {
    "detected": true,
    "conflict": "躲藏（减少被发现）vs 观察（增加暴露风险）"
  },
  "confidence": 0.50,
  "need_confirmation": true
}
```

**AI响应：**
```
[系统: 检测到矛盾意图]

你想躲起来，但又想看清楚清洁工...

这两个行为有冲突：
A) 彻底躲藏（躲在长椅下，不看他）- 安全但失去视野
B) 躲在柱子后偷看（半掩护）- 能看到他但有被发现风险
C) 躲进监控室看监控（最佳方案）- 既安全又有视野

你选择哪个？（A/B/C）
```

---

## 上下文敏感映射示例

### 示例 C.1：同一输入，不同场景

**玩家输入：** `"我看着他"`

**场景1（交接班，张叔在场）：**
```json
{
  "intent": "INTERACT → TALK → LISTEN",
  "target": "张叔",
  "reasoning": "上下文：正在对话，'看着'=倾听",
  "resonance_change": 0
}
```

**场景4（五楼危机，失魂者）：**
```json
{
  "intent": "EXPLORE → OBSERVE_DANGER",
  "target": "失魂者",
  "reasoning": "上下文：危险实体，'看着'=观察威胁",
  "resonance_change": +10
}
```

**场景5（清洁工出现）：**
```json
{
  "intent": "DEFEND → WAIT → OBSERVE",
  "target": "清洁工",
  "reasoning": "上下文：等级2实体，'看着'=等待观察（可能被标记）",
  "resonance_change": +15,
  "warning": "长时间观察可能触发'标记仪式'"
}
```

---

## 错误识别对比

### ❌ 低质量识别

**玩家输入：** `"我躲在桌子下面"`

**低质量AI：**
```json
{
  "intent": "UNKNOWN",
  "error": "无法理解'桌子下面'"
}
```

---

### ✅ 高质量识别

**玩家输入：** `"我躲在桌子下面"`

**高质量AI：**
```json
{
  "intent": "DEFEND → HIDE → BEHIND_OBJECT",
  "target": "长椅（环境中最接近'桌子'的物体）",
  "reasoning": "'桌子'在当前环境不存在，自动映射到'长椅'",
  "auto_correction": true,
  "response_confirmation": "你蹲在长椅下面（这里没有桌子，但长椅可以藏身）..."
}
```

---

**设计理念：** 好的意图识别系统应该"宽进严出"——宽容地接受各种自然语言输入，严格地输出标准化的游戏意图。

