# 静态对话预生成系统 - 设计文档

**版本**: v1.0
**日期**: 2025-10-24
**状态**: 📋 设计阶段

---

## 1. 系统概述

### 1.1 目标

**核心目标**：一次性预生成完整的游戏对话树，实现游戏运行时零等待。

**设计原则**：
- ✅ **完全独立**：与实时生成系统独立，互不影响
- ✅ **数据库驱动**：所有故事存储在数据库中，按需加载
- ✅ **不可中断**：生成过程必须完整完成，确保游戏可玩
- ✅ **高质量保证**：主线游戏时间 >= 15 分钟（按每选择15秒计算）
- ✅ **高可靠性**：自动重试和错误恢复

### 1.2 产品定位

**重要**：实时生成功能暂时雪藏，当前版本仅支持预生成故事！

所有游戏内容必须提前生成完毕，确保：
- 完全流畅的游戏体验（零等待）
- 高质量的叙事内容（使用最优模型）
- 离线游玩支持（无需网络）

### 1.3 运行模式与游戏流程（更新）

当前支持两种模式：

- 动态模式：运行时调用 LLM 实时生成，完整体验；入口 `play_game_full.py`
- 预生成模式：先离线生成完整对话树（存数据库/文件），游玩阶段零等待；入口 `play_game_pregenerated.py`

运行入口：

```bash
# 动态模式
python play_game_full.py

# 预生成模式（推荐体验零等待版本）
./start_pregenerated_game.sh
# 或
python play_game_pregenerated.py
```

```
╔═══════════════════════════════════════════════════════════════╗
║                    第一步：启动游戏                           ║
╚═══════════════════════════════════════════════════════════════╝

$ ./play_now.sh
按 Enter 开始游戏...

╔═══════════════════════════════════════════════════════════════╗
║                    第二步：主菜单                             ║
╚═══════════════════════════════════════════════════════════════╝

欢迎来到 Ghost Story Factory！

请选择：
  1. 📖 选择故事（从已生成的故事中游玩）
  2. ✨ 生成故事（创建新的故事）

输入选项 [1/2]: _

╔═══════════════════════════════════════════════════════════════╗
║              分支 A：选择故事（前提：数据库有故事）            ║
╚═══════════════════════════════════════════════════════════════╝

1. 选择城市
   ┌─────────────────────────────────────┐
   │ 可用城市：                          │
   │  1. 杭州（3 个故事）                │
   │  2. 北京（1 个故事）                │
   │  3. 上海（0 个故事）                │
   └─────────────────────────────────────┘
   输入城市编号: 1

2. 选择故事
   ┌─────────────────────────────────────┐
   │ 杭州 - 可用故事：                   │
   │  1. 钱江新城观景台诡异事件          │
   │     - 角色数：7                     │
   │     - 时长：18 分钟                 │
   │  2. 西湖断桥传说                    │
   │     - 角色数：5                     │
   │     - 时长：22 分钟                 │
   │  3. 灵隐寺夜探                      │
   │     - 角色数：4                     │
   │     - 时长：15 分钟                 │
   └─────────────────────────────────────┘
   输入故事编号: 1

3. 选择角色
   ┌─────────────────────────────────────┐
   │ 钱江新城观景台诡异事件 - 可用角色： │
   │  1. 特检院工程师 [主角线] ⭐       │
   │  2. 夜班保安                        │
   │  3. 登山女跑者                      │
   │  4. 主播                            │
   │  5. 豆瓣组长                        │
   │  6. 录音博主                        │
   │  7. 避雷针维护工                    │
   └─────────────────────────────────────┘
   输入角色编号: 1

4. 开始游戏 🎮

╔═══════════════════════════════════════════════════════════════╗
║              分支 B：生成故事（AI 预生成）                    ║
╚═══════════════════════════════════════════════════════════════╝

1. 输入城市
   ┌─────────────────────────────────────┐
   │ 请输入城市名称（如：杭州、北京）：  │
   └─────────────────────────────────────┘
   > 杭州

2. AI 生成故事简介（等待中...）
   ┌─────────────────────────────────────┐
   │ 🤖 正在为「杭州」生成故事简介...    │
   │                                     │
   │ [███████████░░░░░░░] 60%            │
   │ 预计剩余时间：30 秒                 │
   └─────────────────────────────────────┘

3. 选择故事简介
   ┌─────────────────────────────────────────────────────────┐
   │ AI 为你生成了以下故事简介：                             │
   │                                                         │
   │ 1. 钱江新城观景台诡异事件                               │
   │    你是一名特检院工程师，深夜被派往钱江新城观景台       │
   │    调查异常电磁信号。你发现避雷针系统出现了不明         │
   │    频率共振，而这可能与 15 年前的一起坠楼事件有关...   │
   │                                                         │
   │ 2. 西湖断桥午夜传说                                     │
   │    你是一名民俗研究员，为了验证西湖断桥的传说，         │
   │    你决定在午夜时分独自前往断桥。传说中每逢月圆         │
   │    之夜，桥上会出现一位白衣女子...                     │
   │                                                         │
   │ 3. 灵隐寺夜探秘闻                                       │
   │    你是一名建筑修复专家，接到任务要在灵隐寺进行         │
   │    夜间勘测。然而在深夜的寺庙中，你听到了诡异的         │
   │    诵经声，而此时寺中应该空无一人...                   │
   └─────────────────────────────────────────────────────────┘
   请选择一个故事 [1/2/3]: 1

4. 完整生成故事（不可中断！）
   ┌─────────────────────────────────────────────────────────┐
   │ 🚀 开始生成完整故事：钱江新城观景台诡异事件             │
   │                                                         │
   │ ⚠️  注意：生成过程预计 2-4 小时，请勿中断！             │
   │                                                         │
   │ 当前深度: 5/20                                          │
   │ 已生成节点: 245/估计 1500                               │
   │ 当前分支: S2 → 选项 B → S3                             │
   │ 预计剩余时间: 2小时 30分钟                              │
   │ 已用 Token: 150,000                                     │
   │ 预计总 Token: 800,000                                   │
   │ 预计成本: $12.50                                        │
   │                                                         │
   │ [████████████░░░░░░░░░░░░] 45%                          │
   │                                                         │
   │ 最近生成的节点：                                        │
   │  ✅ node_243: S2 - 检查频谱仪数据                       │
   │  ✅ node_244: S2 - 对比历史记录                         │
   │  🔄 node_245: S2 - 联系值班经理（生成中...）            │
   └─────────────────────────────────────────────────────────┘

5. 生成完成，保存到数据库
   ┌─────────────────────────────────────────────────────────┐
   │ ✅ 故事生成完成！                                       │
   │                                                         │
   │ 故事名称: 钱江新城观景台诡异事件                        │
   │ 生成节点: 1,458 个                                      │
   │ 主线深度: 18 层                                         │
   │ 角色数量: 7 个                                          │
   │ 预计游戏时长: 18 分钟                                   │
   │ 实际用时: 2 小时 15 分钟                                │
   │ 总 Token: 823,450                                       │
   │ 总成本: $14.20                                          │
   │                                                         │
   │ 已保存到数据库 ✓                                        │
   │                                                         │
   │ 按 Enter 返回主菜单，选择「选择故事」开始游玩...        │
   └─────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════╗
║                    第三步：游戏进行中                         ║
╚═══════════════════════════════════════════════════════════════╝

从数据库加载对话树，零等待游玩！
```

