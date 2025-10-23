# State Management - 设计说明 (Design Rationale)

**文档用途：** 本说明阐明"状态管理系统"的核心设计原则。它解释了如何在酒馆式游戏中维护、更新、验证游戏状态，确保世界的因果一致性和可追溯性。

---

## 设计挑战

**核心问题：** 酒馆式游戏是"无限循环"的：玩家输入→AI响应→状态更新→玩家输入...每次循环都可能改变世界状态，如何确保：
1. 状态变化符合世界规则
2. 历史状态可追溯（回溯/调试）
3. 复杂状态的高效查询
4. 跨模块的状态一致性

---

## 核心原则一：状态分层架构 (Layered State Architecture)

**设计说明：** 游戏状态不是"一个大JSON"，而是**分层管理**的数据结构。

**实现方式：**

```
┌─────────────────────────────────────────┐
│ Layer 1: 玩家状态 (Player State)        │
│ - 位置、共鸣度、生命值、道具、情绪      │
├─────────────────────────────────────────┤
│ Layer 2: 世界状态 (World State)         │
│ - 实体位置/等级、环境事件、时间         │
├─────────────────────────────────────────┤
│ Layer 3: 叙事状态 (Narrative State)     │
│ - 当前场景、分支、旗标、历史记录        │
├─────────────────────────────────────────┤
│ Layer 4: 元状态 (Meta State)            │
│ - 游戏版本、会话ID、保存点               │
└─────────────────────────────────────────┘
```

**目的：** 不同层的状态有不同的更新频率和验证规则：
- Layer 1：每次交互都更新
- Layer 2：基于实体行为规则更新
- Layer 3：基于剧情节点更新
- Layer 4：玩家操作或系统事件更新

---

## 核心原则二：不可变历史 + 可变当前 (Immutable History + Mutable Present)

**设计说明：** 当前状态可修改，但历史状态**永远不变**。

**实现方式：**

```python
class GameState:
    current: State  # 可变的当前状态
    history: List[StateSnapshot]  # 不可变的历史快照

    def update(self, changes):
        # 1. 保存当前状态到历史
        self.history.append(self.current.snapshot())

        # 2. 应用变更到当前状态
        self.current.apply(changes)

        # 3. 验证新状态
        if not self.current.is_valid():
            self.rollback()  # 回滚到历史状态
```

**目的：**
1. 调试：出错时可查看历史轨迹
2. 回溯：玩家可读取存档回到某个时间点
3. 分析：统计玩家行为序列（如"从未使用念佛机"）

---

## 核心原则三：状态即契约 (State as Contract)

**设计说明：** 状态不仅是"数据"，更是对《世界书》规则的"契约承诺"。

**实现方式：**

### 契约1：共鸣度约束

```python
class ResonanceState:
    value: int  # 0-100

    def set(self, new_value):
        # 契约：共鸣度永远在0-100之间
        self.value = clamp(new_value, 0, 100)

        # 契约：达到100%触发失衡
        if self.value == 100:
            trigger_event("失衡状态")

        # 契约：共鸣度影响实体等级
        update_entity_levels_based_on_resonance()
```

### 契约2：实体等级进阶

```python
class EntityState:
    level: int  # 0-3

    def upgrade_level(self):
        # 契约：实体等级只能递增，不能降低
        if self.level < 3:
            self.level += 1

        # 契约：等级3触发追猎行为
        if self.level == 3:
            self.behavior = "HUNT"
```

### 契约3：时间单向流动

```python
class TimeState:
    current: datetime  # 游戏内时间

    def advance(self, minutes):
        # 契约：时间只能前进
        self.current += timedelta(minutes=minutes)

        # 契约：到达04:44触发清洁工事件
        if self.current.strftime("%H:%M") == "04:44":
            trigger_event("场景5_清洁工出现")
```

**目的：** 将《世界书》的文字规则转化为代码约束，AI无法违反。

---

## 核心原则四：事件驱动更新 (Event-Driven Update)

**设计说明：** 状态不是"直接修改"，而是通过**事件**触发更新。

**实现方式：**

```python
class StateManager:
    def process_event(self, event):
        # 事件示例：玩家使用念佛机
        if event.type == "USE_BUDDHA_MACHINE":
            # 1. 更新玩家状态
            self.player.inventory["念佛机"].battery -= 20
            self.player.resonance -= 15

            # 2. 更新世界状态
            if self.world.entities["清洁工"].level == 3:
                # 世界规则：念佛机激怒等级3实体
                self.world.entities["清洁工"].state = "ENRAGED"

            # 3. 更新叙事状态
            self.narrative.flags["念佛机_已使用"] = True

            # 4. 触发级联事件
            if self.player.resonance < 30:
                self.trigger_event("共鸣度_降至安全区")
```

**目的：**
1. 可追溯：每个状态变化都有明确的事件来源
2. 可扩展：新增世界规则只需添加事件处理器
3. 可验证：事件日志可用于调试

