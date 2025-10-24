# Ghost Story Factory - 环境变量配置说明

## 必需配置

在项目根目录创建 `.env` 文件，添加以下配置：

```bash
# Kimi API 配置（必需）
KIMI_API_KEY=your_kimi_api_key_here
KIMI_API_BASE=https://api.moonshot.cn/v1
```

## 推荐配置（平衡方案）⭐

```bash
# 快速生成选择点
KIMI_MODEL_CHOICES=moonshot-v1-32k

# 高质量叙事响应
KIMI_MODEL_RESPONSE=kimi-k2-0905-preview

# 高质量开场故事
KIMI_MODEL_OPENING=kimi-k2-0905-preview
```

## 模型说明

| 模型 | 速度 | 质量 | 上下文 | 适用场景 |
|------|------|------|--------|----------|
| `moonshot-v1-8k` | ⚡⚡⚡ 最快 | ⭐⭐ | 8K | 简单任务 |
| `moonshot-v1-32k` | ⚡⚡ 较快 | ⭐⭐⭐ | 32K | 选择点生成 |
| `kimi-k2-0905-preview` | ⚡ 较慢 | ⭐⭐⭐⭐⭐ | 128K | 叙事创作 |

## 其他配置方案

### 全速模式（最快）
```bash
KIMI_MODEL=moonshot-v1-32k
```

### 全质量模式（最好）
```bash
KIMI_MODEL=kimi-k2-0905-preview
```

### 超速模式（实验性）
```bash
KIMI_MODEL_CHOICES=moonshot-v1-8k
KIMI_MODEL_RESPONSE=moonshot-v1-32k
KIMI_MODEL_OPENING=moonshot-v1-32k
```

## 性能对比

使用推荐配置（平衡方案）：

| 功能 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 选择点生成 | 40秒 | 15-20秒 | 50% ↑ |
| 响应生成 | 30-40秒 | 30-40秒 | 保持高质量 |
| 开场生成 | 30-40秒 | 30-40秒 | 保持高质量 |

## 配置优先级

```
KIMI_MODEL_CHOICES > KIMI_MODEL > moonshot-v1-32k（默认）
KIMI_MODEL_RESPONSE > KIMI_MODEL > kimi-k2-0905-preview（默认）
KIMI_MODEL_OPENING > KIMI_MODEL > kimi-k2-0905-preview（默认）
```

## 运行时显示

游戏运行时会显示使用的模型：
```
🤖 [选择点] 使用模型: moonshot-v1-32k
🤖 [响应] 使用模型: kimi-k2-0905-preview
🤖 [开场] 使用模型: kimi-k2-0905-preview
```
