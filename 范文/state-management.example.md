# State Management - 实战范例 (Examples)

**文档用途：** 提供真实的状态管理示例，展示如何初始化、查询、更新、验证游戏状态，以及如何处理复杂的级联更新和回滚场景。

---

## 示例 1：初始状态（游戏开始）

### 场景1开始时的完整状态

```json
{
  "player": {
    "location": "中控室",
    "resonance": 10,
    "health": 100,
    "emotion": "CALM",
    "inventory": {
      "手电筒": {"battery": 100, "on": false},
      "巡更棒": {"durability": 100},
      "对讲机": {"battery": 80, "signal": false},
      "钥匙串": {"keys": ["中控室", "监控室", "楼梯门"]},
      "念佛机": {"battery": 100, "uses_left": 5}
    },
    "status_effects": []
  },
  "world": {
    "time": "00:00 AM",
    "entities": {
      "清洁工": {
        "level": 0,
        "location": "B3",
        "state": "DORMANT",
        "visible": false
      },
      "失魂者": {
        "level": 0,
        "location": "未触发",
        "state": "DORMANT"
      },
      "白衣女子": {
        "level": 1,
        "location": "B3数据中心",
        "state": "WAITING"
      }
    },
    "locations": {
      "中控室": {
        "resonance_modifier": 0,
        "light_level": "明亮",
        "smell": "正常（消毒水+盒饭）",
        "exits": ["一楼大厅", "楼梯"],
        "objects": ["监控墙", "折叠椅", "巡更记录本"]
      }
    },
    "environmental_events": [
      {"type": "荧光灯电流声", "active": true, "sound": "嗡——"}
    ]
  },
  "narrative": {
    "current_scene": "场景1",
    "branch": "主线",
    "checkpoint": "游戏开始",
    "flags": {
      "交接_已完成": true,
      "监控_已检查": false,
      "五楼_发现异常": false
    },
    "choices_made": [],
    "善意标记": 0
  },
  "meta": {
    "session_id": "a1b2c3d4",
    "game_version": "1.0.0",
    "start_time": "2025-10-23T20:00:00Z",
    "play_time_minutes": 0
  }
}
```

---

## 示例 2：状态查询

### 查询 2.1：玩家是否处于危险？

```python
def is_player_in_danger(state):
    """综合判断玩家是否危险"""
    # 检查1：共鸣度
    if state["player"]["resonance"] > 70:
        return (True, "共鸣度过高")

    # 检查2：附近是否有高等级实体
    player_loc = state["player"]["location"]
    for entity_name, entity in state["world"]["entities"].items():
        if entity["location"] == player_loc and entity["level"] >= 2:
            return (True, f"{entity_name}在附近")

    # 检查3：是否有负面状态
    for effect in state["player"]["status_effects"]:
        if effect["name"] in ["被标记", "失衡"]:
            return (True, f"状态：{effect['name']}")

    return (False, "安全")

# 使用示例
is_danger, reason = is_player_in_danger(current_state)
if is_danger:
    ai_response += f"[警告: {reason}]"
```

### 查询 2.2：玩家能否使用道具？

```python
def can_use_item(state, item_name):
    """检查道具是否可用"""
    inventory = state["player"]["inventory"]

    # 检查是否拥有
    if item_name not in inventory:
        return (False, f"你没有{item_name}")

    item = inventory[item_name]

    # 检查电量/耐久
    if "battery" in item and item["battery"] <= 0:
        return (False, f"{item_name}没电了")

    if "durability" in item and item["durability"] <= 0:
        return (False, f"{item_name}已损坏")

    # 检查使用次数
    if "uses_left" in item and item["uses_left"] <= 0:
        return (False, f"{item_name}已用完")

    return (True, "")

# 使用示例
can_use, reason = can_use_item(current_state, "念佛机")
if not can_use:
    return {
        "response": f"[系统: 道具不可用]\n{reason}",
        "state_updates": {}
    }
```

### 查询 2.3：获取当前可用出口

```python
def get_available_exits(state):
    """获取可用的出口"""
    location = state["player"]["location"]
    all_exits = state["world"]["locations"][location]["exits"]

    # 过滤封锁的出口
    available = []
    for exit_name in all_exits:
        # 检查是否需要钥匙
        if exit_name == "B3":
            # B3只能通过北角货梯
            if location != "北角货梯":
                continue

        # 检查是否被实体封锁
        blocked = False
        for entity in state["world"]["entities"].values():
            if entity["location"] == exit_name and entity["level"] >= 2:
                blocked = True
                break

        if not blocked:
            available.append(exit_name)

    return available

# 使用示例
exits = get_available_exits(current_state)
if not exits:
    response = "你被困住了，所有出口都被封锁！"
else:
    response = f"你可以去：{', '.join(exits)}"
```

---

## 示例 3：状态更新

### 更新 3.1：玩家移动

