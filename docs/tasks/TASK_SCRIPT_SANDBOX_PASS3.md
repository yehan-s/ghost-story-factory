# TASK: 正式剧本群像深挖 Pass 3

版本: v1.0
状态: Done
关联:
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS1.md`
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS2.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- GitHub Issue: `#24`

---

## 0. 背景

Pass 2 已经把林晓燕、林志诚、赵某、G-272 的关系压进终局。

但正式剧本仍有一个坏味道:部分角色还像功能按钮。

- 叶某目前能被安抚,也能在结局里被提到,但她对玩家后续玩法的主动影响还不够;
- 7 个工人 / 巡夜员群像目前更像“7 顶帽子”而不是 7 个曾经活过的人;
- B3 / True / Truth / Data 结局已经回收名字,但还可以更明确地回收“你怎么对待他们”。

本任务继续直接修改正式 fragment,目标是让群像开始反过来观察玩家。

---

## 1. 目标 / 非目标

### 目标

- [x] 让叶某从“被救者”升级为会提醒、质问、陪伴其他孩子的角色;
- [x] 让 7 个工人 / 巡夜员群像拥有更清晰的“不要替死鬼,要被记名”的集体诉求;
- [x] 在 B3 和终局前增加群像压力,让玩家感到自己带着一群人进门;
- [x] 让 Truth / Data / True 至少 2 类结局根据叶某或 7 工人状态出现更强差异;
- [x] 保持开放沙盒结构,只增加状态化 variant / choice,不锁死地标顺序。

### 非目标

- 不新增大型角色周目;
- 不新增好感度系统;
- 不改 DB schema;
- 不新增真实图片 / 音频素材;
- 不把 S5/S6 改成固定线性章节。

---

## 2. 切入点

- `n_npc_piano_ghost`:叶某根据红衣女孩、七工人、赵某自我牺牲状态改变回应;
- `n_npc_piano_ghost_payoff`:叶某不只送道具,还给玩家一个“不要替我决定”的明确态度;
- `n_s5_grant_leave`:叶某离开后仍能在重访时回声,并指向群像;
- `n_s6_look_down` / `n_s6_listen_engine`:把 7 个工人从数字变成“七个名字等被叫出口”;
- `n_s6_replace_seven`:强化“我们不要你替死,要你记住”的诉求;
- `n_scene_b3_corridor` / `n_s7_arrive`:终局前让叶某和 7 工人同时施压;
- `n_end_true` / `n_end_truth` / `n_end_data`:按群像状态增加结局差异。

---

## 3. 已完成改动

### 3.1 叶某成为群像触发器

- `n_s5_grant_leave` 增加 `arc.seven_returned` 回声:叶某用“点名时要等本人答到”反向影响 S6;
- `n_s6_look_down` / `n_s6_listen_engine` / `n_s6_replace_seven` 读取 `oneshot.s5_freed_yeh`,让 203 的结案影响 1986 沉船;
- 叶某不再只是被救者,而是把“不要替答到”这个主题带给其他未结者。

### 3.2 7 工人从数字变成群像

- `n_npc_helmet_workers` 增加叶某 + 7 工人组合 variant,明确他们在等“本人答到”;
- `n_npc_helmet_workers_payoff` 增加两条回收:
  - 叶某已下班时,7 工人自己答到;
  - 持有 `武林门 7 人录音` 时,7 工人开始报名字;
- `n_s6_replace_seven` 强化“不要替死鬼,要被记住”的诉求。

### 3.3 B3 与结局回收

- `n_scene_b3_corridor` 增加叶某 + 7 工人同场压力;
- `n_s7_arrive` 增加终局门前点名回声;
- `n_end_true` 增加叶某 / 7 工人 / 林志诚三线各自完成而非被统一替代的变体;
- `n_end_truth` 增加“他们不是材料”的公开档案变体;
- `n_end_data` 增加玩家同时接下叶某循环和第 8 工人循环的坏回收。

### 3.4 小型状态债修复

- `n_s6_look_down` 抢 7 顶帽子路径现在会 set `oneshot.s6_grab_seven`;
- 这修复了 `n_end_bad_drown` 读取该状态但此前无人写入的问题;
- 未新增新 flag,只补齐既有状态的写端。

## 4. 验收结果

- [x] `python3 -m json.tool` 校验已修改 fragment;
- [x] `python3 tools/merge_fragments.py` 能重建正式 `tree.json`;
- [x] `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json` 通过;
- [x] `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json` 不产生新的 `undifferentiated_revisit_nodes`;
- [x] `bash tools/audit_all.sh` 通过;
- [x] `python3 tools/run_all_tests.py` 通过;
- [x] 文档和 GitHub issue 回写。

## 5. 后续边界

- Pass 3 没有新增大型角色周目,只是补正式树里的群像深度;
- 下一步如果继续写剧本,优先处理“清洁工 / 论坛围观者 / 评价室”这三个仍偏功能性的角色;
- 工具债仍是 9 个孤儿道具描述和 `audit_state` 历史噪音分级,不应混进下一轮纯剧本任务。
