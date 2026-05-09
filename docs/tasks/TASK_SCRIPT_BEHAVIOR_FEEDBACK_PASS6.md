# TASK: 正式剧本行为画像与工具回访 Pass 6

版本: v0.2
状态: Done
关联:
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md`
- `docs/tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md`
- GitHub Issue: `#31`

---

## 0. 背景

Pass 4/5 已经让入口、地图、论坛、清洁工、评价室开始读玩家状态。

但反馈还不够“玩法化”:玩家很多时候要等到结局才知道系统怎么看待自己的选择。真正的 VN 沙盒应该在中途回访时就让玩家感到:

- 取证和理解不是同一回事;
- 曝光会把死人交给围观机器;
- 救人不是替人死,而是把名字还给他们;
- 逃避巡逻会被夜班系统当作主动投降;
- 走向判官线不是奖励,而是职位吞人。

本任务不新增好感度、不新增 DB schema。只复用现有 flag / puzzle / shifts,把玩家行为画像提前写进地图、工具节点和终局前场景。

---

## 1. 目标 / 非目标

### 目标

- [x] 地图 hub 增加更早的行为画像反馈;
- [x] 遗失档案 / 红色电话亭等工具节点增强回访反馈;
- [x] B3 / 评价室 / 晨湖前后增强终局前行为判读;
- [x] 至少 4 类姿态有明确文本:取证、曝光、救人、逃避 / 替班;
- [x] 保持开放沙盒结构,不锁死地标顺序;
- [x] 重建正式 `tree.json`;
- [x] 跑全量审计与统一测试;
- [x] 回写 GitHub Issue #31。

### 非目标

- 不新增复杂数值行为画像系统;
- 不新增 DB schema;
- 不新增真实图片 / 音频素材;
- 不改 CLI 渲染器;
- 不把沙盒改成线性章节。

---

## 2. 里程碑

### M1: Task / Issue 对齐

- [x] 创建 GitHub Issue #31;
- [x] 创建本 Task 文档;
- [x] 明确只做剧本数据和文档,不扩大到引擎改造。

### M2: 中途玩法反馈

- [x] `n_landmark_picker` 增加行为画像 variant;
- [x] `n_scene_lost_archive` 增强取证 / 救人反馈;
- [x] `n_scene_red_telephone` 增强联系前任 / 逃避反馈。

### M3: 终局前判读

- [x] `n_scene_b3_corridor` 增强四类玩法姿态汇总;
- [x] `n_scene_evaluator_room` 增强“取证之后如何命名”的审判;
- [x] `n_scene_morning_lakeside` 补中途选择到结局入口的心理回收。

### M4: 验收

- [x] `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`;
- [x] `python3 tools/merge_fragments.py`;
- [x] `bash tools/audit_all.sh`;
- [x] `.venv/bin/python tools/run_all_tests.py`;
- [x] Issue #31 记录结果。

### M5: 路线状态化回补

- [x] 复用现有“取证 / 曝光 / 等待系统来电”状态作为行为画像输入;
- [x] 在地图 hub 增加基于行为画像解锁的 `[回访]` 入口;
- [x] 让评价室读取玩家主动回访,而不是只在终局文本里评价;
- [x] 让 B3 / 清晨继续读取回访结果;
- [x] 只新增 `route.behavior_self_audit`,避免正式树 flag 总数超过上限;
- [x] 保持 DB schema 和运行时引擎不变。

---

## 3. 代码入口

- `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
- `stories/hangzhou_yebanbaoan/tree.json`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`

---

## 4. 验收标准

- 至少 4 个可重访节点新增或强化行为画像 variant;
- 至少 1 个终局前节点明确指出玩家玩法倾向;
- `audit_variants` 仍保持 `undifferentiated_revisit_nodes: []`;
- `audit_all` 通过;
- 统一测试通过。

---

## 5. 完成记录

- `n_landmark_picker` 新增取证/曝光、救人、避险三类玩法姿态反馈;
- `n_scene_lost_archive` 新增“取证 vs 传播”和“名字归档”反馈;
- `n_scene_red_telephone` 新增联系前任与现实压力、跳过巡逻的回访反馈;
- `n_scene_b3_corridor` 新增曝光过量、路线跳过的终局前判读;
- `n_scene_evaluator_room` 新增公开证据与命名死者之间的审判差异;
- `n_scene_morning_lakeside` 新增救人无声回收与直播按钮反咬;
- 正式 `tree.json` 已重建,节点总数不变,variant 总量提升到 309。

## 6. 二次加深记录

用户指出上一轮“没怎么改剧本”。这个判断成立:Pass 6 初版主要增加的是 narrative variants,还没有把玩家行为稳定写成后续路线条件。

本轮补上结构性改动:

- `n_scene_lost_archive` 的“拍照准备公开”继续使用 `arc.all_archives_photoed` 作为取证输入;
- `n_npc_forum_lurkers` 的“继续直播”继续使用 `oneshot.live_streaming` 作为曝光输入;
- `n_scene_red_telephone` 的“等电话亭自己响”继续使用 `know.phone_called_1987` 作为等待系统来电输入;
- `n_landmark_picker` 新增 `[回访] 不选地标,先让记录表判读你的路线。`,根据上述行为或跳过巡逻解锁;
- `[回访]` 会写入 `route.behavior_self_audit`,并被地图、B3、评价室、清晨继续读取;
- 这一层不是单纯旁白,而是“行为 -> 状态 -> 新选择 -> 后续反馈”的闭环。