---

## 2. 架构设计

### 2.1 系统架构

**完整项目结构**：

```
ghost-story-factory/
├── src/ghost_story_factory/
│   ├── engine/              # 核心引擎（共享）
│   │   ├── state.py         # 状态管理
│   │   ├── choices.py       # 选择点生成
│   │   └── response.py      # 响应生成
│   │
│   ├── pregenerator/        # 预生成系统 ✨ 新增
│   │   ├── __init__.py
│   │   ├── tree_builder.py        # 对话树构建器
│   │   ├── tree_traverser.py      # 树遍历算法
│   │   ├── state_manager.py       # 状态合并和剪枝
│   │   ├── progress_tracker.py    # 进度追踪
│   │   └── synopsis_generator.py  # 故事简介生成器 ✨
│   │
│   ├── database/            # 数据库系统 ✨ 新增
│   │   ├── __init__.py
│   │   ├── models.py        # 数据模型（City, Story, Character, DialogueTree）
│   │   ├── db_manager.py    # 数据库管理器
│   │   └── queries.py       # 查询接口
│   │
│   ├── ui/                  # 用户界面
│   │   ├── cli.py           # 游戏界面（已有）
│   │   ├── menu.py          # 主菜单系统 ✨ 新增
│   │   └── story_selector.py # 故事选择器 ✨ 新增
│   │
│   └── runtime/             # 运行时系统 ✨ 新增
│       ├── __init__.py
│       ├── dialogue_loader.py # 对话树加载器
│       └── tree_query.py      # 对话树查询
│
├── database/                # 数据库文件 ✨ 新增
│   └── ghost_stories.db     # SQLite 数据库
│
├── play_now.sh              # 游戏入口（新版）
└── generate_story.py        # 故事生成工具 ✨ 新增
```

### 2.2 数据库设计

**使用 SQLite**：Python 内置的轻量级数据库

**为什么选择 SQLite？**
1. ✅ **零配置**：Python 标准库自带，无需安装
2. ✅ **轻量级**：单文件数据库，便于管理和备份
3. ✅ **高性能**：读取速度快，满足游戏运行需求
4. ✅ **跨平台**：Windows/macOS/Linux 通用
5. ✅ **简单可靠**：无需服务器，直接文件操作

**数据库文件**：`database/ghost_stories.db`（约 10-50 MB/故事）

**核心表结构**：

```sql
-- 城市表
CREATE TABLE cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 故事表
CREATE TABLE stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    synopsis TEXT NOT NULL,  -- 故事简介
    estimated_duration_minutes INTEGER,  -- 预计游戏时长
    total_nodes INTEGER,     -- 对话树节点数
    max_depth INTEGER,       -- 最大深度
    generation_cost_usd REAL,  -- 生成成本
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (city_id) REFERENCES cities(id)
);

-- 角色表
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    is_protagonist BOOLEAN DEFAULT FALSE,  -- 是否主角线
    description TEXT,
    FOREIGN KEY (story_id) REFERENCES stories(id)
);

-- 对话树表（存储 JSON）
CREATE TABLE dialogue_trees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    tree_data TEXT NOT NULL,  -- JSON 格式的完整对话树（可使用 json_extract）
    compressed BOOLEAN DEFAULT FALSE,  -- 是否 gzip 压缩
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (character_id) REFERENCES characters(id),
    UNIQUE(story_id, character_id)  -- 每个故事的每个角色只有一棵对话树
);

-- 元数据表
CREATE TABLE generation_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL,
    total_tokens INTEGER,
    generation_time_seconds INTEGER,
    model_used TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id)
);
```

