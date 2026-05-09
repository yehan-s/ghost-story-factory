# 2026-05-09 项目级同步事务与团队评审留痕

## 1. 任务描述

用户指出:剧本、文档、Issue、PR、验证记录应该同步修改,不应每次由用户提醒;可参考 Claude 的项目级 `script-review-team` skill。

本次任务不改游戏内容,只把流程规则固化到 Codex 侧项目约定。

## 2. Chief Editor — 首席编辑

- 相关度:深度参与
- 意见:这是流程连续性问题。剧本迭代如果不把 Task、团队评审、Issue、PR、测试作为同一事务,下一轮会丢失上下文。
- 产出:要求在 `AGENTS.md` 增加硬规则,并写入本次 team review。

## 3. State Architect — 状态系统建筑师

- 相关度:普通审查
- 意见:流程同步不应新增游戏状态或脚本 flag。正确做法是复用已有项目管理结构:Task 文档、Issue、PR、team review。
- 产出:禁止为了流程留痕改 runtime state。

## 4. Meta-Game Designer — 元游戏设计师

- 相关度:普通审查
- 意见:剧本向 VN / galgame 靠拢时,每次改动都可能影响周目、收集、结局入口。流程规则必须强制检查这些影响。
- 产出:后续剧本 Task 必须说明是否影响周目/收集/结局。

## 5. UX Designer — 文字体验设计师

- 相关度:普通审查
- 意见:用户体验不是只改正文。文字过渡、画面意图、选项解锁、回访反馈都要同步检查。
- 产出:AGENTS 规则中加入 UX / 演出改动同步审查要求。

## 6. Lore Keeper — 世界观考据师

- 相关度:普通审查
- 意见:灵异与杭州本地质感改动不能只存在于节点文本里,需要在 Task / review 里说明新增元素是否破坏世界观。
- 产出:后续剧本评审必须覆盖 lore 影响。

## 7. Topology Designer — 拓扑设计师

- 相关度:深度参与
- 意见:流程缺陷的本质是“同步关系没有数据结构”。把同步事务列成固定 8 步,比靠记忆可靠。
- 产出:Task → Team Review → Issue/Milestone → Implementation → Generated Artifacts → Validation → Issue/PR 回写 → Commit。

## 8. QA / Path Tester — 路径测试官

- 相关度:深度参与
- 意见:必须把验证命令写入 Issue / PR,否则“跑过测试”不可追溯。改 fragment 后必须重建 `tree.json` 并跑审计。
- 产出:AGENTS 规则中明确验证和测试副作用数据库恢复。

## 9. 综合建议

- 决议:修改后放行
- 关键风险:
  - 只写文档但不回写 Issue / PR,流程仍会分裂;
  - 团队评审变成形式主义,没有落到 Task 验收;
  - 测试生成的数据库快照被误提交。
- 后续动作:
  - 更新 `AGENTS.md`;
  - 新增 `TASK_PROJECT_SYNC_WORKFLOW.md`;
  - 更新 `docs/team-reviews/INDEX.md`;
  - 创建并回写 GitHub Issue #33;
  - 将改动追加到 PR #32。
