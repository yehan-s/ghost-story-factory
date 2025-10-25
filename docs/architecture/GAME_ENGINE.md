# 交互式游戏引擎 - 使用指南

## 📖 概述

**阶段4的交互运行层**（choice-points, runtime-response, intent-mapping, state-management）是用于**游戏运行时**的，不是故事生成时用的。

### 区别说明

| 组件 | 用途 | 使用时机 |
|------|------|---------|
| **阶段1-3** | 故事生成 | 开发时（生成故事、世界观、GDD） |
| **阶段4** | 游戏运行 | 运行时（玩家实际玩游戏时） |

---

## 🎮 运行模式（新增）

项目支持两种游玩模式：

- 动态模式（LLM 实时生成）：`python3 play_game_full.py`
- 预生成模式（零等待，读取数据库/文件）：`./start_pregenerated_game.sh` 或 `python3 play_game_pregenerated.py`

> **📘 详细文档**：
> - 预生成系统设计：[PREGENERATION_DESIGN.md](../PREGENERATION_DESIGN.md)
> - **新架构流程图谱（v3.0）**：[NEW_PIPELINE.md](NEW_PIPELINE.md) ⭐

---

## 🎮 完整工作流

### 第一步：生成故事素材（开发阶段）

```bash
# 使用 generate_full_story.py 生成完整的故事素材
python generate_full_story.py --city 武汉
```

**输出文件：**
```
deliverables/程序-武汉/
├── 武汉_lore_v1.md      ← 传说素材
├── 武汉_lore_v2.md      ← 游戏规则 ⭐ 游戏引擎需要
├── 武汉_protagonist.md  ← 角色设定
├── 武汉_gdd.md          ← 剧情流程 ⭐ 游戏引擎需要
└── 武汉_story.md        ← 完整故事（参考）
```

---

### 第二步：运行游戏（运行阶段）

```bash
# 启动交互式游戏引擎
python game_engine.py \
    --city 武汉 \
    --gdd deliverables/程序-武汉/武汉_gdd.md \
    --lore deliverables/程序-武汉/武汉_lore_v2.md
```

**游戏流程：**
```
1. 玩家看到剧情情境
   ↓
2. AI生成2-4个选择选项（choice-points）
   ↓
3. 玩家选择A/B/C/D
   ↓
4. AI生成响应（runtime-response）
   ↓
5. AI更新状态（state-management）
   ↓
6. 检查游戏规则（lore v2）
   ↓
7. 进入下一回合
```

---

## 🎯 阶段4模块详解

### 1. Choice Points（选择点生成器）

**作用：** 在关键剧情节点生成2-4个选项

**输入：**
- 当前剧情情境
- 游戏状态（位置、时间、共鸣度、道具）
- GDD场景信息
- 世界规则

**输出：**
```json
[
  {
    "id": "A",
    "text": "躲进监控室，保持安静",
    "tags": ["保守", "遵守手册"],
    "consequences": {
      "location": "监控室",
      "resonance": 0,
      "flags": {"玩家_已躲藏": true}
    }
  },
  {
    "id": "B",
    "text": "冲向楼梯逃跑",
    "tags": ["激进", "违反手册"],
    "consequences": {
      "location": "楼梯",
      "resonance": 15,
      "flags": {"玩家_已逃跑": true}
    }
  }
]
```

**templates：**
- `templates/choice-points.design.md` - 设计原则
- `templates/choice-points.example.md` - 实战示例
- `templates/choice-points.prompt.md` - AI提示词

---

### 2. Runtime Response（响应生成器）

**作用：** 基于玩家选择生成沉浸式响应

**输入：**
- 玩家选择（A/B/C/D）
- 当前状态
- 世界规则

**输出：**
```markdown
你选择躲进监控室...

你猫着腰，悄无声息地退向监控室。
你挤进去，轻轻关上门，从里面反锁。

'咔哒'——

外面的拖把声没有停。
'啪嗒...啪嗒...啪嗒...'

你透过门缝往外看——
清洁工站在监控室门外。
背对着门。

你的后颈开始发凉...
```

**templates：**
- `templates/runtime-response.design.md`
- `templates/runtime-response.example.md`
- `templates/runtime-response.prompt.md`

---

### 3. State Management（状态管理器）

**作用：** 管理游戏状态，确保规则一致性

**管理的状态：**
```json
{
  "player": {
    "location": "监控室",
    "resonance": 45,
    "inventory": ["手电筒", "念佛机"],
    "health": 100
  },
  "world": {
    "time": "04:44 AM",
    "entities": {
      "清洁工": {
        "level": 2,
        "location": "五楼中庭",
        "state": "ACTIVE"
      }
    }
  },
  "narrative": {
    "current_scene": "场景5",
    "branch": "主线分支A：标记",
    "flags": {
      "场景4_失魂者已救": true,
      "玩家_已被标记": true
    }
  }
}
```

**templates：**
- `templates/state-management.design.md`
- `templates/state-management.example.md`
- `templates/state-management.prompt.md`

---

### 4. Intent Mapping（意图映射器）

**作用：** 在选项式游戏中，验证选项映射

**主要职责：**
1. 确认玩家选择的选项ID对应的意图
2. 检查前置条件（是否有道具、是否满足状态）
3. 绑定后果树（确认选项对应的GDD分支）

**templates：**
- `templates/intent-mapping.design.md`
- `templates/intent-mapping.example.md`
- `templates/intent-mapping.prompt.md`