**独立性保证**：
1. 预生成系统在单独的 `pregenerator/` 包中
2. 运行时读取系统在 `runtime/` 包中
3. 共享 `engine/` 包的核心组件（复用生成逻辑）
4. 游戏引擎通过参数选择使用哪种模式

### 2.3 核心组件

#### 2.3.1 故事简介生成器 (SynopsisGenerator) ✨ 新增

**职责**：根据城市生成多个故事简介供用户选择

**关键方法**：
```python
class SynopsisGenerator:
    def __init__(self, city: str):
        self.city = city

    def generate_synopses(self, count=3) -> List[StorySynopsis]:
        """生成多个故事简介"""
        prompt = f"""
        为城市「{self.city}」创作 {count} 个恐怖灵异故事的简介。

        要求：
        1. 每个故事简介 100-150 字
        2. 必须包含：主角身份、核心任务、恐怖元素
        3. 基于该城市的真实地标或传说
        4. 风格：现代都市灵异
        5. 每个故事的主角职业和场景必须不同

        返回 JSON 格式：
        [
          {{
            "title": "故事标题",
            "synopsis": "故事简介",
            "protagonist": "主角身份",
            "location": "主要场景",
            "estimated_duration": 15-25  # 预计时长（分钟）
          }}
        ]
        """
        # 调用 LLM 生成
        synopses = self.llm.generate(prompt)
        return synopses
```

#### 2.3.2 对话树构建器 (TreeBuilder)

**职责**：构建完整的对话树结构

**关键方法**：
```python
class DialogueTreeBuilder:
    def __init__(self, gdd, lore, main_story):
        self.choice_generator = ChoicePointsGenerator(...)  # 复用
        self.response_generator = RuntimeResponseGenerator(...)  # 复用

    def build_tree(self, max_depth=20, max_branches=4):
        """构建完整对话树"""

    def generate_node(self, state, scene, depth):
        """生成单个节点"""

    def should_prune(self, state):
        """判断是否剪枝"""
```

#### 2.3.3 树遍历器 (TreeTraverser)

**职责**：遍历对话树，生成所有可能的路径

**遍历策略**：
```python
class TreeTraverser:
    def traverse_bfs(self, root_node, max_depth):
        """广度优先遍历"""
        queue = [(root_node, 0)]  # (节点, 深度)

        while queue:
            node, depth = queue.pop(0)

            if depth >= max_depth or is_ending(node):
                continue

            # 生成子节点
            choices = self.generate_choices(node)
            for choice in choices:
                child_node = self.create_child_node(node, choice)
                if not self.is_duplicate(child_node):
                    queue.append((child_node, depth + 1))
```

#### 2.3.4 状态管理器 (StateManager)

**职责**：状态合并和剪枝

**状态哈希**：
```python
class StateManager:
    def get_state_hash(self, game_state):
        """计算状态哈希（用于去重）"""
        return hash((
            game_state.current_scene,
            game_state.PR,
            game_state.GR,
            tuple(sorted(game_state.flags.items())),
            tuple(sorted(game_state.inventory))
        ))

    def should_merge(self, state1, state2):
        """判断两个状态是否应该合并"""
        # PR/GR 差异小于 5 视为相同
        if abs(state1.PR - state2.PR) <= 5:
            if abs(state1.GR - state2.GR) <= 5:
                if state1.current_scene == state2.current_scene:
                    return True
        return False
```

#### 2.3.5 进度追踪器 (ProgressTracker)

**职责**：显示进度，估算剩余时间，支持断点续传

**进度显示**：
```python
class ProgressTracker:
    def __init__(self):
        self.total_nodes = 0
        self.generated_nodes = 0
        self.start_time = time.time()

    def update(self, current_depth, node_count):
        """更新进度"""
        elapsed = time.time() - self.start_time
        speed = self.generated_nodes / elapsed  # 节点/秒
        remaining = self.total_nodes - self.generated_nodes
        eta = remaining / speed

        self.display_progress(current_depth, eta)

    def save_checkpoint(self, tree, filename):
        """保存检查点"""

    def load_checkpoint(self, filename):
        """加载检查点"""
```

#### 2.3.6 数据库管理器 (DatabaseManager) ✨ 新增

**职责**：管理所有数据库操作

