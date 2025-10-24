# 快速参考卡片 - Ghost Story Factory

## ⚡ 推荐流程（自动流水线）- 最简单！

```bash
# Step 1: 获取候选故事
set-city --city "杭州"

# Step 2: 选择故事框架
get-struct --city "杭州" --index 1

# Step 3: 自动生成所有内容（一条命令完成！）
gen-complete --city "杭州" --index 1
```

**一键完成：** Lore v1 → 主角设计 → Lore v2 → GDD → 主线故事

---

## 🎯 完整流程（手动分步，可选）

```bash
# Step 1-2: 选择故事（同上）
set-city --city "杭州"
get-struct --city "杭州" --index 1

# Step 3-7: 手动分步执行（如需精细控制）
get-lore --city "杭州" --index 1
gen-protagonist --city "杭州"
gen-lore-v2 --city "杭州"
gen-gdd --city "杭州"
gen-main-thread --city "杭州"
```

## ⚡ 快速流程（3步）

```bash
set-city --city "杭州"
get-struct --city "杭州" --index 1
get-story --city "杭州"
```

## 📁 输出文件清单

### 完整流程输出
- `杭州_candidates.json` - 候选列表
- `杭州_struct.json` - 故事结构
- `杭州_lore.json` - Lore v1 (JSON)
- `杭州_protagonist.md` - 主角设计
- `杭州_lore_v2.md` - Lore v2 (系统增强)
- `杭州_GDD.md` - AI导演任务简报
- `杭州_main_thread.md` - 主线故事 (≥5000字)

### 快速流程输出
- `杭州_candidates.json` - 候选列表
- `杭州_struct.json` - 故事结构
- `杭州_story.md` - 简化故事

## 🔧 可选命令

```bash
# 生成分支故事
gen-branch --city "杭州" --branch-name "店主线"

# 生成角色拍点（旧版）
gen-role --city "杭州" --role "保安"

# 验证一致性（旧版）
validate-role --city "杭州" --role "保安"
```

## 📖 详细说明

查看 **[WORKFLOW.md](./WORKFLOW.md)** 获取完整文档。

