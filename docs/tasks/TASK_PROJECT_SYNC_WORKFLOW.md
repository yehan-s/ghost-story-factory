# TASK: 项目级同步事务与团队评审留痕

版本: v0.1
状态: Done
关联:
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/skills/script-review-team/SKILL.md`
- `docs/superpowers/specs/2026-05-07-script-review-team-skill-design.md`
- `docs/team-reviews/INDEX.md`
- GitHub Issue: `#33`
- PR: `#32`

---

## 0. 背景

Issue #31 的剧本加深过程中暴露了流程问题:剧本、Task、Issue、PR、测试、团队评审没有被当成一个同步事务处理。

这会导致两个坏结果:

- 剧本改了,但目标 / 风险 / 验收没有同步沉淀;
- 文档写了,但 Issue / PR / 测试记录不同步,下一步开发会失焦。

Claude 侧已经有项目级 `script-review-team` skill,但 Codex 侧 `AGENTS.md` 只描述了黄金流程,没有把“剧本改动时必须同步团队评审和 PR/Issue 状态”写成硬规则。

---

## 1. 目标 / 非目标

### 目标

- [x] 在 `AGENTS.md` 固化剧本开发同步事务;
- [x] 明确剧本 / 玩法 / UX / 演出改动必须同步 Task、团队评审、Issue、PR、测试;
- [x] 参考 Claude 项目级 `script-review-team` skill,把团队评审产物纳入 Codex 工作流;
- [x] 为本次流程修正创建 GitHub Issue;
- [x] 将流程修正追加到当前 PR。

### 非目标

- 不修改 `.claude/skills/script-review-team/` 本身;
- 不新建 Codex 本地 skill;
- 不新增自动化工具或 CI;
- 不改游戏代码和剧本内容。

---

## 2. 同步事务规则

以后凡是修改正式剧本、玩法闭环、UX/演出契约、状态结构、运行时体验,必须把以下事项作为同一个事务完成:

1. **Task**: 创建或更新 `docs/tasks/TASK_*.md`,记录目标、非目标、里程碑、验收、完成记录;
2. **Team Review**: 若属于开发任务,参考 `script-review-team` 角色模型,在 `docs/team-reviews/` 写评审或完成报告,并更新 `INDEX.md`;
3. **Issue / Milestone**: 创建或更新 GitHub Issue,并归入对应 milestone;
4. **Implementation**: 修改代码 / 剧本 / 文档,保持最小必要变更;
5. **Generated Artifacts**: 若改 fragment,必须重建正式 `tree.json`;
6. **Validation**: 执行对应审计和测试,记录命令与结果;
7. **Issue / PR 回写**: 用 `gh issue comment` / PR 描述或评论同步结果;
8. **Commit**: 用规范 commit message 提交,避免把测试副作用数据库混入提交。

---

## 3. 验收记录

- `AGENTS.md` 已补充“剧本开发同步事务”和“团队评审协同”规则;
- 新增本 Task 文档;
- 新增 `docs/team-reviews/2026-05-09-project-sync-workflow.md`;
- `docs/team-reviews/INDEX.md` 已追加索引;
- GitHub Issue #33 已创建;
- 当前 PR #32 将包含本流程修正。
