# TDD & DDD 测试套件总结

**创建日期**: 2025-10-24
**测试框架**: pytest
**测试哲学**: TDD (测试驱动开发) + DDD (领域驱动设计)

---

## 📊 测试统计

| 分类 | 文件数 | 测试类数 | 测试方法数 | 状态 |
|------|-------|---------|-----------|------|
| 领域模型测试 | 2 | 7 | 30+ | ✅ 已完成 |
| 单元测试 | 1 | 8 | 25+ | 🚧 待实现 |
| 集成测试 | 1 | 7 | 20+ | 🚧 待实现 |
| **总计** | **4** | **22** | **75+** | **进行中** |

---

## 🎯 测试覆盖范围

### 1. 领域模型测试（Domain Tests）✅

#### test_dialogue_tree.py

测试对话树的核心领域规则：

**GameState 值对象** (7个测试)
- ✅ 创建有效的游戏状态
- ✅ 共鸣度范围验证（0-100）
- ✅ 负数值拒绝
- ✅ 状态相似性检测（用于剪枝）
- ✅ 值对象不可变性

**DialogueNode 值对象** (9个测试)
- ✅ 创建有效节点
- ✅ 空ID/内容验证
- ✅ 结局节点不能有子节点
- ✅ 添加子节点
- ✅ 重复子节点ID检测
- ✅ 节点深度计算
- ✅ 叶子节点识别

**DialogueTree 聚合根** (6个测试)
- ✅ 创建有效树
- ✅ 重复节点ID检测
- ✅ 根据ID获取节点
- ✅ 总节点数计算
- ✅ 最大深度验证
- ✅ 剪枝相似分支

**DialogueTreeBuilder 领域服务** (2个测试)
- ✅ 创建简单测试树
- ✅ 树结构有效性验证

#### test_branch_role.py

测试支线角色的领域规则：

**BranchRole 值对象** (12个测试)
- ✅ 创建有效角色
- ✅ 值对象不可变性
- ✅ 空角色名验证
- ✅ 空支线类型验证
- ✅ 安全文件名生成
- ✅ 特殊字符处理
- ✅ 惊悚体验支线识别
- ✅ 证据支线识别
- ✅ Boss类型识别
- ✅ 值相等性判断

### 2. 单元测试（Unit Tests）🚧

#### test_dialogue_generator.py

测试对话生成器的核心逻辑：

**配置测试** (3个测试)
- ✅ 必需参数配置
- ✅ 自定义深度
- ✅ 自定义选择数

**上下文加载** (2个测试)
- 🚧 返回字典结构
- 🚧 读取文件

**场景生成** (2个测试)
- 🚧 返回字符串
- 🚧 调用LLM

**选择生成** (2个测试)
- 🚧 返回列表
- 🚧 遵守配置限制

**树构建** (2个测试)
- 🚧 创建树结构
- 🚧 遵守最大深度

**剪枝策略** (2个测试)
- 🚧 返回剪枝数量
- 🚧 减少节点数

**保存加载** (2个测试)
- 🚧 写入JSON
- 🚧 创建输出目录

**完整流程** (2个测试)
- 🚧 执行完整流程
- 🚧 创建输出文件

**进度追踪** (2个测试)
- 🚧 计数从0开始
- 🚧 计数递增

### 3. 集成测试（Integration Tests）🚧

#### test_dialogue_pregeneration_flow.py

测试端到端流程：

**完整流程** (4个测试)
- 🚧 端到端生成
- 🚧 树结构有效性
- 🚧 剪枝效果
- 🚧 加载保存的树

**Mock LLM** (2个测试)
- 🚧 使用模拟响应
- 🚧 错误处理

**性能测试** (2个测试)
- 🚧 时间限制
- 🚧 内存限制

**持久化** (2个测试)
- 🚧 保存加载
- 🚧 JSON格式验证

**真实文件** (1个测试)
- 🚧 杭州示例生成

**错误处理** (3个测试)
- 🚧 缺失文件
- 🚧 无效JSON
- 🚧 权限错误

**进度报告** (2个测试)
- 🚧 回调调用
- 🚧 进度递增

---

## 🏗️ 测试架构设计

### DDD 分层

```
领域层（Domain Layer）
  └─ 值对象（Value Objects）
      ├─ GameState: 游戏状态
      ├─ DialogueNode: 对话节点
      └─ BranchRole: 支线角色
  └─ 聚合根（Aggregate Root）
      └─ DialogueTree: 对话树
  └─ 领域服务（Domain Services）
      └─ DialogueTreeBuilder: 树构建器

应用层（Application Layer）
  └─ 应用服务（Application Services）
      └─ DialogueGenerator: 对话生成器

基础设施层（Infrastructure Layer）
  ├─ LLM客户端
  ├─ 文件系统
  └─ 数据持久化
```

