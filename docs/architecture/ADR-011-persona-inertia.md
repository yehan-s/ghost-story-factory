# ADR-011: 人格惯性 ── ending_seen.last 跨周目反喂协议

## Status

Accepted

## Date

2026-05-13

## Context

ADR-010 把周目实质拓扑定义为沙盒,跨周目联动靠
`endings_seen[story_id]: list[ending_type]`(0 新字段)。Pass 23(M19)
已经在 `n_intro / picker / 早期场景` 铺了 4 条 `ending_seen.ending_id`
形式的变体——表达「**曾经**通关过 X 结局」的反咬残影。

但这层语义对「**最近一次**通关」做不出区分。一个玩家:

- 先通关 E_TRUE(救人 / 还原)
- 再通关 E_DATA(冷血提纯)
- 然后开新周目

按现状,他在 n_intro 既"曾经看过 E_TRUE",又"曾经看过 E_DATA";
两条 variant 都满足,first-match 抓最前面的——但**剧本想表达的**是:
最近一次的人格底色应该压过更早期的——这一周目开场该带的是 E_DATA 的
冷感,不是 E_TRUE 的怀念。

这就是「**人格惯性**」(persona inertia)的需求。

## Decision

新增协议 `ending_seen.last`:匹配 `endings_seen[story_id]` 的**末尾元素**。
配套修改:`SaveManager.record_ending` 在重复通关时把 `ending_type` 移到
list 末尾,保证 `list[-1]` 永远是最近一次通关。

- 完整协议(向后兼容):
  ```jsonc
  {
    "ending_seen": {
      "story_id": "杭州_v7",          // 必填
      "ending_id": "E_TRUE",            // 二选一:历史里出现过
      "last": "E_TRUE"                  // 二选一:**最近一次**通关
      // 两个同时给 = AND
    }
  }
  ```
- 0 新存档字段(ADR-007 兼容):`endings_seen` 结构不变,只新增"末尾即最近"的不变量。
- 0 新引擎概念:`.last` 只是 list 末尾查询,5 行代码实现。

### 5 条 main ending 人格画像映射(剧本端约定)

下面这份表是**剧本人员看的**——引擎不读它,审计也不读它,纯文档:

| ending      | 人格底色                | 反咬残影示例                                         |
|-------------|------------------------|------------------------------------------------------|
| E_TRUE      | 良知 / 归还             | 衣袋里"本来折着"的旧信痕迹;钥匙圈像摸过第二次       |
| E_TRUTH     | 取证 / 拼图狂            | 抽屉里多一张你不认识手迹的旧拓印纸                   |
| E_BROADCAST | 曝光 / 公共审判         | 楼下 NPC 多看你一眼,似乎认得这张脸                  |
| E_DATA      | 冷血提纯 / 信息商人     | 公共显示屏一闪,广告变成一行旧表格                   |
| E_HIDDEN    | 判官 / 隐线             | 某个名字在你嘴边一闪——你叫不出,但你**知道**那是谁 |

**BAD ending / NEUTRAL / LINMOU 不在 `.last` 反咬范围**:
- BAD ending 是"必死分支",跨周目"上次死过"的反咬是 nice-to-have(见 audit_cross_run_continuity 默认豁免)。
- NEUTRAL 是"无人格的混过去",无底色可继承。
- LINMOU ending 由 Pass 24 的 `ending_id` 反咬覆盖(线性遗迹 vs 残影),不需要 `.last`。

## Alternatives Considered

### Option A:加新字段 `last_ending_type: str`

- **优点**:语义最直接,O(1) 查。
- **拒绝**:违反 ADR-007 单一真相源——`endings_seen[story_id][-1]` 已经能表达,新字段是镜像。

### Option B:把 ending → 画像映射写进引擎

- **优点**:剧本只需声明 `behavior_profile.has = "良知"`,引擎自动从最近 ending 推。
- **拒绝**:把"剧本品味"硬编码进引擎,违反 ADR-008 反应契约——画像应是剧本数据,不是引擎逻辑。引擎只读 list 末尾,画像在剧本写。

### Option C:不区分 `.last`,继续用 `ending_id`

- **优点**:0 改动。
- **拒绝**:无法表达"最近一次的底色压过历史"——剧本只能写"曾经通关过",这是 Pass 23 已经覆盖的;Pass 25 的需求是更细的区分。

## Consequences

### Positive

- 剧本端获得「最近一次通关」语义,可以写出"上次冷血 → 这次开场带冷感"的层次。
- 0 新真相源 / 0 新存档字段,ADR-007/008 不动。
- 审计可观测:`audit_profile_inheritance` 报告每个 main ending 的 `.last` consumer 覆盖。

### Negative & Mitigation

- **现有玩家存档兼容**:旧版 `record_ending` 不重排,玩家历史 `endings_seen` 不一定满足"末尾即最近"。
  - **Mitigation**:这是渐进失真——重复通关后即修复。审计接受这条 debt,不阻断。
- **`.last` variant 必须放在 first-match 顺序前**才能压过 `ending_id` 形式。
  - **Mitigation**:剧本审查时人工把关;剧本端约定:`.last` < `ending_id` < `theme_resolved` < `deduction_resolved` 排序。
- **跨周目"忘性"**:玩家久不通关此结局,`.last` 仍指向它,反咬残影一直存在。
  - **Mitigation**:不修。这正是「人格惯性」要表达的——上一次的味道**就是**留得久。需要"健忘"的剧本走 `playthroughs` 计数即可。

## Migration / Rollout

- **Pass 25(已交付)**:协议落地 + `n_intro` E_TRUE 一条示范 variant + `audit_profile_inheritance` INFO 报告。
- **Pass 26(已交付)**:4 条剩余 main ending 的 `.last` 反咬补齐:
  - E_TRUTH → `n_landmark_picker`(指尖虚搭在 B3 档案圈上)
  - E_BROADCAST → `n_npc_forum_lurkers`(匿名 @ 你的工号)
  - E_DATA → `n_npc_predecessor_voice`(键盘敲击 + 字段名 schema 确认)
  - E_HIDDEN → `n_scene_evaluator_room`(名字到了喉咙却叫不出)
- **Pass 26 起**:`audit_profile_inheritance` 升级为默认阻断;`audit_all.sh` 第 13 项一票否决。
  新增 main ending 时,必须同时铺 `.last` consumer,否则 CI 不接受。

## References

- ADR-007 状态契约:`docs/architecture/ADR-007-state-contract.md`
- ADR-008 反应机制:`docs/architecture/ADR-008-reaction-mechanism.md`
- ADR-010 沙盒拓扑:`docs/architecture/ADR-010-sandbox-topology-contract.md`
- Pass 23 跨周目反咬:`docs/tasks/TASK_SCRIPT_CROSS_RUN_FINALE_PASS23.md`
- 实现:`src/ghost_story_factory/runtime/contracts.py`(`_meets_ending_seen`),`src/ghost_story_factory/v7/save_manager.py`(`record_ending`)
- 审计:`tools/audit_profile_inheritance.py`