**关键方法**：
```python
import sqlite3
import json
import gzip
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path="database/ghost_stories.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # 返回字典格式
        self.init_db()

    def init_db(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()

        # 创建所有表（如果不存在）
        with open('sql/schema.sql', 'r') as f:
            cursor.executescript(f.read())

        self.conn.commit()

    def save_story(self, city_name, title, synopsis, characters, dialogue_trees, metadata):
        """保存完整的故事（包括对话树）"""
        cursor = self.conn.cursor()

        # 1. 确保城市存在
        cursor.execute(
            "INSERT OR IGNORE INTO cities (name) VALUES (?)",
            (city_name,)
        )
        cursor.execute("SELECT id FROM cities WHERE name = ?", (city_name,))
        city_id = cursor.fetchone()['id']

        # 2. 插入故事
        cursor.execute("""
            INSERT INTO stories
            (city_id, title, synopsis, estimated_duration_minutes,
             total_nodes, max_depth, generation_cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            city_id, title, synopsis,
            metadata['estimated_duration'],
            metadata['total_nodes'],
            metadata['max_depth'],
            metadata['cost']
        ))
        story_id = cursor.lastrowid

        # 3. 插入角色
        char_id_map = {}
        for char in characters:
            cursor.execute("""
                INSERT INTO characters (story_id, name, is_protagonist, description)
                VALUES (?, ?, ?, ?)
            """, (story_id, char['name'], char['is_protagonist'], char['description']))
            char_id_map[char['name']] = cursor.lastrowid

        # 4. 保存对话树（JSON 格式，可选压缩）
        for char_name, tree in dialogue_trees.items():
            char_id = char_id_map[char_name]

            # 转为 JSON
            tree_json = json.dumps(tree, ensure_ascii=False)

            # 可选：Gzip 压缩（节省空间）
            if len(tree_json) > 10000:  # 大于 10KB 才压缩
                tree_data = gzip.compress(tree_json.encode('utf-8'))
                compressed = True
            else:
                tree_data = tree_json
                compressed = False

            cursor.execute("""
                INSERT INTO dialogue_trees (story_id, character_id, tree_data, compressed)
                VALUES (?, ?, ?, ?)
            """, (story_id, char_id, tree_data, compressed))

        # 5. 保存元数据
        cursor.execute("""
            INSERT INTO generation_metadata
            (story_id, total_tokens, generation_time_seconds, model_used)
            VALUES (?, ?, ?, ?)
        """, (
            story_id,
            metadata['total_tokens'],
            metadata['generation_time'],
            metadata['model']
        ))

        self.conn.commit()
        return story_id

    def get_cities(self) -> List[dict]:
        """获取所有城市（含故事数量）"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.description, COUNT(s.id) as story_count
            FROM cities c
            LEFT JOIN stories s ON c.id = s.city_id
            GROUP BY c.id
            ORDER BY c.name
        """)
        return [dict(row) for row in cursor.fetchall()]

    def get_stories_by_city(self, city_id) -> List[dict]:
        """获取某城市的所有故事"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, COUNT(DISTINCT c.id) as character_count
            FROM stories s
            LEFT JOIN characters c ON s.id = c.story_id
            WHERE s.city_id = ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """, (city_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_characters_by_story(self, story_id) -> List[dict]:
        """获取某故事的所有角色"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM characters
            WHERE story_id = ?
            ORDER BY is_protagonist DESC, name
        """, (story_id,))
        return [dict(row) for row in cursor.fetchall()]

    def load_dialogue_tree(self, story_id, character_id) -> dict:
        """加载对话树"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT tree_data, compressed
            FROM dialogue_trees
            WHERE story_id = ? AND character_id = ?
        """, (story_id, character_id))

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"未找到对话树：story_id={story_id}, character_id={character_id}")

        tree_data = row['tree_data']
        compressed = row['compressed']

        # 解压缩（如果需要）
        if compressed:
            tree_json = gzip.decompress(tree_data).decode('utf-8')
        else:
            tree_json = tree_data

        return json.loads(tree_json)

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
```

**使用示例**：

```python
# 初始化数据库
db = DatabaseManager("database/ghost_stories.db")

# 保存故事
story_id = db.save_story(
    city_name="杭州",
    title="钱江新城观景台诡异事件",
    synopsis="你是一名特检院工程师...",
    characters=[
        {"name": "特检院工程师", "is_protagonist": True, "description": "..."},
        {"name": "夜班保安", "is_protagonist": False, "description": "..."}
    ],
    dialogue_trees={
        "特检院工程师": {...},  # 完整对话树
        "夜班保安": {...}
    },
    metadata={
        "estimated_duration": 18,
        "total_nodes": 1458,
        "max_depth": 18,
        "cost": 14.20,
        "total_tokens": 823450,
        "generation_time": 8100,  # 秒
        "model": "kimi-k2-0905-preview"
    }
)

# 查询城市
cities = db.get_cities()
# [{'id': 1, 'name': '杭州', 'story_count': 3}, ...]

# 查询故事
stories = db.get_stories_by_city(city_id=1)
# [{'id': 1, 'title': '钱江新城观景台诡异事件', ...}, ...]

# 查询角色
characters = db.get_characters_by_story(story_id=1)
# [{'id': 1, 'name': '特检院工程师', 'is_protagonist': True}, ...]

# 加载对话树
tree = db.load_dialogue_tree(story_id=1, character_id=1)
# {'root': {...}, 'node_001': {...}, ...}
```

#### 2.3.7 主菜单系统 (MenuSystem) ✨ 新增

**职责**：显示主菜单，处理用户选择

**关键方法**：
```python
class MenuSystem:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def show_main_menu(self) -> str:
        """显示主菜单，返回选择"""
        print("请选择：")
        print("  1. 📖 选择故事")
        print("  2. ✨ 生成故事")
        choice = input("输入选项 [1/2]: ")
        return choice

    def select_story_flow(self):
        """故事选择流程"""
        # 1. 选择城市
        city = self.select_city()
        # 2. 选择故事
        story = self.select_story(city)
        # 3. 选择角色
        character = self.select_character(story)
        return city, story, character

    def generate_story_flow(self):
        """故事生成流程"""
        # 1. 输入城市
        city = self.input_city()
        # 2. 生成简介
        synopses = self.generate_synopses(city)
        # 3. 选择简介
        synopsis = self.select_synopsis(synopses)
        # 4. 完整生成
        story = self.generate_full_story(city, synopsis)
        return story
```

---

## 3. 数据结构

### 3.1 对话树节点

