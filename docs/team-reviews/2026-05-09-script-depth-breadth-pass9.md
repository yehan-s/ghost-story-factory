# 团队评审: Pass 9 正式剧本深度与广度补强

日期: 2026-05-09
任务: `TASK_SCRIPT_DEPTH_BREADTH_PASS9.md`
Issue: `#39`
决议: 修改后放行

---

## 1. 评审结论

Pass 9 值得做。当前杭州树已经可玩,但“可玩”和“像视觉小说一样有厚度”不是同一件事。

ADR-010 的沙盒骨架审计只能证明没有退回死剧本,不能证明普通场景、前传线、复访反馈和演出意图达标。本轮新增 `tools/audit_script_depth.py`,把这类问题正式纳入机器红线。

---

## 2. 角色意见

### Chief Editor

- 原问题成立:145 节点和 21 结局不能自动等于剧本厚;
- 林某 1985 线最短 3 步结局是最大坏味道,必须先加因果链;
- 新增 15 个林某节点后,四地标从“选态度”变成“查证据 / 背债 / 决定死法”。

### State Architect

- 本轮没有新增 DB schema,只复用 `flags`、`ending_seen` 和现有角色 start_node;
- 林某投湖前增加 `all_of` 条件,要求四地标都走过后才开放正式投湖过场;
- 风险:旧工具对多角色 start 仍有少量“孤儿”口径,但 `audit_playability` 已把 `characters.start_node` 纳入可达。

### Meta-Game Designer

- 林某线不应只服务自己,必须能回灌 G-273 主周目;
- 本轮 S3 / S4 / S5 新增 `E_LINMOU_*` 回声,能让前传结局影响主线地标叙述;
- 后续应继续把前传通关结果推到结局或档案视图。

### UX Designer

- `presentation` 145/145 覆盖不是充分条件,因为默认补齐会掩盖“没设计过镜头”;
- 本轮把演出意图节点从 21 提到 32,并由 `audit_script_depth` 锁住最低数;
- 后续应让播放器实际消费 presentation,否则仍是 JSON 好看、玩家看不到。

### Lore Keeper

- 1985 线新增内容继续围绕 26 联签、第 13 行、替死空格、锦带桥投湖;
- S3 / S4 / S5 的回声没有改写既有 lore,只让既有年代互相照面;
- 未新增禁用术语。

### Topology Designer

- 新增节点没有把沙盒改成线性章节;
- 林某线仍以 picker 为中心,但正式投湖前必须走完四处地点;
- G-273 主线地标结构未被破坏。

### QA / Path Tester

- 新审计基线:
  - 节点 160;
  - 演出意图节点 32;
  - 林某可达节点 42;
  - 林某最短结局路径 5;
  - 林某 4 地标全部有 variant;
  - G-273 林某回声节点 7。
- `audit_script_depth`、`audit_sandbox`、`audit_playability` 已通过。

---

## 3. 放行条件

- `tools/audit_script_depth.py stories/hangzhou_yebanbaoan/tree.json` 必须通过;
- `bash tools/audit_all.sh` 必须通过;
- `.venv/bin/python tools/run_all_tests.py` 必须通过;
- Task 与 Issue #39 要回写实际指标。
