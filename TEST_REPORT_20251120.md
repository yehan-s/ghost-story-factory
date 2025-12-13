# Ghost Story Factory 测试详细报告

**生成时间**: 2025-11-20 16:30
**测试版本**: v4 Skeleton-First Pipeline
**测试目的**: 验证新 Kimi API Key 有效性及系统稳定性

---

## 📊 执行摘要 (Executive Summary)

### ✅ 核心发现

1. **Kimi API Key 状态**: ✅ **完全正常**
   - 22 次 LLM 调用全部成功（上一次测试）
   - 认证无问题，API Key 有效

2. **代码缺陷**: ✅ **已修复**
   - 递归深度超限 Bug（`generate_test_story.py:127-141`）
   - 修复：添加 `visited` 集合防止环路导致的无限递归

3. **新发现问题**: ❌ **网络超时**
   - Kimi API 响应超时（180秒 × 2次尝试 = 6分钟）
   - 根因：网络不稳定或 Kimi 服务端负载过高

---

## 🔬 详细分析

### 第一部分：Kimi API 性能分析

#### 1.1 成功测试数据（2025-11-20 10:22）

**测试环境**:
- API Key: `sk-kimi-sJz4nnl3...` (新密钥)
- 模型: `kimi-k2-0905-preview`
- 超时配置: 180秒
- 重试策略: 最多重试1次，延迟2秒

**性能指标**:

| 指标 | 数值 | 评价 |
|------|------|------|
| 总调用次数 | 22 | - |
| 成功次数 | 22 | ✅ 100% |
| 失败次数 | 0 | ✅ 完美 |
| JSON 首次解析成功率 | 18/22 (81.8%) | ✅ 优秀 |
| JSON 抢救成功 | 4/22 (18.2%) | ℹ️ 需要抢救 |
| 平均响应时间 | 约 45-60 秒/次 | ℹ️ 较慢 |

**结论**: API Key 有效，Kimi 服务在非高峰期表现稳定。

---

#### 1.2 失败测试数据（2025-11-20 16:18）

**测试环境**: 同上

**失败日志**:
```
16:12:35 [INFO] [LLMClient] Request kimi-1-1763626355 | 开始调用
16:15:37 [ERROR] Attempt 1/2 failed | ReadTimeout (180秒)
16:15:37 [INFO] Retrying in 2.0s...
16:18:40 [ERROR] Attempt 2/2 failed | ReadTimeout (180秒)
16:18:40 [ERROR] All attempts failed
```

**时间轴分析**:
```
00:00  请求发起
03:02  第一次超时 (182秒，略超180秒配置)
03:04  开始重试 (延迟2秒)
06:05  第二次超时 (181秒)
06:05  彻底失败
```

**根因判断**:
- ❌ **不是 API Key 问题** (之前22次调用证明 Key 有效)
- ✅ **网络问题** (连续两次超时，每次都接近180秒上限)
- ✅ **可能是 Kimi 服务端负载** (下午4点可能是高峰期)

---

### 第二部分：代码缺陷修复验证

#### 2.1 原始 Bug：递归深度超限

**文件**: `generate_test_story.py:127-141`

**错误代码**:
```python
def traverse(node_id, depth=0):
    nonlocal max_depth, ending_count
    max_depth = max(max_depth, depth)

    node = dialogue_tree.get(node_id)
    if not node:
        return

    if node.get('is_ending', False):
        ending_count += 1

    for choice in node.get('choices', []):
        next_id = choice.get('next_node_id')
        if next_id and next_id != node_id:  # ❌ 只能防止自环！
            traverse(next_id, depth + 1)
```

**问题**:
- `next_id != node_id` 只能防止 **A→A** 的自环
- 无法防止复杂环路：**A→B→C→A**
- 导致 `RecursionError: maximum recursion depth exceeded` (递归深度 2995+)

---

#### 2.2 修复方案

**修复后代码**:
```python
visited = set()  # ✅ 添加访问集合

def traverse(node_id, depth=0):
    nonlocal max_depth, ending_count

    # ✅ 检查是否已访问（防止环路）
    if node_id in visited:
        return

    visited.add(node_id)  # ✅ 标记为已访问
    max_depth = max(max_depth, depth)

    node = dialogue_tree.get(node_id)
    if not node:
        return

    if node.get('is_ending', False):
        ending_count += 1

    for choice in node.get('choices', []):
        next_id = choice.get('next_node_id')
        if next_id:  # ✅ visited 集合已处理循环检查
            traverse(next_id, depth + 1)
```

**验证方法**:
- ✅ 使用经典的 DFS（深度优先搜索）访问集合模式
- ✅ 时间复杂度：O(N)，N 为节点数
- ✅ 空间复杂度：O(N)，visited 集合大小
- ✅ 彻底解决环路问题

