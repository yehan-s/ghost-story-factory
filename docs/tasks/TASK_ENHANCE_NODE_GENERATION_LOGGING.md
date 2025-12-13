# Issue: 增强对话树节点生成的错误日志记录

**优先级**: P1（高优先级）
**类别**: 工程质量改进
**关联组件**: `tree_builder.py`, `logging_utils.py`

---

## 问题描述

当前 `tree_builder.py` 中节点生成的错误日志记录过于简陋：

```python
# Line 465-468 (当前实现)
try:
    results.append(fut.result())
except Exception as e:
    print(f"⚠️  子节点生成异常: {e}")  # ❌ 问题：信息不足
```

**存在的问题**:
1. ❌ 只有简单的 `print`，不是结构化日志
2. ❌ 缺少上下文信息（当前节点ID、选择内容、深度等）
3. ❌ 没有堆栈跟踪（无法定位根因）
4. ❌ 没有记录是哪个 `choice` 导致的错误
5. ❌ 无法追踪生成失败对整体对话树的影响

---

## 改进方案

### 1. 在 TreeBuilder 中初始化 Logger

```python
# tree_builder.py: __init__ 方法
from ..utils.logging_utils import get_logger

class DialogueTreeBuilder:
    def __init__(self, ...):
        # ... 现有初始化代码 ...

        # 初始化 logger
        try:
            self.logger, _ = get_logger()
        except Exception:
            self.logger = None  # Fallback: 无 logger 时不阻塞
```

### 2. 节点生成开始时记录

```python
# tree_builder.py: generate_tree() 方法
def generate_tree(self, ...):
    if self.logger:
        self.logger.info(
            "开始生成对话树",
            extra={
                "city": self.city,
                "max_depth": self.max_depth,
                "guided_mode": self.guided_mode,
                "concurrent_workers": self.concurrent_workers
            }
        )
```

### 3. 每个节点生成时记录详细信息

```python
# tree_builder.py: _expand_choice 函数内部
def _expand_choice(choice: dict) -> dict:
    choice_id = choice.get("choice_id", "unknown")
    choice_text = choice.get("choice_text", "")

    if self.logger:
        self.logger.debug(
            f"[节点生成] 开始扩展选择",
            extra={
                "parent_id": current_node.node_id,
                "parent_depth": depth,
                "choice_id": choice_id,
                "choice_text": choice_text[:50],
                "parent_scene": current_node.scene,
                "parent_state_hash": current_node.state_hash
            }
        )

    try:
        # ... 现有的节点生成逻辑 ...

        if self.logger:
            self.logger.info(
                f"[节点生成] 成功创建子节点",
                extra={
                    "parent_id": current_node.node_id,
                    "child_id": child_node.node_id,
                    "child_depth": child_node.depth,
                    "child_scene": child_node.scene,
                    "is_ending": child_node.is_ending,
                    "choice_id": choice_id
                }
            )

        return {"type": "new", "parent_id": current_node.node_id, ...}

    except Exception as e:
        # ✅ 详细的错误日志记录
        if self.logger:
            self.logger.exception(
                f"[节点生成失败] 扩展选择时发生异常",
                exc_info=True,
                extra={
                    "parent_id": current_node.node_id,
                    "parent_depth": depth,
                    "parent_scene": current_node.scene,
                    "parent_state_hash": current_node.state_hash,
                    "choice_id": choice_id,
                    "choice_text": choice_text,
                    "choice_full": choice,
                    "game_state": {
                        "PR": new_state.get("PR"),
                        "GR": new_state.get("GR"),
                        "WF": new_state.get("WF"),
                        "current_scene": new_state.get("current_scene"),
                        "inventory_size": len(new_state.get("inventory", [])),
                        "flags_count": len(new_state.get("flags", {}))
                    },
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
        raise  # 重新抛出异常供并发框架捕获
```

### 4. 并发任务失败时记录汇总信息

```python
# tree_builder.py: Line 461-468 (改进后)
results: List[dict] = []
failed_choices: List[dict] = []  # 记录失败的选择

with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrent_workers) as executor:
    futures = {executor.submit(_expand_choice, c): c for c in choices_batch}

    for fut in concurrent.futures.as_completed(futures):
        original_choice = futures[fut]
        try:
            results.append(fut.result())
        except Exception as e:
            failed_choices.append({
                "choice": original_choice,
                "error": str(e),
                "error_type": type(e).__name__
            })

            if self.logger:
                self.logger.error(
                    f"[并发失败] 子节点生成异常（将跳过该分支）",
                    extra={
                        "parent_id": current_node.node_id,
                        "choice_id": original_choice.get("choice_id"),
                        "choice_text": original_choice.get("choice_text", "")[:50],
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )

# 在批次完成后记录失败统计
if failed_choices and self.logger:
    self.logger.warning(
        f"[批次完成] 本批次有 {len(failed_choices)}/{len(choices_batch)} 个选择生成失败",
        extra={
            "parent_id": current_node.node_id,
            "parent_depth": depth,
            "success_count": len(results),
            "failure_count": len(failed_choices),
            "failed_choice_ids": [fc["choice"]["choice_id"] for fc in failed_choices],
            "error_types": list(set(fc["error_type"] for fc in failed_choices))
        }
    )
```

### 5. 关键阶段日志记录

