# Pass 26 ── 人格惯性 `.last` debt 清零 + 升级为阻断

## 上下文

Pass 25 落地了 `ending_seen.last` 协议,但只补了 E_TRUE(n_intro)1 条
示范变体,留下 4 个 main ending(E_TRUTH / E_BROADCAST / E_DATA / E_HIDDEN)
的 `.last` 反咬作为 debt。`audit_profile_inheritance` 以 INFO 模式
报告但不阻断。

本 pass 清账:补完 4 条 `.last` 变体,把审计升级为默认阻断,纳入
`audit_all.sh` 红线。

## 实施(已完成)

### 4 条 `.last` 反咬 variant

全部插入 `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`,放在
宿主节点 `narrative_variants[0]`(first-match 优先,压过原 `ending_id` 形式):

| ending     | 宿主节点                       | 残影意象                                                       |
|------------|--------------------------------|----------------------------------------------------------------|
| E_TRUTH    | `n_landmark_picker`            | 你食指**已经虚搭在 B3 档案室那个圈上**——还没看图,手已经知道。 |
| E_BROADCAST| `n_npc_forum_lurkers`          | 匿名首楼:「**@G-273 你回来了**」——他认得这张工牌号。         |
| E_DATA     | `n_npc_predecessor_voice`      | 对讲机背景**只有键盘敲击连音**;前任先报字段名问你 schema。     |
| E_HIDDEN   | `n_scene_evaluator_room`       | 第 12 本记录表**已摊在桌面**;某个名字**几乎到了喉咙**。       |

文案克制"后视镜叙事":角色**不知道自己为什么熟**——这正是人格惯性的核心。

### 审计升级

- `tools/audit_profile_inheritance.py`:`--strict` 改为默认行为,新增 `--lenient`(本地铺剧本临时绕开,CI 不接受)。
- `tools/audit_all.sh` 第 13 项升级:从 INFO 报告变为阻断退出(任一 main ending 缺 .last consumer → audit_all 退出码 2)。

### 测试更新

- `tests/test_audit_pass22.py`:`test_profile_inheritance_official_tree_zero_debt` 替换原
  `_pass_24_25_state` 测试,断言 5/5 main ending 都有期望 consumer。

## 验收

- `audit_all.sh` 13/13 全绿,人格惯性审计**通过**(不再报 debt)
- `tools/run_all_tests.py` 7/7
- `audit_profile_inheritance.py` 默认行为退出码 0(0 problems);CI 现在天然阻断任何 main ending 缺 `.last` consumer 的 PR

## 状态

✅ Done(2026-05-14)

## 后续

- 4 条变体目前都是"残影意象",未来 pass 可继续扩写"残影 → 行为反馈 → 真叙事归位"的二跳。
- ADR-011 第 5 条 main ending 画像映射表保持文档级,**不**进引擎(剧本品味不应硬编码)。
- 新增 main ending 时,自动阻断未配 `.last` consumer 的 PR——审计已守门。

## 相关

- 前置:Pass 25 协议落地(`TASK_PERSONA_INERTIA_PASS25.md`)
- 契约:`docs/architecture/ADR-011-persona-inertia.md`
