## Ghost Story Factory 使用指南（精简版）

本工具提供两种使用方式：
- 一键出稿（最省心）
- 顶层设计工作流 Top‑Down（最稳定、可复用）

建议先用“一键出稿”，满意后再用 Top‑Down 打磨多角色长篇。

---

### 0. 环境准备

- 安装 uv（如未安装）：`pip install uv`
- 在项目根目录创建 `.env`（示例见 `.env.example`）
  - 必填：`KIMI_API_KEY=...`
  - 可选：`KIMI_API_BASE=https://api.moonshot.cn/v1`
  - 可选：Google 搜索：`GOOGLE_API_KEY`、`GOOGLE_CSE_ID`（不配也能跑）

---

### 1. 一键出稿（最简单）

仅一条命令，直接在当前目录生成 `[城市名]_story.md`：

```bash
uvx --from . get-story --city "广州"
```

可指定输出文件名：

```bash
uvx --from . get-story --city "广州" --out "deliverables/程序-广州/广州_story.md"
```

---

### 2. 顶层设计（Top‑Down，推荐）

以“世界观 → 角色拍点 → 成稿”的顺序，保证一致性、可复用、可扩展：

```bash
# 2.1 生成世界观圣经（lore）
uvx --from . get-lore --city "广州" --title "荔湾"
# 输出：广州_lore.json

# 2.2 生成角色剧情拍点（beats）
uvx --from . gen-role --city "广州" --role "保安" --pov "第二人称"
# 输出：广州_role_保安.json

# 2.3 （可选）一致性校验
uvx --from . validate-role --city "广州" --role "保安"

# 2.4 按角色线成稿（若有 role 文件将优先使用）
uvx --from . get-story --city "广州" --role "保安" --out "deliverables/程序-广州/广州_story.md"
```

说明：
- 若未提供 `--role` 且存在 `广州_role_*.json`，也会被自动优先使用。
- 若没有角色线但存在 `广州_struct.json`，会按结构文件写作。
- 再不满足则自动走“搜索→提炼→写作”全流程。

---

### 3. 传统三令（备选）

更贴近 demo.md 的“候选→结构→成稿”路径：

```bash
# 3.1 候选（只输出 JSON 数组）
uvx --from . set-city --city "广州"
# 输出：广州_candidates.json（或 .txt 回退）

# 3.2 结构（从候选选一个）
uvx --from . get-struct --city "广州" --index 1
# 输出：广州_struct.json

# 3.3 成稿（按上一步结构写作）
uvx --from . get-story --city "广州"
```

---

### 4. 可选参数速查

- `--out`（get-story / get-struct 支持）：自定义输出路径与文件名
- `--role`（get-story 支持）：优先按 `<city>_role_<role>.json` 写作
- `--index` / `--title`（get-struct / get-lore 支持）：从候选中选取目标

---

### 5. Prompt 文件（可自定义）

根目录存在以下 md 文件时将被优先加载（缺失则用内置模板）：
- `set-city.md`：候选生成（只返回 JSON 代码块，字段：title/blurb/source）
- `get-struct.md`：结构化框架（只返回 JSON，字段：title/city/location_name/core_legend/key_elements/potential_roles）
- `lore.md`：世界观圣经（只返回 JSON：world_truth/rules/motifs/locations/timeline_hints/allowed_roles）
- `role-beats.md`：角色拍点（只返回 JSON：role/pov/goal/constraints_used/beats）
- `get-story.md`：UP 主讲述风格扩写（只返回 Markdown，≥1800 字）

---

### 6. 产物约定（默认命名）

- 世界观：`<城市>_lore.json`
- 角色线：`<城市>_role_<角色>.json`
- 结构框架：`<城市>_struct.json`
- 候选列表：`<城市>_candidates.json`
- 成稿：`<城市>_story.md`

---

### 7. 常见问题（FAQ）

- 401/鉴权失败：检查 `.env` 的 `KIMI_API_KEY` 是否有效；`KIMI_API_BASE` 是否为 `https://api.moonshot.cn/v1`。
- JSON 花引号解析失败：工具已做容错；若仍失败，命令会回退 `.txt` 供人工选择。
- 无 Google Key：搜索工具自动禁用，不影响整体出稿。
- 慢/超时：首次运行会安装依赖；Top‑Down 生成（尤其 get-lore）较耗时，建议耐心等待或先走“一键出稿”。

---

### 8. 最小演示（武汉）

```bash
# 一键出稿（最省心）
uvx --from . get-story --city "武汉"

# 或 Top‑Down（更稳）
uvx --from . get-lore --city "武汉" --title "东湖"
uvx --from . gen-role --city "武汉" --role "夜跑者"
uvx --from . get-story --city "武汉" --role "夜跑者" --out "deliverables/程序-武汉/武汉_story.md"
```

如需进一步定制（例如批量多角色、对接 CI/CD），可联系维护者补充脚本与文档。
