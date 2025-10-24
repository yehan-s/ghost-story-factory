# 完整游戏引擎使用指南

## 🎮 完整版 vs 演示版

### 演示版（play_game_correct.py）
- ❌ 硬编码场景（8-10个）
- ❌ 游玩时长：3-5 分钟
- ❌ 缺少 S3-S6 场景
- ✅ 无需 API Key
- ✅ 立即可玩

### 完整版（play_game_full.py）⭐ 推荐
- ✅ LLM 动态生成（20-30+ 场景）
- ✅ 游玩时长：15-30 分钟
- ✅ 完整的 S1-S6 主线
- ✅ 根据选择自适应生成
- ⚠️  需要 Kimi API Key

---

## 🚀 快速开始

### 1. 准备工作

#### 安装依赖
```bash
source venv/bin/activate
pip install pydantic rich crewai langchain-community langchain-openai python-dotenv
```

#### 获取 Kimi API Key
1. 访问 https://platform.moonshot.cn/
2. 注册账号
3. 创建 API Key
4. 复制你的 API Key

#### 设置环境变量
```bash
# 方式 1: 环境变量
export KIMI_API_KEY=your_kimi_api_key_here

# 方式 2: .env 文件（推荐）
echo "KIMI_API_KEY=your_kimi_api_key_here" > .env
```

---

### 2. 准备故事资源

#### 检查现有资源
```bash
ls examples/hangzhou/

# 应该看到：
#  杭州_GDD.md
#  杭州_lore_v2.md
```

#### 如果资源不存在，生成新的
```bash
gen-complete --city 杭州 --index 1
```

---

### 3. 运行完整游戏

```bash
source venv/bin/activate
python3 play_game_full.py
```

---

## 🎯 游戏特性

### 完整主线（S1-S6）

#### S1: 观景台 - 雨夜校准
- 65Hz 异常声波检测
- 高速相机拍摄
- 生成校准日志
- **时长**: 3-5 分钟

#### S2: 值班室 - 监控悖论
- 查看监控录像
- 发现"不存在的清洁工" T1
- 监控盲区守恒
- **时长**: 3-5 分钟

#### S3: 避雷针锚点 - 共振掩蔽
- 0.8Hz 共振测试
- 遇到失魂者 T1
- 获得关键暗号
- **时长**: 3-5 分钟

#### S4: B3 数据中心 - 下潜
- 65Hz 共振开锁
- 残片拼图谜题
- 获得残片密钥
- **时长**: 3-5 分钟

#### S5: 核心解密 - 18秒录音
- 播放 0:18 经典录音
- 密码解密
- 失魂者 T2-T4 出现
- **时长**: 3-5 分钟

#### S6: 第三节车厢 - 数字孪生
- 进入数字孪生空间
- 寻找失魂核心
- 多结局分支
- **时长**: 5-10 分钟

**总游玩时长**: 15-30 分钟 ✅

---

## 💡 游戏提示

### 选择策略

#### PR（个人共鸣度）管理
- **建议**: 保持在 40-80 之间
- **太低 (<20)**: 无法看到实体，错过关键线索
- **太高 (>80)**: 实体攻击性增强，危险

#### 关键道具
必须获得的道具：
1. 📊 **校准日志** (S1) - 进入值班室必需
2. 🔨 **共振记录** (S3) - 开启 B3 入口
3. 🧩 **残片密钥** (S4) - 核心解密必需
4. 💎 **失魂核心** (S6) - 达成"补完"结局

#### 标志位管理
重要的标志位：
- `录音_已播放`: 结局判定关键
- `失魂者_已拍照`: 获得暗号
- `监控_已检查`: 了解真相

---

## 🏆 多结局系统

### 结局 1: 补完 ⭐
**条件**:
- 持有失魂核心
- 播放 0:18 录音
- PR 80-100

**效果**: 全服 GR 重置，WF 清零

---

### 结局 2: 旁观 👁️
**条件**:
- 未持有失魂核心
- 播放 0:18 录音
- PR 60-80

**效果**: 个人获得见证者称号

---

### 结局 3: 迷失 💀
**条件**:
- 未播放录音
- 超时（时间 >= 04:00）
- 或 PR >= 100

**效果**: 成为失魂者 NPC

---

### 结局 4: 超时 ⏰
**条件**:
- 游戏时间 >= 06:00
- 未完成任务

**效果**: 被早班员工发现

---

## 🎮 游戏命令

### 游戏中命令
- `/save [名称]` - 保存游戏（默认 quicksave）
- `/load [名称]` - 加载存档
- `/quit` - 退出游戏
- `数字编号` - 选择选项

### 存档管理
```bash
# 查看存档
ls saves/

# 删除存档
rm saves/quicksave.save

# 备份存档
cp saves/important.save saves/important.backup
```

---

## ⚠️ 常见问题

### Q: 提示"未找到 Kimi API Key"
```bash
# 检查环境变量
echo $KIMI_API_KEY

# 如果为空，设置它
export KIMI_API_KEY=your_key
```

### Q: 生成场景太慢
**原因**: Kimi API 调用需要时间（通常 3-10 秒）

**解决**:
- 正常现象，请耐心等待
- 每个场景只生成一次
- 可以查看 Kimi 控制台监控 API 使用情况

### Q: 生成的内容质量不佳
**解决**:
- 重新生成该场景（重新加载存档）
- 调整 prompt templates（高级用户）
- 使用更高级的 Kimi 模型

### Q: 游戏中途崩溃
```bash
# 查看最近的自动保存
ls -lt saves/ | head -5

# 加载最近的存档
python3 play_game_full.py
# 然后在游戏中输入 /load
```

---

## 🎨 高级配置

### 自定义 Kimi 模型
编辑 `.env` 文件：
```bash
KIMI_API_KEY=your_key
KIMI_MODEL=moonshot-v1-8k  # 默认
# 或
KIMI_MODEL=moonshot-v1-32k  # 更大上下文
# 或
KIMI_MODEL=moonshot-v1-128k  # 最大上下文
```

### 调整生成长度
编辑 `src/ghost_story_factory/engine/response.py`:
```python
# 找到 generate_response 方法
# 调整 max_tokens 参数
```

---

## 📊 性能优化

### API 调用优化
- **缓存**: 相同场景+状态的响应会被缓存
- **批处理**: 选择点和响应分开生成
- **降级**: API 失败时使用默认内容

### 成本估算
- **每场景**: 约 500-1000 tokens
- **完整游戏**: 约 15,000-30,000 tokens
- **估算成本**: 参考 Kimi 定价页面

---

## 🎯 对比总结

| 特性 | 演示版 | 完整版 |
|------|--------|--------|
| 场景数 | 8-10 | 20-30+ |
| 时长 | 3-5分钟 | 15-30分钟 |
| 主线 | S0-S2 部分 | S1-S6 完整 |
| LLM生成 | ❌ | ✅ |
| API依赖 | ❌ | ✅ Kimi |
| 动态内容 | ❌ | ✅ |
| 多结局 | ✅ | ✅ |
| 可重玩性 | 低 | 高 |
| 推荐 | 快速体验 | 完整体验 |

---

## 🚀 立即开始

```bash
# 1. 确保依赖已安装
source venv/bin/activate

# 2. 设置 API Key
echo "KIMI_API_KEY=your_key" > .env

# 3. 运行完整游戏
python3 play_game_full.py

# 4. 开始你的北高峰之旅！
```

**准备好了吗？开始探索"空厢夜行"的真相！** 🎭✨

