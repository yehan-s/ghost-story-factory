# Ghost Story Factory - 测试套件

完整的TDD和DDD测试套件，用于静态对话预生成系统。

## 📂 测试结构

```
tests/
├── domain/                    # 领域模型测试（DDD）
│   ├── test_dialogue_tree.py     # 对话树领域模型
│   └── test_branch_role.py       # 支线角色领域模型
├── unit/                      # 单元测试（TDD）
│   └── test_dialogue_generator.py # 对话生成器单元测试
├── integration/               # 集成测试
│   └── test_dialogue_pregeneration_flow.py # 端到端流程测试
└── README.md                 # 本文件
```

## 🎯 测试分层

### 1. 领域模型测试（Domain Tests）

**目的**：测试核心业务规则和领域对象

**文件**：
- `domain/test_dialogue_tree.py` - 对话树聚合根测试
  - `GameState` 值对象
  - `DialogueNode` 值对象
  - `DialogueTree` 聚合根
  - `DialogueTreeBuilder` 领域服务

**特点**：
- ✅ 无外部依赖
- ✅ 测试不变性（Immutability）
- ✅ 测试业务规则
- ✅ 快速执行（< 1秒）

### 2. 单元测试（Unit Tests）

**目的**：测试单个组件的功能

**文件**：
- `unit/test_dialogue_generator.py` - 对话生成器测试
  - 配置加载
  - 场景生成
  - 选择生成
  - 树构建
  - 剪枝策略

**特点**：
- ✅ 使用Mock隔离依赖
- ✅ 测试单一职责
- ✅ TDD驱动开发
- ✅ 快速执行（< 5秒）

### 3. 集成测试（Integration Tests）

**目的**：测试端到端流程

**文件**：
- `integration/test_dialogue_pregeneration_flow.py` - 完整流程测试
  - 文件读写
  - LLM集成
  - 树持久化
  - 错误处理

**特点**：
- ⚠️ 有外部依赖（文件系统、Mock LLM）
- ⚠️ 较慢（可能几秒到几分钟）
- ✅ 真实场景验证

## 🚀 运行测试

### 安装测试依赖

```bash
# 安装pytest和相关插件
pip install pytest pytest-cov pytest-mock

# 或使用uv
uv pip install pytest pytest-cov pytest-mock
```

### 运行所有测试

```bash
pytest
```

### 按类型运行

```bash
# 只运行领域模型测试
pytest -m domain

# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢测试
pytest -m "not slow"
```

### 运行特定文件

```bash
# 运行对话树测试
pytest tests/domain/test_dialogue_tree.py

# 运行生成器测试
pytest tests/unit/test_dialogue_generator.py

# 运行集成测试
pytest tests/integration/
```

### 运行特定测试

```bash
# 运行特定测试类
pytest tests/domain/test_dialogue_tree.py::TestGameStateDomain

# 运行特定测试方法
pytest tests/domain/test_dialogue_tree.py::TestGameStateDomain::test_valid_game_state_creation
```

### 代码覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src/ghost_story_factory --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 详细输出

```bash
# 显示print输出
pytest -s

# 显示详细错误
pytest -vv

# 显示最慢的10个测试
pytest --durations=10
```

## 📋 测试标记（Markers）

```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试
@pytest.mark.domain        # 领域模型测试
@pytest.mark.slow          # 慢测试（> 1分钟）
@pytest.mark.skip_ci       # CI环境跳过
```

## 🎨 测试命名规范

### 测试方法命名

```python
def test_<被测试的功能>_<预期行为>():
    """测试：<中文描述>"""
    pass

# 示例
def test_game_state_creation_with_valid_values():
    """测试：使用有效值创建游戏状态"""
    pass

def test_empty_node_id_raises_error():
    """测试：空节点ID应抛出错误"""
    pass
```

### AAA模式（Arrange-Act-Assert）