### TDD 工作流

```
1. RED（红灯）
   ├─ 编写失败的测试
   └─ 验证测试确实失败

2. GREEN（绿灯）
   ├─ 编写最小实现
   └─ 使测试通过

3. REFACTOR（重构）
   ├─ 改进代码质量
   └─ 保持测试通过
```

---

## 📋 测试规范

### 命名规范

```python
# 测试文件
test_<模块名>.py

# 测试类
class Test<功能名>:
    pass

# 测试方法
def test_<功能>_<预期行为>():
    """测试：<中文描述>"""
    pass
```

### AAA 模式

```python
def test_example():
    # Given (Arrange): 准备测试数据
    config = DialogueGeneratorConfig(...)

    # When (Act): 执行被测试的操作
    result = generator.generate()

    # Then (Assert): 验证结果
    assert result is not None
```

### 测试标记

```python
@pytest.mark.unit          # 单元测试
@pytest.mark.integration   # 集成测试
@pytest.mark.domain        # 领域模型测试
@pytest.mark.slow          # 慢测试
@pytest.mark.skip_ci       # CI跳过
```

---

## 🚀 运行测试

### 安装依赖

```bash
pip install -r requirements-dev.txt
```

### 运行所有测试

```bash
pytest
```

### 按标记运行

```bash
# 只运行领域测试（快速）
pytest -m domain

# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 排除慢测试
pytest -m "not slow"
```

### 代码覆盖率

```bash
pytest --cov=src/ghost_story_factory --cov-report=html
open htmlcov/index.html
```

---

## 📈 覆盖率目标

| 层级 | 目标覆盖率 | 当前状态 | 优先级 |
|------|-----------|---------|--------|
| 领域模型 | 95%+ | ✅ 测试完成 | P0 |
| 应用服务 | 90%+ | 🚧 待实现 | P1 |
| 基础设施 | 80%+ | 🚧 待实现 | P2 |
| 集成测试 | 80%+ | 🚧 待实现 | P2 |

---

## 🎯 下一步计划

### Phase 1: 完成单元测试 🚧

**目标**: 实现 DialogueGenerator 并通过所有单元测试

**任务**:
1. 实现 `load_context()` 方法
2. 实现 `generate_scene_content()` 方法
3. 实现 `generate_choices()` 方法
4. 实现 `build_dialogue_tree()` 方法
5. 实现 `apply_pruning()` 方法
6. 实现 `save_tree()` 方法

**预计时间**: 2-3天

### Phase 2: 完成集成测试 🚧

**目标**: 端到端流程测试通过

**任务**:
1. 集成LLM客户端（Kimi API）
2. 实现文件读写
3. 实现进度报告
4. 添加错误处理
5. 性能优化

**预计时间**: 1-2天

### Phase 3: 实现CLI工具 ⏳

**目标**: 创建 pregenerate_dialogues.py 命令行工具

**任务**:
1. 命令行参数解析
2. 进度条显示
3. 日志输出
4. 断点续传
5. 统计报告

**预计时间**: 1天

---

## ✅ 测试质量保证

### 代码审查检查项

- [ ] 测试是否独立？（无依赖顺序）
- [ ] 测试是否快速？（< 1秒）
- [ ] 测试是否清晰？（命名 + 文档）
- [ ] 是否使用AAA模式？
- [ ] 是否有适当的断言？
- [ ] Mock使用是否合理？
- [ ] 是否测试了边界情况？
- [ ] 是否测试了错误处理？

### 持续集成

```yaml
# 建议的CI流程
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest -m unit
      - name: Run integration tests
        run: pytest -m integration -m "not slow"
      - name: Coverage report
        run: pytest --cov --cov-report=xml
```

---

## 📚 参考资料

- [Pytest 官方文档](https://docs.pytest.org/)
- [Domain-Driven Design](https://www.domainlanguage.com/ddd/)
- [Test-Driven Development by Example](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)

---

## 🤝 贡献

如需添加新测试或改进现有测试，请参考：
- `tests/README.md` - 详细测试指南
- `pytest.ini` - 测试配置
- 现有测试文件作为示例

---

**更新日期**: 2025-10-24
**维护者**: Ghost Story Factory Team
**状态**: 进行中（领域层已完成，应用层和集成测试待实现）

