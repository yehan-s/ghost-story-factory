# 2026-05-07 项目级评审团 Skill 设计

> 把"7 人剧本评审团"的启动流程封装成项目级 skill,让每次开发任务都先经过审查再动手。

---

## 1. 背景与动机

### 1.1 项目现状
- 现有剧本「杭州夜班保安」v7,109 节点 / 5.6 万字 / 7 地标 / 13 共享 NPC / 8 主结局 / 41 种结局体验
- 引擎已经支持重复访问分化机制(`narrative_variants` + `visit_counts` + `flags`,见 `src/ghost_story_factory/v5/player.py:554-561`)
- 已有 spec 资产:v7-maze-master-spec、PROJECT-STATE-AND-FORESHADOW-REGISTRY、v8-character-roster-spec

### 1.2 用户痛点
1. **剧情悖论多** — 时序矛盾、因果漏洞、角色立场漂移在现有 109 节点里没有统一守门人
2. **重复操作返回相同反馈** — 例:第二次打开对讲机给的对话和第一次一样。引擎层支持但数据层覆盖不足
3. **缺少沙盒方向的设计文档** — 现有 spec 都是 v7 maze 的结构,没有"开放沙盒"的设计

### 1.3 目标方向
基于现有剧本做开放沙盒,体验对标 **galgame + 超越小说阅读**。两个核心维度:
- **状态密集叙事** — 同一节点根据玩家状态产生数十种独特变体,从根上消除重复体验
- **元游戏维度** — 多周目知识继承、CG/结局收集本、NPC 好感度、日记系统

终端保持 CLI/TUI(不上视觉演出)。

### 1.4 工作流约束
用户决策:**每次开发任务前必须经过 7 人评审团审查**,故把团队启动封装成项目级 skill,而非一次性团队任务。

---

## 2. Skill 元信息

| 项 | 值 |
|---|---|
| **名称** | `script-review-team` |
| **位置** | `.claude/skills/script-review-team/SKILL.md` |
| **类型** | 项目级 skill(随仓库发布) |
| **触发方式** | 1) CLAUDE.md 强制规则:任何"开发任务"开始前必须调用<br>2) 手动:用户输入"启动团队"、"召集团队"、"召集审查"、`/script-review-team` |
| **跳过例外** | 拼写修复 / 单文件 < 10 行 bug / 配置调整 / 纯重命名 |

---

## 3. 团队组成(7 人均衡组)

| # | 角色 | 一句话职责 | 核心产出 |
|---|---|---|---|
| 1 | **Chief Editor**<br>首席编辑·连续性审查官 | 找悖论(时序/因果/角色漂移)与重复体验,守伏笔-兑现链 | 悖论清单、伏笔-兑现矩阵、叙事一致性规范 |
| 2 | **State Architect**<br>状态系统建筑师 | Linus 角色——设计玩家知识图谱 + flags + variants 条件矩阵,从根上消除"重复操作给同样反馈" | 状态体系设计、引擎扩展需求清单 |
| 3 | **Meta-Game Designer**<br>元游戏设计师 | 周目知识继承、CG/结局收集本、true ending 解锁条件、日记/档案系统 | 周目机制、收集本设计、元游戏 UI 概念 |
| 4 | **UX Designer**<br>文字体验设计师 | 文字节奏、状态可视化、信息层级,把"galgame + 超越小说"具体落到 CLI/TUI | 排版规范、状态 UI 草图、玩家旅程图 |
| 5 | **Lore Keeper**<br>世界观考据师 | 守"杭州本地 + 国营夜班 + 都市传说"质感,新增元素全部要考据 | Lore Bible、新增元素考据清单 |
| 6 | **Topology Designer**<br>拓扑设计师 | 守图论简洁,质问每个新增 flag/状态"真的需要全局吗?",防状态空间爆炸 | 新拓扑设计、状态空间维度规范、可达性证明 |
| 7 | **QA / Path Tester**<br>路径测试官 | 跑测试路径,验证 variants 全可触发、状态机闭环、周目继承按预期 | 路径覆盖报告、Bug 清单、回归测试套件 |

### 3.1 关键设计选择
- **State Architect ↔ Topology Designer 必须互相 challenge** — State 倾向"加 flag 解决",Topology 倾向"砍状态保持简洁",这种张力是防止状态爆炸的核心机制
- **Chief Editor 守入口,QA 守出口** — 一个看现状,一个看落地
- **Lore Keeper 全程参与** — 任何新增/重构都要过她一遍

### 3.2 没列入的角色及理由
- ❌ Producer/团队主持人 — Chief Editor 兼任协调,引入 Producer 变官僚
- ❌ NPC Voice Writer — 现阶段 Lore Keeper + Chief Editor 合作即可

---

## 4. 团队启动模式

**MVP 决定:7 人全员上场,但分级参与**

### 4.1 为什么不做"任务类型驱动子集"
子集分派需要"任务分类"逻辑,会引入特殊情况——Linus 哲学"消除特殊情况"否决之。

### 4.2 替代方案:相关度自报
7 人都收到任务描述,**每人自报相关度**:
- **深度参与** — 主导这次评审,详细产出
- **普通审查** — 提一份意见
- **放行** — 一句话"无 X 影响,放行"

