# TASK: 正式剧本薄节点压缩 Pass 18

版本: v0.2
状态: Done
创建时间: 2026-05-10
关联:
- GitHub Issue: `#57`
- GitHub Milestone: `v7 剧本薄节点压缩`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/tasks/TASK_SCRIPT_DEPTH_BREADTH_PASS9.md`
- `docs/team-reviews/2026-05-10-script-thin-nodes-pass18.md`

---

## 0. 用户质疑记录

用户要求继续深挖剧本,不能停留在 TUI 或结构闭环。

这个质疑成立。Pass 17 修掉了终局菜单、单行路和主角履历泄漏,但 `audit_script_depth` 仍报告 50 个薄节点。薄节点集中在两类地方:

- 林某 1985 线的证据链节点:很多是 120-180 字的剧情提纲;
- G-273 前半夜行动节点:S1-S6 的取证、逃避、触碰、回访节点,选择多但正文短。

【核心判断】
✅ 值得做:这是“视觉小说厚度”的真实问题。

【关键洞察】
- 数据结构:薄节点不是节点数问题,而是“玩家做了事,场景没有足够反馈”。
- 复杂度:先压缩关键薄节点,不要盲目扩写全树。
- 风险点:不能把每个节点都写成长段独白;要补动作、感官、后果,而不是堆设定。

---

## 1. 目标

- 将 `audit_script_depth` 的薄节点数从 50 压到 31;
- 优先补强林某审计链与 G-273 前半夜行动节点;
- 增加审计红线,防止关键薄节点回退;
- 保持开放沙盒,不新增 DB schema,不改玩法主结构;
- 合并 fragments 重建正式 `tree.json`。

---

## 2. 非目标

- 不新增真实图片 / 音频资产;
- 不重写全部地标;
- 不把林某线改成线性长篇;
- 不把选择反馈改成数值优化表格;
- 不改 CLI 作为本轮重点。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 创建本 Task;
- 创建 Issue `#57` 和 milestone `v7 剧本薄节点压缩`;
- 新增团队评审报告;
- 更新索引与下一阶段目标。

### M2: 林某线薄节点补强

状态: Done

- 修改 `stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json`;
- 优先补 `n_l1985_*_audit_*`、`n_l1985_*_registry_*`、`n_l1985_*_line13_*`;
- 让证据节点从“发现一条信息”变成“证据改变林某行动判断”。

### M3: G-273 前半夜行动节点补强

状态: Done

- 修改 S1-S6 fragment 中的关键薄节点;
- 优先补取证、擦除、拒绝、接受、回访动作;
- 强化赵某的穷、怕、工牌压力和“我不是摄像机”的选择后果。

### M4: 审计与测试

状态: Done

- 在 `tools/audit_script_depth.py` 中增加薄节点上限检查;
- 将正式树薄节点上限收紧到 31;
- 新增 / 更新测试,防止薄节点回退。

### M5: 验证与同步

状态: Done

- 执行:
  - `python3 -m json.tool <changed-fragment>`;
  - `python3 tools/merge_fragments.py`;
  - `bash tools/audit_all.sh`;
  - `.venv/bin/python tools/run_all_tests.py`;
  - `git diff --check`;
- 测试污染 `database/ghost_stories_test.db` 时恢复;
- 回写 Issue / PR。

---

## 4. 代码入口

- 林某线: `stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json`
- G-273 地标: `stories/hangzhou_yebanbaoan/_fragment_v7_landmark_s*.json`
- 正式树: `stories/hangzhou_yebanbaoan/tree.json`
- 审计: `tools/audit_script_depth.py`
- 测试: `tests/test_audit_script_depth.py`

---

## 5. 完成记录

- 2026-05-10: 确认病根:正式树通过可玩性和终局门槛审计,但仍有 50 个薄节点,大量选择仍像提纲跳转。
- 2026-05-10: 补强林某 1985 入口、算盘房审计链、锅炉房炉灰链、档案室入职册链、凉亭第 13 行链和投湖前交叉核对链。
- 2026-05-10: 补强 G-273 早期高频节点: S1 抄账、S2 擦鞋、S3 拒绝 H 编号、S5 琴凳取证。
- 2026-05-10: `audit_script_depth` 薄节点从 50 降到 31,并把上限 31 写入审计错误;`tests/test_audit_script_depth.py` 扩展到 7 个用例。
- 2026-05-10: 已执行 `json.tool`、`merge_fragments.py`、`audit_script_depth.py`、局部 pytest、`bash tools/audit_all.sh`、`.venv/bin/python tools/run_all_tests.py`、`git diff --check`;测试数据库副作用已恢复。
