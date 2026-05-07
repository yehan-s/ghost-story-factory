---
name: script-review-team
description: 项目级开发评审团。任何"开发任务"开始前必须调用——召集 7 人 agent team(Chief Editor / State Architect / Meta-Game Designer / UX Designer / Lore Keeper / Topology Designer / QA),评审后产出报告再决定是否动手。触发关键词:启动团队 / 召集团队 / 召集审查 / 评审 / 实现 / 添加 / 改造 / 重构 / 重写 / 扩展 / 集成 / 迁移 / 设计 / 规划 / 方案 / 架构 / 修复(影响 ≥ 10 行)
---

# 项目级评审团 Skill

把"7 人剧本评审团"的启动流程封装为可复用 skill,让每次开发任务都先经过审查再动手。

> 完整设计依据:`docs/superpowers/specs/2026-05-07-script-review-team-skill-design.md`

---

## 何时调用本 skill

### 必须调用(任一即触发)

**关键词触发**(用户描述任务时含以下任一):
- 实现 / 添加 / 改造 / 重构 / 重写 / 扩展 / 集成 / 迁移
- 设计 / 规划 / 方案 / 架构
- 修 / 修复(影响 ≥ 10 行 或 跨文件)

**主动召集**:
- 用户输入"启动团队"、"召集团队"、"召集审查"、"评审"
- 用户输入 `/script-review-team`

### 跳过例外(可直接动手,不调用本 skill)

- 拼写修复 / 注释更新
- 单文件 < 10 行 bug 修复
- 配置文件调整(.env / pyproject.toml 字段 / 环境变量值)
- 纯重命名 / 格式化
- 文档错别字

### Bootstrap 例外

**创建或修改本 skill 自身的任务跳过**(否则会形成循环依赖)。
具体指 `.claude/skills/script-review-team/` 目录内的任何文件改动。

### 用户覆盖

用户输入"跳过团队"显式覆盖时,助手必须**确认一次**再跳过:
> "我理解你想跳过评审团,这次任务直接动手。确认吗?"

确认后才跳过,且在最终回复里注明"本次跳过评审团"。

---

## 工作流(11 步)

```
1. 助手识别"开发任务"或用户主动召集
2. 助手用 TeamCreate 启动 team(team_name 用 script-review-<slug>)
3. 助手生成 7 个 sub-agent(角色 prompt 见 references/team-roles.md)
4. 助手把任务描述只发给 Chief Editor(单点入口,不广播)
5. Chief Editor 判定任务层级:剧本 / 引擎 / UX / lore / 多层
6. Chief Editor 把"任务 + 层级判定"广播给其余 6 人
7. 6 人按层级 + 自身职责自报相关度:深度参与 / 普通审查 / 放行
8. 7 人并行产出意见(放行者一句话即可)
9. Chief Editor 汇总意见 + 同步更新 INDEX.md → 写入
   docs/team-reviews/YYYY-MM-DD-<slug>.md
10. 助手把报告路径返回给用户
11. 用户放行 → 进入开发(Edit/Write 或 writing-plans)
    用户打回 → 重新评审或要求团队补充
```

**关键顺序约束**:
- 第 5 步(层级判定)必须在第 7 步(相关度自报)之前——否则 7 人各说各话
- 第 9 步 Chief Editor 同时负责报告和 INDEX 更新,不另设维护人

**时间约束**:
- 整个流程目标 30 分钟内完成。超过则说明流程过重,需简化(放行者直接路过、深度参与者控制在 10 分钟以内)

---

## TeamCreate 调用模板

```
TeamCreate({
  "team_name": "script-review-<task-slug>",
  "agent_type": "chief_editor",
  "description": "评审 <task summary>:7 人评审团对当前开发任务给出意见,产出 docs/team-reviews/<date>-<slug>.md"
})
```

7 个 sub-agent 用 Agent 工具创建,team_name 复用上面 TeamCreate 的值,name 字段用对应角色名:

| name | 角色 |
|---|---|
| `chief_editor` | Chief Editor |
| `state_architect` | State Architect |
| `meta_game_designer` | Meta-Game Designer |
| `ux_designer` | UX Designer |
| `lore_keeper` | Lore Keeper |
| `topology_designer` | Topology Designer |
| `qa_path_tester` | QA / Path Tester |

每个 agent 的 `subagent_type` 用 `general-purpose`(需要全工具访问)。
完整 prompt 模板见 `references/team-roles.md`。

---

## 报告输出

- 路径:`docs/team-reviews/YYYY-MM-DD-<task-slug>.md`(slug 用任务关键词,不超过 30 字符)
- 格式:9 节固定结构,见 `templates/review-report.template.md`
- 索引:Chief Editor 在写报告时同步追加一行到 `docs/team-reviews/INDEX.md`

---

## 相关文档

- 完整 spec:`docs/superpowers/specs/2026-05-07-script-review-team-skill-design.md`
- 团队角色定义与 prompt 模板:`references/team-roles.md`
- 报告 9 节格式说明:`references/report-format.md`
- 相关度自报判定:`references/relevance-self-report.md`
- 报告占位符模板:`templates/review-report.template.md`
