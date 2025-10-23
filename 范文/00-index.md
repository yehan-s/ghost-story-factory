# 范文索引 - AI 使用指南

**目的：** 本文件帮助 AI 快速定位所需模块，避免一次性加载所有范文文件。

---

## 🎯 使用原则

**分层加载策略：**
1. **第一次对话：** 只读取本索引文件 + `00-architecture.md`（了解全局架构）
2. **需要具体模块时：** 根据任务只加载相关的 `{module}.design.md`
3. **需要参考示例时：** 再加载对应的 `{module}.example.md`
4. **生成内容时：** 最后加载 `{module}.prompt.md`

**❌ 禁止：** 一次性读取所有 35 个文件（会浪费 15-20万 tokens）

---

## 📁 文件组织结构

```
范文/
├── 00-architecture.md      [178行] - 架构总览 ⭐ 必读
├── README.md               [590行] - 项目说明 ⭐ 必读
│
├── [阶段1: 地基层]
│   ├── lore-v1.design.md    [58行] - 世界书1.0设计理念
│   ├── lore-v1.example.md   [158行] - 荔湾广场世界书示例
│   └── lore-v1.prompt.md    [72行] - 世界书1.0生成器
│
├── [阶段2: 逻辑层]
│   ├── protagonist.design.md [45行] - 角色分析设计理念
│   ├── protagonist.example.md [95行] - 保安角色分析示例
│   ├── protagonist.prompt.md [68行] - 角色分析生成器
│   │
│   ├── lore-v2.design.md    [112行] - 世界书2.0设计理念
│   ├── lore-v2.example.md   [240行] - 共鸣度系统示例
│   └── lore-v2.prompt.md    [85行] - 世界书2.0生成器
│
├── [阶段3: 故事层]
│   ├── GDD.design.md        [43行] - AI导演任务简报设计理念
│   ├── GDD.example.md       [76行] - 保安线GDD示例
│   ├── GDD.prompt.md        [95行] - GDD生成器
│   │
│   ├── main-thread.design.md [85行] - 主线故事设计理念
│   ├── main-thread.example.md [444行] - 保安线完整故事 ⚠️ 大文件
│   ├── main-thread.prompt.md [102行] - 主线故事生成器
│   │
│   ├── branch-1.design.md   [52行] - 支线1(店主线)设计
│   ├── branch-1.example.md  [266行] - 店主线完整故事
│   ├── branch-1.prompt.md   [78行] - 支线1生成器
│   │
│   ├── branch-2.design.md   [48行] - 支线2(顾客线)设计
│   ├── branch-2.example.md  [254行] - 顾客线完整故事
│   └── branch-2.propmt.md   [74行] - 支线2生成器
│
└── [阶段4: 运行时层] 🎯 核心
    ├── choice-points.design.md      [500行] - 选择点设计系统 ⚠️ 大文件
    ├── choice-points.example.md     [608行] - 选项设计实战示例 ⚠️ 大文件
    ├── choice-points.prompt.md      [461行] - 选项生成器 ⚠️ 大文件
    │
    ├── runtime-response.design.md   [258行] - 响应生成设计理念
    ├── runtime-response.example.md  [529行] - 响应生成示例 ⚠️ 大文件
    ├── runtime-response.prompt.md   [359行] - 响应生成器
    │
    ├── intent-mapping.design.md     [494行] - 意图映射设计理念 ⚠️ 大文件
    ├── intent-mapping.example.md    [663行] - 意图映射示例 ⚠️ 最大文件
    ├── intent-mapping.prompt.md     [505行] - 意图验证器 ⚠️ 大文件
    │
    ├── state-management.design.md   [581行] - 状态管理设计理念 ⚠️ 大文件
    ├── state-management.example.md  [547行] - 状态管理示例 ⚠️ 大文件
    └── state-management.prompt.md   [485行] - 状态管理器 ⚠️ 大文件
```

---

## 🎮 常见任务的加载策略

### 任务1：理解整体架构
```
只读取：
✅ 00-index.md (本文件)
✅ 00-architecture.md
✅ README.md

Token消耗：~5,000 tokens
```

---

### 任务2：生成某个城市的世界书1.0
```
第1步：
✅ lore-v1.design.md (了解设计原则)
✅ lore-v1.example.md (参考荔湾广场示例)

第2步：
✅ lore-v1.prompt.md (加载生成器提示)

Token消耗：~15,000 tokens
不需要读取：其他28个文件
```

---

### 任务3：为某个角色生成GDD（AI导演任务简报）
```
前置依赖：
✅ lore-v2.example.md (需要世界规则)
✅ protagonist.example.md (需要角色信息)

核心文件：
✅ GDD.design.md
✅ GDD.example.md
✅ GDD.prompt.md

Token消耗：~25,000 tokens
不需要读取：阶段4的所有文件（除非要生成选择点）
```

---

### 任务4：生成选择点（Choice Points）
```
前置依赖：
✅ GDD.example.md (需要知道场景流程)
✅ lore-v2.example.md (需要知道规则)

核心文件：
✅ choice-points.design.md ⚠️ 500行
✅ choice-points.example.md ⚠️ 608行
✅ choice-points.prompt.md ⚠️ 461行

Token消耗：~80,000 tokens
建议：可以只读 design + prompt，跳过 example
```

---

