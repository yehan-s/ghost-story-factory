# 📚 文档索引

## 🚀 快速导航

### 新手入门（按顺序阅读）

1. **[QUICK_START.md](QUICK_START.md)** ⭐⭐⭐
   - 5 分钟快速上手
   - 环境配置
   - 第一次运行

2. **[docs/COMMANDS.md](docs/COMMANDS.md)** ⭐⭐
   - 所有命令详解
   - 使用场景示例
   - 常见问题解答

3. **[docs/CHECKPOINT_RESUME.md](docs/CHECKPOINT_RESUME.md)** ⭐
   - 断点续传使用说明
   - 恢复流程
   - 最佳实践

---

## 📖 完整文档列表

### 核心文档

| 文档 | 类型 | 说明 | 推荐度 |
|------|------|------|-------|
| [README.md](README.md) | 总览 | 项目介绍、功能特性、架构概览 | ⭐⭐⭐ |
| [QUICK_START.md](QUICK_START.md) | 教程 | 5分钟快速开始 | ⭐⭐⭐ |
| [docs/COMMANDS.md](docs/COMMANDS.md) | 参考 | 命令速查手册 | ⭐⭐⭐ |

### 功能文档

| 文档 | 说明 | 适合人群 |
|------|------|---------|
| [docs/PREGENERATION_DESIGN.md](docs/PREGENERATION_DESIGN.md) | 静态对话预生成系统设计 | 开发者 |
| [docs/CHECKPOINT_RESUME.md](docs/CHECKPOINT_RESUME.md) | 断点续传功能说明 | 所有用户 |
| [docs/CHECKPOINT_FEATURE_COMPLETE.md](docs/CHECKPOINT_FEATURE_COMPLETE.md) | 断点续传实现报告 | 开发者 |

### 配置文档

| 文档 | 说明 |
|------|------|
| [ENV_EXAMPLE.md](ENV_EXAMPLE.md) | 环境变量配置示例 |
| [docs/OPTIMIZATION_SUMMARY.md](docs/OPTIMIZATION_SUMMARY.md) | 性能优化总结 |

### 开发文档

| 文档 | 说明 |
|------|------|
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | 项目状态 |
| [docs/specs/SPEC_TODO.md](docs/specs/SPEC_TODO.md) | 开发规格与待办 |

---

## 🔍 按需查找

### 我想...

#### 快速开始使用

👉 [QUICK_START.md](QUICK_START.md)

#### 了解所有命令

👉 [docs/COMMANDS.md](docs/COMMANDS.md)

#### 使用断点续传功能

👉 [docs/CHECKPOINT_RESUME.md](docs/CHECKPOINT_RESUME.md)

#### 配置环境变量

👉 [ENV_EXAMPLE.md](ENV_EXAMPLE.md)

#### 了解技术实现

👉 [docs/PREGENERATION_DESIGN.md](docs/PREGENERATION_DESIGN.md)

#### 解决问题

👉 [docs/COMMANDS.md](docs/COMMANDS.md) - 常见问题部分

#### 了解项目全貌

👉 [README.md](README.md)

---

## 📂 文档目录结构

```
ghost-story-factory/
│
├── README.md                        # 项目总览
├── QUICK_START.md                   # 快速开始
├── DOCUMENTATION_INDEX.md           # 本文档（文档索引）
│
├── ENV_EXAMPLE.md                   # 环境配置示例
├── PROJECT_STATUS.md                # 项目状态
│
├── docs/
│   ├── COMMANDS.md                  # 命令速查手册 ⭐
│   ├── CHECKPOINT_RESUME.md         # 断点续传说明
│   ├── CHECKPOINT_FEATURE_COMPLETE.md  # 实现报告
│   ├── PREGENERATION_DESIGN.md      # 预生成设计
│   ├── OPTIMIZATION_SUMMARY.md      # 优化总结
│   │
│   └── specs/
│       └── SPEC_TODO.md             # 开发规格
│
└── ...
```

---

## 🎯 推荐阅读路径

### 路径1：新手快速上手

```
QUICK_START.md
    ↓
docs/COMMANDS.md (基础命令部分)
    ↓
开始使用！
    ↓
遇到问题？查 docs/COMMANDS.md (FAQ部分)
```

### 路径2：深入了解系统

```
README.md
    ↓
docs/PREGENERATION_DESIGN.md
    ↓
docs/CHECKPOINT_RESUME.md
    ↓
docs/CHECKPOINT_FEATURE_COMPLETE.md
```

### 路径3：配置优化

```
ENV_EXAMPLE.md
    ↓
docs/OPTIMIZATION_SUMMARY.md
    ↓
docs/COMMANDS.md (环境配置部分)
```

---

## 📊 文档更新记录

| 日期 | 文档 | 更新内容 |
|------|------|---------|
| 2025-10-24 | docs/COMMANDS.md | 新建命令速查手册 |
| 2025-10-24 | QUICK_START.md | 新建快速开始指南 |
| 2025-10-24 | README.md | 更新预生成模式和文档索引 |
| 2025-10-24 | docs/CHECKPOINT_RESUME.md | 新建断点续传说明 |
| 2025-10-24 | docs/CHECKPOINT_FEATURE_COMPLETE.md | 新建实现报告 |
| 2025-10-24 | check_progress.sh | 新建进度查看脚本 |

---

## 💡 使用技巧

### 快速查找命令

使用 `Ctrl+F` 在 [docs/COMMANDS.md](docs/COMMANDS.md) 中搜索关键词：
- 搜索 "启动" - 找到所有启动命令
- 搜索 "检查点" - 找到断点续传相关内容
- 搜索 "错误" - 找到故障排除部分

### 离线阅读

所有文档都是 Markdown 格式，可以：
- 在 GitHub 上直接阅读
- 用任何文本编辑器打开
- 用 Markdown 阅读器查看

### 打印友好

如果需要打印文档：
1. 在浏览器中打开 Markdown 文件
2. 使用浏览器的打印功能
3. 选择"保存为 PDF"

---

## 🆘 获取帮助

### 文档中找不到答案？

1. 查看 [docs/COMMANDS.md](docs/COMMANDS.md) 的"常见问题"部分
2. 查看 [docs/CHECKPOINT_RESUME.md](docs/CHECKPOINT_RESUME.md) 的"常见问题"部分
3. 查看 [GitHub Issues](https://github.com/your-username/ghost-story-factory/issues)

### 报告文档问题

如果发现文档中的错误或需要补充：
1. 提交 [GitHub Issue](https://github.com/your-username/ghost-story-factory/issues/new)
2. 标记为 `documentation`
3. 描述问题或建议

---

<p align="center">
  <strong>Happy Reading! 📖</strong>
</p>

