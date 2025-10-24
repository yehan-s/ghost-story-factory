## Ghost Story Factory 项目规格说明（SPEC）

本文件面向“新加入/重开窗口就能看明白”的使用者与维护者，完整说明项目在做什么、为什么这样做、如何正确使用与扩展。它是原 demo.md 的增强版：内容更系统，但不牺牲可读性。

---

### 1. 这是什么？（项目概览）

- 一个本地命令行工具（CLI），输入一个“城市名”，自动：
  1) 搜索并汇编城市灵异传说素材；
  2) 将素材提炼成结构化“故事骨架”；
  3) 扩写为“UP 主讲述风格”的长篇 Markdown 文案。
- 人类在环：AI 做体力活，创意与最后审稿由人类完成。
- 发布目标：可通过 `uvx` 临时运行，或安装为常驻工具。

产物（默认命名）：
- 世界观圣经：`<城市>_lore.json`
- 角色拍点：`<城市>_role_<角色>.json`
- 结构框架：`<城市>_struct.json`
- 候选列表：`<城市>_candidates.json`
- 成稿：`<城市>_story.md`

---

### 2. 为什么要这样做？（方法论）

我们采用“顶层设计 Top‑Down”的专业叙事流程：
- 先有“世界观圣经（Lore Bible）”：定义世界真相、超自然规则、母题（象征物）、关键地点与时间线提示。
- 再派生“角色拍点（Role Beats）”：用七拍结构稳住节奏与可视化镜头（opening→first_contact→investigation→mid_twist→confrontation→aftershock→cta）。
- 最后按“UP 主口播风格”扩写成稿：第二人称代入、强节奏停顿、多感官细节、符号反复召回。

这样可以保障：
- 一致性：不同角色线在同一世界规则下“指向同一谜团”。
- 可复用：相同 Lore 可衍生多角色线，形成系列化内容。
- 可验证：角色线对 Lore 的引用可被工具校验（软约束），降低漂移。

---

### 3. 我该如何开始？（两条路）

最省心：一键出稿（见 USAGE.md:一键出稿）
- `get-story --city <城市>`；需要指定输出名则加 `--out`。

最稳定：顶层设计 Top‑Down（推荐）
- `get-lore` → `gen-role` → `validate-role` → `get-story --role`。

三令备选（兼容 demo.md）
- `set-city` → `get-struct` → `get-story`。

完整命令清单见下文第 6 节，参数速查见 USAGE.md。

---

### 4. 技术栈与约束（给维护者）

- LLM 适配：优先 Kimi(Moonshot)（`KIMI_*` / `MOONSHOT_*`），回退 OpenAI（`OPENAI_*`）。
- 搜索工具：配置 `GOOGLE_API_KEY` 与 `GOOGLE_CSE_ID` 时启用 GoogleSearchRun；未配置不阻塞。
- JSON 容错：对中文花引号/BOM 做清洗；解析失败回退 `.txt` 以备人工处理。
- 角色校验：`validate-role` 会检查 `constraints_used.rules/motifs/locations` 是否在 lore 文本中可命中（软校验）。

---

### 5. 目录结构（最重要文件）

- `pyproject.toml`：脚本入口（get-story / set-city / get-struct / get-lore / gen-role / validate-role）
- `src/ghost_story_factory/main.py`：命令实现
- `USAGE.md`：面向使用者的快速上手
- `SPEC.md`：本文件（面向使用者+维护者的总览）
- `*.md` 提示词（根目录优先加载）：
  - `set-city.md` / `get-struct.md` / `lore.md` / `role-beats.md` / `get-story.md`
- `.env` / `.env.example`：环境变量（Kimi Key 等）

---

### 6. 命令详解（你永远会回看的部分）

一键出稿：
- `get-story --city <城市> [--out <文件>] [--role <角色>]`
  - 优先使用 `<城市>_role_<角色>.json` 或 `<城市>_role_*.json`；不在则用 `<城市>_struct.json`；再不在走全流程。