```python
# tree_builder.py: generate_tree() 方法中的关键位置

# BFS 循环开始
if self.logger:
    self.logger.info(
        f"[BFS] 开始第 {iterations} 轮迭代",
        extra={
            "queue_size": len(queue),
            "tree_size": len(dialogue_tree),
            "current_depth": depth
        }
    )

# 状态去重
if state_hash in self.state_manager.state_cache:
    if self.logger:
        self.logger.debug(
            f"[状态去重] 节点已存在，跳过",
            extra={
                "parent_id": current_node.node_id,
                "duplicate_node_id": existing_node_id,
                "state_hash": state_hash
            }
        )
    continue

# Checkpoint 保存
if self.logger:
    self.logger.info(
        f"[Checkpoint] 保存检查点",
        extra={
            "checkpoint_path": checkpoint_path,
            "tree_size": len(dialogue_tree),
            "current_depth": depth,
            "queue_size": len(queue)
        }
    )
```

---

## 日志输出示例

### 成功案例

```
2025-12-14 18:30:15 [INFO] 开始生成对话树 (city=杭州, max_depth=50, guided_mode=True)
2025-12-14 18:30:16 [INFO] [节点生成] 成功创建子节点 (parent_id=root, child_id=node_0001, choice_id=C1)
2025-12-14 18:30:17 [INFO] [节点生成] 成功创建子节点 (parent_id=root, child_id=node_0002, choice_id=C2)
2025-12-14 18:30:18 [INFO] [BFS] 开始第 1 轮迭代 (queue_size=2, tree_size=3)
```

### 失败案例（详细信息）

```
2025-12-14 18:30:20 [ERROR] [节点生成失败] 扩展选择时发生异常
    extra: {
        "parent_id": "node_0005",
        "parent_depth": 3,
        "parent_scene": "S3",
        "choice_id": "C12",
        "choice_text": "调查神龛",
        "choice_full": {"choice_id": "C12", "choice_text": "调查神龛", ...},
        "game_state": {"PR": 45, "GR": 10, "WF": 2, "current_scene": "S3", ...},
        "error_type": "JSONDecodeError",
        "error_message": "Expecting value: line 1 column 1 (char 0)"
    }
Traceback (most recent call last):
  File "tree_builder.py", line 422, in _expand_choice
    child_node.narrative = self._generate_response(choice, new_state)
  File "tree_builder.py", line 950, in _generate_response
    response_data = json.loads(response_text)
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

2025-12-14 18:30:21 [WARNING] [批次完成] 本批次有 1/3 个选择生成失败
    extra: {
        "parent_id": "node_0005",
        "success_count": 2,
        "failure_count": 1,
        "failed_choice_ids": ["C12"],
        "error_types": ["JSONDecodeError"]
    }
```

---

## 实施步骤

### Phase 1: 基础日志框架（1h）

1. [ ] 在 `TreeBuilder.__init__()` 中初始化 logger
2. [ ] 在 `generate_tree()` 开始/结束时记录基本信息
3. [ ] 在 BFS 循环的关键位置添加日志

### Phase 2: 节点生成详细日志（2h）

1. [ ] 在 `_expand_choice` 函数开始时记录参数
2. [ ] 在节点创建成功时记录详细信息
3. [ ] 在节点创建失败时记录完整上下文（使用 `logger.exception()`）

### Phase 3: 并发失败处理（1h）

1. [ ] 改进 Line 461-468 的异常捕获
2. [ ] 记录失败选择的列表
3. [ ] 在批次完成后记录失败统计

### Phase 4: 测试与验证（1h）

1. [ ] 故意引入错误（如断开 API 连接）测试日志输出
2. [ ] 验证日志文件包含所有必要信息
3. [ ] 检查日志格式和可读性

**总估算工作量**: 5 小时

---

## 预期效果

### 1. 完整的错误追踪

- ✅ 每个失败节点都有完整的上下文信息
- ✅ 可以快速定位问题根因（choice_id, parent_id, game_state）
- ✅ 堆栈跟踪帮助定位代码层面的问题

### 2. 生成质量监控

- ✅ 统计失败率（如 3% 的节点生成失败）
- ✅ 识别高风险选择（某些 choice_id 反复失败）
- ✅ 监控 API 稳定性（JSONDecodeError 频率）

### 3. 调试效率提升

- ✅ 从日志文件直接获取所有信息，无需重新运行
- ✅ 可以搜索特定节点 ID 或 choice_id
- ✅ 时间戳帮助定位性能瓶颈

---

## 后续优化（可选）

### 1. 结构化日志输出

使用 `structlog` 或 `python-json-logger` 输出 JSON 格式日志，便于日志分析工具解析。

### 2. 日志聚合与可视化

- 集成 ELK Stack（Elasticsearch + Logstash + Kibana）
- 实时监控节点生成成功率
- 错误类型分布饼图

### 3. 告警机制

- 失败率 >5% 时发送通知
- 某个 parent_id 连续失败 3 次时告警
- API 超时次数 >10 时告警

---

## 参考资料

- **logging_utils.py**: 项目现有的日志系统
- **Python logging best practices**: https://docs.python.org/3/howto/logging.html
- **Structlog**: https://www.structlog.org/en/stable/

---

**创建日期**: 2025-12-14
**预计完成**: 1 工作日（5 小时）
**优先级**: P1（建议在下一个 Sprint 实施）
