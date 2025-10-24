# Ghost Story Factory - 使用指南

## ⚡ 快速开始

### 1. 配置环境变量

编辑 `.env` 文件（或创建一个）：

```bash
# 必需
KIMI_API_KEY=your_kimi_api_key_here
KIMI_API_BASE=https://api.moonshot.cn/v1

# 推荐配置（平衡速度和质量）
KIMI_MODEL_CHOICES=moonshot-v1-32k
KIMI_MODEL_RESPONSE=kimi-k2-0905-preview
KIMI_MODEL_OPENING=kimi-k2-0905-preview
```

### 2. 启动游戏

```bash
./play_now.sh
```

就这么简单！

---

## 🎮 游戏操作

### 选择选项
- 输入数字（如 `1`, `2`, `3`）选择对应选项
- 或输入 `5` 保存进度
- 或输入 `6` 退出游戏

### 游戏提示
游戏运行时会显示使用的模型：
```
�� [选择点] 使用模型: moonshot-v1-32k
🤖 [响应] 使用模型: kimi-k2-0905-preview
🤖 [开场] 使用模型: kimi-k2-0905-preview
```

---

## ⚙️ 配置说明

### 模型选择

| 模型 | 速度 | 质量 | 使用场景 |
|------|------|------|----------|
| `moonshot-v1-8k` | ⚡⚡⚡ 最快 | ⭐⭐ | 简单任务 |
| `moonshot-v1-32k` | ⚡⚡ 较快 | ⭐⭐⭐ | 选择点生成（推荐） |
| `kimi-k2-0905-preview` | ⚡ 较慢 | ⭐⭐⭐⭐⭐ | 叙事创作（推荐） |

### 推荐配置方案

#### 平衡方案（推荐）⭐
```bash
KIMI_MODEL_CHOICES=moonshot-v1-32k
KIMI_MODEL_RESPONSE=kimi-k2-0905-preview
KIMI_MODEL_OPENING=kimi-k2-0905-preview
```

#### 全速模式
```bash
KIMI_MODEL=moonshot-v1-32k
```

#### 全质量模式
```bash
KIMI_MODEL=kimi-k2-0905-preview
```

---

## 📊 性能指标

使用推荐配置（平衡方案）：

| 功能 | 时间 |
|------|------|
| 首次选择生成 | 15-20秒 |
| 后续选择生成 | 0秒（预加载） |
| 响应生成 | 30-40秒 |

---

## 🎯 游戏时长

基于 15 秒/选择的估算：
- 单次游玩：15-20 分钟
- 完整探索：30-45 分钟
- 多结局收集：1-2 小时

---

## 📚 更多文档

- [环境变量详细说明](ENV_EXAMPLE.md)
- [项目状态](PROJECT_STATUS.md)
- [优化总结](docs/OPTIMIZATION_SUMMARY.md)
- [快速开始](docs/QUICK_START.md)

---

## 🆘 常见问题

### Q: 为什么第一次生成很慢？
A: 第一次需要生成开场和首批选择点（约 40-50 秒），之后的选择都已预加载，无需等待。

### Q: 如何让游戏更快？
A: 在 `.env` 中设置 `KIMI_MODEL=moonshot-v1-32k`，但质量会略有下降。

### Q: 为什么有时解析失败？
A: 已优化到 95% 成功率，偶尔失败会自动重试。

### Q: 如何保存进度？
A: 游戏中输入 `5` 即可保存，下次启动时会提示是否加载存档。

---

🎮 现在开始你的恐怖之旅吧！