```python
def update_player_move(state, new_location):
    """玩家移动更新"""
    old_location = state["player"]["location"]

    # 更新位置
    state["player"]["location"] = new_location

    # 更新时间
    if is_different_floor(old_location, new_location):
        state["world"]["time"] = advance_time(state["world"]["time"], 5)
    else:
        state["world"]["time"] = advance_time(state["world"]["time"], 2)

    # 更新共鸣度（基于新位置）
    location_data = state["world"]["locations"][new_location]
    resonance_modifier = location_data["resonance_modifier"]
    state["player"]["resonance"] += resonance_modifier
    state["player"]["resonance"] = clamp(state["player"]["resonance"], 0, 100)

    # 更新叙事旗标
    flag_name = f"{new_location}_已访问"
    state["narrative"]["flags"][flag_name] = True

    # 级联更新：检查是否触发新事件
    if new_location == "五楼中庭" and not state["narrative"]["flags"].get("五楼_拍皮球_已触发"):
        # 触发拍皮球事件
        state["world"]["entities"]["失魂者"]["level"] = 1
        state["narrative"]["flags"]["五楼_拍皮球_已触发"] = True

    return state
```

### 更新 3.2：使用念佛机

```python
def update_use_buddha_machine(state):
    """使用念佛机的状态更新"""
    # 1. 消耗道具
    state["player"]["inventory"]["念佛机"]["battery"] -= 20
    state["player"]["inventory"]["念佛机"]["uses_left"] -= 1

    # 2. 降低共鸣度
    state["player"]["resonance"] -= 15
    state["player"]["resonance"] = max(0, state["player"]["resonance"])

    # 3. 检查实体反应
    for entity_name, entity in state["world"]["entities"].items():
        if entity["level"] == 3:
            # 等级3实体被激怒
            entity["state"] = "ENRAGED"
            entity["aggro"] = True
        elif entity["level"] >= 1:
            # 等级1-2实体暂时退缩
            entity["state"] = "RETREATING"

    # 4. 更新叙事旗标
    state["narrative"]["flags"]["念佛机_已使用"] = True

    # 5. 记录选择
    state["narrative"]["choices_made"].append({
        "scene": state["narrative"]["current_scene"],
        "choice": "使用念佛机",
        "timestamp": state["world"]["time"]
    })

    return state
```

### 更新 3.3：触发失衡状态

```python
def trigger_imbalance(state):
    """触发失衡状态（共鸣度100%）"""
    # 1. 共鸣度强制为100
    state["player"]["resonance"] = 100

    # 2. 添加状态效果
    state["player"]["status_effects"].append({
        "name": "失衡",
        "duration": -1,  # 永久
        "effects": {
            "vision": "扭曲",
            "control": "受限"
        }
    })

    # 3. 所有实体升至最高等级
    for entity in state["world"]["entities"].values():
        entity["level"] = 3
        entity["state"] = "ACTIVE"

    # 4. 强制场景转换
    state["narrative"]["current_scene"] = "场景5"
    state["narrative"]["branch"] = "后果A：失衡"

    # 5. 触发清洁工提前出现
    state["world"]["entities"]["清洁工"]["location"] = state["player"]["location"]
    state["world"]["time"] = "04:44 AM"

    return state
```

---

## 示例 4：级联更新

### 级联 4.1：时间推进触发04:44事件

```python
def update_time_cascade(state, minutes):
    """时间推进的级联更新"""
    old_time = state["world"]["time"]
    new_time = advance_time(old_time, minutes)
    state["world"]["time"] = new_time

    # 检查是否跨过04:44
    if old_time < "04:44 AM" <= new_time:
        # 强制触发清洁工事件
        state["narrative"]["current_scene"] = "场景5"
        state["world"]["entities"]["清洁工"]["level"] = 2
        state["world"]["entities"]["清洁工"]["location"] = "五楼中庭"
        state["world"]["entities"]["清洁工"]["state"] = "RITUAL"

        # 共鸣度暴涨
        state["player"]["resonance"] += 20
        state["player"]["resonance"] = min(100, state["player"]["resonance"])

        # 环境变化
        state["world"]["locations"]["五楼中庭"]["smell"] = "土腥味浓重到令人作呕"
        state["world"]["environmental_events"].append({
            "type": "泥印出现",
            "active": True,
            "pattern": "人形轮廓"
        })

    # 检查是否到达06:00（早班到来）
    if new_time >= "06:00 AM":
        state["narrative"]["flags"]["早班_已到达"] = True
        # 触发特殊结局
        trigger_ending(state, "平安度过")

    return state
```

### 级联 4.2：共鸣度变化影响实体

```python
def update_resonance_cascade(state, change):
    """共鸣度变化的级联影响"""
    old_resonance = state["player"]["resonance"]
    new_resonance = clamp(old_resonance + change, 0, 100)
    state["player"]["resonance"] = new_resonance

    # 级联1：实体等级升级
    for entity_name, entity in state["world"]["entities"].items():
        if entity["level"] == 0 and new_resonance >= 30:
            entity["level"] = 1
            entity["state"] = "OBSERVING"
        elif entity["level"] == 1 and new_resonance >= 60:
            entity["level"] = 2
            entity["state"] = "LOCKING"
        elif entity["level"] == 2 and new_resonance >= 80:
            entity["level"] = 3
            entity["state"] = "HUNTING"

    # 级联2：环境事件
    if new_resonance >= 70 and old_resonance < 70:
        # 进入高危区
        state["world"]["environmental_events"].append({
            "type": "幻觉增强",
            "active": True,
            "description": "你开始看到不该看到的东西..."
        })

    # 级联3：触发失衡
    if new_resonance == 100:
        trigger_imbalance(state)

    return state
```

