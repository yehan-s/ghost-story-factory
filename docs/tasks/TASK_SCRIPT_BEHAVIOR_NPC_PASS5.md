# TASK: 正式剧本行为反馈与功能 NPC 人格化 Pass 5

版本: v1.0
状态: Done
关联:
- `docs/tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- GitHub Issue: `#26`

---

## 0. 背景

Pass 4 已经把赵某入口、地图转场、晨湖和核心结局补成了更像视觉小说的体验。

但正式剧本还有一个坏味道:清洁工、论坛围观者、评价室仍然偏功能按钮。

- 论坛像曝光入口,还不像会诱导、索取、误读玩家的群体;
- 清洁工像删除工具,还不像有自己目的的“空白维护者”;
- 评价室像结局权限检查器,还不像会根据玩家行为姿态给出审判;
- 玩家行为画像已经有素材,但没有集中回收:救人、取证、曝光、替班、拒绝规则、生活压力。

本任务不新增数值系统,只复用既有 flag / inv / puzzle,让三类系统 NPC 反过来观察玩家。

---

## 1. 目标 / 非目标

### 目标

- [x] 强化 `n_npc_forum_lurkers`,让论坛不只是流量按钮,而是会消费玩家真相的“围观者群体”;
- [x] 强化 `n_npc_cleaner_null`,让清洁工成为“删除名字 / 删除证据 / 删除自我”的人格化存在;
- [x] 强化 `n_npc_evaluator_chair` 和 `n_scene_evaluator_room`,让评价室读出玩家行为画像;
- [x] 给这些关键节点补明确 `presentation` 覆盖,让画面、音效、转场意图稳定;
- [x] 在 Data / Broadcast / Hidden 等结局里补系统 NPC 对玩家姿态的回收;
- [x] 保持开放沙盒结构,不锁死地标顺序。

### 非目标

- 不新增好感度 / 行为画像数值系统;
- 不改 DB schema;
- 不新增真实图片 / 音频素材;
- 不改 CLI 渲染器;
- 不新增大型支线。

---

## 2. 复用状态

本任务优先复用:

- 曝光 / 取证: `oneshot.posted_photo`, `oneshot.live_streaming`, `arc.all_archives_photoed`;
- 拒绝规则: `oneshot.defied_token`, `arc.s3_refused_h1987`;
- 救人 / 记名: `oneshot.s5_freed_yeh`, `arc.seven_returned`, `arc.named_the_dead`;
- 替班 / 牺牲: `oneshot.sacrificed_id`, `arc.became_judge`, `arc.s6_replaced_seven`;
- 现实压力: `arc.rent_pressure`;
- 已有道具: `前任电话号码`, `工牌 G-273`, `武林门 7 人录音`。

---

## 3. 里程碑

- [x] M1: Task 与 GitHub Issue 创建完成;
- [x] M2: 论坛围观者人格化完成;
- [x] M3: 不存在的清洁工人格化完成;
- [x] M4: 评价室行为画像回收完成;
- [x] M5: Data / Broadcast / Hidden 等结局补系统 NPC 回收;
- [x] M6: 合并正式 `tree.json`,执行审计与测试;
- [x] M7: 回写 Task / Issue 并提交。

---

## 4. 测试计划

- [x] `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
- [x] `python3 tools/merge_fragments.py`
- [x] `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `bash tools/audit_all.sh`
- [x] `python3 tools/run_all_tests.py`

---

## 5. 验收标准

- 玩家至少在 3 个节点看到自己的玩法姿态被反咬;
- 论坛、清洁工、评价室不再只是工具节点;
- 不新增未登记资产引用;
- 不新增孤儿节点 / 死路 / 不可达 variant;
- 全量测试通过。

---

## 6. 已完成改动

### 6.1 论坛从流量按钮变成围观机器

- `n_npc_forum_lurkers` 增加整套档案公开、直播、S1/S4 爆款组合的反应;
- 论坛会把名字剪成标题,让玩家看到“公开真相”和“守住名字”不是一回事;
- “再发一帖”从调试式 stay 循环改为一次性更正帖,避免刷状态感。

### 6.2 清洁工成为身份注销者

- `n_npc_cleaner_null` 增加直播回放与整套档案照片反应;
- 清洁工不再只是吓人,而是负责把证据改名成重复文件、把名字擦成马赛克;
- 选择文案从“删物品”改为“删除与前任之间最危险的联系”,和移除 `前任电话号码` 的效果对齐。

### 6.3 评价室从发章器变成案由系统

- `n_npc_evaluator_chair` 的 variant 从“授予称号”改成“案由 / 证据 / 风险”;
- 修复“不去。继续巡逻。”仍设置 `arc.got_judge_seal` 的错误因果;
- `n_scene_evaluator_room` 增加无指纹未注销、整套档案取证的行为画像回收。

### 6.4 结局回收

- `n_end_data` 增加直播数据化后“只留下 G-273,无人记得赵某”的回收;
- `n_end_broadcast` 增加公开档案被弹幕二次消费的回收;
- `n_end_hidden` 增加无指纹者坐上判官椅后的职位吞人回收。

### 6.5 最小 VN 演出意图字段

- 在本轮触及的关键节点补 `camera` / `cg_intent` / `transition_intent`;
- 这些字段暂不要求运行时识别,用于先把未来 CG / 镜头 / 转场语义写进源数据;
- 后续可基于这些字段增加轻量审计工具,但本轮不扩大工具范围。

## 7. 验收结果

- `python3 -m json.tool` 通过;
- `python3 tools/merge_fragments.py` 通过,正式 `tree.json` 已重建;
- `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json` 通过;
- `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json` 无 unreachable variant / 无 undifferentiated revisit nodes;
- `bash tools/audit_all.sh` 通过,仅保留既有 9 个孤儿道具 warning;
- `python3 tools/run_all_tests.py` 6/6 全部通过。
