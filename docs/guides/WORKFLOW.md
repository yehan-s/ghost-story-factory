# Ghost Story Factory - 完整工作流程指南

> **Version:** v3.1 🎯
> **更新日期:** 2025-10-24
> **适用于:** 基于"templates"的完整故事生成流程

---

## 📋 目录

1. [快速开始](#快速开始)
2. [完整流程](#完整流程-推荐)
3. [简化流程](#简化流程-快速生成)
4. [命令参考](#命令参考)
5. [文件输出说明](#文件输出说明)

---

## 🚀 快速开始

### ⚡ 方式一：自动流水线（最推荐！）

```bash
# 1. 设置城市，获取候选故事
set-city --city "杭州"

# 2. 选择故事并生成结构框架
get-struct --city "杭州" --index 1

# 3. 一键生成所有内容（自动执行 5 个步骤！）
gen-complete --city "杭州" --index 1
```

**🎯 自动完成：** Lore v1 → 主角设计 → Lore v2 → GDD → 主线故事

---

### 🎯 方式二：手动分步（精细控制）

```bash
# 1-2. 设置城市和选择故事（同上）
set-city --city "杭州"
get-struct --city "杭州" --index 1

# 3-7. 手动分步执行
get-lore --city "杭州" --index 1
gen-protagonist --city "杭州"
gen-lore-v2 --city "杭州"
gen-gdd --city "杭州"
gen-main-thread --city "杭州"

# 8. (可选) 生成分支故事
gen-branch --city "杭州" --branch-name "店主线"
```

### 方式三：简化流程（快速，无游戏系统）

```bash
# 1-2. 设置城市和选择故事
set-city --city "杭州"
get-struct --city "杭州" --index 1

# 3. 直接生成简化版故事（跳过 Lore v2/GDD）
get-story --city "杭州"
```

---

## 📐 完整流程 (推荐)

### Stage 1: 候选与结构

#### 1.1 获取候选故事列表

```bash
set-city --city "杭州"
```

**输出文件:** `杭州_candidates.json`
**内容:** 5-7 个候选灵异传说，包含 title、blurb、source

**示例输出:**
```json
[
  {
    "title": "北高峰午夜缆车空厢",
    "blurb": "夜爬者称凌晨缆车轨道传来空厢运行声，监控却显示无车厢移动。",
    "source": "百度贴吧"杭州北高峰"深夜贴，关键词"缆车 空箱 怪声""
  },
  ...
]
```

#### 1.2 选择故事并生成结构

```bash
get-struct --city "杭州" --index 1
# 或指定标题
get-struct --city "杭州" --title "北高峰午夜缆车空厢"
```

**输出文件:** `杭州_struct.json`
**内容:** 故事框架，包含 title、city、location_name、core_legend、key_elements、potential_roles

---

### Stage 2: Lore v1 与主角设计

#### 2.1 生成世界观基础 (Lore v1)

```bash
get-lore --city "杭州" --index 1
```

**输出文件:** `杭州_lore.json`
**内容:** 世界观圣经，包含：
- `world_truth` - 核心真相
- `rules[]` - 世界规则
- `motifs[]` - 意象符号
- `locations[]` - 地点设定
- `timeline_hints[]` - 时间线提示
- `allowed_roles[]` - 可选角色

#### 2.2 生成主角设计

```bash
gen-protagonist --city "杭州"
```

**输出文件:** `杭州_protagonist.md`
**内容:** 主角分析报告 (Markdown)
- 三维评估模型（访问权、交集点、动机）
- 每个角色的分析与结论
- 最终推荐的主角线

---

### Stage 3: Lore v2 与 GDD

#### 3.1 生成深化世界观 (Lore v2)

```bash
gen-lore-v2 --city "杭州"
```

**输出文件:** `杭州_lore_v2.md`
**内容:** 世界书 2.0 (系统增强版)
- 完整保留 Lore v1 内容
- 新增：共鸣度系统
- 新增：实体行为等级
- 新增：后果树 (Consequence Tree)
- 新增：核心游戏系统

**依赖:** 需要先运行 `get-lore`

#### 3.2 生成 AI 导演任务简报 (GDD)

```bash
gen-gdd --city "杭州"
```

**输出文件:** `杭州_GDD.md`
**内容:** 游戏设计文档 (Markdown)
- 主角目标与访问权
- 关键场景流程（5-6个）
- 系统整合（共鸣度、后果树）
- AI 导演指令

**依赖:** 需要先运行 `gen-lore-v2` 和 `gen-protagonist`

---

### Stage 4: 完整故事生成

#### 4.1 生成主线完整故事

```bash
gen-main-thread --city "杭州"
```

**输出文件:** `杭州_main_thread.md`
**内容:** 完整主线故事 (Markdown, ≥5000字)
- B站UP主风格
- 沉浸式第二人称叙述
- 8-10个章节，每章500-800字
- 完整的开场、高潮、结局

**依赖:** 需要先运行 `gen-gdd`

#### 4.2 (可选) 生成分支故事

```bash
gen-branch --city "杭州" --branch-name "店主线"
gen-branch --city "杭州" --branch-name "顾客线"
```

**输出文件:** `杭州_branch_店主线.md`
**内容:** 分支故事 (Markdown)

**依赖:** 需要先运行 `gen-lore-v2`

---

## ⚡ 简化流程 (快速生成)

适用于：
- 快速原型
- 不需要完整游戏系统
- 只需要一个单线故事

```bash
# Step 1: 获取候选
set-city --city "杭州"

# Step 2: 生成结构
get-struct --city "杭州" --index 1

# Step 3: 生成简化版故事
get-story --city "杭州"
```

**输出文件:** `杭州_story.md`
**特点:**
- 跳过 Lore v2、主角设计、GDD
- 直接基于 struct.json 生成故事
- 更快，但缺少深度系统设计

---

## 📚 命令参考

### Stage 1 命令

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `set-city` | 获取候选故事列表 | `--city` |
| `get-struct` | 生成故事结构框架 | `--city`, `--index`/`--title` |

### Stage 2 命令

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `get-lore` | 生成 Lore v1 | `--city`, `--index`/`--title` |
| `gen-protagonist` | 生成主角设计 | `--city`, `--lore` |

### Stage 3 命令

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `gen-lore-v2` | 生成 Lore v2 | `--city`, `--lore-v1` |
| `gen-gdd` | 生成 GDD | `--city`, `--lore-v2`, `--protagonist` |

### Stage 4 命令

| 命令 | 说明 | 主要参数 |
|------|------|----------|
| `gen-main-thread` | 生成主线故事 | `--city`, `--gdd`, `--lore-v2` |
| `gen-branch` | 生成分支故事 | `--city`, `--branch-name`, `--lore-v2` |

### Legacy 命令

| 命令 | 说明 | 备注 |
|------|------|------|
| `get-story` | 简化版故事生成 | 旧版，不使用 GDD |
| `gen-role` | 生成角色拍点 | 旧版 |
| `validate-role` | 验证角色一致性 | 旧版 |

---

## 📁 文件输出说明

### 完整流程输出文件（8个）

```
杭州_candidates.json      # 候选列表
杭州_struct.json          # 故事结构
杭州_lore.json            # Lore v1 (JSON)
杭州_protagonist.md       # 主角设计 (Markdown)
杭州_lore_v2.md           # Lore v2 (Markdown, 系统增强)
杭州_GDD.md               # AI 导演任务简报
杭州_main_thread.md       # 主线完整故事 (≥5000字)
杭州_branch_店主线.md     # 分支故事 (可选)
```

### 简化流程输出文件（3个）

```
杭州_candidates.json      # 候选列表
杭州_struct.json          # 故事结构
杭州_story.md             # 简化版故事
```

---

## 🎯 推荐工作流

### 1. 内容创作者（只需要故事）

```bash
set-city --city "城市名"
get-struct --city "城市名" --index 1
get-story --city "城市名"
```

### 2. 游戏开发者（需要完整系统）

```bash
# 依次运行完整流程的 1-7 步
set-city → get-struct → get-lore → gen-protagonist → gen-lore-v2 → gen-gdd → gen-main-thread
```

### 3. 研究者/设计师（需要分析文档）

```bash
# 运行到 Stage 3 即可
set-city → get-struct → get-lore → gen-protagonist → gen-lore-v2 → gen-gdd
```

---

## 🔧 高级选项

### 自定义输出路径

所有命令支持 `--out` 参数：

```bash
gen-main-thread --city "杭州" --out "deliverables/杭州_主线.md"
```

### 指定输入文件

如果文件名不是默认格式：

```bash
gen-lore-v2 --city "杭州" --lore-v1 "custom_lore.json"
gen-gdd --city "杭州" --lore-v2 "custom_lore_v2.md" --protagonist "custom_protagonist.md"
```

---

## 🛠️ 故障排查

### 问题 1: 命令未找到

```bash
# 重新安装
uv pip install -e .
```

### 问题 2: Kimi API 超时

- 检查 `.env` 中的 `KIMI_API_KEY`
- 分步执行，避免长时间运行

### 问题 3: 缺少依赖文件

- 确保按顺序执行命令
- 检查前置步骤是否成功生成文件

---

## 📖 相关文档

- [templates/README.md](./templates/README.md) - 设计文档总览
- [templates/00-index.md](./templates/00-index.md) - templates索引与上下文管理
- [templates/00-architecture.md](./templates/00-architecture.md) - 架构设计
- [SPEC.md](./SPEC.md) - 项目规范
- [USAGE.md](./USAGE.md) - 使用说明

---

## ✨ 示例：杭州完整流程

```bash
# 1. 获取候选
set-city --city "杭州"
# 输出: 杭州_candidates.json (6个候选故事)

# 2. 选择第1个故事
get-struct --city "杭州" --index 1
# 输出: 杭州_struct.json ("北高峰午夜缆车空厢")

# 3. 生成 Lore v1
get-lore --city "杭州" --index 1
# 输出: 杭州_lore.json (世界观基础)

# 4. 分析主角
gen-protagonist --city "杭州"
# 输出: 杭州_protagonist.md (主角分析报告)

# 5. 升级为 Lore v2
gen-lore-v2 --city "杭州"
# 输出: 杭州_lore_v2.md (含共鸣度系统)

# 6. 生成 GDD
gen-gdd --city "杭州"
# 输出: 杭州_GDD.md (AI导演任务简报)

# 7. 生成主线故事
gen-main-thread --city "杭州"
# 输出: 杭州_main_thread.md (≥5000字完整故事)

# 8. (可选) 生成分支
gen-branch --city "杭州" --branch-name "检修工线"
# 输出: 杭州_branch_检修工线.md
```

---

**Happy Storytelling! 🎭👻**