---

## 示例 5：状态验证

### 验证 5.1：基础验证

```python
def validate_state(state):
    """验证状态的合法性"""
    errors = []

    # 验证共鸣度范围
    if not (0 <= state["player"]["resonance"] <= 100):
        errors.append(f"共鸣度超出范围: {state['player']['resonance']}")

    # 验证位置存在
    location = state["player"]["location"]
    if location not in state["world"]["locations"]:
        errors.append(f"无效位置: {location}")

    # 验证实体等级
    for entity_name, entity in state["world"]["entities"].items():
        if not (0 <= entity["level"] <= 3):
            errors.append(f"{entity_name}等级无效: {entity['level']}")

    # 验证时间格式
    try:
        datetime.strptime(state["world"]["time"], "%H:%M %p")
    except:
        errors.append(f"时间格式无效: {state['world']['time']}")

    return (len(errors) == 0, errors)
```

### 验证 5.2：业务规则验证

```python
def validate_business_rules(state):
    """验证业务逻辑"""
    errors = []

    # 规则1：等级3实体必须处于追猎/激怒状态
    for entity_name, entity in state["world"]["entities"].items():
        if entity["level"] == 3 and entity["state"] not in ["HUNTING", "ENRAGED"]:
            errors.append(f"{entity_name}等级3但状态不是追猎: {entity['state']}")

    # 规则2：场景5必须在04:44之后
    if state["narrative"]["current_scene"] == "场景5":
        if state["world"]["time"] < "04:44 AM":
            errors.append("场景5在04:44之前触发")

    # 规则3：失衡状态下共鸣度必须是100
    has_imbalance = any(
        e["name"] == "失衡"
        for e in state["player"]["status_effects"]
    )
    if has_imbalance and state["player"]["resonance"] != 100:
        errors.append("失衡状态但共鸣度不是100")

    return (len(errors) == 0, errors)
```

---

## 示例 6：快照与回滚

### 快照 6.1：创建场景快照

```python
def create_scene_checkpoint(state):
    """创建场景检查点"""
    snapshot = {
        "player": copy.deepcopy(state["player"]),
        "world": copy.deepcopy(state["world"]),
        "narrative": copy.deepcopy(state["narrative"]),
        "timestamp": datetime.now().isoformat(),
        "scene": state["narrative"]["current_scene"]
    }

    # 保存到历史
    snapshot_id = f"checkpoint_{snapshot['scene']}_{timestamp()}"
    save_snapshot(snapshot_id, snapshot)

    return snapshot_id
```

### 回滚 6.1：无效操作回滚

```python
def try_update_with_rollback(state, update_func):
    """尝试更新，失败则回滚"""
    # 创建快照
    snapshot = copy.deepcopy(state)

    try:
        # 尝试更新
        new_state = update_func(state)

        # 验证新状态
        is_valid, errors = validate_state(new_state)
        if not is_valid:
            raise InvalidStateError(errors)

        is_valid_business, errors = validate_business_rules(new_state)
        if not is_valid_business:
            raise BusinessRuleError(errors)

        return new_state

    except Exception as e:
        # 回滚到快照
        log_error(f"状态更新失败，回滚: {e}")
        return snapshot
```

---

## 示例 7：完整的交互循环

```python
def process_player_action(state, player_input):
    """处理玩家行为的完整流程"""

    # 1. 创建快照
    snapshot = copy.deepcopy(state)

    # 2. 意图识别
    intent = intent_mapper.parse(player_input, state)

    # 3. 状态查询（验证可行性）
    if intent["type"] == "USE_ITEM":
        can_use, reason = can_use_item(state, intent["target"])
        if not can_use:
            return {
                "response": f"[无效操作] {reason}",
                "state": snapshot  # 状态不变
            }

    # 4. 应用状态更新
    try:
        if intent["type"] == "MOVE":
            state = update_player_move(state, intent["target"])
        elif intent["type"] == "USE_BUDDHA_MACHINE":
            state = update_use_buddha_machine(state)

        # 5. 级联更新
        state = update_resonance_cascade(state, intent["resonance_change"])
        state = update_time_cascade(state, intent["time_cost"])

        # 6. 验证新状态
        is_valid, errors = validate_state(state)
        if not is_valid:
            raise InvalidStateError(errors)

        # 7. 生成响应
        response = runtime_response.generate(intent, state)

        return {
            "response": response,
            "state": state
        }

    except Exception as e:
        # 回滚
        log_error(f"处理失败: {e}")
        return {
            "response": "[系统错误] 操作无效，请重试",
            "state": snapshot
        }
```

---

**设计理念：** 好的状态管理系统应该"对外宽松，对内严格"——接受各种外部输入，但内部状态必须100%符合规则。每一次状态变化都应该可追溯、可验证、可回滚。