---

## 核心原则五：状态查询接口 (State Query Interface)

**设计说明：** 其他模块不直接访问状态数据，而是通过**查询接口**。

**实现方式：**

```python
class StateManager:
    # 高级查询
    def is_player_in_danger(self) -> bool:
        """玩家是否处于危险中"""
        nearby_threats = self.get_nearby_entities(threat_only=True)
        return len(nearby_threats) > 0 or self.player.resonance > 70

    def can_player_use_item(self, item_name: str) -> tuple[bool, str]:
        """玩家能否使用某道具"""
        if item_name not in self.player.inventory:
            return (False, "你没有这个道具")

        item = self.player.inventory[item_name]
        if item.battery <= 0:
            return (False, f"{item_name}没电了")

        return (True, "")

    def get_available_exits(self) -> List[str]:
        """获取当前位置的可用出口"""
        exits = self.world.locations[self.player.location].exits
        # 过滤被封锁的出口
        return [e for e in exits if not e.is_blocked]
```

**目的：**
1. 封装：状态内部结构可以改变，接口保持稳定
2. 语义化：`is_player_in_danger()` 比 `state.resonance > 70` 更易读
3. 验证：查询接口可以包含业务逻辑

---

## 核心原则六：状态快照与恢复 (Snapshot & Restore)

**设计说明：** 支持"存档/读档"机制，用于玩家保存进度或系统回滚。

**实现方式：**

```python
class StateManager:
    def create_snapshot(self, name: str) -> str:
        """创建状态快照"""
        snapshot = {
            "player": self.player.to_dict(),
            "world": self.world.to_dict(),
            "narrative": self.narrative.to_dict(),
            "timestamp": datetime.now().isoformat(),
            "name": name
        }
        snapshot_id = save_to_storage(snapshot)
        return snapshot_id

    def restore_snapshot(self, snapshot_id: str):
        """恢复到某个快照"""
        snapshot = load_from_storage(snapshot_id)
        self.player = Player.from_dict(snapshot["player"])
        self.world = World.from_dict(snapshot["world"])
        self.narrative = Narrative.from_dict(snapshot["narrative"])

    def auto_checkpoint(self):
        """自动存档点（场景切换时）"""
        if self.narrative.should_checkpoint():
            self.create_snapshot(f"auto_{self.narrative.current_scene}")
```

---

## 数据结构定义

### Layer 1: 玩家状态

```json
{
  "player": {
    "location": "五楼中庭",
    "resonance": 45,
    "health": 100,
    "emotion": "FEAR",
    "inventory": {
      "手电筒": {"battery": 75, "on": true},
      "念佛机": {"battery": 50, "uses_left": 2},
      "对讲机": {"signal": false}
    },
    "status_effects": [
      {"name": "被标记", "duration": -1, "source": "清洁工"}
    ]
  }
}
```

### Layer 2: 世界状态

```json
{
  "world": {
    "time": "04:15 AM",
    "weather": "室内（无天气）",
    "entities": {
      "清洁工": {
        "level": 2,
        "location": "五楼中庭",
        "state": "RITUAL（拖地仪式）",
        "target": null,
        "aggro": false
      },
      "失魂者": {
        "level": 0,
        "location": "未触发",
        "state": "DORMANT"
      },
      "白衣女子": {
        "level": 1,
        "location": "B3数据中心",
        "state": "WAITING",
        "dialogue_state": "未对话"
      }
    },
    "locations": {
      "五楼中庭": {
        "resonance_modifier": 10,
        "light_level": "暗淡（荧光灯）",
        "smell": "土腥味浓重",
        "exits": ["楼梯", "北角货梯", "监控室"],
        "objects": ["长椅", "柱子", "枯萎绿植"]
      }
    },
    "environmental_events": [
      {"type": "荧光灯闪烁", "active": true, "interval": 30}
    ]
  }
}
```

### Layer 3: 叙事状态

```json
{
  "narrative": {
    "current_scene": "场景4",
    "branch": "主线",
    "checkpoint": "场景3_完成",
    "flags": {
      "交接_已完成": true,
      "五楼_拍皮球_已触发": true,
      "场景3_电梯失控": true,
      "念佛机_已使用": false,
      "善意标记": 0
    },
    "choices_made": [
      {"scene": "场景2", "choice": "调查五楼", "outcome": "发现皮球"},
      {"scene": "场景3", "choice": "使用货梯", "outcome": "触发失控"}
    ],
    "unlocked_endings": []
  }
}
```

### Layer 4: 元状态

```json
{
  "meta": {
    "session_id": "a1b2c3d4",
    "game_version": "1.0.0",
    "start_time": "2025-10-23T20:00:00Z",
    "play_time_minutes": 35,
    "save_slots": [
      {"id": "auto_场景3", "timestamp": "2025-10-23T20:25:00Z"},
      {"id": "manual_1", "timestamp": "2025-10-23T20:30:00Z"}
    ]
  }
}
```

