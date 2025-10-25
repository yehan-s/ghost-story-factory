# Bug 修复：角色提取逻辑优化

**日期**: 2025-10-24
**问题**: 主角选择被旧的 struct.json 覆盖
**状态**: ✅ 已修复并测试通过

---

## 🐛 问题描述

### 症状

用户选择生成故事时：
- 选择主角：**出租车司机**
- 故事标题：**杭州夜行记**
- 场景：**杭州街道**

但系统实际生成：
- 主角变成：**夜爬驴友** ❌
- 故事内容：**北高峰缆车** ❌
- 还生成了 8 个无关角色 ❌

### 根本原因（两个 Bug）

#### Bug 1：忽略用户选择的主角

代码错误地从 `examples/hangzhou/杭州_struct.json` 读取角色列表，完全忽略了用户选择的主角。

#### Bug 2：只检查第一个文件 ⚠️ **更严重**

当一个城市有多个故事时（多个 struct.json），代码**只检查第一个文件**：

```python
# ❌ 旧逻辑
matches = glob.glob(f"examples/*/{city}_struct.json")
if matches:
    test_path = matches[0]  # 只取第一个！
    # 如果第一个不匹配，其他文件就被忽略了
```

**场景演示**：
```
examples/hangzhou/
  ├── 杭州_struct_北高峰.json   (故事A)
  ├── 杭州_struct_西湖.json     (故事B)  ← 用户选的这个
  └── 杭州_struct_灵隐寺.json   (故事C)

# 用户选择：西湖断桥传说
# 但 glob 返回顺序可能是：[北高峰, 西湖, 灵隐寺]
# 代码只检查北高峰 → 标题不匹配 → 跳过
# ❌ 其他文件（包括西湖）被忽略了！
```

```python
# ❌ 旧逻辑（有问题）
def _extract_characters(self, main_story: str) -> list:
    # 直接读取 examples 目录的 struct.json
    struct_path = glob.glob(f"examples/*/{self.city}_struct.json")[0]

    # 使用文件里的第一个角色作为主角
    characters = []
    for idx, role_name in enumerate(potential_roles):
        characters.append({
            "name": role_name,
            "is_protagonist": (idx == 0),  # ❌ 错误！
            ...
        })
```

**问题**：
1. ❌ 无条件读取旧文件，不检查故事是否匹配
2. ❌ 忽略 `self.synopsis.protagonist`（用户选择的主角）
3. ❌ 即使故事完全不同，也强制使用旧文件的角色

---

## ✅ 修复方案

### 核心原则

1. **优先使用用户选择的主角**
2. **默认只生成单角色故事**
3. **多角色需要显式启用 + 故事标题匹配**

### 修复后的逻辑

```python
# ✅ 新逻辑（已修复）
def _extract_characters(self, main_story: str) -> list:
    # 1. 始终使用用户选择的主角
    protagonist_name = self.synopsis.protagonist

    characters = [
        {
            "name": protagonist_name,  # ✅ 正确！
            "is_protagonist": True,
            "description": f"{self.synopsis.title} - {protagonist_name}的故事"
        }
    ]

    # 2. 只有显式启用多角色模式时才查找配角
    if self.multi_character:
        # 收集所有可能的文件
        all_matches = []
        for pattern in possible_patterns:
            matches = glob.glob(pattern)
            all_matches.extend(matches)

        # 去重
        all_matches = list(set(all_matches))

        # 3. ✅ 遍历所有文件（不只是第一个！）
        for test_path in all_matches:
            struct_data = json.load(open(test_path))

            # 4. 检查故事标题是否匹配
            if struct_data.get('title') == self.synopsis.title:
                # 找到匹配的！添加配角
                ...
                break
            else:
                # 标题不匹配，继续检查下一个
                print(f"⏭️ 跳过 {test_path}：标题不匹配")
                continue

    return characters
```

**关键改进**：
- ✅ **遍历所有文件**：不再只检查第一个
- ✅ **标题验证**：确保匹配后才使用
- ✅ **清晰提示**：告诉用户跳过了哪些文件

### 新增参数

```python
class StoryGeneratorWithRetry:
    def __init__(
        self,
        city: str,
        synopsis: StorySynopsis,
        test_mode: bool = False,
        multi_character: bool = False  # ✨ 新增参数
    ):
        self.multi_character = multi_character
```

---

## 🎯 修复效果

### 场景 1：默认行为（单角色）

```python
# 用户选择
synopsis = StorySynopsis(
    title="杭州夜行记",
    protagonist="出租车司机",
    ...
)

# 生成
generator = StoryGeneratorWithRetry(city="杭州", synopsis=synopsis)
# multi_character 默认为 False

# 结果
✅ 使用主角: 出租车司机
ℹ️ [单角色模式] 只生成主角故事

角色列表:
  ⭐ 出租车司机  ← 正确！
```

### 场景 2：启用多角色但标题不匹配

```python
# 启用多角色
generator = StoryGeneratorWithRetry(
    city="杭州",
    synopsis=synopsis,
    multi_character=True
)

# 结果
✅ 使用主角: 出租车司机
🎭 [多角色模式] 尝试查找额外角色...
⚠️ 跳过 examples/hangzhou/杭州_struct.json：故事标题不匹配
    期望: 杭州夜行记
    实际: 北高峰午夜缆车空厢
ℹ️ 未找到匹配的配角，只生成主角故事

角色列表:
  ⭐ 出租车司机  ← 还是正确！
```

### 场景 3：启用多角色且标题匹配

