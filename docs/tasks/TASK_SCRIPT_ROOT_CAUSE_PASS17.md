# TASK: 正式剧本病根深改 Pass 17

版本: v0.2
状态: Done
创建时间: 2026-05-10
关联:
- GitHub Issue: `#55`
- GitHub Milestone: `v7 剧本病根深改`
- `docs/tasks/TASK_SCRIPT_DEPTH_BREADTH_PASS9.md`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/team-reviews/2026-05-10-script-root-cause-pass17.md`

---

## 0. 用户质疑记录

用户指出:不能只改 TUI,剧本缺陷同样特别大。

这个质疑成立。Pass 9 的审计证明正式树有节点数、演出字段和可达闭环,但没有证明它已经像 galgame / 视觉小说一样“由玩家行为压出结局”。

当前最糟糕的病根不是某段文字短,而是:

- `n_scene_morning_lakeside` 的终局选择像菜单,高阶结局缺少足够 `require`;
- 主角赵某的房租、工牌、记录表压力在开场出现,但终局没有强制读取本轮行为账本;
- 审计指标偏结构,会掩盖“True End 可以被点出来,不是挣出来”的坏味道;
- 正式树局部文本仍残留旧主角履历,会把 G-273 写成 51 岁、有妻儿、做了多年夜班的旧版本主角。

【核心判断】
✅ 值得做:这是正式剧本可玩闭环的根问题。

【关键洞察】
- 数据结构:结局入口必须有 `require`,不能只靠 narrative 暗示。
- 复杂度:先修晨湖终局门槛,不要重写整棵树。
- 风险点:不能把开放沙盒改成线性章节;锁门必须基于既有道具、拼图和 flag。

---

## 1. 目标

- 给正式剧本终局入口增加数据门槛;
- 让 True / Truth / Data / Broadcast / Bad / Hidden / Neutral 等结局由玩家本轮行为解锁或隐藏;
- 增加审计,防止终局再次退回无门槛菜单;
- 增加审计,防止 G-273 首访文本混入旧版主角履历;
- 补强晨湖文本,让玩家明确感到“这一晚做过的事正在审判自己”;
- 合并 fragments 重建正式 `tree.json`。

---

## 2. 非目标

- 不新增 DB schema;
- 不改 CLI 作为本轮重点;
- 不把沙盒改成线性章节;
- 不新增真实图片 / 音频资产;
- 不重写所有地标。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: Done

- 创建本 Task;
- 创建 Issue `#55` 和 milestone `v7 剧本病根深改`;
- 新增团队评审报告;
- 更新索引与下一阶段目标。

### M2: 终局入口数据门槛

状态: Done

- 修改 `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`;
- 给 `n_scene_morning_lakeside` 的高阶结局 choice 增加 `require`;
- 保留 Neutral / Bad 类结局作为低完成度或失败路径;
- 不删除开放路线。

### M3: 剧本压力补强

状态: Done

- 补强 `n_scene_morning_lakeside` narrative / variants;
- 强化记录表、赵某、房租、工牌、名字与行为账本的关系;
- 避免把结局页写成系统菜单。
- 补强 G-273 对讲机与遗失档案室首访文本,让主角保持“2024 新入职、缺钱、误接编号”的一致定位。

### M4: 审计与测试

状态: Done

- 在 `tools/audit_script_depth.py` 中增加终局门槛检查;
- 更新 / 新增测试,锁住晨湖终局 choice 的 `require`;
- 防止 True / Truth / Data / Hidden 无门槛回退。
- 在 `tools/audit_script_depth.py` 中增加 G-273 旧履历泄漏检查;
- 新增测试覆盖终局门槛、单行路、G-273 resolved narrative 履历一致性。

### M5: 验证与同步

状态: Done

- 执行:
  - `python3 -m json.tool stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`;
  - `python3 tools/merge_fragments.py`;
  - `bash tools/audit_all.sh`;
  - `.venv/bin/python tools/run_all_tests.py`;
  - `git diff --check`;
- 测试污染 `database/ghost_stories_test.db` 时恢复;
- 回写 Issue / PR。

---

## 4. 代码入口

- 剧本: `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
- 正式树: `stories/hangzhou_yebanbaoan/tree.json`
- 审计: `tools/audit_script_depth.py`
- 测试: `tests/test_audit_script_depth.py`

---

## 5. 完成记录

- 2026-05-10: 确认病根:Pass 9 结构审计过线,但终局入口仍像菜单,高阶结局没有被本轮行为充分锁住。
- 2026-05-10: 给晨湖高阶结局补上 True / Truth / Broadcast / Data / Hidden 等门槛,让结局读取道具、拼图、flag、PR 与完成地标数量。
- 2026-05-10: 修正 B3 工牌路径,避免 `n_s7_arrive` 直接跳 Data End;单行路节点不再偷偷返回地图。
- 2026-05-10: 补写 G-273 对讲机、遗失档案室和民俗地标首访文本,将主角稳定为 2024 新入职夜班保安,不再默认混入旧版中年老保安履历。
- 2026-05-10: `audit_script_depth` 新增终局门槛、单行路、主角履历三类硬审计;`tests/test_audit_script_depth.py` 扩展到 6 个用例。
- 2026-05-10: 已执行 `json.tool`、`merge_fragments.py`、`audit_script_depth.py`、局部 pytest、`bash tools/audit_all.sh`、`.venv/bin/python tools/run_all_tests.py`、`git diff --check`;测试数据库副作用已恢复。