```python
@dataclass
class DialogueNode:
    """对话树节点"""
    node_id: str              # 唯一标识
    scene: str                # 场景 ID
    depth: int                # 深度（从根节点算起）

    # 游戏状态
    game_state: GameState
    state_hash: str           # 状态哈希（用于去重）

    # 内容
    narrative: Optional[str] = None  # 叙事文本（响应或开场）
    choices: List[Choice] = field(default_factory=list)

    # 树结构
    parent_id: Optional[str] = None
    parent_choice_id: Optional[str] = None
    children: List[str] = field(default_factory=list)  # 子节点 ID

    # 元数据
    is_ending: bool = False
    ending_type: Optional[str] = None
    generated_at: str = ""
```

### 3.2 对话树结构

```json
{
  "metadata": {
    "city": "杭州",
    "generated_at": "2025-10-24T14:30:00Z",
    "generator_version": "1.0.0",
    "total_nodes": 1234,
    "max_depth": 20,
    "estimated_playtime_minutes": 45,
    "generation_stats": {
      "duration_seconds": 7200,
      "total_tokens": 850000,
      "estimated_cost_usd": 15.50
    }
  },

  "nodes": {
    "root": {
      "node_id": "root",
      "scene": "S1",
      "depth": 0,
      "narrative": "开场叙事文本...",
      "game_state": {
        "PR": 5,
        "GR": 0,
        "current_scene": "S1",
        "inventory": [],
        "flags": {}
      },
      "choices": [
        {
          "choice_id": "A",
          "choice_text": "选项 A 的文本",
          "choice_type": "normal",
          "next_node_id": "node_001",
          "state_changes": {
            "PR": 10,
            "flags": {"flag1": true}
          }
        },
        {
          "choice_id": "B",
          "choice_text": "选项 B 的文本",
          "next_node_id": "node_002"
        }
      ],
      "children": ["node_001", "node_002"]
    },

    "node_001": {
      "node_id": "node_001",
      "scene": "S1",
      "depth": 1,
      "parent_id": "root",
      "parent_choice_id": "A",
      "narrative": "选择 A 后的响应文本...",
      "game_state": {
        "PR": 15,
        "GR": 0,
        "current_scene": "S1",
        "inventory": [],
        "flags": {"flag1": true}
      },
      "choices": [...]
    }
  },

  "index": {
    "by_scene": {
      "S1": ["root", "node_001", "node_002"],
      "S2": ["node_010", "node_011"]
    },
    "by_depth": {
      "0": ["root"],
      "1": ["node_001", "node_002"],
      "2": ["node_003", "node_004", "node_005"]
    },
    "endings": [
      {
        "node_id": "ending_001",
        "ending_type": "good_ending",
        "depth": 18
      }
    ]
  }
}
```

---

## 4. 生成流程

### 4.1 故事简介生成

**目标**：快速生成 3 个故事简介供用户选择

**时间**：30-60 秒

**流程**：
```python
def generate_synopses_for_city(city: str) -> List[StorySynopsis]:
    """为城市生成故事简介"""

    # 1. 加载城市信息（如果有）
    city_info = load_city_info(city)

    # 2. 构建 Prompt
    prompt = build_synopsis_prompt(city, city_info)

    # 3. 调用 LLM 生成
    llm = LLM(model="kimi-k2-0905-preview", ...)
    result = llm.generate(prompt)

    # 4. 解析 JSON
    synopses = parse_synopses(result)

    # 5. 验证（每个简介必须有标题、简介、主角、场景）
    validated_synopses = validate_synopses(synopses)

    return validated_synopses
```

### 4.2 完整故事生成

**目标**：生成完整的对话树（不可中断！）

**时间**：2-4 小时

**要求**：
- 主线深度 >= 15 层（确保游戏时长 >= 15 分钟）
- 每层 2-4 个选择
- 节点总数 800-1500

**流程**：
```python
def generate_full_story(city: str, synopsis: StorySynopsis) -> Story:
    """生成完整故事（不可中断）"""

    try:
        # 1. 创建 GDD、Lore、主线故事文档
        gdd = generate_gdd(city, synopsis)
        lore = generate_lore(city, synopsis)
        main_story = generate_main_thread(city, synopsis)

        # 2. 提取角色列表
        characters = extract_characters(main_story)

        # 3. 为每个角色生成对话树
        dialogue_trees = {}
        for char in characters:
            print(f"🔄 正在为角色「{char.name}」生成对话树...")
            tree = generate_dialogue_tree(
                city=city,
                synopsis=synopsis,
                character=char,
                gdd=gdd,
                lore=lore,
                main_story=main_story,
                min_depth=15  # 强制要求
            )
            dialogue_trees[char.id] = tree

        # 4. 验证游戏时长
        main_tree = dialogue_trees[protagonist.id]
        estimated_duration = estimate_playtime(main_tree)
        if estimated_duration < 15:
            raise ValueError(f"游戏时长不足！当前 {estimated_duration} 分钟，需要至少 15 分钟")

        # 5. 保存到数据库
        story = Story(
            city=city,
            title=synopsis.title,
            synopsis=synopsis.synopsis,
            characters=characters,
            dialogue_trees=dialogue_trees,
            estimated_duration=estimated_duration
        )
        db_manager.save_story(story)

        print(f"✅ 故事生成完成！时长：{estimated_duration} 分钟")
        return story

    except Exception as e:
        # 失败时清理部分数据，要求重新生成
        print(f"❌ 生成失败：{e}")
        print("⚠️  请重新开始生成流程")
        raise
```

### 4.3 广度优先遍历 (BFS)

