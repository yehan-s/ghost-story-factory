# Pass 25 ── 人格惯性 ending_seen.last 协议

## 上下文

Pass 23 铺了 5 个 main ending 的 `ending_seen.ending_id` 反咬变体——
表达"**曾经**通关过这个结局"。但跨周目玩家可能多结局连刷,只用
"曾经"无法表达"**最近一次**通关的人格底色应压过历史"。

State Architect 在 2026-05-13 评审里给出 A方案:

> 1. 引擎加 `endings_seen.last` 取值器(≈ 5 行)
> 2. ending → 画像 映射写 ADR/剧本 README,**不**进引擎
> 3. 不给 BAD ending / NEUTRAL / LINMOU 写 .last 反咬
> 4. 只 5 main ending(E_TRUE/E_TRUTH/E_BROADCAST/E_DATA/E_HIDDEN)触发
> 5. 新增 audit_profile_inheritance,默认 INFO,留 debt

## 目标

把"人格惯性"协议落地为可消费、可审计的能力,**不**强求一次铺满 5 个变体。

## 实施(已完成)

### 引擎(0 新存档字段)

- `src/ghost_story_factory/runtime/contracts.py`:`_meets_ending_seen` 加 `last` 字段。
  - `last + ending_id` 同给 = AND;两者都缺 fail-closed。
  - `last` 比较 `endings_seen[story_id][-1]`。
- `src/ghost_story_factory/v7/save_manager.py`:`record_ending` 重复通关时把 ending 移到末尾。
  - 不变量:`endings_seen[story_id][-1] == 最近一次通关 ending_type`。
  - 0 新字段、0 新概念。所有现有 `"x in list"` 消费侧语义不变。

### 文档

- 新增 `docs/architecture/ADR-011-persona-inertia.md`:协议 + 5 条 main ending 画像映射表。
- `docs/INDEX.md` 加 ADR-011 / Pass 24 / Pass 25 任务条目。

### 剧本示范

- `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`:
  - `n_intro.variant[0]` 新增 `ending_seen.last = E_TRUE` 人格惯性残影:
    "钥匙圈像摸过第二次 / 衣袋里本来折着一封旧信"。
  - 放在 variant[0](first-match 优先),压过 `ending_id` 形式的 variant[1]。

### 审计

- 新增 `tools/audit_profile_inheritance.py`:扫描 5 个 main ending 是否有非结局 variant 通过 `.last` 反咬。
- INFO 模式默认,缺 .last consumer 只报告不阻断;`--strict` 升级为 ERROR。
- `tools/audit_all.sh` 扩展为 13/13(原 12 + Pass 25 新增 1)。
- 当前状态:E_TRUE 已偿(n_intro),E_TRUTH/E_BROADCAST/E_DATA/E_HIDDEN 共 4 个 debt(留剧本扩写偿还)。

### 测试

- `tests/test_ending_seen.py` 新增 4 个 `.last` 协议测试(末尾匹配 / 非末尾 false / 空 list false / last+ending_id AND)。
- `tests/test_save_manager_query.py` 新增 `test_record_ending_repeat_moves_to_tail` 验证重排不变量。
- `tests/test_audit_pass22.py` 新增 5 个 audit_profile_inheritance 测试(空树 / 命中 / 忽略 ending_id 形式 / 跳过 ending 节点 / story_id 别名 / 正式树状态)。

## 验收

- `audit_all.sh` 13/13 全绿(E_TRUE 已偿,4 项 debt 申报)
- `tools/run_all_tests.py` 7/7 全绿
- `pytest tests/test_audit_pass22.py tests/test_ending_seen.py tests/test_save_manager_query.py -q` 全绿

## 状态

✅ Done(2026-05-13)

## 后续 debt

- 给剩余 4 个 main ending(E_TRUTH / E_BROADCAST / E_DATA / E_HIDDEN)各补 1 条 `.last` 变体。
- 决策点:补完后是否把 audit_profile_inheritance 升级为 `--strict`(纳入 audit_all.sh 阻断)。

## 相关

- 评审:`docs/team-reviews/2026-05-13-pass24-25-finale-inertia.md`
- 契约:`docs/architecture/ADR-011-persona-inertia.md`
- 前置:Pass 23 主结局反咬;Pass 24 linmou ending 反咬
