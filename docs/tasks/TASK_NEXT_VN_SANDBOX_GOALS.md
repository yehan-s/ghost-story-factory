# TASK: 下一阶段目标 - 剧本深挖与 VN 沙盒可玩闭环

版本: v0.1
状态: Active
关联:
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS1.md`
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS2.md`
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS3.md`
- `docs/tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md`
- `docs/tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md`
- `docs/tasks/TASK_SCRIPT_BEHAVIOR_FEEDBACK_PASS6.md`
- `docs/tasks/TASK_V7_AUDIT_DEBT_CLEANUP.md`
- `docs/tasks/TASK_GAMETREE_V1.md`
- GitHub Issue: `#22`

---

## 0. 当前判断

正式杭州剧本已经从“不可玩散点”推进到“可审计、可抵达、可重访有差异”的状态。

但它还没有达到目标里的 galgame / 视觉小说厚度。真正的问题不是再加几个吓人名词,而是三件事:

1. 玩家选择对角色关系的影响还不够可见;
2. 清洁工、论坛围观者、评价室已经完成第一轮人格化,Pass 8 已把三者推进为“曝光 / 删除 / 审判”的同一张 NPC 账本;
3. VN 演出字段已经覆盖正式节点,关键节点已补 `camera / cg_intent / transition_intent`,并被 `audit_playability` 关键节点 warning 锁住。

本任务记录下一阶段的目标,避免后续继续凭感觉修文本。

---

## 1. 当前问题记录

### 1.1 阻塞级问题

- 无。`bash tools/audit_all.sh` 已通过;
- 正式树当前节点可达率为 145/145;
- 当前结局节点为 21;
- `audit_variants` 未发现 `undifferentiated_revisit_nodes`。

### 1.2 非阻塞技术债

- `database/ghost_stories_test.db` 会被测试改动,当前是本地脏文件,不应提交;
- `audit_tree` 的 9 个 `inv_descriptions` 孤儿道具已在 Issue `#27` 第一批处理中收敛为 0;
- `audit_state` 已新增 `severity.errors / warnings / info` 分级输出,剩余 warning/info 可按后续任务继续压缩;
- `TASK_GAMETREE_V1.md` 和 GitHub Issue `#19` 仍处于 Active,需要单独收尾或拆出剩余项;
- `docs/specs/ISSUE_*` 与 `SPEC_TODO.md` 存在大量历史 TODO,不能作为下一阶段唯一真相源。

---

## 2. 下一阶段目标

### M1: 剧本 Pass 3 - 叶某与巡夜员群像

状态: Done,见 `docs/tasks/TASK_SCRIPT_SANDBOX_PASS3.md`。

目标:

- 让叶某从“203 琴房事件”升级为能影响林晓燕、赵某、True/Truth/Data 三类结局的角色;
- 让 7 名巡夜员不只是安全帽数字,而是在 S6/B3/结局中体现不同失败方式;
- 让清洁工、论坛围观者、评价室不再只承担功能判断,而是反馈玩家之前的选择姿态;
- 继续保持开放沙盒,不锁死固定地标顺序。

验收:

- 至少 3 个旧 NPC 在重访时出现新的关系型 variant;
- 至少 2 个结局根据叶某或巡夜员群像状态出现差异文本;
- `audit_variants` 仍保持 `undifferentiated_revisit_nodes: []`。

### M2: 互动反馈 - 玩家不是摄像机

状态: Done。Pass 4 已完成入口、地图、晨湖和核心结局的赵某身份回收;Pass 5 已完成论坛 / 清洁工 / 评价室对曝光、注销、审判姿态的回收;Pass 6 已把行为画像前移到地图 hub、工具回访、B3 与晨湖。见 `docs/tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md`、`docs/tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md` 与 `docs/tasks/TASK_SCRIPT_BEHAVIOR_FEEDBACK_PASS6.md`。

目标:

- 建立“玩家行为画像”的最小规则,例如:救人优先、取证优先、替班逃避、曝光冲动;
- 把行为画像写进 B3、评价室、晨湖、Data/Truth/True End 的文本回收;
- 不新增复杂好感度系统,优先复用现有 flag / deduction / theme。

