# Handcrafted Dialogue Tree —— v5 设计

**日期**: 2026-05-06
**状态**: Accepted (用户授权直接执行)
**作者**: yehan + Claude Opus 4.7

## Context

v1-v4 都让 LLM 在生成阶段"自由发挥",用工程手段(skeleton / beam / plateau / approx merge)兜底。结果:故事循环、不收敛、连 PoC 都做不到。5400 行 engine + tree_builder 都是补丁。

## Decision

**把 LLM 从 critical path 上彻底拿走。** 由 Claude Opus 4.7 离线手工写完整对话树作为内容资产,引擎只负责加载、播放、维护状态。运行时零 LLM 调用。

## 数据结构(唯一的关键)

```json
{
  "story_id": "hangzhou_yebanbaoan",
  "title": "断桥残雪·夜班外卖",
  "protagonist": "赵某 (G-273)",
  "start_node": "n_intro",
  "initial_state": {"PR": 0, "GR": 0, "shifts_completed": 0, "shifts_skipped": 0, "inv": []},
  "endings": {"E_TRUE": "...", "E_BAD_1987": "...", "E_BAD_DROWN": "...", "E_DATA": "...", "E_NEUTRAL": "..."},
  "nodes": {
    "n_intro": {
      "scene": "S0",
      "narrative": "...(150-300 字第二人称)",
      "choices": [
        {
          "text": "...",
          "next": "n_s1_arrive",
          "effects": {"PR": 0, "GR": 0, "inv_add": ["商场总控钥匙"]},
          "require": null
        }
      ]
    },
    "n_ending_true": {
      "is_ending": true,
      "ending_type": "E_TRUE",
      "narrative": "..."
    }
  }
}
```

**关键不变量(数据层强制):**
- 没有 `next` 指回上游 → 物理上不可能循环
- `is_ending=true` 的节点没有 `choices` → 物理上必终止
- `require` 字段做选项可见性过滤(如 require={"PR_min": 30, "inv_has": ["⺶ 符文"]})
- 节点 ID 唯一,一次写定不再变

## 引擎职责(player.py)

只做四件事:

1. 加载 `tree.json` 到字典
2. 显示当前节点的 `narrative` 和可见 `choices`(过滤 require)
3. 接受用户输入,应用 `effects` 到 state,跳转到 `next`
4. 遇到 `is_ending` 节点 → 渲染结局 → 退出

**不做:** 不调 LLM、不做状态哈希、不做 BFS 扩展、不做 plateau 检测。这些都是上一代为了兜 LLM 失控而存在的,现在数据不会失控。

## 范围(本次交付)

- 1 个故事:杭州·夜班保安·G-273
- 35-50 节点(主线 18 + 重要支线 ~20)
- 7 个夜班 + 终局 B3 Mainframe
- 5 个真正不同结局
- 玩一次 ~15-20 分钟

## 不做(YAGNI)

- 多故事菜单、SQLite、rich UI、存档/读档、多结局成就、CrewAI/LangGraph/LLMClient。这些日后需要再说。

## 后续

老代码(`src/ghost_story_factory/engine/`、`pregenerator/`、`orchestration/`)保留不删,但不再触碰。新代码全部走 `src/ghost_story_factory/v5/`。