例:引擎扩展任务 → State Architect 深度,Lore Keeper 一句"无 lore 影响,放行"。

---

## 5. 工作流

```
1. 助手识别开发任务,或用户主动召集
   ↓
2. 助手调用 script-review-team skill
   ↓
3. skill 用 TeamCreate 启动 7 人 agent team
   ↓
4. 助手把任务描述发给 team
   ↓
5. Chief Editor 开第一声:任务在剧本/引擎/UX/lore 哪一层?
   ↓
6. 7 人按相关度自报,并行评审
   ↓
7. Chief Editor 汇总意见 → 写入 docs/team-reviews/YYYY-MM-DD-<slug>.md
   ↓
8. 助手把报告路径返给用户,等用户审阅
   ↓
9a. 用户放行 → 进入开发(Edit/Write 或 writing-plans)
9b. 用户打回 → 重新评审或要求团队补充
```

---

## 6. 产出物结构

### 6.1 文件路径
```
docs/team-reviews/
├── INDEX.md                                    # 评审历史索引
├── 2026-05-07-状态密集化对讲机重构.md            # 一次评审一个文件
├── 2026-05-09-新增武汉剧本.md
└── ...
```

### 6.2 报告格式(固定 9 节)
```markdown
# YYYY-MM-DD <任务标题>

## 1. 任务描述
<用户的需求原话或助手转述>

## 2. Chief Editor — 首席编辑
- 相关度:深度参与 / 普通审查 / 放行
- 意见:...
- 产出:...

## 3-8. State Architect / Meta-Game Designer / UX Designer / Lore Keeper / Topology Designer / QA
(同上格式)

## 9. 综合建议(Chief Editor 汇总)
- 决议:放行 / 修改后放行 / 打回
- 关键风险:...
- 后续动作:...
```

### 6.3 累积价值
- 历次评审形成项目知识库
- 新评审可引用旧评审避免重复讨论
- INDEX.md 维护索引,方便检索

---

## 7. Skill 文件布局

```
.claude/skills/script-review-team/
├── SKILL.md                       # 主入口,被 Skill 工具加载
├── references/
│   ├── team-roles.md              # 7 角色详细职责(Section 3 扩展)
│   ├── report-format.md           # 报告 9 节模板说明
│   └── relevance-self-report.md   # 相关度自报机制说明
└── templates/
    └── review-report.template.md  # 占位符模板,直接复制改用
```

### 7.1 SKILL.md 主要内容
- 何时触发(匹配 CLAUDE.md 强制规则)
- 工作流的 9 步(Section 5)
- 何时**不**触发(跳过例外)
- 调用 TeamCreate 的代码模板

### 7.2 references/ 内容
- `team-roles.md`:每个角色的完整职责说明 + 示例任务下的相关度判断
- `report-format.md`:9 节格式逐节说明,什么内容写在哪节
- `relevance-self-report.md`:深度参与/普通审查/放行的判定标准

---

## 8. 与项目体验目标的连结

| 体验目标 | 守护角色 |
|---|---|
| 状态密集叙事 | State Architect(数据结构)+ Topology Designer(状态空间简洁) |
| 元游戏维度 | Meta-Game Designer |
| 文字体验质感 | UX Designer |
| 杭州夜班质感 | Lore Keeper |
| 剧情连续性 | Chief Editor |
| 落地正确性 | QA / Path Tester |

每个体验目标都有对应的守护人——这是团队 7 人配置的根本依据。

---

## 9. 实施任务清单(给 writing-plans 用)

1. 创建 `.claude/skills/script-review-team/` 目录结构
2. 写 `SKILL.md` 主入口
3. 写 `references/team-roles.md`(7 角色详细职责)
4. 写 `references/report-format.md`(报告格式说明)
5. 写 `references/relevance-self-report.md`(相关度自报机制)
6. 写 `templates/review-report.template.md`(报告模板)
7. 创建 `docs/team-reviews/` 目录 + 初始 `INDEX.md`
8. 在项目 CLAUDE.md 加触发规则(强制约束)
9. 跑一次端到端测试:**以"对讲机重复对话问题"作为试金石任务**,验证整套流程

---

## 10. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 7 人全员让小任务变重 | 相关度自报机制,放行可以一句话 |
| agent team 消息复杂度 | Chief Editor 总协调,统一汇总,避免 7 人互相喊话 |
| 报告积累后查找困难 | INDEX.md 索引 + 文件名带任务关键词 |
| skill 触发规则太硬,影响快速修改 | 跳过例外清单(< 10 行 bug、拼写、配置)+ 用户可强制跳过 |
| 团队意见不一致僵持 | Chief Editor 决议,有不同意见在报告"风险"节记录,不阻塞放行 |

---

## 11. 相关文档

- `docs/superpowers/specs/2026-05-07-v7-maze-master-spec.md` — 当前剧本架构基础
- `docs/superpowers/specs/2026-05-07-PROJECT-STATE-AND-FORESHADOW-REGISTRY.md` — 当前剧本状态快照
- `docs/architecture/ADR-004-core-llm-refactor.md` — LLMClient 设计(State Architect 工作时参考)
- `CLAUDE.md` — 触发规则将写入此处