```python
def generate_dialogue_tree(self, max_depth=20):
    """生成完整对话树"""

    # 1. 初始化根节点
    root_state = GameState()
    root_node = DialogueNode(
        node_id="root",
        scene=root_state.current_scene,
        depth=0,
        game_state=root_state
    )

    # 生成开场
    root_node.narrative = self.generate_opening()
    root_node.choices = self.generate_choices(root_state, root_node.scene)

    # 2. BFS 遍历
    queue = [root_node]
    tree = {"root": root_node}
    state_cache = {self.get_state_hash(root_state): "root"}

    while queue:
        current_node = queue.pop(0)

        # 检查终止条件
        if current_node.depth >= max_depth:
            continue
        if current_node.is_ending:
            continue

        # 生成子节点
        for choice in current_node.choices:
            # 创建新状态
            new_state = copy.deepcopy(current_node.game_state)
            new_state.update(choice.consequences)

            # 检查状态是否已存在（去重）
            state_hash = self.get_state_hash(new_state)
            if state_hash in state_cache:
                # 复用已有节点
                existing_node_id = state_cache[state_hash]
                choice.next_node_id = existing_node_id
                continue

            # 创建新节点
            child_node = DialogueNode(
                node_id=f"node_{len(tree):04d}",
                scene=new_state.current_scene,
                depth=current_node.depth + 1,
                game_state=new_state,
                parent_id=current_node.node_id,
                parent_choice_id=choice.choice_id
            )

            # 生成内容
            child_node.narrative = self.generate_response(choice, new_state)
            child_node.choices = self.generate_choices(new_state, child_node.scene)

            # 检查是否结局
            child_node.is_ending = self.check_ending(new_state)
            if child_node.is_ending:
                child_node.ending_type = self.determine_ending_type(new_state)

            # 添加到树
            tree[child_node.node_id] = child_node
            state_cache[state_hash] = child_node.node_id
            choice.next_node_id = child_node.node_id
            current_node.children.append(child_node.node_id)

            # 加入队列
            if not child_node.is_ending:
                queue.append(child_node)

            # 更新进度
            self.progress_tracker.update(child_node.depth, len(tree))

            # 定期保存检查点
            if len(tree) % 50 == 0:
                self.save_checkpoint(tree)

    return tree
```

### 4.4 游戏时长保证

**关键要求**：主线游戏时长 >= 15 分钟

**计算方式**：
```python
def estimate_playtime(dialogue_tree, seconds_per_choice=15):
    """估算游戏时长"""

    # 找到主线路径（最长路径）
    main_path = find_longest_path(dialogue_tree)

    # 计算选择点数量
    choice_count = len(main_path) - 1  # 减去根节点

    # 估算时长
    estimated_seconds = choice_count * seconds_per_choice
    estimated_minutes = estimated_seconds / 60

    return estimated_minutes

def ensure_minimum_depth(tree_builder, min_depth=15):
    """确保对话树深度"""

    # 在生成时强制要求
    tree_builder.generate_tree(
        max_depth=25,  # 最大深度（有余量）
        min_main_path_depth=min_depth  # 主线最小深度 ✨
    )

    # 生成后验证
    main_path_depth = get_main_path_depth(tree)
    if main_path_depth < min_depth:
        raise ValueError(f"主线深度不足：{main_path_depth} < {min_depth}")
```

### 4.5 状态去重策略

**目标**：减少对话树节点数量，避免状态爆炸

**策略1：状态哈希**
- 相同状态只保留一个节点
- 通过 `(scene, PR, GR, flags, inventory)` 计算哈希

**策略2：状态合并**
- PR/GR 差异 <= 5 视为相同
- 忽略不重要的标志位

**策略3：剪枝**
- 深度达到 `max_depth` 停止
- 遇到结局停止
- 某些"死路"分支提前终止

### 4.6 不可中断机制

**重要**：故事生成过程不允许中断！

**实现策略**：
1. **自动重试**：任何 LLM 调用失败自动重试 3 次
2. **异常恢复**：遇到异常不退出，记录日志后继续
3. **进度持久化**：每 50 个节点保存一次，但用于恢复而非中断
4. **用户提示**：明确告知用户生成需要 2-4 小时，不要关闭

```python
def generate_with_no_interrupt(self):
    """不可中断的生成流程"""

    print("⚠️  生成过程预计 2-4 小时，请勿中断！")
    print("⚠️  关闭窗口或强制退出将导致生成失败，需重新开始！")
    print()
    input("按 Enter 确认开始生成...")

    # 禁用 Ctrl+C（可选，可能不友好）
    # signal.signal(signal.SIGINT, signal.SIG_IGN)

    retry_count = 0
    max_retries = 3

    while True:
        try:
            tree = self.build_dialogue_tree()

            # 验证完整性
            if not self.validate_tree(tree):
                raise ValueError("对话树验证失败")

            # 验证游戏时长
            duration = estimate_playtime(tree)
            if duration < 15:
                raise ValueError(f"游戏时长不足：{duration} 分钟")

            print("✅ 生成成功！")
            return tree

        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"❌ 生成失败（重试 {max_retries} 次后）：{e}")
                print("⚠️  请重新开始生成")
                raise

            print(f"⚠️  遇到错误，自动重试 {retry_count}/{max_retries}...")
            print(f"   错误信息：{e}")
            time.sleep(10)  # 等待 10 秒后重试
```

---

## 5. LLM 配置

### 5.1 关键参数

```python
llm = LLM(
    model="kimi-k2-0905-preview",  # 使用最高质量模型
    api_key=kimi_key,
    base_url=kimi_base,
    max_tokens=128000,  # 最大化输出（128K）
    temperature=0.8,     # 保持一定创意
    timeout=300,         # 5 分钟超时
)
```