```python
def test_example():
    # Given: 准备测试数据
    state = GameState(pr=50, gr=30, wf=20)
    
    # When: 执行被测试的操作
    result = state.is_similar_to(other_state)
    
    # Then: 验证结果
    assert result is True
```

## 📊 测试覆盖率目标

| 组件 | 覆盖率目标 | 当前状态 |
|------|----------|---------|
| 领域模型 | 95%+ | ✅ 已完成 |
| 对话生成器 | 90%+ | 🚧 待实现 |
| 集成流程 | 80%+ | 🚧 待实现 |

## 🔧 TDD 工作流程

### 1. 红灯（Red）- 写失败的测试

```python
def test_generate_scene_content_returns_string():
    """测试：生成场景内容返回字符串"""
    # Given
    generator = DialogueGenerator(config)
    
    # When
    content = generator.generate_scene_content("场景描述", {})
    
    # Then
    assert isinstance(content, str)  # ❌ 此时会失败，因为还未实现
```

### 2. 绿灯（Green）- 实现最小代码使测试通过

```python
class DialogueGenerator:
    def generate_scene_content(self, scene_desc: str, state: Dict) -> str:
        return "临时内容"  # ✅ 最简单的实现
```

### 3. 重构（Refactor）- 改进代码质量

```python
class DialogueGenerator:
    def generate_scene_content(self, scene_desc: str, state: Dict) -> str:
        # ✅ 改进后的实现
        prompt = self._build_scene_prompt(scene_desc, state)
        return self.llm_client.generate(prompt)
```

## 🐛 调试测试

### 进入调试器

```python
def test_example():
    import pdb; pdb.set_trace()  # 设置断点
    assert True
```

### 查看变量

```bash
pytest -s  # 显示print输出
pytest --pdb  # 失败时自动进入调试器
```

## 📚 最佳实践

### ✅ 好的测试

```python
def test_valid_state_creation():
    """测试：创建有效状态"""
    # Given
    pr, gr, wf = 50.0, 30.0, 20.0
    
    # When
    state = GameState(personal_resonance=pr, group_resonance=gr, world_fatigue=wf)
    
    # Then
    assert state.personal_resonance == pr
    assert state.group_resonance == gr
```

**特点**：
- ✅ 测试一个功能
- ✅ 清晰的AAA结构
- ✅ 描述性的命名
- ✅ 无外部依赖

### ❌ 不好的测试

```python
def test_stuff():
    # 测试多个功能
    state = GameState(50, 30, 20)
    assert state.personal_resonance == 50
    node = DialogueNode("id", NodeType.SCENE, "content", state)
    assert node.id == "id"
    tree = DialogueTree(node)
    assert tree.total_nodes() == 1
```

**问题**：
- ❌ 测试太多功能
- ❌ 命名不清晰
- ❌ 难以定位失败原因

## 📖 参考资料

- [Pytest 文档](https://docs.pytest.org/)
- [DDD 领域驱动设计](https://domainlanguage.com/ddd/)
- [TDD 测试驱动开发](https://testdriven.io/test-driven-development/)

## 🤝 贡献指南

添加新测试时：

1. **选择正确的目录**：
   - 领域模型 → `domain/`
   - 业务逻辑 → `unit/`
   - 端到端流程 → `integration/`

2. **遵循命名规范**：
   - 文件：`test_<模块名>.py`
   - 类：`Test<功能名>`
   - 方法：`test_<功能>_<行为>()`

3. **添加文档字符串**：
   ```python
   def test_example():
       """测试：简短的中文描述"""
   ```

4. **使用合适的标记**：
   ```python
   @pytest.mark.unit
   @pytest.mark.slow  # 如果测试很慢
   ```

5. **运行测试验证**：
   ```bash
   pytest tests/your_new_test.py
   ```

---

**最后更新**: 2025-10-24
**测试框架**: pytest 7.4+
**覆盖率**: 待完善

