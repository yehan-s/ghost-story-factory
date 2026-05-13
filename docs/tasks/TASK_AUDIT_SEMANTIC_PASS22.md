# TASK: audit 语义化三件套 + 行为画像不变量 Pass 22

版本: v0.1
状态: Done
创建时间: 2026-05-13
完成时间: 2026-05-13
关联:
- `docs/tasks/TASK_NEXT_VN_SANDBOX_GOALS.md` §M19
- `docs/team-reviews/2026-05-13-next-direction-survey.md`(Chief / QA 共振 2 票)
- ADR-008(反应契约)
- ADR-010(沙盒拓扑契约)

---

## 0. 背景

评审团 QA / Path Tester 指出当前 8 项 audit 都偏**结构合规**(引用闭合、flag 矩阵、骨架完整),
对**语义运行时**(variant 实际触发率、跨周目继承、玩家路径分布)零覆盖——
"在测代码能跑,没测剧本能演"。

Chief Editor 同样指出需要 `audit_foreshadow_chain` 工具守"伏笔埋了但没人捡 / 捡了没回响"。

【核心判断】
✅ 值得做:Pass 20/21 落地了跨周目联动 + 沙盒骨架,需要工具守护它们不回退。
✅ 纯引擎工具,不改剧本——可与 Pass 21 并行启动。
✅ 配 debt 报告模式:不立即阻断剧本债务,只揭示。

---

## 1. 目标

- 新增 4 件审计工具:
  1. `audit_foreshadow_chain.py` — reaction_contracts 链条完整性(label / consumer 注册 / 实际消费)
  2. `audit_cross_run_continuity.py` — endings_seen 消费侧覆盖(每个非 BAD 主结局应被引用)
  3. `audit_variant_trigger.py` — variant 触发难度计数(warn 5 / error 8 atoms)
  4. `audit_protagonist_behavior.py` — G-273 主结局必须识别玩家行为
- 全部纳入 `tools/audit_all.sh`(8 项 → 12 项);
- debt 性质问题降级(cross_run 默认非阻断、micro_ending 豁免);
- 加测试套件覆盖核心检测 + 豁免规则;
- 不修剧本本体,不重写既有 8 项 audit。

---

## 2. 非目标

- 不强制要求 4 个无反咬主结局立即补 variant(留剧本扩写偿还);
- 不重写 8 项既有 audit 的检测逻辑;
- 不引入 TUI session 回放校验(留挂账);
- 不动 DB schema。

---

## 3. 已落地里程碑

### M1: 4 件工具实现 — Done(commit `dac5e19`)

#### audit_foreshadow_chain
检测 3 类问题:
- `MISSING_LABEL`:contract 缺 `_label` 人类可读标签
- `CONSUMER_NOT_REGISTERED`:声明的 consumer_node 不在 nodes 表
- `CONSUMER_NOT_CONSUMING`:声明 consumer 但实际节点无 variant 引用 _resolved

#### audit_cross_run_continuity
- 检测项:`ENDING_NO_CROSS_REFERENCE`(主结局无反咬)
- **默认非阻断**(debt 性质),加 `--strict` 才阻断
- `E_BAD_*` 自动豁免,节点声明 `_no_cross_ref_ok: true` 显式豁免
- 跨 story_id 引用 skip(沿 audit_reactions Pass 20 设计)

#### audit_variant_trigger
- 度量 `variant.if` 的"前置原子条件数"(展开 all_of,any_of 取最小)
- WARN 阈值 5(可调),ERROR 阈值 8(可调)
- 输出 atoms 直方图,辅助薄/厚节点分布观察
- 正式树当前最大 atoms=4,0 ERROR

#### audit_protagonist_behavior
- G-273 ending 必须有 ≥ 1 个 variant 通过 behavior_profile / *_resolved / flags / inv_has 等识别玩家
- linmou ending(`E_LINMOU_*`)不在审计范围(走 audit_paths_linmou)
- 微结局豁免:无 variant 且非 `n_end_*` / `_is_main_ending` 视为段子级 ending

### M2: audit_all.sh 升级 — Done(commit `dac5e19`)

从 8 项升到 12 项。其中:
- foreshadow_chain / variant_trigger / protagonist_behavior 阻断
- cross_run_continuity 默认非阻断,debt 输出 ⚠️ warning

### M3: 测试 — Done(commit `dac5e19`)

14 个测试:
- 正式树健康度(4 个)
- 每件工具的 happy path + 错误检测 + 豁免规则(10 个)

### M4: 验证 — Done(commit `dac5e19`)

- audit_all 12/12 全绿 ✅
- run_all_tests 7/7 全绿 ✅

---

## 4. 验收对照

| M19 验收条款 | 现状 |
|---|---|
| 三件工具落地并跑通 tree.json | ✅ 全部 0 ERROR |
| audit_all.sh 升级到 11 项,全绿 | ✅ 升到 12 项(多了保安线行为画像) |
| 新增 3 个测试文件 | ✅ 合并到单文件 14 个 test case |
| 保安线"主角行为画像不变量"审计 | ✅ audit_protagonist_behavior |
| audit_all 与统一测试通过 | ✅ 12/12 + 7/7 全绿 |

---

## 5. 揭示的剧本债务(留挂账)

audit_cross_run_continuity 默认非阻断报出 4 处主结局无跨周目反咬:

| ending_type | 节点 | 建议偿还 Pass |
|---|---|---|
| E_TRUE | n_end_true | Pass 23+(高优先,主线 True End) |
| E_BROADCAST | n_end_broadcast | Pass 23+ |
| E_NEUTRAL | n_end_neutral | Pass 23+(注:已有 1 个 ending_seen=E_TRUTH 的 variant,但 E_NEUTRAL 自身未被其他节点引用) |
| E_HIDDEN | n_end_hidden | Pass 23+(隐藏路线) |

这些不是错误,是 audit 揭示的"跨周目联动可扩展空间"。Pass 20 已加 2 处反咬(n_end_neutral / n_end_truth),后续 Pass 可继续补完。

audit_variant_trigger atoms 直方图:
- 0 atoms: 13 个 variant(空 if fallback)
- 1 atom: 269 个 variant(健康主力)
- 2-4 atoms: 61 个 variant(可控)
- ≥ 5 atoms: 0 个 ✅

---

## 6. 代码入口

- `tools/audit_foreshadow_chain.py`(128 行)
- `tools/audit_cross_run_continuity.py`(135 行)
- `tools/audit_variant_trigger.py`(125 行)
- `tools/audit_protagonist_behavior.py`(111 行)
- `tools/audit_all.sh`:12 项 audit 流水
- `tests/test_audit_pass22.py`:14 个测试 case

---

## 7. 后续

- 长线挂账:audit_cross_run_continuity 揭示的 4 处主结局反咬补 variant(Pass 23+)
- TUI session 回放校验(QA Path Tester 中危盲区):Pass 24+ 可考虑
- 路线短名单 Pass 20/21/22 全部落地——回到评审团表上挑选下一阶段方向