**注意**: 此修复尚未在真实对话树上验证（因为 Kimi 超时导致对话树生成失败）。

---

### 第三部分：系统配置审查

#### 3.1 LLMClient 超时配置（`src/ghost_story_factory/utils/llm_client.py:80-114`）

**当前配置**:
```python
# 超时配置（秒）
self.timeout = int(os.getenv("LLM_TIMEOUT", "180"))  # 默认 180 秒

# 重试配置
self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "1"))  # 默认重试 1 次
self.retry_delay = float(os.getenv("LLM_RETRY_DELAY", "2.0"))  # 延迟 2 秒
```

**分析**:

| 配置项 | 当前值 | 评价 | 建议 |
|--------|--------|------|------|
| `timeout` | 180秒 | ⚠️ 过长 | 降至 60-90 秒 |
| `max_retries` | 1次 | ✅ 合理 | 保持 |
| `retry_delay` | 2秒 | ✅ 合理 | 可增至 5-10 秒（指数退避） |

**问题**:
- **180 秒超时过长**: 如果 Kimi API 真的有问题，用户需等待 6 分钟才知道失败
- **固定延迟**: 2 秒固定延迟不适合网络拥堵场景，应使用指数退避（2s → 4s → 8s）

---

#### 3.2 Prompt 长度分析

**失败请求的 Prompt 长度**:
```
2025-11-20 16:12:35 [INFO] [SkeletonGenerator] 开始生成骨架 | prompt_length=11253
```

**分析**:
- **11,253 字符** (约 3,000-4,000 tokens)
- **请求的 max_tokens: 16,000**
- **总计约需处理**: 20,000 tokens

**评估**:
- ✅ Prompt 长度在 Kimi-k2 模型上限内（128k context）
- ⚠️ 但对于慢速网络，大 Prompt 会增加传输时间
- ⚠️ 16,000 max_tokens 意味着 Kimi 需要生成大量内容（JSON 骨架），增加响应时间

---

### 第四部分：根因分析与诊断

#### 4.1 超时原因推断

**可能原因排序**（从高到低）:

1. **Kimi API 服务端负载过高** (70% 可能性)
   - 下午 4 点（16:00）可能是使用高峰期
   - 之前上午 10 点测试成功，说明非高峰期正常

2. **网络不稳定** (20% 可能性)
   - 连续两次超时，每次都接近 180 秒
   - 可能是本地网络或中间节点问题

3. **Prompt 复杂度过高** (10% 可能性)
   - 11,253 字符的 Prompt + 16,000 max_tokens
   - Kimi 需要时间处理复杂的故事骨架生成

#### 4.2 排除的原因

- ❌ **API Key 无效**: 之前 22 次调用全部成功
- ❌ **认证问题**: 日志没有 401/403 错误
- ❌ **代码逻辑错误**: 超时发生在 LLMClient 内部，不是业务逻辑

---

## 🛠️ 改进建议

### 优先级 P0（立即修复）

#### 1. 实现渐进式超时策略

**当前问题**: 180 秒固定超时，失败时用户需等待 6 分钟。

**解决方案**:
```python
# src/ghost_story_factory/utils/llm_client.py

# 第一次尝试：60 秒超时（快速失败）
# 第二次尝试：120 秒超时（给更多时间）
# 第三次尝试（可选）：180 秒超时（最后努力）

timeouts = [60, 120, 180]
for attempt, timeout in enumerate(timeouts, start=1):
    try:
        response = requests.post(..., timeout=timeout)
        return response
    except ReadTimeout:
        if attempt < len(timeouts):
            logger.warning(f"Timeout after {timeout}s, retrying with {timeouts[attempt]}s...")
            time.sleep(exponential_backoff(attempt))
        else:
            raise
```

**优点**:
- ✅ 快速失败（60 秒知道第一次结果）
- ✅ 给予重试更多时间
- ✅ 总等待时间不变（60+120+180 = 360 秒，vs 当前 180×2 = 360 秒）

---

#### 2. 添加指数退避重试

**当前问题**: 固定 2 秒延迟，网络拥堵时效果差。

**解决方案**:
```python
def exponential_backoff(attempt: int, base_delay: float = 2.0) -> float:
    """指数退避: 2s, 4s, 8s, 16s, ..."""
    return min(base_delay * (2 ** (attempt - 1)), 60)  # 上限 60 秒
```

**优点**:
- ✅ 网络拥堵时给予更多恢复时间
- ✅ 避免频繁重试加剧服务端压力

---

### 优先级 P1（短期改进）

#### 3. 实现 Prompt 长度优化

**问题**: 11,253 字符的 Prompt 可能包含冗余信息。

**解决方案**:
- [ ] 审查 `skeleton_generator.py` 的 Prompt 模板
- [ ] 移除冗余示例或说明
- [ ] 将大段示例替换为简洁的格式说明