### 任务5：运行时响应生成
```
必需文件：
✅ runtime-response.design.md
✅ runtime-response.prompt.md
✅ state-management.design.md (需要知道状态规则)

可选文件：
⭕ runtime-response.example.md (仅在需要参考时读取)

Token消耗：~40,000 tokens (不读example) 或 ~70,000 tokens (读example)
```

---

## 💡 极简加载策略（推荐）

**AI 第一次对话时，只需要：**

```
✅ 00-index.md (本文件，了解所有模块)
✅ 00-architecture.md (了解数据流)

总共：~900行 ≈ 4,000 tokens
```

**然后根据用户的具体需求，再按需加载相关模块。**

---

## 📏 文件大小分级

**超大文件（>500行）：** ⚠️ 谨慎加载，确认需要时再读
- intent-mapping.example.md (663行)
- choice-points.example.md (608行)
- README.md (590行)
- state-management.design.md (581行)
- state-management.example.md (547行)
- runtime-response.example.md (529行)
- intent-mapping.prompt.md (505行)
- choice-points.design.md (500行)

**大文件（200-500行）：** 有选择地加载
- intent-mapping.design.md (494行)
- state-management.prompt.md (485行)
- choice-points.prompt.md (461行)
- main-thread.example.md (444行)
- runtime-response.prompt.md (359行)
- branch-1.example.md (266行)
- runtime-response.design.md (258行)
- branch-2.example.md (254行)
- lore-v2.example.md (240行)

**中小文件（<200行）：** 可以按需加载
- 其余文件

---

## 🚀 快速参考

### 我想了解...

| 需求 | 必读文件 | 可选文件 | 估算Token |
|------|---------|---------|-----------|
| 整体架构 | 00-architecture.md | README.md | 5k |
| 如何生成世界书1.0 | lore-v1.{design,prompt} | lore-v1.example | 10k |
| 如何生成角色分析 | protagonist.{design,prompt} | protagonist.example | 8k |
| 如何生成世界书2.0 | lore-v2.{design,prompt} | lore-v2.example | 15k |
| 如何生成GDD | GDD.{design,prompt} | GDD.example | 12k |
| 如何生成主线故事 | main-thread.{design,prompt} | main-thread.example | 20k |
| 如何设计选择点 🎯 | choice-points.design | choice-points.example | 60k |
| 如何生成运行时响应 | runtime-response.{design,prompt} | runtime-response.example | 35k |
| 如何管理状态 | state-management.{design,prompt} | state-management.example | 70k |

---

## 🎯 针对不同用户的建议

### 用户类型1：内容创作者
**目标：** 生成新城市的灵异故事

**推荐加载顺序：**
1. 00-architecture.md（了解流程）
2. lore-v1 系列（生成世界书1.0）
3. protagonist 系列（分析角色）
4. lore-v2 系列（完善规则）
5. GDD 系列（设计任务简报）
6. main-thread 系列（生成主线故事）

**总计：** ~60,000 tokens（不读example）或 ~100,000 tokens（读example）

---

### 用户类型2：游戏开发者
**目标：** 实现交互式游戏引擎

**推荐加载顺序：**
1. 00-architecture.md（了解架构）
2. GDD.example（了解游戏逻辑）
3. choice-points 系列（选择点系统）🎯
4. runtime-response 系列（响应生成）
5. state-management 系列（状态管理）
6. intent-mapping 系列（意图映射）

**总计：** ~150,000 tokens（精简版）或 ~250,000 tokens（完整版）

---

### 用户类型3：AI Prompt工程师
**目标：** 优化某个模块的Prompt

**推荐加载策略：**
1. 只读取目标模块的 `{module}.design.md`
2. 参考 `{module}.example.md` 的输出格式
3. 优化 `{module}.prompt.md`

**总计：** ~30,000-50,000 tokens（单个模块）

---

## 🔄 实战示例

### 示例：用户说"帮我生成武汉的世界书1.0"

**AI应该这样做：**

```
第1步：读取 lore-v1.design.md（了解设计原则）
第2步：读取 lore-v1.example.md（参考荔湾广场的格式）
第3步：读取 lore-v1.prompt.md（使用生成器提示）
第4步：生成武汉的世界书1.0

❌ 不需要读取：GDD、choice-points、runtime-response 等其他模块
```

**Token节省：** 从 200,000 → 15,000 tokens（节省92.5%）

---

### 示例：用户说"我想实现一个选择点生成器"

**AI应该这样做：**

```
第1步：读取 00-architecture.md（了解choice-points在流程中的位置）
第2步：读取 choice-points.design.md（核心设计原则）
第3步：读取 GDD.example.md（了解游戏场景结构）
第4步：参考 choice-points.example.md（如果需要具体示例）
第5步：使用 choice-points.prompt.md 作为系统提示

❌ 不需要读取：lore-v1、protagonist、main-thread 等故事生成模块
```

**Token节省：** 从 200,000 → 80,000 tokens（节省60%）

---

## 📌 总结

**核心原则：按需加载，分层阅读**

1. **第一层（必读）：** 00-index.md + 00-architecture.md (~1,000行)
2. **第二层（按需）：** 相关模块的 .design.md (~50-500行)
3. **第三层（参考）：** 相关模块的 .example.md (~100-600行)
4. **第四层（执行）：** 相关模块的 .prompt.md (~70-500行)

**这样可以将token消耗从 200,000 降低到 10,000-80,000，提升80-95%的效率！** 🚀

---

*创建日期：2025-10-23*
*最后更新：2025-10-23*

