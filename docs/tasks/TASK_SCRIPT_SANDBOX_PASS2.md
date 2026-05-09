# TASK: 正式剧本人物弧线深挖 Pass 2

版本: v1.0
状态: Done
关联:
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS1.md`
- `docs/tasks/TASK_GAMETREE_V1.md`
- GitHub Issue: `#21`

---

## 0. 背景

Pass 1 已经把正式剧本从“地标散点”推进到“物件和地点互相承认”。

但这还不够。视觉小说 / galgame 的厚度不靠更多灵异名词堆出来,而靠角色关系反复推进:

- 林晓燕不能只是 1996 货梯谜题的钥匙;
- 林志诚不能只是 1985 账本和父亲身份的标签;
- G-272 不能只是设定讲解员;
- 赵某不能只是玩家摄像机;
- 终局不能只是系统把条件结算成结局。

本任务继续直接修改正式 fragment,重点补人物弧线和终局前压力。

---

## 1. 目标 / 非目标

### 目标

- [x] 建立林晓燕三段式弧线:害怕带路 -> 信任赵某 -> 主动面对父亲;
- [x] 让林志诚在 S1/S3/S7/True End 中以“父亲和欠债者”双重身份回响;
- [x] 让 G-272 在二周目和终局前不再只讲设定,而是表达“替班疲惫”和对赵某的警告;
- [x] 给赵某增加持续的现实压力和道德压力,让他不是无人格摄像机;
- [x] 让终局前选择回收角色关系,而不是只回收道具 checklist;
- [x] 保持开放沙盒结构,新增文本和选择不能强制固定地标顺序。

### 非目标

- 不新增图形 VN 客户端;
- 不改 DB schema;
- 不引入外部素材;
- 不把所有地标改成线性章节;
- 不新增一套好感度系统。

---

## 2. 第一批切入点

- `n_intro`:补赵某现实压力后的后续回声;
- `n_npc_predecessor_voice`:补二周目 / 数据结局后的 G-272 反应;
- `n_npc_red_dress_girl`:补林晓燕信任后第二、第三层反应,让她逐步从“问路”变成“选择面对”;
- `n_npc_drowned_official`:补林志诚对“女儿林晓燕”的承认;
- `n_s1_close_touch` / `n_s3_examine_face`:让林志诚父亲身份在早期地标被暗示;
- `n_s7_arrive`:终局门前按角色关系改变文本;
- `n_scene_27th_floor_corridor`:补父女重逢前的压迫;
- `n_end_true` / `n_end_data` / `n_end_neutral`:回收赵某和 G-272 的选择代价。

---

## 3. 已完成改动

### 3.1 林晓燕弧线

- `n_npc_red_dress_girl` 增加信任后的二层反应:她不再只问路,而是能说出自己是否要走进 27 楼;
- `n_scene_27th_floor_corridor` 增加她在门前练习叫“爸爸”的文本;
- `n_scene_27th_floor_corridor` 增加“让林晓燕先敲门,你站在她身后”的终局选择,把 True End 从道具结算推进到关系选择。

### 3.2 林志诚父亲 / 欠债者双重身份

- `n_npc_drowned_official` 增加听到“林晓燕”后的承认反应;
- `n_s1_close_touch` 用雨衣和水迹提前暗示“晓燕”这个名字;
- `n_s3_examine_face` 用旧照片把 1985 西湖账目和 1996 货梯事故接起来;
- `n_end_true` 回收父女门前重逢,并让赵某记录“只负责把门打开”,避免替角色做决定。

### 3.3 G-272 与赵某压力

- `n_npc_predecessor_voice` 增加数据结局后的二周目警告:不要再把工牌交出去,不要让林晓燕独自去 27 楼;
- `n_scene_b3_corridor` 增加赵某现实压力回响:租金、工资、离职压力被 B3 电视墙读取;
- `n_end_data` 增加数据化后的现实断联:赵某还能收到催租语音,但已经不能回复。

### 3.4 开放沙盒保持

- 新增选择只挂在已有节点和已有 flag 上,没有新增强制线性章节;
- 关键推进仍依赖 `arc.redgirl_trusts_zhao`、`know.claimed_linmou`、`know.redgirl_wants_father` 等状态组合;
- 没有修改 DB schema、运行时接口、地标访问顺序。

## 4. 验收结果

- [x] `python3 -m json.tool` 校验已修改 fragment;
- [x] `python3 tools/merge_fragments.py` 能重建正式 `tree.json`;
- [x] `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json` 通过;
- [x] `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json` 不产生新的 `undifferentiated_revisit_nodes`;
- [x] `bash tools/audit_all.sh` 通过;
- [x] `python3 tools/run_all_tests.py` 通过;
- [x] 文档和 GitHub issue 回写。

## 5. 后续边界

- Pass 2 已经把“人物关系”压进终局,但还没有增加新的大型角色线;
- 后续如果继续深挖,优先补 `叶某` 和 `巡夜员群像`,不要再堆孤立物件谜题;
- 如果要再加系统,应该先做“正式剧情关系审计器”,而不是手工凭感觉检查文本。