验收:

- 玩家至少能在终局前看到自己玩法被系统或 NPC 反咬一次;
- 至少 3 类选择姿态能在不同节点产生可读差异;
- 不新增 DB schema。

### M3: VN 演出契约 - 素材未到,结构先到

状态: Done for current baseline。Pass 4 已给入口 / 简报 / 地图 / 晨湖补关键 `presentation`;Pass 5 已在论坛 / 清洁工 / 评价室 / Data / Broadcast / Hidden 结局补 `camera / cg_intent / transition_intent`;Pass 7 已补遗失档案、红色电话亭、B3、红衣女孩、8 棺自己、True / Truth / Bad / Neutral 等关键节点,并在 `audit_playability` 中锁定关键节点演出意图 warning。正式树仍保持 145/145 演出字段覆盖。

目标:

- 明确 `presentation` 字段的最小契约:背景、角色位、音效、镜头、CG fallback;
- 对关键节点标记“未来应替换为 CG / 立绘 / 音效”的素材槽;
- 增加审计,保证正式节点不会缺少基础演出字段。

验收:

- 关键 NPC 和结局节点有稳定的 `presentation` 语义;
- 审计能报告缺失素材槽,但不要求真实图片音频立刻存在;
- CLI 仍能用 text fallback 正常运行。

### M4: 工具债收敛

状态: Done for current baseline。Issue `#27` 已完成 audit_tree 孤儿道具口径修正与 audit_state 分级输出;Issue `#19` 已关闭并把 v4 生成器对齐拆到 `#23`;已完成的 `#31` / `#33` 也已关闭,当前 milestone 只剩 roadmap `#22` 与 v4 生成器对齐 `#23`。

目标:

- 处理 9 个孤儿道具描述:要么接入节点,要么删除注册;
- 给 `audit_state` 增加分级输出,把历史噪音从真正错误里拆开;
- 收尾 `TASK_GAMETREE_V1.md` 与 Issue `#19`,把已完成项勾掉,剩余项拆新任务。

验收:

- `audit_tree` 不再报告无意义孤儿道具;
- `audit_state` 的输出能分出 error / warning / info;
- Issue `#19` 状态与 Task 文档一致。

### M5: 剧本 Pass 8 - NPC 关系账本与终局前回咬

状态: Done,见 `docs/tasks/TASK_SCRIPT_NPC_ACCOUNTABILITY_PASS8.md` 与 GitHub Issue `#36`。

目标:

- 让论坛、清洁工、评价室不再只是功能节点,而是共同读取玩家取证、曝光、删痕、审判和命名行为;
- 用既有 `arc.named_the_dead / oneshot.live_streaming / oneshot.s6_no_fingerprint / arc.got_judge_seal / route.behavior_self_audit` 建立终局前回咬;
- 保持开放沙盒和 DB schema 不变。

验收:

- `n_npc_forum_lurkers` 写入命名死者状态;
- `n_npc_cleaner_null`、`n_scene_b3_corridor`、`n_scene_evaluator_room`、`n_scene_morning_lakeside` 读取 NPC 账本状态;
- 新增 `tests/test_npc_accountability_pass8.py`;
- `audit_all` 与统一测试通过。

---

## 3. 推荐执行顺序

1. 先做 M4 的 `TASK_GAMETREE_V1` 收尾,把项目账本理干净;
2. 再做 M1 剧本 Pass 3,优先补叶某和巡夜员群像;
3. 然后做 M2 行为画像,让玩家选择被世界记住;
4. 最后做 M3 VN 演出契约,给未来图形化客户端铺路。

理由很简单:先清账,再加戏。否则后面每一次剧本增强都会被旧告警和旧任务拖住。

---

## 4. 非目标

- 不做 Web UI;
- 不做真实图片 / 音频资产生产;
- 不新增数据库 schema;
- 不把沙盒改成线性章节;
- 不引入复杂数值好感度系统。
