# TASK: 正式剧本深度与广度补强 Pass 9

版本: v1.0
状态: Done
创建时间: 2026-05-09
关联:
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/architecture/ADR-010-sandbox-topology-contract.md`
- `stories/hangzhou_yebanbaoan/tree.json`
- GitHub Milestone: `v7 剧本深度与广度补强`
- GitHub Issue: `#39`

---

## 0. 背景

Pass 1-8 已经让杭州正式树从“不可玩节点集合”推进到“可审计沙盒”:

- `tools/audit_all.sh` 通过;
- `audit_sandbox` 显示 145 节点、11 地标、10 工具节点、9 个 stay 自循环工具、14 个反应 variant 节点;
- `audit_playability` 已保证正式树可玩闭环和 145/145 presentation 覆盖;
- NPC 关系账本已经能回收曝光、删痕、审判、命名死者等行为。

但这仍不等于达标的 galgame / 视觉小说体验。当前坏味道是:

1. **深度不够**:部分支线节点像功能按钮,关键选择没有形成足够长的心理/因果链;
2. **广度不够**:林某 1985 线虽在 `characters` 注册,但默认路径覆盖里仍像孤立前传;
3. **演出不够可见**:JSON 中有 `presentation`,但玩家主要仍在读文本,关键镜头/转场意图密度不足;
4. **指标太松**:ADR-010 只证明“有沙盒骨架”,不能证明“剧本厚”。

本任务的目标是把“剧本厚度”变成可开发、可审计、可回归的最低标准。

---

## 1. 目标 / 非目标

### 目标

- [x] 建立剧本深度/广度审计,把节点数、结局数、最短结局路径、薄节点比例、地标层数、工具复访、variant 密度、presentation 意图覆盖转成报告;
- [x] 让林某 1985 线成为正式可达内容,至少能从角色入口游玩,并能被主周目回声入口提示;
- [x] 补强林某线的沙盒广度:4 个 1985 地标不能只是四个选择按钮,要有互相影响的债务/证据/人物关系;
- [x] 补强 G-273 主线关键地标的深度:至少 3 个地标新增“前置行为 → 当前节点 → 终局/回访”因果回收;
- [x] 增加 VN 体验密度:新增/强化关键节点的 `camera / cg_intent / transition_intent`,并让审计报告暴露覆盖率;
- [x] 新增自动化测试,防止后续把 Pass 9 的深度/广度退回去。

### 非目标

- 不新增 DB schema;
- 不把开放沙盒改成线性章节;
- 不新增真实图片 / 音频资产;
- 不引入复杂好感度系统;
- 不用 env heuristic 硬凹生成深度;
- 不把 `presentation` 当真实资源加载系统来做。

---

## 2. 当前基线

从 2026-05-09 当前 `main` 基线看:

- 总节点:145;
- 结局节点:21;
- `audit_sandbox`:通过;
- picker hub:3;
- landmark_map 地标:11;
- 工具节点:10;
- stay 自循环工具:9;
- 反应 variant 节点:14;
- presentation 覆盖:145/145;
- `path_explorer` 默认 start 覆盖:118/145;
- 默认 start 下未访问节点:27,主要是 `linmou_1985` 前传线;
- variant 触发覆盖:150/319(47.0%);
- 孤立 require key:3 个。

判断:这不是“不能玩”,而是“厚度没达标”。ADR-010 的最低沙盒骨架已经过线,Pass 9 要补的是内容密度和体验密度。

---

## 3. 切入点

### 3.1 剧本数据

- `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
  - 主地图、传闻索引、主角状态回收、晨湖收束;
- `stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json`
  - 林某 1985 前传线,当前是广度短板;
- `stories/hangzhou_yebanbaoan/_fragment_v7_landmark_s3.json`
  - 铜锈侧脸与林某/红衣女孩关系,适合承接 1985 回声;
- `stories/hangzhou_yebanbaoan/_fragment_v7_landmark_s4.json`
  - 羊血弄与“替死/签名/屠宰”主题,适合承接林某账本;
- `stories/hangzhou_yebanbaoan/_fragment_v7_landmark_s5.json`
  - 叶某与 1991 儿童线,适合承接“父亲/签名/替答到”主题。

### 3.2 工具与测试

- 新增 `tools/audit_script_depth.py`;
- 新增 `tests/test_audit_script_depth.py`;
- 更新 `tools/audit_all.sh`;
- 更新 `tools/run_all_tests.py`;
- 更新 `stories/hangzhou_yebanbaoan/README.md`。

---

## 4. 里程碑

- [x] M1: 新建 Task、Milestone、Issue;
- [x] M2: 新增剧本深度/广度审计工具与测试;
- [x] M3: 补强林某 1985 可达性与 4 地标互相回收;
- [x] M4: 补强 G-273 至少 3 个关键地标的跨地标因果回收;
- [x] M5: 增加关键节点 VN 演出意图覆盖,并让审计报告输出覆盖率;
- [x] M6: 合并 fragments,跑全量审计与统一测试;
- [x] M7: 团队评审、Task/Issue 回写、PR 创建。

---

## 5. 验收标准

- `tools/audit_script_depth.py stories/hangzhou_yebanbaoan/tree.json` 通过;
- 正式树节点数不得低于 160;
- 林某线必须从 `characters.linmou_1985.start_node` 可玩,且在深度审计里单独计入;
- 林某线至少 4 个地标、4 个结局、每个地标至少 1 个复访/回收 variant;
- G-273 主线至少 3 个地标新增跨地标或跨角色回收 variant;
- `camera / cg_intent / transition_intent` 覆盖的关键节点数量不得低于 30;
- 不新增悬空 next / 非结局死路 / 未声明 ending_type;
- `bash tools/audit_all.sh` 通过;
- `.venv/bin/python tools/run_all_tests.py` 通过。

---

## 6. 测试计划

- [x] `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json >/dev/null`
- [x] `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json >/dev/null`
- [x] `python3 tools/merge_fragments.py`
- [x] `python3 tools/audit_script_depth.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `python3 tools/audit_sandbox.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json`
- [x] `bash tools/audit_all.sh`
- [x] `.venv/bin/python -m pytest tests/test_audit_script_depth.py -q`
- [x] `.venv/bin/python tools/run_all_tests.py`

---

## 7. 执行记录

### 2026-05-09

- 创建 Pass 9 任务,正式把“剧本深度/广度不达标”从主观反馈转成可验收任务;
- 当前基线确认:结构闭环已经过线,真正问题是内容密度、林某线入口、关键地标因果回收和 VN 演出意图覆盖。

### 2026-05-09 完成记录

- 新增 `tools/audit_script_depth.py` 和 `tests/test_audit_script_depth.py`,接入 `tools/audit_all.sh` 与统一测试;
- 正式树从 145 节点提升到 160 节点;
- 林某 1985 线新增 15 个深度节点:
  - 算盘房:第 13 行补名;
  - 锅炉房:烧毁调拨单与张某纸灰;
  - 档案室:1972 入职册与替死空格;
  - 锦带桥凉亭:张某解释空格机制;
  - 投湖前:四地点证据交叉确认。
- 林某正式投湖前需要四地标都走过,最短结局路径从 3 提升到 5;
- 林某 4 个地标全部新增复访 / 回收 variant;
- G-273 主线 S3 / S4 / S5 新增 `E_LINMOU_*` 前传结局回声;
- 关键演出意图节点从 21 提升到 32;
- `bash tools/audit_all.sh` 通过;
- `.venv/bin/python tools/run_all_tests.py` 7/7 通过。
