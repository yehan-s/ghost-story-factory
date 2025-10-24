# 🎮 完整游戏引擎 - 快速开始

## 一行命令启动

```bash
./start_full_game.sh
```

脚本会自动：
- ✅ 检查并创建虚拟环境
- ✅ 安装所有依赖
- ✅ 检查 Kimi API Key
- ✅ 检查故事资源
- ✅ 启动完整游戏

---

## 手动启动

如果自动脚本失败，可以手动启动：

### 1. 准备环境
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install pydantic rich crewai langchain-community langchain-openai python-dotenv
```

### 2. 设置 API Key
```bash
# 设置环境变量
export KIMI_API_KEY=your_kimi_api_key_here

# 或创建 .env 文件
echo "KIMI_API_KEY=your_key" > .env
```

### 3. 运行游戏
```bash
python3 play_game_full.py
```

---

## 获取 Kimi API Key

1. 访问 https://platform.moonshot.cn/
2. 注册账号
3. 创建 API Key
4. 复制你的密钥

---

## 游戏特性

### ✨ 完整体验
- **20-30+ 个动态场景**
- **15-30 分钟游玩时长**
- **完整的 S1-S6 主线**
- **4 个不同结局**

### 🎯 主线场景

1. **S1**: 观景台 - 65Hz 异常检测
2. **S2**: 值班室 - 监控悖论
3. **S3**: 避雷针锚点 - 共振测试
4. **S4**: B3 入口 - 数据中心下潜
5. **S5**: 核心解密 - 18 秒录音波形
6. **S6**: 第三节车厢 - 数字孪生空间

### 🏆 多结局

- **补完**: 持有核心 + 播放录音
- **旁观**: 无核心 + 播放录音
- **迷失**: 未播放录音或超时
- **献祭**: 特殊选择路线

---

## 对比演示版

| 特性 | 演示版 | 完整版 |
|------|--------|--------|
| 文件 | play_game_correct.py | play_game_full.py |
| 场景数 | 8-10 | 20-30+ |
| 时长 | 3-5分钟 | 15-30分钟 |
| 主线 | S0-S2部分 | S1-S6完整 |
| LLM | ❌ | ✅ Kimi |
| 需要API | ❌ | ✅ |
| 动态生成 | ❌ | ✅ |
| 推荐 | 快速体验 | 完整体验 |

---

## 常见问题

### Q: 提示"未找到 API Key"
```bash
# 检查
echo $KIMI_API_KEY

# 设置
export KIMI_API_KEY=your_key
```

### Q: 场景生成太慢
**正常现象**：Kimi API 调用需要 3-10 秒

### Q: 游戏中途崩溃
```bash
# 查看最近保存
ls -lt saves/

# 游戏中使用 /save 命令定期保存
```

---

## 更多信息

- 📖 完整指南：`cat FULL_GAME_GUIDE.md`
- 🎯 快速开始：`cat QUICK_START.md`
- 📊 项目总结：`cat FINAL_SUMMARY.md`

---

**准备好了吗？开始探索北高峰的秘密！** 🎭✨