### 5.2 重试机制

```python
def generate_with_retry(self, func, *args, max_retries=3):
    """带重试的生成"""
    for attempt in range(max_retries):
        try:
            return func(*args)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"⚠️  生成失败，重试 {attempt + 1}/{max_retries}: {e}")
            time.sleep(5 * (attempt + 1))  # 指数退避
```

---

## 6. 运行时集成（更新）

### 6.1 对话树加载器

```python
class DialogueTreeLoader:
    """对话树加载器"""

    def __init__(self, tree_path):
        self.tree_path = tree_path
        self.tree = None
        self.index = None

    def load(self):
        """加载对话树"""
        with open(self.tree_path, 'r') as f:
            data = json.load(f)

        self.tree = data["nodes"]
        self.index = data["index"]
        print(f"✅ 已加载对话树：{len(self.tree)} 个节点")

    def get_node(self, node_id):
        """获取节点"""
        return self.tree.get(node_id)

    def get_choices(self, node_id):
        """获取选择"""
        node = self.get_node(node_id)
        return node["choices"] if node else []

    def get_response(self, node_id):
        """获取响应"""
        node = self.get_node(node_id)
        return node["narrative"] if node else None
```

### 6.2 游戏引擎集成

```python
class GameEngine:
    def __init__(self, ..., pregenerated_path=None):
        self.pregenerated_path = pregenerated_path

        if pregenerated_path and Path(pregenerated_path).exists():
            # 预生成模式
            self.mode = "pregenerated"
            self.dialogue_loader = DialogueTreeLoader(pregenerated_path)
            self.dialogue_loader.load()
            self.current_node_id = "root"
            print("🎮 [预生成模式] 已加载对话树，零等待模式！")
        else:
            # 实时生成模式
            self.mode = "realtime"
            self.choice_generator = ChoicePointsGenerator(...)
            self.response_generator = RuntimeResponseGenerator(...)
            print("🎮 [实时模式] 使用 LLM 即时生成")

    def get_choices(self):
        """获取选择（支持两种模式）"""
        if self.mode == "pregenerated":
            return self.dialogue_loader.get_choices(self.current_node_id)
        else:
            return self.choice_generator.generate_choices(...)

    def get_response(self, choice):
        """获取响应（支持两种模式）"""
        if self.mode == "pregenerated":
            # 从对话树读取
            next_node_id = choice.next_node_id
            response = self.dialogue_loader.get_response(next_node_id)
            self.current_node_id = next_node_id
            return response
        else:
            # 实时生成
            return self.response_generator.generate_response(...)
```

---

## 7. 游戏启动流程

### 7.1 新版启动命令

```bash
# 启动游戏（唯一入口）
./play_now.sh

# 或
python3 play_game.py
```

**注意**：不再有 `--pregenerated` 参数，所有故事都从数据库加载！

### 7.2 主菜单交互

```python
class GameLauncher:
    def __init__(self):
        self.db = DatabaseManager()
        self.menu = MenuSystem(self.db)

    def start(self):
        """游戏启动入口"""
        print("╔═══════════════════════════════════════╗")
        print("║  Welcome to Ghost Story Factory!     ║")
        print("╚═══════════════════════════════════════╝")
        print()
        input("按 Enter 开始游戏...")

        while True:
            choice = self.menu.show_main_menu()

            if choice == "1":
                # 选择故事
                city, story, character = self.menu.select_story_flow()
                if story:
                    self.play_story(story, character)

            elif choice == "2":
                # 生成故事
                story = self.menu.generate_story_flow()
                print("✅ 故事已生成！返回主菜单选择「选择故事」开始游玩")

            elif choice == "q":
                print("再见！")
                break

    def play_story(self, story, character):
        """开始游戏"""
        # 从数据库加载对话树
        dialogue_tree = self.db.load_dialogue_tree(story.id, character.id)

        # 启动游戏引擎
        engine = GameEngine(
            city=story.city,
            dialogue_tree=dialogue_tree,  # 直接传入对话树
            mode="pregenerated"  # 强制预生成模式
        )
        engine.run()
```

### 7.3 故事生成命令（内部使用）

**用户通过菜单生成，不直接调用命令**

内部实现：
```python
class StoryGenerator:
    def generate_full_story(self, city: str, synopsis: StorySynopsis):
        """完整生成流程（不可中断）"""

        print(f"🚀 开始生成故事：{synopsis.title}")
        print(f"⚠️  预计 2-4 小时，请勿中断！")
        print()

        # 1. 生成 GDD、Lore、主线
        self.generate_documents(city, synopsis)

        # 2. 提取角色
        characters = self.extract_characters()

        # 3. 为每个角色生成对话树
        for char in characters:
            self.generate_character_tree(char)

        # 4. 验证并保存
        self.validate_and_save()
```

---

## 8. 预期效果

### 8.1 生成阶段

| 指标 | 估算值 | 说明 |
|------|--------|------|
| 生成时间 | 2-4 小时 | 取决于对话树大小 |
| 节点数量 | 800-1500 | 深度 20，每层 3 个选择 |
| Token 消耗 | 500K-1M | 每节点约 600-1000 tokens |
| 成本 | $10-20 | 一次性成本 |
| 文件大小 | 10-50 MB | 压缩后 2-10 MB |

### 8.2 游戏阶段

| 指标 | 值 | 对比实时模式 |
|------|-----|-------------|
| 响应时间 | < 0.1 秒 | 实时：15-25 秒 |
| 流畅度 | 完美 | 实时：有等待 |
| 成本 | $0 | 实时：$1.20/次 |
| 网络依赖 | 无 | 实时：必需 |
| 离线游玩 | ✅ 支持 | 实时：不支持 |

