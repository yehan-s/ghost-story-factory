# Ghost Story Factory - 项目状态

**更新时间**: 2025-10-24
**状态**: ✅ 生产就绪

## 🎯 项目概述

《鬼故事工厂》是一个基于 LLM 的交互式文字冒险游戏引擎，支持动态生成剧情、选择点和多结局。

## ✅ 已完成功能

### P0 核心功能（全部完成）
- ✅ 游戏状态管理（PR, GR, WF, 道具, 标志位）
- ✅ 选择点生成系统（Micro/Normal/Critical）
- ✅ 运行时响应生成（分层叙事，状态更新）
- ✅ 意图映射系统（自由输入转选择）
- ✅ 多结局系统（条件判定，结局渲染）
- ✅ CLI 用户界面（Rich 库美化）

### P1 高级功能（全部完成）
- ✅ 完整游戏流程（开场 → 探索 → 结局）
- ✅ Kimi LLM 集成（CrewAI + LiteLLM）
- ✅ 游戏状态保存/加载
- ✅ 配置系统（GDD + Lore 加载）

### P1.5 优化功能（全部完成）
- ✅ Prompt 优化（Token 减少 88%）
- ✅ 异步预加载（消除等待）
- ✅ 分模型配置（速度提升 50%）
- ✅ JSON 解析鲁棒性
- ✅ 第二人称视角修正
- ✅ 动态开场生成

## 📦 项目结构

```
ghost-story-factory/
├── src/ghost_story_factory/
│   ├── engine/              # 游戏引擎核心
│   │   ├── state.py         # 状态管理
│   │   ├── choices.py       # 选择点生成
│   │   ├── response.py      # 响应生成
│   │   └── game_loop.py     # 主循环
│   └── ui/
│       └── cli.py           # CLI 界面
├── examples/hangzhou/       # 杭州故事示例
├── docs/                    # 文档
│   ├── specs/               # 需求文档
│   ├── archive/             # 历史文档归档
│   ├── QUICK_START.md       # 快速开始
│   ├── INSTALLATION.md      # 安装指南
│   └── OPTIMIZATION_SUMMARY.md  # 优化总结
├── play_game_full.py        # 游戏入口
├── play_now.sh              # 快速启动脚本
├── start_full_game.sh       # 完整启动脚本
├── ENV_EXAMPLE.md           # 环境变量配置示例
└── README.md                # 项目主文档
```

## 🚀 快速开始

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 添加 KIMI_API_KEY

# 2. 启动游戏
./play_now.sh
```

## 🤖 推荐模型配置

在 `.env` 中添加：

```bash
# 快速生成选择点
KIMI_MODEL_CHOICES=moonshot-v1-32k

# 高质量叙事响应
KIMI_MODEL_RESPONSE=kimi-k2-0905-preview

# 高质量开场故事
KIMI_MODEL_OPENING=kimi-k2-0905-preview
```

## 📊 性能指标

| 指标 | 当前值 |
|------|--------|
| 首次选择生成 | 15-20秒 |
| 后续选择生成 | 0秒（预加载） |
| Token 消耗/次 | ~600 |
| 解析成功率 | ~95% |

## 🔧 技术栈

- **语言**: Python 3.10+
- **LLM 框架**: CrewAI + LiteLLM
- **LLM 提供商**: Kimi (Moonshot AI)
- **UI 库**: Rich
- **配置**: YAML, Markdown, .env

## 🎯 混合加载方案

**实现日期**: 2025-10-24

### 策略

| 功能 | 模式 | Token | 时间 | 质量 |
|------|------|-------|------|------|
| 选择点生成 | 精简 | ~600 | 15-20秒 | 好 |
| 响应生成 | 完整 | ~6,000 | 22-25秒 | 高 ⭐ |
| 开场生成 | 完整 | ~6,000 | 22-25秒 | 高 ⭐ |

### 效果

- **平均 Token**: ~2,000/次
- **平均时间**: ~18秒/次
- **游戏成本**: ~$1.20/次
- **质量**: 关键时刻（响应+开场）使用完整故事背景

### 自动检测

- 如果有主线故事文件：自动启用混合模式
- 如果没有：自动降级到精简模式

详见：`HYBRID_APPROACH.md`

## 📚 文档

- [快速开始](docs/QUICK_START.md)
- [安装指南](docs/INSTALLATION.md)
- [优化总结](docs/OPTIMIZATION_SUMMARY.md)
- [环境变量配置](ENV_EXAMPLE.md)
- [需求文档](docs/specs/SPEC_TODO.md)

## 🎮 游戏时长

基于 15 秒/选择的估算：
- **主线单结局**: 15-20 分钟
- **完整探索**: 30-45 分钟
- **多结局收集**: 1-2 小时

## 🔄 开发状态

- ✅ 核心引擎：完成
- ✅ 杭州故事：完成
- ✅ 性能优化：完成
- ✅ 用户体验：完成
- ✅ 混合加载方案：完成
- 🔄 静态对话预生成：规划中
- 🔄 多城市故事：待扩展
- 🔄 Web 界面：待开发

## 📝 更新日志

### 2025-10-24
- ✅ 实现分模型配置
- ✅ 优化 Prompt（Token 减少 88%）
- ✅ 实现异步预加载
- ✅ 修复 JSON 解析
- ✅ 修正第二人称视角
- ✅ 实现动态开场生成
- ✅ 清理测试文件
- ✅ 归档历史文档
- ✅ 实现混合加载方案
  - 响应生成使用完整故事背景
  - 开场生成使用完整故事背景
  - 选择点生成保持精简（快速）

## 🙏 致谢

- Kimi (Moonshot AI) 提供 LLM 服务
- CrewAI 框架提供 Agent 支持
- Rich 库提供美观的 CLI 界面