---

## 🔧 游戏引擎架构

```
game_engine.py
├── GameState（游戏状态类）
├── Choice（选择选项类）
└── GameEngine（游戏引擎类）
    ├── generate_choices()      ← 使用 choice-points.prompt.md
    ├── generate_response()     ← 使用 runtime-response.prompt.md
    ├── update_state()          ← 使用 state-management.prompt.md
    └── run()                   ← 主游戏循环
```

---

## 🎮 游戏循环示例

### 回合1

**情境：**
```
你正在荔湾广场五楼巡逻，时间是03:30 AM。
走廊尽头传来...拍皮球的声音。
'啪嗒...啪嗒...啪嗒...'
```

**AI生成选项：**
```
[A] 走过去检查声音来源
[B] 返回中控室查看监控
[C] 先巡逻其他楼层
```

**玩家选择：** A

**AI响应：**
```
你握紧手电筒，慢慢走向声音传来的方向...
（200-500字的沉浸式描述）
```

**状态更新：**
```
位置: 五楼深层走廊 → 五楼柱子后
共鸣度: 35% → 50%
旗标: 五楼_皮球_已接触 = True
```

---

## 📊 数据流

```
┌─────────────────────────────────────────────────────────┐
│            开发阶段（阶段1-3）                              │
│                                                           │
│  templates/lore-v1.prompt.md                                   │
│       ↓                                                   │
│  生成: 武汉_lore_v1.md (传说素材)                          │
│       ↓                                                   │
│  templates/lore-v2.prompt.md                                   │
│       ↓                                                   │
│  生成: 武汉_lore_v2.md (游戏规则) ✅                       │
│       ↓                                                   │
│  templates/GDD.prompt.md                                       │
│       ↓                                                   │
│  生成: 武汉_gdd.md (剧情流程) ✅                           │
│       ↓                                                   │
│  templates/main-thread.prompt.md                               │
│       ↓                                                   │
│  生成: 武汉_story.md (完整故事)                            │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│            运行阶段（阶段4）                                │
│                                                           │
│  game_engine.py 启动                                      │
│       ↓                                                   │
│  加载: 武汉_gdd.md + 武汉_lore_v2.md                       │
│       ↓                                                   │
│  游戏循环:                                                │
│    1. 生成情境                                            │
│    2. templates/choice-points.prompt.md → 生成选项             │
│    3. 玩家选择                                            │
│    4. templates/runtime-response.prompt.md → 生成响应          │
│    5. templates/state-management.prompt.md → 更新状态          │
│    6. 检查 lore_v2 规则 → 触发事件                        │
│       ↓                                                   │
│  重复直到结局                                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 完整演示流程

```bash
# 第一步：生成故事素材
python generate_full_story.py --city 武汉

# 第二步：运行游戏
python game_engine.py \
    --city 武汉 \
    --gdd deliverables/程序-武汉/武汉_gdd.md \
    --lore deliverables/程序-武汉/武汉_lore_v2.md
```

---

## 💡 扩展建议

### 1. 真实玩家输入

当前是Demo模式，自动选择第一个选项。改为：

```python
# 在 game_engine.py 的 run() 方法中
player_input = input("\n请输入你的选择 (A/B/C): ").strip().upper()
selected = next((c for c in choices if c.id == player_input), None)
```

### 2. 保存游戏进度

```python
def save_game(self, filename: str):
    """保存游戏状态"""
    with open(filename, 'w') as f:
        json.dump(self.state.to_dict(), f, ensure_ascii=False, indent=2)

def load_game(self, filename: str):
    """加载游戏状态"""
    with open(filename, 'r') as f:
        data = json.load(f)
        self.state = GameState(**data)
```

### 3. Web界面

使用Flask或FastAPI创建Web界面：

```python
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
engine = GameEngine(city="武汉", ...)

@app.route('/game')
def game():
    return render_template('game.html')

@app.route('/api/choices', methods=['GET'])
def get_choices():
    narrative = engine._generate_narrative_context()
    choices = engine.generate_choices(narrative)
    return jsonify({
        'narrative': narrative,
        'choices': [c.__dict__ for c in choices]
    })

@app.route('/api/choose', methods=['POST'])
def choose():
    choice_id = request.json['choice_id']
    # ...处理选择
    return jsonify({'response': response})
```

### 4. 多结局系统

基于玩家的累积选择（保守/激进/策略）决定不同结局：

```python
def calculate_ending(self):
    """根据玩家行为计算结局"""
    if self.state.resonance >= 100:
        return "坏结局：被场域吞噬"
    elif self.state.flags.get("遵守手册") and self.state.resonance < 50:
        return "好结局A：安全逃脱"
    elif self.state.flags.get("揭开真相"):
        return "好结局B：真相大白"
    else:
        return "普通结局：惊魂一夜"
```

---

## 📝 总结

**阶段1-3（generate_full_story.py）**
- 用途：生成故事素材（开发时）
- 输出：Lore、GDD、Story等Markdown文件
- templates：lore-v1, protagonist, lore-v2, GDD, main-thread

**阶段4（game_engine.py）**
- 用途：运行交互式游戏（运行时）
- 输入：生成的GDD和Lore v2
- templates：choice-points, runtime-response, state-management, intent-mapping

**两者配合：**
```
generate_full_story.py (开发) → 素材文件 → game_engine.py (运行)
```

---

**祝您玩得愉快！** 🎮👻