---

## 9. 技术挑战与解决方案

### 9.1 挑战1：生成时间长

**问题**：
- 预计 2-4 小时
- 容易中断
- 用户等待久

**解决方案**：
1. ✅ 断点续传：每 50 个节点保存一次
2. ✅ 进度显示：实时显示进度和 ETA
3. ✅ 后台运行：支持 `nohup` 后台执行
4. ✅ 多次运行：支持分批生成，逐步完善

### 9.2 挑战2：状态爆炸

**问题**：
- 分支选择导致节点数指数增长
- 深度 20，每层 4 个选择 = 4^20 = 1万亿节点！

**解决方案**：
1. ✅ 状态去重：相同状态复用节点
2. ✅ 状态合并：相近状态视为相同
3. ✅ 智能剪枝：提前终止无意义分支
4. ✅ 限制分支数：每节点最多 3-4 个选择

**效果**：
- 理论节点数：4^20 = 1.1万亿
- 去重后：约 1500 节点（减少 99.9999%）

### 9.3 挑战3：内容质量

**问题**：
- 批量生成可能质量下降
- 缺少人工审核

**解决方案**：
1. ✅ 使用最高质量模型（kimi-k2-0905-preview）
2. ✅ 使用完整故事背景（混合方案）
3. ✅ 生成后可人工审核和调整
4. ✅ 支持重新生成特定分支

### 9.4 挑战4：文件管理

**问题**：
- JSON 文件可能很大（50MB+）
- 加载速度慢
- 不易编辑

**解决方案**：
1. ✅ Gzip 压缩：减小 80% 体积
2. ✅ 延迟加载：按需加载节点
3. ✅ SQLite 存储：大型对话树用数据库
4. ✅ 可视化工具：提供对话树查看器

---

## 10. 里程碑

### Phase 1: 数据库系统（1 天）
- [ ] 数据库表设计和创建
- [ ] DatabaseManager 实现
- [ ] 数据模型（City, Story, Character, DialogueTree）
- [ ] 基本的 CRUD 操作

### Phase 2: 故事简介生成（0.5 天）
- [ ] SynopsisGenerator 实现
- [ ] Prompt 设计和优化
- [ ] JSON 解析和验证

### Phase 3: 核心对话树生成器（2 天）
- [ ] 对话树数据结构
- [ ] BFS 遍历算法
- [ ] 状态去重和合并
- [ ] 游戏时长验证（>= 15 分钟）
- [ ] 不可中断机制
- [ ] 自动重试和错误恢复
- [ ] 详细的进度显示

### Phase 4: 主菜单系统（1 天）
- [ ] MenuSystem 实现
- [ ] 故事选择流程（城市→故事→角色）
- [ ] 故事生成流程（城市→简介→完整生成）
- [ ] 精美的 CLI 界面

### Phase 5: 运行时集成（1 天）
- [ ] 对话树加载器
- [ ] GameEngine 集成（仅预生成模式）
- [ ] 从数据库加载对话树
- [ ] 性能测试

### Phase 6: 完善和优化（1 天）
- [ ] 文件压缩（Gzip）
- [ ] 错误处理完善
- [ ] 用户体验优化
- [ ] 文档完善

**总工期**：6-7 天

---

## 11. 后续扩展

### 11.1 可视化工具

```bash
# 查看对话树结构
python3 view_dialogue_tree.py dialogues/hangzhou/dialogue_tree.json

# 输出为图形
python3 view_dialogue_tree.py --format svg --output tree.svg
```

### 11.2 编辑工具

```bash
# 重新生成某个节点
python3 regenerate_node.py --node-id node_042

# 手动编辑对话
python3 edit_dialogue.py --node-id node_042 --edit
```

### 11.3 多语言支持

- 生成英文版对话树
- 生成中文+英文双语对话树

---

## 12. 总结

### 优势

✅ **零等待**：游戏完全流畅
✅ **离线游玩**：不依赖网络和 API
✅ **成本低**：游戏阶段零成本
✅ **可控性高**：可人工审核和调整内容
✅ **复用性强**：一次生成，多次使用

### 限制

❌ **生成耗时**：首次生成需 2-4 小时
❌ **生成成本**：$10-20/次
❌ **不可中断**：生成过程必须完整完成
❌ **存储需求**：需要 SQLite 数据库，每个故事约 10-50 MB

### 设计决策

**✅ 为什么雪藏实时生成功能？**

1. **体验优先**：零等待的游戏体验远好于每次等待 15-25 秒
2. **质量保证**：预生成可以使用最高质量模型，确保内容质量
3. **成本优化**：一次性成本 $10-20，而实时模式每次游玩 $1.20
4. **离线游玩**：支持完全离线，不依赖网络和 API
5. **稳定性高**：避免 API 调用失败、网络问题等影响游戏体验

**🔄 何时重新启用实时生成？**

优化完成后，可作为"专家模式"提供：
- 默认模式：预生成（推荐，零等待）
- 专家模式：实时生成（动态，每次不同）

### 产品定位

**当前版本**：
- 专注于预生成模式
- 提供精品化的故事体验
- 确保流畅的游戏体验

**未来扩展**：
- 故事编辑器（可视化编辑对话树）
- 社区分享（分享自己生成的故事）
- 多语言支持（生成英文版故事）

---

**文档状态**: ✅ 完成
**等待**: 用户确认后开始实现

