# TASK: v7 审计噪声与孤儿道具债收敛

版本: v0.1
状态: Done
关联:
- Milestone: `v7 VN 沙盒可玩闭环`
- GitHub Issue: `#27`
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md` § M4
- `docs/tasks/TASK_GAMETREE_V1.md`

---

## 0. 背景

PR #14 合并后,正式杭州树已经达到 145/145 可达、21 个结局、基础 VN 演出字段全覆盖。

剩下的问题不是玩法闭环,而是守门工具的噪声:

- `audit_tree` 把 NPC 档案 `key_items` 当成未使用道具,导致真实世界观物件被误报为孤儿;
- `inv_descriptions` 里残留了几条没有入包、没有 require、也没有档案用途的旧道具说明;
- `audit_state` 输出所有历史状态、年份和 schema 问题时不分级,人工阅读时容易把真正阻断和历史噪声混在一起。

这不是大系统重构。正确做法是收紧审计口径,保持旧字段兼容,不要为了消 warning 把剧情物件硬塞进玩法。

---

## 1. 目标 / 非目标

### 目标

- [x] `audit_tree` 将 NPC 档案 `key_items` 纳入道具使用口径;
- [x] 删除没有实际玩法/档案用途的旧 `inv_descriptions`;
- [x] `audit_state` 增加 `severity.errors / warnings / info` 分级汇总;
- [x] 保留 `audit_state` 旧字段,不破坏已有测试与脚本;
- [x] 跑全套审计与统一测试;
- [x] 回写 Issue #27。

### 非目标

- 不新增 DB schema;
- 不改变正式树主拓扑;
- 不引入真实 VN 图形客户端;
- 不把展示型 lore 物件强行变成 `require.inv_has` 道具。

---

## 2. 里程碑

### M1: audit_tree 道具口径修正

- [x] `npcs[*].key_items` 算作被使用物件;
- [x] 保留 `effects.inv_add / inv_remove / require.inv_has / inv_lacks` 的旧统计;
- [x] 删除无实际用途的旧 `inv_descriptions`;
- [x] 重新运行 `tools/merge_fragments.py` 生成正式 `tree.json`。

### M2: audit_state 分级输出

- [x] 新增 `severity.errors`;
- [x] 新增 `severity.warnings`;
- [x] 新增 `severity.info`;
- [x] 新增 `severity.counts`;
- [x] 新增单元测试覆盖分级输出。

### M3: 验收

- [x] `python3 tools/audit_tree.py stories/hangzhou_yebanbaoan/tree.json`;
- [x] `bash tools/audit_all.sh`;
- [x] `.venv/bin/python tools/run_all_tests.py`;
- [x] GitHub Issue #27 记录结果。

---

## 3. 代码入口

- `tools/audit_tree.py`
- `tools/audit_state.py`
- `tools/merge_fragments.py`
- `stories/hangzhou_yebanbaoan/tree.json`
- `tests/test_audit_state.py`

---

## 4. 验收标准

- `audit_tree` 不再报告无意义孤儿道具;
- `audit_state` 输出分级为 error / warning / info;
- `audit_all` 保持通过;
- 统一测试保持通过。