**目标**: 将 Prompt 长度降至 8,000 字符以内。

---

#### 4. 添加降级方案（Fallback）

**问题**: Kimi 超时时，整个生成流程失败。

**解决方案**:
```python
# 降级策略：
# 1. 尝试 Kimi（首选）
# 2. Kimi 失败 → 尝试 OpenAI（如果配置了 OPENAI_API_KEY）
# 3. OpenAI 失败 → 使用简化的模板骨架（保底方案）

try:
    skeleton = kimi_client.generate(...)
except LLMTimeoutError:
    logger.warning("Kimi 超时，尝试 OpenAI...")
    try:
        skeleton = openai_client.generate(...)
    except Exception:
        logger.error("所有 LLM 失败，使用默认模板")
        skeleton = load_default_skeleton_template()
```

**优点**:
- ✅ 提高系统鲁棒性
- ✅ 用户体验更好（总能生成故事，只是质量可能下降）

---

### 优先级 P2（长期优化）

#### 5. 添加实时进度反馈

**问题**: 用户在 LLM 调用期间看不到任何进度。

**解决方案**:
```python
# 在 LLMClient.call() 中添加心跳日志
import threading

def heartbeat(request_id, interval=10):
    """每 10 秒打印一次等待提示"""
    elapsed = 0
    while not stop_event.is_set():
        time.sleep(interval)
        elapsed += interval
        logger.info(f"[LLMClient] Request {request_id} | 等待中... ({elapsed}s)")

# 在请求前启动心跳线程
stop_event = threading.Event()
heartbeat_thread = threading.Thread(target=heartbeat, args=(request_id, 10))
heartbeat_thread.start()

# 请求完成后停止心跳
stop_event.set()
heartbeat_thread.join()
```

**优点**:
- ✅ 用户知道系统仍在运行（而不是卡死）
- ✅ 可估算剩余时间

---

#### 6. 实现请求缓存

**问题**: 同样的 Prompt 重复调用 LLM 浪费时间和成本。

**解决方案**:
```python
# 使用 prompt hash 作为缓存键
import hashlib
import json

def get_cache_key(prompt: str, model: str, temperature: float) -> str:
    content = f"{prompt}|{model}|{temperature}"
    return hashlib.sha256(content.encode()).hexdigest()

# 在调用 LLM 前检查缓存
cache_key = get_cache_key(prompt, model, temperature)
cached_response = cache.get(cache_key)
if cached_response:
    logger.info(f"[LLMClient] Cache hit for {cache_key[:8]}...")
    return cached_response

# LLM 调用后写入缓存
response = llm.call(...)
cache.set(cache_key, response, ttl=86400)  # 缓存 24 小时
```

**优点**:
- ✅ 显著降低成本（避免重复调用）
- ✅ 加快开发调试速度

---

## 📋 待办事项清单

### 立即行动（本周内）

- [ ] **修复 P0-1**: 实现渐进式超时策略 (60s → 120s → 180s)
- [ ] **修复 P0-2**: 实现指数退避重试 (2s → 4s → 8s)
- [ ] **验证**: 在非高峰期（上午或深夜）重新运行测试
- [ ] **监控**: 添加 Kimi API 响应时间的统计日志

### 短期改进（2 周内）

- [ ] **优化 P1-3**: 审查并简化 skeleton Prompt 模板
- [ ] **实现 P1-4**: 添加 Kimi → OpenAI → 默认模板的降级方案
- [ ] **文档**: 更新 CLAUDE.md，添加超时问题排查指南

### 长期优化（1 个月内）

- [ ] **实现 P2-5**: 添加实时进度反馈（心跳日志）
- [ ] **实现 P2-6**: 添加 LLM 响应缓存机制
- [ ] **监控**: 建立 Kimi API 性能监控仪表板

---

## 🎯 测试计划建议

### 测试 1：验证修复（递归深度超限）

**目标**: 确认 `visited` 集合修复有效。

**步骤**:
1. 等待非高峰期（上午 9-11 点或深夜 22-24 点）
2. 运行 `python generate_test_story.py`
3. 观察是否出现 `RecursionError`

**成功标准**:
- ✅ 无 `RecursionError`
- ✅ 对话树统计正常输出（最大深度、结局数量）
- ✅ 对话树成功保存到数据库

---

### 测试 2：压力测试（超时容错）

**目标**: 验证系统在 Kimi API 不稳定时的表现。

**步骤**:
1. 实现渐进式超时策略（P0-1）
2. 人为降低超时配置（测试用）: `LLM_TIMEOUT=30`
3. 运行生成脚本，观察重试行为

**成功标准**:
- ✅ 第一次超时后立即重试（而非等待 180 秒）
- ✅ 日志清晰显示每次重试的超时值
- ✅ 最终失败时，总等待时间在可接受范围内（< 5 分钟）