---

## 状态更新规则

### 规则1：原子性更新

```python
def update_state(state, changes):
    # 开始事务
    transaction = Transaction()

    try:
        # 应用所有变更
        for change in changes:
            transaction.apply(change)

        # 验证新状态
        if not transaction.is_valid():
            raise InvalidStateError()

        # 提交事务
        transaction.commit()
    except Exception as e:
        # 回滚事务
        transaction.rollback()
        raise e
```

**目的：** "要么全部成功，要么全部失败"，不允许部分更新。

---

### 规则2：级联更新

```python
def update_resonance(new_value):
    # 直接更新
    state.player.resonance = new_value

    # 级联更新1：影响实体等级
    for entity in state.world.entities.values():
        if entity.level < 3:
            threshold = entity.upgrade_threshold
            if state.player.resonance >= threshold:
                entity.level += 1

    # 级联更新2：触发环境事件
    if new_value >= 80:
        state.world.environmental_events.append({
            "type": "幻觉增强",
            "active": true
        })
```

---

### 规则3：延迟更新

```python
# 某些状态变化不立即生效
state.player.mark_for_delayed_update(
    field="location",
    new_value="B3",
    delay_condition="清洁工完成标记仪式"
)

# 在条件满足时批量应用
if state.narrative.flags["清洁工_标记完成"]:
    state.player.apply_delayed_updates()
```

---

## 状态验证规则

### 验证1：范围检查

```python
def validate_player_state(player):
    assert 0 <= player.resonance <= 100
    assert player.health > 0
    assert player.location in valid_locations
```

### 验证2：依赖检查

```python
def validate_entity_state(entity):
    if entity.level == 3 and entity.state != "HUNT":
        raise InconsistentStateError(
            "等级3实体必须处于追猎状态"
        )
```

### 验证3：时间线检查

```python
def validate_narrative_state(narrative):
    # 场景必须按顺序推进
    if narrative.current_scene == "场景5":
        assert narrative.flags["场景4_已完成"]
```

---

## 状态同步机制

### 同步点1：场景切换

```python
def transition_to_scene(new_scene):
    # 1. 保存当前状态快照
    snapshot = state.create_snapshot(f"before_{new_scene}")

    # 2. 应用场景初始化
    state.narrative.current_scene = new_scene
    state.apply_scene_init(new_scene)

    # 3. 验证新状态
    if not state.is_valid():
        state.restore_snapshot(snapshot)
        raise SceneTransitionError()
```

### 同步点2：实体升级

```python
def upgrade_entity_level(entity_name):
    # 1. 检查升级条件
    if not can_upgrade(entity_name):
        return

    # 2. 升级实体
    state.world.entities[entity_name].level += 1

    # 3. 同步行为模式
    new_behaviors = get_behaviors_for_level(
        entity_name,
        state.world.entities[entity_name].level
    )
    state.world.entities[entity_name].behaviors = new_behaviors
```

---

## 性能优化

### 优化1：懒加载

```python
class WorldState:
    _locations: Optional[Dict] = None

    @property
    def locations(self):
        # 只在访问时才加载位置数据
        if self._locations is None:
            self._locations = load_locations_from_lore()
        return self._locations
```

### 优化2：增量更新

```python
class StateManager:
    def update(self, changes):
        # 只更新变化的字段
        for field, value in changes.items():
            if self.current[field] != value:
                self.dirty_fields.add(field)
                self.current[field] = value
```

### 优化3：缓存查询

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_nearby_entities(location):
    # 缓存附近实体查询结果
    return [e for e in entities if e.location == location]
```

---

## 与其他模块的关系

```
┌─────────────────┐
│ Intent Mapping   │ 识别玩家意图
└────────┬────────┘
         ↓
┌─────────────────┐
│ State Management │ 验证意图是否可行（检查状态）
└────────┬────────┘
         ↓
┌─────────────────┐
│ Runtime Response │ 基于状态生成响应
└────────┬────────┘
         ↓
┌─────────────────┐
│ State Management │ 应用状态变更
└────────┬────────┘
         ↓
┌─────────────────┐
│ GDD Check        │ 检查是否触发新场景/事件
└────────┬────────┘
         ↓
┌─────────────────┐
│ State Management │ 级联更新（实体升级/环境变化）
└─────────────────┘
```

---

## 设计哲学

**核心理念：** State Management 是游戏世界的"记忆"和"规则守护者"。它确保：
1. 世界的每一次变化都有据可查
2. 《世界书》的规则被严格执行
3. 玩家的每个选择都被永久记录
4. AI 无法违反物理和逻辑约束

**质量标尺：**
- 一致性：100%符合《世界书》规则
- 可追溯性：任何状态都能追溯到触发事件
- 性能：查询和更新在 <10ms 内完成
- 容错性：无效更新会被自动回滚

