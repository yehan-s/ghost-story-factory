# 故事示例 (Examples)

这个目录包含使用 Ghost Story Factory 生成的城市灵异故事示例。

---

## 📁 目录结构

```
examples/
├── hangzhou/     # 杭州 - 完整示例 ⭐ 推荐参考
├── wuhan/        # 武汉 - 部分示例
├── guangzhou/    # 广州 - 经典故事
└── test-city/    # 测试城 - 测试数据
```

---

## 🎭 城市故事列表

### hangzhou/ - 杭州（完整示例）⭐

**故事名称**: 北高峰午夜缆车空厢
**主角**: 特检院工程师 - 顾栖迟
**状态**: ✅ 完整（所有阶段已生成）

**包含文件**:
```
杭州_candidates.json   # Stage 1: 候选故事列表
杭州_struct.json       # Stage 1: 故事结构框架
杭州_lore.json         # Stage 2: Lore v1（世界观基础）
杭州_protagonist.md    # Stage 2: 主角分析报告
杭州_lore_v2.md        # Stage 3: Lore v2（含游戏系统）
杭州_GDD.md            # Stage 3: AI 导演任务简报
杭州_main_thread.md    # Stage 4: 主线完整故事 (≥5000字)
杭州_story.md          # Stage 4: 简化版故事
```

**推荐阅读顺序**:
1. `杭州_protagonist.md` - 了解主角分析方法
2. `杭州_GDD.md` - 学习游戏设计文档
3. `杭州_main_thread.md` - 阅读完整故事

**故事简介**:
特检院工程师顾栖迟受命对北高峰停运索道进行安全复核。在雨夜测试中，他用频谱仪捕获到神秘的 65 Hz 低频竖线，监控却显示一切静止。随着调查深入，他发现这不仅是设备故障，而是一个隐藏在城市暗层的"共鸣"系统...

---

### wuhan/ - 武汉（部分示例）

**故事名称**: （多个候选）
**主角**: 夜跑者
**状态**: 🔄 部分（Stage 1-2 已生成）

**包含文件**:
```
武汉_candidates.json       # 候选故事列表
武汉_lore.json             # Lore v1
武汉_role_夜跑者.json      # 主角设计
武汉_struct.json           # 故事结构
武汉_story.md              # 简化版故事
```

---

### guangzhou/ - 广州（经典故事）

**故事名称**: 荔湾广场·第七块玻璃
**主角**: 夜班保安
**状态**: ✅ 经典templates

**包含文件**:
```
广州_荔湾广场_第七块玻璃.md  # 完整故事templates
```

**故事简介**:
荔湾广场的都市传说 - "第七块玻璃"与"借光"仪式。这是项目的经典templates故事，展示了理想的叙事风格和恐怖氛围营造。

---

### test-city/ - 测试城（测试数据）

**用途**: 开发测试
**状态**: 🧪 测试数据

**包含文件**:
```
测试城_lore.json           # 测试用 Lore v1
测试城_role_保安.json      # 测试用主角设计
```

---

## 🚀 如何生成新的城市故事

### 方法 1: 自动化流程（推荐）

```bash
# 一键生成完整故事
gen-complete --city "北京" --index 1

# 输出位置：项目根目录
# 北京_candidates.json
# 北京_struct.json
# 北京_lore.json
# 北京_protagonist.md
# 北京_lore_v2.md
# 北京_GDD.md
# 北京_main_thread.md
```

### 方法 2: 分步执行

```bash
# Step 1: 生成候选
set-city --city "北京"

# Step 2: 选择故事（假设选第1个）
get-struct --city "北京" --index 1

# Step 3: 生成世界观
get-lore --city "北京"

# Step 4: 生成主角
gen-protagonist --city "北京"

# Step 5: 生成 Lore v2
gen-lore-v2 --city "北京"

# Step 6: 生成 GDD
gen-gdd --city "北京"

# Step 7: 生成主线故事
gen-main-thread --city "北京"
```

### 整理到 examples/

```bash
# 创建城市文件夹
mkdir examples/beijing

# 移动生成的文件
mv 北京_* examples/beijing/
```

---

## 📋 文件命名规范

### 生成的文件命名格式

```
{城市拼音}_{模块}.{扩展名}

示例：
- hangzhou_candidates.json
- hangzhou_lore.json
- hangzhou_protagonist.md
- hangzhou_GDD.md
- hangzhou_main_thread.md
```

**注意**: 历史文件使用中文命名（如 `杭州_lore.json`），新生成的文件建议使用拼音。

---

## 🔍 文件说明

### Stage 1: 候选与结构
- `*_candidates.json` - 候选故事列表（3-5个）
- `*_struct.json` - 选中故事的结构框架

### Stage 2: 世界观基础
- `*_lore.json` - Lore v1（世界观、规则、意象、地理）
- `*_protagonist.md` - 主角分析报告（8种角色评估）

### Stage 3: 系统增强
- `*_lore_v2.md` - Lore v2（含游戏系统：共鸣度、后果树、实体AI）
- `*_GDD.md` - AI 导演任务简报（6个场景、抉择点、触发机制）

### Stage 4: 故事生成
- `*_main_thread.md` - 主线完整故事（≥5000字，第一人称）
- `*_story.md` - 简化版故事（快速生成）
- `*_branch_*.md` - 分支故事（可选）

---

## 📊 质量参考

### ⭐⭐⭐⭐⭐ 完整示例
- **hangzhou/** - 所有阶段完整，可直接参考

### ⭐⭐⭐ 部分示例
- **wuhan/** - 前期阶段完整，可补充后续

### ⭐⭐⭐⭐⭐ 经典templates
- **guangzhou/** - 高质量templates，叙事标杆

### ⭐ 测试数据
- **test-city/** - 仅用于开发测试

---

## 💡 使用建议

### 学习叙事设计
1. 先读 `hangzhou/杭州_protagonist.md` 了解主角分析方法
2. 再读 `hangzhou/杭州_GDD.md` 学习游戏设计
3. 对比 `guangzhou/广州_荔湾广场_第七块玻璃.md` 学习叙事风格

### 快速生成故事
1. 使用 `gen-complete --city "城市名" --index 1`
2. 等待 5-10 分钟
3. 得到完整的故事文件

### 自定义创作
1. 分步执行命令，在每个阶段查看输出
2. 根据需要调整参数或手动编辑中间文件
3. 继续下一阶段

---

## 🗂️ 归档建议

生成新故事后，建议：
1. 创建城市文件夹（使用拼音）：`mkdir examples/城市拼音`
2. 移动所有相关文件：`mv 城市_* examples/城市拼音/`
3. 添加到本 README 的城市列表

---

**最后更新**: 2025-10-24
**示例总数**: 4 个城市