```python
# 使用匹配的故事
synopsis = StorySynopsis(
    title="北高峰午夜缆车空厢",  # 与 struct.json 匹配
    protagonist="夜爬驴友",
    ...
)

generator = StoryGeneratorWithRetry(
    city="杭州",
    synopsis=synopsis,
    multi_character=True
)

# 结果
✅ 使用主角: 夜爬驴友
🎭 [多角色模式] 尝试查找额外角色...
✅ 从 examples/hangzhou/杭州_struct.json 添加了 7 个配角

角色列表:
  ⭐ 夜爬驴友      ← 主角正确
     索道检修工     ← 配角
     监控室值班员
     ... (共 7 个配角)
```

---

## 🧪 测试验证

### 测试 1：基础功能测试

运行测试：
```bash
uv run python test_character_fix.py
```

测试结果：
```
✅ 测试 1：单角色模式（默认）- 通过
✅ 测试 2：多角色模式（标题不匹配）- 通过
✅ 测试 3：多角色模式（标题匹配）- 通过

🎉 所有测试通过！
```

### 测试 2：多故事场景测试 🆕

运行测试：
```bash
uv run python test_multiple_stories.py
```

测试结果：
```
✅ 测试 1：在 3 个故事中找到正确的那个 - 通过
   🔍 找到 3 个 struct.json 文件，检查标题匹配...
   ✅ 从 xihu_struct.json 添加了 2 个配角

✅ 测试 2：标题与所有故事都不匹配 - 通过
   ⏭️ 跳过 xihu_struct.json：标题不匹配
   ⏭️ 跳过 lingyin_struct.json：标题不匹配
   ⏭️ 跳过 beigaofeng_struct.json：标题不匹配
   ℹ️ 所有文件标题都不匹配，只生成主角故事

✅ 测试 3：匹配第一个故事 - 通过
✅ 测试 4：匹配最后一个故事 - 通过

🎉 所有测试通过！
```

**验证内容**：
- ✅ 能在多个文件中找到标题匹配的那个
- ✅ 不会只检查第一个文件
- ✅ 无论匹配的是第几个文件都能正确找到
- ✅ 所有文件都不匹配时只生成主角

---

## 📝 使用指南

### 对于普通用户（推荐）

```bash
# 启动游戏
uv run python play_game_pregenerated.py

# 选择"生成故事" → 输入城市 → 选择故事
# 系统会自动使用单角色模式（默认）
# ✅ 只生成你选择的主角
```

**特点**：
- ✅ 简单快速（只生成 1 个角色）
- ✅ 避免混乱（不会读取旧文件）
- ✅ 符合预期（主角就是你选的）

### 对于高级用户（多角色）

如果你想生成多个角色的对话树（需要更长时间）：

```python
# 1. 准备匹配的 struct.json
# examples/你的城市/城市_struct.json
{
  "title": "完全匹配的故事标题",
  "potential_roles": ["主角", "配角1", "配角2"]
}

# 2. 在代码中启用多角色模式
from src.ghost_story_factory.pregenerator import StoryGeneratorWithRetry

generator = StoryGeneratorWithRetry(
    city="你的城市",
    synopsis=synopsis,
    multi_character=True  # ← 启用多角色
)
```

**注意**：
- ⚠️ 故事标题必须完全匹配
- ⚠️ 生成时间会成倍增加（8 个角色 = 8 倍时间）
- ⚠️ 需要更多 Token 和成本

---

## 🔧 技术细节

### 修改的文件

```
src/ghost_story_factory/pregenerator/story_generator.py
  - __init__(): 添加 multi_character 参数
  - _extract_characters(): 重构角色提取逻辑
```

### 关键改进

1. **优先级调整**：
   ```
   ❌ 旧：struct.json > 用户选择
   ✅ 新：用户选择 > struct.json
   ```

2. **安全检查**：
   ```python
   # 检查标题是否匹配
   if struct_data.get('title') == self.synopsis.title:
       # 使用配角
   else:
       # 跳过，并提示用户
   ```

3. **默认行为**：
   ```python
   # 默认 multi_character=False
   # 只生成用户选择的主角
   ```

---

## 🎓 学到的教训

### 问题根源

1. **隐式依赖旧文件**：代码依赖 examples 目录的文件，但用户不知道
2. **缺少验证**：没有检查故事是否匹配就使用数据
3. **优先级错误**：文件数据 > 用户输入（应该反过来）

### 设计原则

1. **用户输入优先**：始终优先使用用户的选择
2. **显式优于隐式**：需要特殊功能时显式启用（multi_character）
3. **防御式编程**：验证数据是否匹配再使用
4. **清晰的提示**：告诉用户发生了什么

---

## 📚 相关文档

- 快速开始：[QUICK_START.md](../QUICK_START.md)
- 命令手册：[docs/COMMANDS.md](COMMANDS.md)
- 预生成设计：[docs/PREGENERATION_DESIGN.md](PREGENERATION_DESIGN.md)

---

## ✨ 总结

**修复前**：
- ❌ 主角被旧文件覆盖
- ❌ 生成无关的角色
- ❌ 浪费时间和 Token
- ❌ 用户困惑

**修复后**：
- ✅ 主角始终是用户选择的
- ✅ 默认只生成主角（快速）
- ✅ 多角色需要显式启用
- ✅ 验证故事标题后才使用旧文件
- ✅ 清晰的提示信息

**测试状态**：✅ 所有测试通过

**推荐使用**：默认模式（单角色），简单快速！

