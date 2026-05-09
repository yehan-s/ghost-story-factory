# TASK: 正式剧本主角体验与 VN 演出 Pass 4

版本: v1.0
状态: Done
关联:
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS1.md`
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS2.md`
- `docs/tasks/TASK_SCRIPT_SANDBOX_PASS3.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- GitHub Issue: `#25`

---

## 0. 背景

前三轮已经把正式剧本从“节点集合”推进到“群像会回收玩家选择”。

但主角赵某仍有坏味道:

- 入口更像任务派发,不像玩家正在进入一个人的身体;
- 赵某的生活压力、羞耻感、求生欲和被 G-273 工号吞掉的过程不够连续;
- 地图节点像菜单,缺少从更衣室到城市夜景的镜头过渡;
- presentation 字段已有,但关键节点没有足够明确的背景 / 音效 / 转场意图;
- 结局会回收群像,但对“赵某到底变成了谁”回收还不够强。

本任务做一次主角体验和 VN 演出补强。原则是不改玩法、不改 DB schema、不新增真实素材,只把已有正式树写得更像可玩的视觉小说。

---

## 1. 目标 / 非目标

### 目标

- [x] 重写 `n_intro`,让赵某从“工号”变成有生活压力和身体感的主角;
- [x] 强化 `n_briefing`,把简报写成第一次可感知的“游戏规则压迫”;
- [x] 强化 `n_landmark_picker`,让地图节点承接前一选择和当前状态,而不是只列目的地;
- [x] 给入口 / 简报 / 地图 / 清晨收束等关键节点补明确 `presentation`;
- [x] 在清晨收束与核心结局里回收赵某的身份变化,让玩家看到自己如何被这夜班改写;
- [x] 保持开放沙盒结构,不锁死地标顺序,不新增大系统。

### 非目标

- 不新增真实图片 / 音频素材;
- 不新增立绘系统;
- 不改 CLI 渲染器;
- 不改 DB schema;
- 不新增独立主角属性系统;
- 不把地图改成固定线性章节。

---

## 2. 切入点

- `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
  - `n_intro`:主角生活压力、工牌身体感、第一批选择的心理代价;
  - `n_briefing`:规则压迫、空衣柜、前任痕迹、从更衣室到地图的转场;
  - `n_landmark_picker`:根据 `arc.rent_pressure` / `oneshot.defied_token` / `oneshot.contacted_predecessor` 等既有状态补主角变体;
  - `n_scene_morning_lakeside`:根据主角一路选择给清晨收束更强的自我认知;
  - `n_end_true` / `n_end_truth` / `n_end_data` / `n_end_neutral`:补赵某身份弧线的终局回收。
- `docs/INDEX.md`:登记本任务。

---

## 3. 里程碑

- [x] M1: Task 与 GitHub Issue 创建完成;
- [x] M2: 入口、简报、地图节点完成主角体验重写;
- [x] M3: 关键节点补 `presentation` 覆盖,明确背景 / 音效 / 转场;
- [x] M4: 清晨收束与核心结局补赵某身份回收;
- [x] M5: 合并正式 `tree.json`,执行审计与测试;
- [x] M6: 回写 Task / Issue 并提交。

---

## 4. 测试计划

- [x] `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
- [x] `python3 tools/merge_fragments.py`
- [x] `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `bash tools/audit_all.sh`
- [x] `python3 tools/run_all_tests.py`

---

## 6. 已完成改动

### 6.1 主角入口重写

- `n_intro` 从“工号介绍”改为“赵某带着房租压力进入夜班”;
- 房东消息、手机电量、工资焦虑和工牌贴上制服的身体感,共同建立玩家第一分钟代入;
- 保留原有四个入口选择和既有 flag,不新增状态系统。

### 6.2 简报和地图转场

- `n_briefing` 增加灯管、影子、第 272 号储物柜、旧雨衣和 7 个空格的压迫;
- `n_landmark_picker` 增加基于 `oneshot.contacted_predecessor` / `oneshot.defied_token` / `arc.rent_pressure` 的状态化转场;
- 地图选择文案从纯地点列表改成带动作与镜头意图的 VN 选择。

### 6.3 演出字段补强

- 入口、简报、地图、清晨湖滨增加明确 `presentation`;
- 使用已有 text fallback 资产: `bg_hangzhou_night` / `bg_locker_room` / `bg_map` / `bg_lakeside`,未新增未登记资产引用;
- SFX 增加心跳、翻页、对讲机、湖水的节点级意图。

### 6.4 主角身份终局回收

- `n_scene_morning_lakeside` 增加工牌被献出、撕小票、联系前任等路径的主角回收;
- `n_end_true` 增加“赵某归还给赵某”的真实生活回收;
- `n_end_truth` 增加“公开你为什么不得不上这班”的前任回收,避免真相线只像资料上传。

## 7. 验收结果

- `python3 -m json.tool` 通过;
- `python3 tools/merge_fragments.py` 通过,正式 `tree.json` 已重建;
- `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json` 通过;
- `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json` 无 unreachable variant / 无 undifferentiated revisit nodes;
- `bash tools/audit_all.sh` 通过,仅保留既有 9 个孤儿道具 warning;
- `python3 tools/run_all_tests.py` 6/6 全部通过。

---

## 5. 验收标准

- 玩家第一分钟能明确感到:
  - 赵某不是空壳主角;
  - G-273 是正在吞噬人的工号;
  - 地图不是菜单,而是一张会读玩家状态的夜班契约;
  - 视觉小说 presentation 信息能表达镜头切换意图;
- 不新增未登记资产引用;
- 不新增孤儿节点 / 死路 / 高重复选项问题;
- 全量测试通过。
