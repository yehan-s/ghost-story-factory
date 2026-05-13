# TASK: G-273 主角身份泄漏清扫 Pass 19

版本: v0.1
状态: Active
创建时间: 2026-05-10
关联:
- GitHub Issue: 待创建
- GitHub Milestone: 待创建
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md`
- `docs/tasks/TASK_SCRIPT_ROOT_CAUSE_PASS17.md`
- `docs/tasks/TASK_SCRIPT_THIN_NODES_PASS18.md`
- `docs/team-reviews/2026-05-10-script-protagonist-leak-pass19.md`

---

## 0. 用户质疑记录

用户要求继续深挖,并反复指出“主角剧本不行”“剧本深度广度不达标”“不要只管 TUI”。

这个质疑继续成立。Pass 17 已经把 G-273 的默认首访文本纳入审计,但审计口径太窄:它只解析 `resolve_narrative()` 的默认结果,没有扫描 `narrative_variants`,也没有扫描 TUI 首开地图时的硬编码文案。

实际问题:

- 正式树仍有旧版中年老保安设定泄漏:妻儿、51 岁、夜班 14 年、2010 接班、1985 入职等;
- 泄漏集中在民俗工具复访 variant、前任对讲机、遗失档案室和 TUI 地图首开;
- 这会让赵某一会儿是 2024 新入职、缺钱误接编号的年轻保安,一会儿又变成有妻儿、老单位、老工龄的中年保安;
- 这是主角数据结构错误,不是普通文风问题。

【核心判断】
✅ 值得做:主角身份不稳定会直接破坏视觉小说代入感和周目叙事可信度。

【关键洞察】
- 数据结构:主角身份约束必须覆盖所有正式文本载体,包括 `narrative_variants` 和 TUI 硬编码文案。
- 复杂度:不要重写主角系统,先把旧履历词纳入审计红线并修掉已知泄漏。
- 风险点:部分旧年份属于杭州民俗 lore,不能把所有年份都删掉;只清理“赵某旧履历”。

---

## 1. 目标

- 清理正式剧本中 G-273 旧版中年老保安身份泄漏;
- 将 `audit_script_depth` 的主角履历审计从默认 narrative 扩展到所有 `narrative_variants`;
- 将 TUI 地图首开文案从“媳妇合照”改为 2024 新入职、缺钱、临时工、误接编号的主角语境;
- 合并 fragments 重建正式 `tree.json`;
- 新增 / 更新测试,防止 variant 与 TUI 硬编码再次泄漏。

---

## 2. 非目标

- 不改 CLI 作为本轮重点;
- 不新增 DB schema;
- 不重写全部民俗工具节点;
- 不删除合法的杭州历史年份;
- 不把主角改成无背景摄像机。

---

## 3. 里程碑

### M1: Task / Issue / 团队评审同步

状态: In Progress

- 创建本 Task;
- 创建 GitHub Issue 和 milestone;
- 新增团队评审报告;
- 更新索引与下一阶段目标。

### M2: 泄漏定位与剧本清扫

状态: Pending

- 修改 `stories/hangzhou_yebanbaoan/_fragment_v7_folklore.json`;
- 修改 `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`;
- 清理以下节点的旧履历泄漏:
  - `n_lore_leifeng_worm`
  - `n_lore_songmuchang_inn`
  - `n_lore_zheda_clock_girl`
  - `n_lore_wulinmen_execution`
  - `n_lore_kongque_collapse`
  - `n_npc_predecessor_voice`
  - `n_scene_lost_archive`
  - `n_scene_red_telephone`

### M3: TUI 首开地图文案清扫

状态: Pending

- 修改 `src/ghost_story_factory/v7/tui_player.py`;
- 移除 `action_show_map()` 中“你媳妇 2023 年的合照”旧设定;
- 让手机地图首开反馈服务于当前赵某设定。

### M4: 审计与测试

状态: Pending

- 扩展 `tools/audit_script_depth.py`;
- 让主角履历审计扫描所有 `narrative_variants`;
- 补充测试覆盖 variant 泄漏与 TUI 硬编码泄漏。

### M5: 验证与同步

状态: Pending

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

- 民俗工具: `stories/hangzhou_yebanbaoan/_fragment_v7_folklore.json`
- G-273 共享节点: `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json`
- 正式树: `stories/hangzhou_yebanbaoan/tree.json`
- TUI: `src/ghost_story_factory/v7/tui_player.py`
- 审计: `tools/audit_script_depth.py`
- 测试: `tests/test_audit_script_depth.py` / `tests/test_tui_experience_pass14.py`

---

## 5. 完成记录

- 2026-05-10: 初步定位主角旧履历泄漏集中在 `narrative_variants` 和 TUI 首开地图硬编码;Pass 17 审计口径不足。
