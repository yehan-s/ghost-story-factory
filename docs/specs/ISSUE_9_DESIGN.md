# Issue #9: 静态对话树预生成器 - API 设计文档

**文档版本**: v1.0
**创建日期**: 2025-12-14
**Issue 链接**: [#9](https://github.com/yehan-s/ghost-story-factory/issues/9)
**Milestone**: [v0.2.0](https://github.com/yehan-s/ghost-story-factory/milestone/2)

---

## 1. 概述

### 1.1 背景

当前游戏引擎使用**动态模式**（运行时 LLM 生成），每次选择后需等待15-25秒。Issue #9 要求实现**静态对话树预生成系统**，一次性生成所有对话内容，游玩时从数据库/文件读取，实现零等待。

### 1.2 现有代码基础

**已实现组件**（代码分析结果）：

| 组件 | 文件 | 状态 | 说明 |
|------|------|------|------|
| `DialogueNode` | `pregenerator/dialogue_node.py` | ✅ 完整 | 节点数据结构 |
| `TreeBuilder` | `pregenerator/tree_builder.py` | 🟡 基础版 | BFS遍历+checkpoint |
| `DatabaseManager` | `database/db_manager.py` | ✅ 完整 | SQLite存储 |
| `MenuSystem` | `ui/menu.py` | 🟡 待集成 | 主菜单（生成故事流程） |

**需要增强的部分**：
- 状态去重与剪枝（防止对话树爆炸）
- 进度显示与时间估算（用户体验）
- API 标准化（清晰的接口设计）

---

## 2. 核心 API 设计

### 2.1 DialogueTreeGenerator（主类）

**职责**：封装完整的对话树生成流程，提供统一接口。

```python
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

@dataclass
class GenerationConfig:
    """生成配置"""
    max_depth: int = 20              # 最大深度
    min_main_path_depth: int = 15    # 主线最小深度
    max_branches_per_node: int = 3   # 每节点最大分支数
    checkpoint_interval: int = 25    # Checkpoint间隔（节点数）
    enable_state_pruning: bool = True  # 启用状态剪枝
    concurrent_workers: int = 6      # 并发worker数
    progress_callback: Optional[Callable] = None  # 进度回调函数

@dataclass
class GenerationResult:
    """生成结果"""
    tree_data: Dict[str, Any]        # 完整对话树
    metadata: Dict[str, Any]         # 元数据（节点数/耗时/Token等）
    checkpoint_used: bool            # 是否使用了checkpoint恢复

class DialogueTreeGenerator:
    """
    对话树生成器（Issue #9 核心类）

    用法：
        config = GenerationConfig(max_depth=30, enable_state_pruning=True)
        generator = DialogueTreeGenerator(
            city="杭州",
            gdd_path="path/to/gdd.md",
            lore_path="path/to/lore_v2.md",
            config=config
        )

        result = generator.generate()
        print(f"生成完成：{result.metadata['total_nodes']} 个节点")
    """

    def __init__(
        self,
        city: str,
        gdd_path: str,
        lore_path: str,
        config: GenerationConfig = GenerationConfig()
    ):
        """初始化生成器"""
        self.city = city
        self.gdd = self._load_file(gdd_path)
        self.lore = self._load_file(lore_path)
        self.config = config

        # 内部组件
        self._tree_builder = DialogueTreeBuilder(...)
        self._state_hasher = StateHasher()
        self._progress_tracker = ProgressTracker()

    def generate(
        self,
        checkpoint_path: Optional[str] = None
    ) -> GenerationResult:
        """
        生成完整对话树

        Args:
            checkpoint_path: Checkpoint文件路径（用于恢复）

        Returns:
            GenerationResult对象
        """
        # 1. 检查checkpoint
        if checkpoint_path and self._has_checkpoint(checkpoint_path):
            self._progress_tracker.log("从checkpoint恢复...")
            tree_data = self._resume_from_checkpoint(checkpoint_path)
        else:
            tree_data = {}

        # 2. BFS遍历生成
        root = self._create_root_node()
        queue = [root]
        visited_states = set()  # 状态去重

        self._progress_tracker.start(estimated_total=1000)

        while queue:
            node = queue.pop(0)

            # 跳过重复状态
            state_hash = self._state_hasher.hash(node.game_state)
            if self.config.enable_state_pruning and state_hash in visited_states:
                continue
            visited_states.add(state_hash)

            # 生成选择点
            choices = self._tree_builder.generate_choices(node)
            node.choices = choices

            # 剪枝：限制分支数
            if len(choices) > self.config.max_branches_per_node:
                choices = choices[:self.config.max_branches_per_node]

            # 扩展子节点
            for choice in choices:
                child = self._create_child_node(node, choice)

                # 检查深度
                if child.depth < self.config.max_depth:
                    queue.append(child)
                else:
                    child.is_ending = True

                tree_data[child.node_id] = child.to_dict()

            # Checkpoint保存
            if len(tree_data) % self.config.checkpoint_interval == 0:
                self._save_checkpoint(checkpoint_path, tree_data)

            # 进度更新
            if self.config.progress_callback:
                self.config.progress_callback(
                    current=len(tree_data),
                    estimated_total=self._progress_tracker.estimated_total
                )

        # 3. 返回结果
        metadata = self._collect_metadata(tree_data)
        return GenerationResult(
            tree_data=tree_data,
            metadata=metadata,
            checkpoint_used=(checkpoint_path is not None)
        )
```

---

### 2.2 StateHasher（状态去重）

**职责**：计算游戏状态的哈希值，用于识别重复状态。

```python
import hashlib
import json

class StateHasher:
    """
    状态哈希计算器

    用于状态去重：相同状态的节点应合并，避免对话树爆炸。
    """

    def hash(self, game_state: Dict[str, Any]) -> str:
        """
        计算状态哈希

        只考虑核心状态字段：
        - PR (个人共鸣度)
        - GR (全局共鸣度)
        - WF (世界疲劳值)
        - current_scene (当前场景)
        - inventory (道具栏，排序后)
        - flags (标志位，排序后)

        忽略：
        - timestamp (时间戳，不影响后续选择)
        """
        core_state = {
            "PR": game_state.get("PR", 5),
            "GR": game_state.get("GR", 0),
            "WF": game_state.get("WF", 0),
            "current_scene": game_state.get("current_scene", "S1"),
            "inventory": sorted(game_state.get("inventory", [])),
            "flags": {k: v for k, v in sorted(game_state.get("flags", {}).items())}
        }

        # 序列化为JSON字符串（确保顺序一致）
        state_json = json.dumps(core_state, sort_keys=True)

        # 计算MD5哈希
        return hashlib.md5(state_json.encode('utf-8')).hexdigest()
```

---

### 2.3 ProgressTracker（进度追踪）

**职责**：实时显示生成进度，估算剩余时间和Token消耗。

```python
import time
from typing import Optional
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

class ProgressTracker:
    """
    进度追踪器

    显示：
    - 当前深度 / 已生成节点数
    - 预计剩余时间
    - Token消耗统计
    - 进度条
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.start_time = None
        self.total_nodes = 0
        self.estimated_total = 1000
        self.total_tokens = 0

        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        )
        self.task_id = None

    def start(self, estimated_total: int = 1000):
        """开始追踪"""
        self.start_time = time.time()
        self.estimated_total = estimated_total
        self.progress.start()
        self.task_id = self.progress.add_task(
            "生成对话树...",
            total=estimated_total
        )

    def update(
        self,
        current: int,
        depth: int,
        tokens_used: int = 0
    ):
        """更新进度"""
        self.total_nodes = current
        self.total_tokens += tokens_used

        self.progress.update(
            self.task_id,
            completed=current,
            description=f"深度 {depth} | 节点 {current}/{self.estimated_total} | Token {self.total_tokens}"
        )

    def stop(self):
        """停止追踪"""
        self.progress.stop()

        elapsed = time.time() - self.start_time
        self.console.print(f"\n✅ 生成完成！")
        self.console.print(f"   - 总节点数: {self.total_nodes}")
        self.console.print(f"   - 耗时: {elapsed:.1f} 秒")
        self.console.print(f"   - Token消耗: {self.total_tokens}")
        self.console.print(f"   - 预计成本: ${self.total_tokens * 0.00001:.2f}")
```

---

## 3. 数据结构增强

### 3.1 DialogueNode 增强

在现有 `DialogueNode` 基础上添加 `state_hash` 字段：

```python
# pregenerator/dialogue_node.py

@dataclass
class DialogueNode:
    # ... 现有字段 ...
    state_hash: Optional[str] = None  # 🆕 状态哈希（用于去重）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于保存）"""
        return {
            # ... 现有字段 ...
            "state_hash": self.state_hash,  # 🆕
        }
```

### 3.2 Checkpoint 数据结构

```python
# checkpoints/{city}_tree.json
{
  "version": "1.0",
  "city": "杭州",
  "checkpoint_at": "2025-12-14T10:30:00Z",
  "progress": {
    "total_nodes": 458,
    "current_depth": 12,
    "visited_states": 312,  # 去重后的状态数
    "total_tokens": 150000
  },
  "tree_data": {
    "root": {...},
    "node_001": {...},
    ...
  },
  "queue": [  # 🔴 关键：保存BFS队列状态
    {"node_id": "node_458", "depth": 12},
    {"node_id": "node_459", "depth": 12}
  ]
}
```

---

## 4. 集成方案

### 4.1 菜单系统集成

在 `ui/menu.py` 中调用生成器：

```python
# ui/menu.py

from ghost_story_factory.pregenerator import DialogueTreeGenerator, GenerationConfig

class MenuSystem:
    def generate_story_flow(self) -> Optional[Story]:
        """生成故事流程（用户交互）"""

        # 1. 用户输入城市名
        city = self._input_city_name()

        # 2. 调用生成器
        config = GenerationConfig(
            max_depth=30,
            min_main_path_depth=20,
            enable_state_pruning=True,
            progress_callback=self._on_progress
        )

        generator = DialogueTreeGenerator(
            city=city,
            gdd_path=f"deliverables/{city}/{city}_gdd.md",
            lore_path=f"deliverables/{city}/{city}_lore_v2.md",
            config=config
        )

        try:
            result = generator.generate(
                checkpoint_path=f"checkpoints/{city}_tree.json"
            )

            # 3. 保存到数据库
            story_id = self.db.save_story(
                city_name=city,
                title=f"{city}故事",
                synopsis="AI生成的灵异故事",
                characters=[{"name": "主角", "is_protagonist": True}],
                dialogue_trees={"主角": result.tree_data},
                metadata=result.metadata
            )

            return self.db.get_story_by_id(story_id)

        except KeyboardInterrupt:
            self.console.print("\n⚠️  生成中断（已保存checkpoint）")
            return None

    def _on_progress(self, current: int, estimated_total: int):
        """进度回调"""
        pass  # ProgressTracker already handles display
```

---

## 5. 验收标准映射

| Issue #9 验收标准 | API设计对应组件 | 实现方式 |
|------------------|----------------|---------|
| BFS遍历算法 | `DialogueTreeGenerator.generate()` | 队列+while循环 |
| 状态去重和剪枝 | `StateHasher` + `visited_states` | MD5哈希+集合去重 |
| Checkpoint/Resume | `_save_checkpoint()` + `_resume_from_checkpoint()` | JSON文件保存队列状态 |
| 进度显示与时间估算 | `ProgressTracker` | rich.Progress库 |
| 单元测试 >80% | pytest | Mock LLMClient |

---

## 6. 开发计划

### Phase 1: 核心算法（3天）
- [ ] 实现 `StateHasher` 类
- [ ] 增强 `DialogueNode`（添加 `state_hash`）
- [ ] 实现状态去重逻辑

### Phase 2: 进度追踪（2天）
- [ ] 实现 `ProgressTracker` 类
- [ ] 集成 rich.Progress
- [ ] 添加 Token 统计

### Phase 3: Checkpoint 优化（2天）
- [ ] 优化 checkpoint 数据结构
- [ ] 实现队列状态保存
- [ ] 测试恢复功能

### Phase 4: API 封装（2天）
- [ ] 实现 `DialogueTreeGenerator` 主类
- [ ] 集成到 `MenuSystem`
- [ ] 端到端测试

### Phase 5: 单元测试（2天）
- [ ] 编写 `test_state_hasher.py`
- [ ] 编写 `test_progress_tracker.py`
- [ ] 编写 `test_dialogue_tree_generator.py`
- [ ] 确保覆盖率 >80%

**总计**: 11天

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 状态哈希冲突 | 中 | 使用MD5（冲突概率极低）+ 添加冲突检测日志 |
| 内存溢出（大对话树） | 高 | 分批写入数据库 + 限制max_depth |
| Checkpoint 损坏 | 中 | 多版本备份 + JSON格式验证 |
| 生成时间过长（>4小时） | 中 | 优化剪枝策略 + 提供中断恢复 |

---

## 8. 下一步

1. ✅ 代码分析完成
2. ✅ API设计文档完成
3. ⏭️  创建 `feature/9` 分支
4. ⏭️  开始 Phase 1 开发

**设计审查**: 请确认API设计是否满足需求，然后开始开发。
