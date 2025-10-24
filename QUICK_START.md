# 快速开始 ⚡

## 🎯 5 分钟上手

### 1. 环境准备

```bash
# 1.1 克隆项目
git clone https://github.com/your-username/ghost-story-factory.git
cd ghost-story-factory

# 1.2 安装依赖
uv venv && source .venv/bin/activate
uv pip install -e .

# 1.3 配置 API Key
cat > .env << 'EOF'
KIMI_API_KEY=your_kimi_api_key_here
KIMI_API_BASE=https://api.moonshot.cn/v1
OTEL_SDK_DISABLED=true
EOF
```

### 2. 开始游玩

```bash
# 启动游戏
./start_pregenerated_game.sh
```

### 3. 主菜单操作

```
╔══════════════════════════════════════╗
║          鬼故事工厂              ║
╚══════════════════════════════════════╝

1. 选择故事    ← 游玩已生成的故事（首次为空）
2. 生成故事    ← 生成新故事（首次选这个）

请选择：2
```

### 4. 生成故事

```bash
# 输入城市名
请输入城市名称：上海

# 选择故事简介（从3个AI生成的简介中选择）
请选择一个故事（1-3）：1

# 确认生成
⚠️  [警告] 生成过程预计 2-4 小时
✅ [支持] 如果中断，下次可以从断点继续！

按 Enter 确认开始生成...
[Enter]

# 等待生成（可随时 Ctrl+C 中断）
💾 [检查点] 已保存 50 个节点...
💾 [检查点] 已保存 100 个节点...
```

### 5. 恢复生成（如果中断）

```bash
# 如果上一步中断了，重新启动
./start_pregenerated_game.sh

# 选择生成，输入相同城市名
选择：2
城市：上海  ← 必须与之前相同

# 自动恢复
✅ 发现未完成的检查点！正在恢复...
   已恢复 100 个节点
   从节点 #101 继续生成...
```

### 6. 游玩故事

```bash
# 生成完成后，重新启动游戏
./start_pregenerated_game.sh

# 选择"选择故事"
选择：1

# 选择城市、故事、角色
请选择城市：
1. 上海
选择：1

请选择故事：
1. 废弃楼盘的诡异直播
选择：1

请选择角色：
⭐ 1. 废弃网红主播（主角）
选择：1

# 开始游玩（零等待！）
[游戏开始]
```

---

## 🔥 核心要点

### ✅ 必须记住的

1. **城市名必须一致**
   ```
   ✅ 第一次：上海，第二次：上海  ← 正确
   ❌ 第一次：上海，第二次：shanghai  ← 错误
   ```

2. **随时可以中断**
   - Ctrl+C ✅
   - 关机 ✅
   - 断网 ✅
   - 关闭终端 ✅

3. **查看进度**
   ```bash
   ./check_progress.sh
   ```

### ⚠️ 常见错误

**错误1：找不到命令**
```bash
# 问题
bash: ./start_pregenerated_game.sh: command not found

# 解决
chmod +x start_pregenerated_game.sh
chmod +x check_progress.sh
```

**错误2：API Key 无效**
```bash
# 问题
Error: Invalid API key

# 解决
# 检查 .env 文件
cat .env | grep KIMI_API_KEY

# 确保格式正确
KIMI_API_KEY=sk-xxxxxxxxx  # 不要有空格
```

**错误3：没找到检查点**
```bash
# 问题
🆕 开始新的对话树生成...  # 应该是"发现未完成的检查点"

# 原因
城市名输错了！

# 解决
1. Ctrl+C 停止
2. 运行 ./check_progress.sh 查看正确的城市名
3. 重新输入正确的城市名
```

---

## 📝 下一步

- **详细命令文档**：`docs/COMMANDS.md`
- **断点续传说明**：`docs/CHECKPOINT_RESUME.md`
- **完整 README**：`README.md`

---

## 🎮 开始游玩吧！

```bash
./start_pregenerated_game.sh
```

🎉 祝你玩得开心！