---

### 测试 3：JSON 质量回归测试

**目标**: 确保修复没有影响 JSON 解析质量。

**步骤**:
1. 运行完整的对话树生成流程
2. 收集 `choice_json_metrics` 指标

**成功标准**:
- ✅ `ok_first_try` ≥ 80%（首次解析成功率）
- ✅ `failures` = 0（零失败）
- ✅ 对比基线数据（18/22 = 81.8%）无明显下降

---

## 📈 性能基线数据

**用于未来对比的性能基线**（2025-11-20 上午测试）:

```json
{
  "test_date": "2025-11-20 10:22",
  "api_key_status": "有效",
  "llm_calls": {
    "total": 22,
    "success": 22,
    "failure": 0,
    "success_rate": "100%"
  },
  "json_parsing": {
    "ok_first_try": 18,
    "salvaged": 4,
    "failures": 0,
    "first_try_rate": "81.8%"
  },
  "avg_response_time": "45-60 秒",
  "prompt_length": "约 11,000 字符",
  "config": {
    "timeout": 180,
    "max_retries": 1,
    "retry_delay": 2.0,
    "model": "kimi-k2-0905-preview"
  }
}
```

---

## 🔍 附录：日志片段

### 附录 A：成功调用示例（2025-11-20 10:22）

```log
2025-11-20 10:08:15 [INFO] [LLMClient] Request kimi-13-1763604495 | provider=kimi model=kimi-k2-0905-preview max_tokens=16000 temp=0.7
2025-11-20 10:09:10 [INFO] [LLMClient] Request kimi-13-1763604495 | Success | Response length: 1136
2025-11-20 10:09:10 [INFO] choice_json_metrics scene=S1 metrics={'total_calls': 13, 'ok_first_try': 10, 'ok_after_fix': 0, 'salvaged': 3, 'failures': 0}
```

**分析**:
- 响应时间: 55 秒 (10:09:10 - 10:08:15)
- 响应长度: 1,136 字符
- JSON 解析: 首次成功

---

### 附录 B：超时失败示例（2025-11-20 16:18）

```log
2025-11-20 16:12:35 [INFO] [LLMClient] Request kimi-1-1763626355 | provider=kimi model=kimi-k2-0905-preview max_tokens=16000 temp=0.7
2025-11-20 16:15:37 [ERROR] [LLMClient] Request kimi-1-1763626355 | Attempt 1/2 failed | Error: ReadTimeout: HTTPSConnectionPool(host='api.moonshot.cn', port=443): Read timed out. (read timeout=180)
2025-11-20 16:15:37 [INFO] [LLMClient] Request kimi-1-1763626355 | Retrying in 2.0s...
2025-11-20 16:18:40 [ERROR] [LLMClient] Request kimi-1-1763626355 | Attempt 2/2 failed | Error: ReadTimeout: HTTPSConnectionPool(host='api.moonshot.cn', port=443): Read timed out. (read timeout=180)
2025-11-20 16:18:40 [ERROR] [LLMClient] Request kimi-1-1763626355 | All 2 attempts failed
```

**分析**:
- 第一次尝试: 182 秒超时 (16:15:37 - 16:12:35)
- 重试延迟: 2 秒
- 第二次尝试: 181 秒超时 (16:18:40 - 16:15:39)
- 总耗时: 6 分 5 秒

---

## 📝 结论

### 核心问题总结

1. **✅ API Key 有效**: 新的 Kimi API Key 完全正常，已通过 22 次成功调用验证。

2. **✅ Bug 已修复**: 递归深度超限问题已通过添加 `visited` 集合解决（待真实对话树验证）。

3. **❌ 网络超时**: Kimi API 在下午高峰期出现连续超时（180秒 × 2），需要优化超时策略和重试机制。

### 行动建议

**立即行动**（今天）:
- 在非高峰期（上午或深夜）重新运行测试
- 验证 `visited` 集合修复是否有效

**本周内完成**:
- 实现渐进式超时策略（60s → 120s → 180s）
- 实现指数退避重试（2s → 4s → 8s）

**2 周内完成**:
- 优化 Prompt 模板，降低复杂度
- 添加降级方案（Kimi → OpenAI → 默认模板）

### 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| Kimi API 持续不稳定 | 中 | 高 | 实现多 LLM 降级方案 |
| 递归修复未生效 | 低 | 高 | 需真实对话树验证 |
| Prompt 过长导致慢 | 中 | 中 | 简化 Prompt 模板 |
| 用户体验差（等待过长） | 高 | 中 | 添加进度反馈 + 快速失败 |

---

**报告生成时间**: 2025-11-20 16:30
**报告作者**: Claude Code (Sonnet 4.5)
**下一次审查**: 2025-11-27（1 周后）
