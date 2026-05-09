# TASK: VN 演出意图契约 Pass 7

版本: v0.1
状态: Done
关联:
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/tasks/TASK_SCRIPT_PROTAGONIST_UX_PASS4.md`
- `docs/tasks/TASK_SCRIPT_BEHAVIOR_NPC_PASS5.md`
- `docs/tasks/TASK_GAMETREE_V1.md`
- `docs/team-reviews/2026-05-09-vn-presentation-contract-pass7.md`
- GitHub Issue: `#34`

---

## 0. 背景

正式树已经做到 145/145 节点有 `presentation`,但很多关键节点仍是默认补齐:

- 有背景 / BGM / 转场,但没有镜头意图;
- 有 `cg_unlock`,但长期为空,没有未来 CG 替换语义;
- 关键结局和核心 NPC 仍靠通用 `bg_ending` / `fade_to_black` 表达。

这会让文本已经接近 VN,演出契约却仍像“纯文本菜单加字段”。

---

## 1. 目标 / 非目标

### 目标

- [x] 第一批补齐关键节点的 `camera / cg_intent / transition_intent`;
- [x] 增加审计,让正式树关键节点缺演出意图时产生可见 warning;
- [x] 不要求真实图片 / 音频素材立刻存在;
- [x] 重建正式 `tree.json`;
- [x] 跑 `audit_all` 与统一测试;
- [x] 回写 Issue #34 和 PR。

### 非目标

- 不新增真实 CG 图片;
- 不改 CLI / TUI 渲染;
- 不改 DB schema;
- 不把所有 145 节点一次性补完整;
- 不改变剧情跳转和结局条件。

---

## 2. 里程碑

### M1: 同步事务启动

- [x] 创建 GitHub Issue #34;
- [x] 创建本 Task;
- [x] 创建团队评审报告并更新 INDEX。

### M2: 第一批关键演出意图

- [x] 工具 / 场景:遗失档案、红色电话亭、B3、清晨湖滨;
- [x] 核心 NPC:红衣女孩、8 棺自己;
- [x] 主结局:True / Truth / Bad 1987 / Bad Drown / Neutral;
- [x] 已补过的 Data / Broadcast / Hidden 保持不回退。

### M3: 审计锁定

- [x] `tools/audit_playability.py` 检查关键节点的演出意图字段;
- [x] `tests/test_audit_playability.py` 覆盖缺失 warning;
- [x] 正式杭州树不产生演出意图 warning。

### M4: 验收

- [x] `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`;
- [x] `python3 tools/merge_fragments.py`;
- [x] `bash tools/audit_all.sh`;
- [x] `.venv/bin/python tools/run_all_tests.py`;
- [x] Issue / PR 回写。

---

## 3. 代码入口

- `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
- `stories/hangzhou_yebanbaoan/tree.json`
- `tools/audit_playability.py`
- `tests/test_audit_playability.py`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`

---

## 4. 验收标准

- 关键节点有稳定 `camera / cg_intent / transition_intent`;
- 审计能发现关键节点缺演出意图;
- 正式树仍 145/145 可达、145/145 有 presentation;
- 不新增 DB schema;
- 全量测试通过。

---

## 5. 完成记录

- `n_intro` / `n_briefing` / `n_landmark_picker` 补入口、简报、地图的镜头与转场意图;
- `n_scene_lost_archive` / `n_scene_red_telephone` / `n_scene_b3_corridor` / `n_scene_morning_lakeside` 补工具和终局前场景演出意图;
- `n_npc_red_dress_girl` / `n_npc_eight_self` 补核心 NPC 的画面意图;
- `n_end_true` / `n_end_truth` / `n_end_bad_1987` / `n_end_bad_drown` / `n_end_neutral` 补主结局镜头语义;
- `tools/audit_playability.py` 新增关键节点演出意图 warning;
- `tests/test_audit_playability.py` 新增缺失演出意图测试;
- 正式树重建后 `audit_playability` 显示 145/145 演出节点,无错误 / 无警告。
