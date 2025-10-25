# 🧪 测试指南

## 测试文件说明

### 核心测试

| 测试文件 | 测试内容 | 运行时间 |
|---------|---------|----------|
| `test_database.py` | 数据库系统（SQLite CRUD 操作） | ~5秒 |
| `test_full_flow.py` | 完整流程（简介生成、数据库、对话树加载、菜单） | ~15秒 |
| `test_engine_integration.py` | GameEngine 集成（预生成模式） | ~5秒 |

---

## 快速测试

### 运行所有测试

```bash
# 使用统一测试套件（推荐）
python3 run_all_tests.py
```

### 运行单个测试

```bash
# 数据库测试
python3 test_database.py

# 完整流程测试
python3 test_full_flow.py

# GameEngine 集成测试
python3 test_engine_integration.py
```

---

## 测试覆盖范围

### 1. 数据库系统测试 (`test_database.py`)

**测试内容**:
- ✅ 数据库初始化（5张表）
- ✅ 创建城市
- ✅ 保存故事（包括对话树）
- ✅ 查询城市列表
- ✅ 查询故事列表
- ✅ 查询角色列表
- ✅ 加载对话树
- ✅ Gzip 压缩/解压

**预期输出**:
```
======================================================================
✅ 数据库测试完成！
======================================================================
```

---

### 2. 完整流程测试 (`test_full_flow.py`)

**测试内容**:
- ✅ 故事简介生成（调用 Kimi LLM）
- ✅ 数据库操作
- ✅ 对话树加载
- ✅ 菜单组件初始化

**预期输出**:
```
╔══════════════════════════════════════════════════════════════════╗
║              ✅ 所有测试通过！                                  ║
╚══════════════════════════════════════════════════════════════════╝

📋 测试总结：
   ✅ 故事简介生成: 正常
   ✅ 数据库操作: 正常
   ✅ 对话树加载: 正常
   ✅ 菜单组件: 正常
```

---

### 3. GameEngine 集成测试 (`test_engine_integration.py`)

**测试内容**:
- ✅ GameEngine 初始化（预生成模式）
- ✅ 对话加载和节点导航
- ✅ Choice 对象转换
- ✅ 双模式支持验证

**预期输出**:
```
╔══════════════════════════════════════════════════════════════════╗
║              ✅ 测试结果总结                                    ║
╚══════════════════════════════════════════════════════════════════╝

   ✅ PASS - 引擎初始化
   ✅ PASS - 对话加载

🎉 所有测试通过！GameEngine 集成完成！
```

---

## 测试环境要求

### 必需的环境变量

```bash
# Kimi API 配置
export KIMI_API_KEY="your-api-key"
export KIMI_API_BASE="https://api.moonshot.cn/v1"

# 可选：指定模型
export KIMI_MODEL_CHOICES="moonshot-v1-32k"      # 选择生成（快速）
export KIMI_MODEL_RESPONSE="kimi-k2-0905-preview" # 响应生成（高质量）
export KIMI_MODEL_OPENING="kimi-k2-0905-preview"  # 开场生成（高质量）
```

### 依赖包

```bash
pip install -r requirements.txt
```

主要依赖：
- `crewai` - LLM 编排
- `rich` - 终端 UI
- `pydantic` - 数据验证

---

## 故障排除

### 问题 1: Kimi API 调用失败

**症状**:
```
❌ LLM 初始化失败
```

**解决方案**:
1. 检查环境变量是否设置
2. 验证 API Key 有效性
3. 确认网络连接

```bash
# 检查环境变量
echo $KIMI_API_KEY
echo $KIMI_API_BASE

# 测试 API 连接
curl -H "Authorization: Bearer $KIMI_API_KEY" \
     $KIMI_API_BASE/models
```

---

### 问题 2: 数据库文件锁定

**症状**:
```
sqlite3.OperationalError: database is locked
```

**解决方案**:
```bash
# 删除测试数据库
rm database/ghost_stories_test.db

# 重新运行测试
python3 test_database.py
```

---

### 问题 3: CrewAI 未安装

**症状**:
```
ModuleNotFoundError: No module named 'crewai'
```

**解决方案**:
```bash
# 使用国内镜像安装
pip install crewai -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 测试数据

测试使用的数据库：
- **位置**: `database/ghost_stories_test.db`
- **大小**: ~50KB（包含测试故事和对话树）
- **内容**:
  - 1 个城市（杭州）
  - 2 个故事（钱江新城观景台诡异事件）
  - 2 个角色（特检院工程师、夜班保安）
  - 1 个对话树（3 个节点）

**清理测试数据**:
```bash
rm database/ghost_stories_test.db
```

---

## 持续集成

如果要在 CI/CD 中运行测试：

```bash
# 1. 设置环境变量（示例）
export KIMI_API_KEY="${KIMI_API_KEY}"
export KIMI_API_BASE="https://api.moonshot.cn/v1"

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行测试套件
python3 run_all_tests.py

# 4. 检查退出码
if [ $? -eq 0 ]; then
    echo "✅ 所有测试通过"
else
    echo "❌ 测试失败"
    exit 1
fi
```

---

## 贡献测试

如果你要添加新的测试：

1. **命名规范**: `test_<功能名>.py`
2. **放置位置**: 项目根目录
3. **导入路径**: 使用相对导入
4. **输出格式**: 使用 Rich 库格式化输出
5. **返回码**: 成功返回 0，失败返回 1

**示例模板**:
```python
#!/usr/bin/env python3
"""
<功能名> 测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console


def test_something():
    """测试某功能"""
    console = Console()

    try:
        # 测试逻辑
        assert True
        console.print("✅ 测试通过")
        return True
    except Exception as e:
        console.print(f"[red]❌ 测试失败: {e}[/red]")
        return False


def main():
    """主函数"""
    console = Console()

    console.print("\n╔═══ 测试标题 ═══╗\n")

    results = []
    results.append(("测试1", test_something()))

    # 总结
    all_passed = all(r[1] for r in results)

    if all_passed:
        console.print("\n✅ 所有测试通过\n")
        return 0
    else:
        console.print("\n❌ 部分测试失败\n")
        return 1


if __name__ == "__main__":
    exit(main())
```

---

## 性能基准

| 测试 | 预期时间 | 实际时间 | 状态 |
|-----|---------|---------|------|
| 数据库测试 | ~5秒 | - | ⏱️ |
| 完整流程测试 | ~15秒 | - | ⏱️ |
| GameEngine测试 | ~5秒 | - | ⏱️ |
| **总计** | **~25秒** | - | ⏱️ |

> 注：实际时间会因网络状况和 LLM API 响应速度而有所不同

---

**最后更新**: 2025-10-24
**维护者**: AI Assistant

