# 2026-05-09 v4 GameTreePlan 沙盒骨架审计接入团队评审

关联 Task: `docs/tasks/TASK_V4_GAMETREE_ALIGNMENT.md`
关联 Issue: `#23`

---

## 0. 结论

【核心判断】
✅ 值得做。`GameTreePlan` 已经能产出最小可玩树,但“能跑”不等于“是沙盒”。ADR-010 已经把沙盒最小骨架写清楚,必须有机器守门。

【关键洞察】
- 数据结构: `PlotSkeleton` 继续做内容大纲,`GameTreePlan` 才承接沙盒拓扑计划;
- 复杂度: `audit_sandbox.py` 只检查沙盒骨架,不重复 `audit_playability / audit_reactions / audit_variants`;
- 风险点:如果 `audit_reactions.py` 不理解动态 picker,`GameTreePlan` 导出树必须同时给静态选项,不能靠测试豁免。

---

## 1. 架构评审

新增 `audit_sandbox.py` 是正确边界:

- `audit_playability.py`:能否跑通、坏跳转、死路、presentation 资产;
- `audit_sandbox.py`:是否满足 ADR-010 沙盒骨架;
- `audit_reactions.py`:反应契约注册与 resolver 可达;
- `audit_variants.py`:重访是否有分化。

工具职责没有混成一个大泥球。

---

## 2. 生成链路评审

`GameTreePlan.to_minimal_tree()` 必须比“测试样例”更认真:

- 补最小 ending;
- 顶层 `endings` 注册;
- picker 保留动态 `_is_map_picker`,同时提供静态地标入口,让通用 BFS 工具可验证;
- 地标连接变成实际 choice;
- 工具节点保留 `stay: true` 自循环,但也能回地图或结束调查;
- 反应 variant 有 `reaction_contracts.deductions.sandbox_probe.resolver_node`。

这让 v4 导出树开始像 GameTree v1,不是一张假地图。

---

## 3. QA

新增测试覆盖:

- `GameTreePlan` 最小导出树通过 sandbox audit;
- 正式杭州树通过 sandbox audit;
- 缺 picker / 地标 / 工具 / stay / 反应 clause 的线性树失败;
- `GameTreePlan` 最小导出树有真实结局、真实地标跳转和反应契约声明。

全量验证:

- `.venv/bin/python -m pytest tests/test_audit_sandbox.py tests/test_gametree_plan.py -q`;
- `python3 tools/audit_sandbox.py stories/hangzhou_yebanbaoan/tree.json`;
- `bash tools/audit_all.sh`;
- `.venv/bin/python tools/run_all_tests.py`。

---

## 4. 风险

- `audit_sandbox.py` 不检查文案质量,这是故意的。文案质量属于剧本评审和正式树审计,不是拓扑骨架工具;
- 正式生成器还没有把 `GameTreePlan` 产物写入最终故事文件,后续如果接生产链路,需要单独任务;
- 现有 `audit_reactions.py` 仍是静态 BFS,因此导出树需要静态 choices 配合动态 picker。