顶层设计（Top‑Down）：
- `get-lore --city <城市> [--index | --title] [--out <文件>]`
  - 从候选与原始素材抽象出世界观（`world_truth/rules/motifs/locations/timeline_hints/allowed_roles`）。
- `gen-role --city <城市> --role <角色> [--pov <视角>] [--lore <路径>] [--out <文件>]`
  - 产出七拍 `beats` 与 `constraints_used`；便于校验一致性。
- `validate-role --city <城市> [--role <角色>] [--lore <路径>] [--role-file <文件>]`
  - 软校验角色线是否只引用了 lore 中的元素；拍点是否齐全。

三令备选（兼容）：
- `set-city --city <城市>` → `<城市>_candidates.json`
- `get-struct --city <城市> [--index | --title] [--out <文件>]` → `<城市>_struct.json`
- `get-story --city <城市>` → `<城市>_story.md`

---

### 7. Prompt 约定（根目录优先加载）

- `set-city.md`：JSON 数组（`title/blurb/source`），仅一个 ```json 代码块，强制 ASCII 引号。
- `get-struct.md`：JSON 对象（`title/city/location_name/core_legend/key_elements/potential_roles`）。
- `lore.md`：JSON 对象（`world_truth/rules/motifs/locations/timeline_hints/allowed_roles`）。
- `role-beats.md`：JSON 对象（`role/pov/goal/constraints_used/beats{...}`）。
- `get-story.md`：Markdown 长文（≥1800 字，UP 主风格，第二人称/停顿/音效/多感官/象征物召回）。

缺失时将使用内置模板，保证可用性。

---

### 8. 环境变量与运行条件

- 必填：`KIMI_API_KEY`
- 可选：`KIMI_API_BASE=https://api.moonshot.cn/v1`、`KIMI_MODEL=kimi-k2-0905-preview`
- 回退：`OPENAI_API_KEY`（以及 `OPENAI_BASE_URL/OPENAI_API_BASE/OPENAI_MODEL`）
- 可选：`GOOGLE_API_KEY`、`GOOGLE_CSE_ID`（启用搜索工具）

---

### 9. 快速开始（复制即可）

一键出稿：
```bash
uvx --from . get-story --city "广州" --out "deliverables/程序-广州/广州_story.md"
```

Top‑Down：
```bash
uvx --from . get-lore --city "广州" --title "荔湾"
uvx --from . gen-role --city "广州" --role "保安" --pov "第二人称"
uvx --from . validate-role --city "广州" --role "保安"
uvx --from . get-story --city "广州" --role "保安" --out "deliverables/程序-广州/广州_story.md"
```

---

### 10. 常见问题（FAQ）

- 401/鉴权失败：检查 `.env` 的 `KIMI_API_KEY`；`KIMI_API_BASE` 是否为官方域名；密钥是否过期。
- 解析失败：工具已做中文引号/BOM 容错；仍失败会落 `.txt` 做人工回退；可调整 Prompt 重新生成。
- 速度慢：首次运行安装依赖；生成 lore/role 需要较长上下文，建议耐心等待或先“一键出稿”。
- 搜索禁用：没配 Google Key 时会自动禁用搜索工具，不影响写作流程。

---

### 11. 原则与质量标尺（文化）

- Good Taste：能重构就不加分支；把“特殊情况”变成“正常情况”。
- Never break userspace：命令名/产物命名/默认行为保持稳定；新增能力用参数开关或新命令承载。
- 实用主义：只为真实问题引入复杂度，避免“为理论完美”而堆砌。

---

### 12. 变更记录（要点）

- 新增 Top‑Down 三令：`get-lore` / `gen-role` / `validate-role`
- `get-story` 支持 `--role` 与 `--out`；优先角色线→结构→全流程
- 增加 Prompt 文件：`lore.md` / `role-beats.md`；强化 set‑city/get‑struct 约束
- 文档拆分：USAGE.md（上手） + SPEC.md（全貌）

---

如需“多角色批量”“CI 集成”“风格金标 Few‑shot”等高级支持，请在 issues 中提出需求。
