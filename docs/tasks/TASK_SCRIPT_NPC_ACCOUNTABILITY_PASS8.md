# TASK: 正式剧本 NPC 关系账本与终局前回咬 Pass 8

版本: v1.0
状态: Done
关联:
- Milestone: `v7 VN 沙盒可玩闭环`
- GitHub Issue: `#36`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/tasks/TASK_SCRIPT_BEHAVIOR_FEEDBACK_PASS6.md`
- `docs/tasks/TASK_VN_PRESENTATION_CONTRACT_PASS7.md`

---

## 0. 背景

Pass 4-7 已经把主角身份、玩家行为画像、工具回访和 VN 演出契约推进到可审计状态。

但正式剧本还有一个核心体验缺口:共享 NPC 仍然更像功能菜单,不是会记账的角色。论坛负责曝光,清洁工负责删除痕迹,评价室负责审判,三者本该构成同一套“身份与责任系统”,现在联系还不够硬。

本轮目标是把玩家在取证、曝光、删痕、等待系统、救人、避险中的选择,提前反咬到论坛 / 清洁工 / 评价室 / B3 / 晨湖,让玩家在终局前看见自己被 NPC 记账。

---

## 1. 目标 / 非目标

### 目标

- [x] 强化 `n_npc_forum_lurkers`:论坛不只是加 PR,而是区分“命名死者”和“把死者剪成素材”;
- [x] 强化 `n_npc_cleaner_null`:清洁工不只是删道具,而是读取直播、照片、无指纹、砸监控等身份痕迹;
- [x] 强化 `n_npc_evaluator_chair` / `n_scene_evaluator_room`:评价室按案由审玩家,不再只像结局按钮房;
- [x] 强化至少 2 个终局前节点对 NPC 账本的回咬,优先 `n_scene_b3_corridor` 与 `n_scene_morning_lakeside`;
- [x] 复用现有 `flags / puzzle / theme / deductions / PR / GR`,不新增 DB schema;
- [x] 重建正式 `tree.json`,并通过全量审计与统一测试。

### 非目标

- 不引入通用好感度系统;
- 不新增真实图片 / 音频资产;
- 不新增数据库 schema;
- 不把开放沙盒改成线性章节;
- 不为每个 NPC 新建独立数值轨道。

---

## 2. 设计约束

### 2.1 状态复用

优先复用这些既有状态:

- 曝光 / 传播: `oneshot.posted_photo`, `oneshot.forum_posted`, `oneshot.live_streaming`, `arc.s1_post_forum`, `oneshot.s4_posted_blood_face`, `arc.all_archives_photoed`;
- 删除 / 身份痕迹: `oneshot.s4_smashed_monitor`, `oneshot.s6_no_fingerprint`, `oneshot.sacrificed_id`;
- 审判 / 案由: `arc.got_judge_seal`, `piece_judge_seal`, `arc.s4_refused_yanggui`, `arc.s3_refused_h1987`, `arc.s6_replaced_seven`, `oneshot.defied_token`;
- 救人与命名: `oneshot.s5_freed_yeh`, `arc.seven_returned`, `arc.redgirl_trusts_zhao`, `arc.named_the_dead`, `know.claimed_linmou`;
- 避险 / 等待系统: `shifts_skipped_min`, `know.phone_called_1987`, `route.behavior_self_audit`;
- 现实压力: `arc.rent_pressure`。

### 2.2 Good Taste 红线

- 新增文本可以多,新增状态必须少;
- 同一节点 `narrative_variants` 不应无限膨胀,优先修改已有 variant 文本和少量补关键 variant;
- 选择效果必须和行为一致,不能出现“不去评价室也拿审判章”这类因果错位;
- 改 fragment 后必须运行 `tools/merge_fragments.py`,以正式 `tree.json` 为验收对象。

---

## 3. 里程碑

### M1: 论坛与清洁工账本

- [x] 论坛区分“更正命名 / 继续直播 / 删帖 / 回 G-272”四种姿态;
- [x] 清洁工读取直播、档案照片、无指纹、砸监控、工牌献祭等痕迹;
- [x] 清洁工选择文本从“删某个道具”升级为“清理某类身份痕迹”。

### M2: 评价室案由化

- [x] `n_npc_evaluator_chair` narrative variants 明确案由,不是通用授章通知;
- [x] `n_scene_evaluator_room` 补充至少 2 条 NPC 账本相关 variant;
- [x] 修正选择文案和 effects 的因果,确保只有真正进入报到才获得 `arc.got_judge_seal`。

### M3: 终局前回咬

- [x] `n_scene_b3_corridor` 新增或强化论坛/清洁工/评价室联动判词;
- [x] `n_scene_morning_lakeside` 新增或强化 NPC 账本回收;
- [x] 至少 3 类玩家姿态能在终局前被 NPC 或系统点名。

### M4: 验收与同步

- [x] 更新团队评审文档;
- [x] 重建 `stories/hangzhou_yebanbaoan/tree.json`;
- [x] `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json >/dev/null`;
- [x] `python3 tools/merge_fragments.py`;
- [x] `bash tools/audit_all.sh`;
- [x] `.venv/bin/python tools/run_all_tests.py`;
- [x] 回写 GitHub Issue 与本 Task。

---

## 4. 验收标准

- 正式树节点数保持稳定或有明确解释;
- `audit_variants` 保持 `undifferentiated_revisit_nodes: []`;
- `audit_playability` 无 error,关键演出意图 warning 不回归;
- 至少 5 个正式节点新增或强化“NPC 账本 / 终局前回咬”文本;
- 不新增 DB schema;
- 不新增未注册资源引用。

---

## 5. 完成记录

本轮完成 Pass 8 最小闭环:

- `n_npc_forum_lurkers` 的“这些不是素材,是名字”现在写入既有 `arc.named_the_dead`;
- `n_npc_cleaner_null` 增加直播 + 命名、工牌献祭后的身份清理反馈;
- `n_npc_evaluator_chair` 与 `n_scene_evaluator_room` 增加论坛更正帖 / 无指纹但仍需签名的案由;
- `n_scene_b3_corridor` 增加论坛、清洁工、评价室三列账本判词;
- `n_scene_morning_lakeside` 增加回看路线 + 命名、无指纹 + 候补判官章的终局前回收;
- 新增 `tests/test_npc_accountability_pass8.py`,并接入 `tools/run_all_tests.py`。

已验证:

- `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json >/dev/null`;
- `python3 tools/merge_fragments.py`;
- `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json`;
- `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json --strict`;
- `bash tools/audit_all.sh`;
- `.venv/bin/python tools/run_all_tests.py`。

结果:

- 正式树节点数保持 `145`;
- 结局节点保持 `21`;
- variants 总数从 `309` 提升到 `319`;
- `undifferentiated_revisit_nodes: []`;
- `audit_playability` 无 error / warning;
- 统一测试 `7/7` 通过。
