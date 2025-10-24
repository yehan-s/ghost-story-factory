"""
数据库管理器

负责所有数据库操作，包括：
- 初始化数据库
- 保存和查询故事
- 管理对话树
"""

import sqlite3
import json
import gzip
from pathlib import Path
from typing import List, Dict, Optional, Any

from .models import City, Story, Character, DialogueTree, GenerationMetadata


class DatabaseManager:
    """SQLite 数据库管理器"""

    def __init__(self, db_path: str = "database/ghost_stories.db"):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # 返回字典格式

        # 启用外键约束
        self.conn.execute("PRAGMA foreign_keys = ON")

        self.init_db()

    def init_db(self):
        """初始化数据库表（如果不存在）"""
        schema_path = Path(__file__).parent.parent.parent.parent / "sql" / "schema.sql"

        if not schema_path.exists():
            print(f"⚠️  Schema 文件不存在：{schema_path}")
            return

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        cursor = self.conn.cursor()
        cursor.executescript(schema_sql)
        self.conn.commit()

        print(f"✅ 数据库初始化完成：{self.db_path}")

    # ==================== 城市操作 ====================

    def get_cities(self) -> List[City]:
        """获取所有城市（含故事数量）"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.description, c.created_at,
                   COUNT(s.id) as story_count
            FROM cities c
            LEFT JOIN stories s ON c.id = s.city_id
            GROUP BY c.id
            ORDER BY c.name
        """)

        return [City.from_db_row(dict(row)) for row in cursor.fetchall()]

    def get_city_by_name(self, name: str) -> Optional[City]:
        """根据名称获取城市"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE name = ?", (name,))
        row = cursor.fetchone()

        return City.from_db_row(dict(row)) if row else None

    def create_city(self, name: str, description: str = None) -> int:
        """
        创建城市（如果不存在）

        Returns:
            城市 ID
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO cities (name, description) VALUES (?, ?)",
            (name, description)
        )

        # 获取城市 ID
        cursor.execute("SELECT id FROM cities WHERE name = ?", (name,))
        city_id = cursor.fetchone()['id']

        self.conn.commit()
        return city_id

    # ==================== 故事操作 ====================

    def get_stories_by_city(self, city_id: int) -> List[Story]:
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

        return [Story.from_db_row(dict(row)) for row in cursor.fetchall()]

    def get_story_by_id(self, story_id: int) -> Optional[Story]:
        """根据 ID 获取故事"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.*, COUNT(DISTINCT c.id) as character_count
            FROM stories s
            LEFT JOIN characters c ON s.id = c.story_id
            WHERE s.id = ?
            GROUP BY s.id
        """, (story_id,))
        row = cursor.fetchone()

        return Story.from_db_row(dict(row)) if row else None

    # ==================== 角色操作 ====================

    def get_characters_by_story(self, story_id: int) -> List[Character]:
        """获取某故事的所有角色"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM characters
            WHERE story_id = ?
            ORDER BY is_protagonist DESC, name
        """, (story_id,))

        return [Character.from_db_row(dict(row)) for row in cursor.fetchall()]

    def get_character_by_id(self, character_id: int) -> Optional[Character]:
        """根据 ID 获取角色"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM characters WHERE id = ?", (character_id,))
        row = cursor.fetchone()

        return Character.from_db_row(dict(row)) if row else None

    # ==================== 对话树操作 ====================

    def load_dialogue_tree(self, story_id: int, character_id: int) -> Dict[str, Any]:
        """
        加载对话树

        Args:
            story_id: 故事 ID
            character_id: 角色 ID

        Returns:
            对话树字典

        Raises:
            ValueError: 如果未找到对话树
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT tree_data, compressed
            FROM dialogue_trees
            WHERE story_id = ? AND character_id = ?
        """, (story_id, character_id))

        row = cursor.fetchone()
        if not row:
            raise ValueError(
                f"未找到对话树：story_id={story_id}, character_id={character_id}"
            )

        tree_data = row['tree_data']
        compressed = row['compressed']

        # 解压缩（如果需要）
        if compressed:
            try:
                tree_json = gzip.decompress(tree_data).decode('utf-8')
            except Exception as e:
                raise ValueError(f"解压对话树失败：{e}")
        else:
            tree_json = tree_data

        # 解析 JSON
        try:
            return json.loads(tree_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"解析对话树 JSON 失败：{e}")

    # ==================== 保存完整故事 ====================

    def save_story(
        self,
        city_name: str,
        title: str,
        synopsis: str,
        characters: List[Dict[str, Any]],
        dialogue_trees: Dict[str, Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> int:
        """
        保存完整的故事（包括对话树）

        Args:
            city_name: 城市名称
            title: 故事标题
            synopsis: 故事简介
            characters: 角色列表 [{"name": "...", "is_protagonist": True, "description": "..."}]
            dialogue_trees: 对话树字典 {"角色名": {对话树数据}}
            metadata: 元数据 {"estimated_duration": 18, "total_nodes": 1458, ...}

        Returns:
            故事 ID
        """
        cursor = self.conn.cursor()

        try:
            # 1. 确保城市存在
            city_id = self.create_city(city_name)

            # 2. 插入故事
            cursor.execute("""
                INSERT INTO stories
                (city_id, title, synopsis, estimated_duration_minutes,
                 total_nodes, max_depth, generation_cost_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                city_id,
                title,
                synopsis,
                metadata.get('estimated_duration', 0),
                metadata.get('total_nodes', 0),
                metadata.get('max_depth', 0),
                metadata.get('cost', 0.0)
            ))
            story_id = cursor.lastrowid

            # 3. 插入角色
            char_id_map = {}
            for char in characters:
                cursor.execute("""
                    INSERT INTO characters (story_id, name, is_protagonist, description)
                    VALUES (?, ?, ?, ?)
                """, (
                    story_id,
                    char['name'],
                    1 if char.get('is_protagonist', False) else 0,
                    char.get('description', '')
                ))
                char_id_map[char['name']] = cursor.lastrowid

            # 4. 保存对话树（JSON 格式，可选压缩）
            for char_name, tree in dialogue_trees.items():
                char_id = char_id_map.get(char_name)
                if not char_id:
                    print(f"⚠️  角色 {char_name} 不存在，跳过对话树")
                    continue

                # 转为 JSON
                tree_json = json.dumps(tree, ensure_ascii=False, indent=2)

                # 可选：Gzip 压缩（大于 10KB 才压缩）
                if len(tree_json) > 10000:
                    tree_data = gzip.compress(tree_json.encode('utf-8'))
                    compressed = 1
                else:
                    tree_data = tree_json
                    compressed = 0

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
                metadata.get('total_tokens', 0),
                metadata.get('generation_time', 0),
                metadata.get('model', '')
            ))

            self.conn.commit()
            print(f"✅ 故事已保存：ID={story_id}, 标题=「{title}」")
            return story_id

        except Exception as e:
            self.conn.rollback()
            print(f"❌ 保存故事失败：{e}")
            raise

    # ==================== 工具方法 ====================

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        print("✅ 数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

