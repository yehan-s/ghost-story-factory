"""
数据库功能测试脚本

测试数据库的基本操作：
1. 初始化数据库
2. 创建城市
3. 保存故事
4. 查询数据
5. 加载对话树
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from ghost_story_factory.database import DatabaseManager, City, Story, Character


def test_database():
    """测试数据库功能"""

    print("=" * 70)
    print("开始测试数据库功能")
    print("=" * 70)
    print()

    # 初始化数据库
    print("1️⃣  初始化数据库...")
    db = DatabaseManager("database/ghost_stories_test.db")
    print()

    # 创建城市
    print("2️⃣  创建测试城市...")
    city_id = db.create_city("杭州", "浙江省省会，电商之都")
    print(f"   城市 ID: {city_id}")
    print()

    # 保存测试故事
    print("3️⃣  保存测试故事...")
    story_id = db.save_story(
        city_name="杭州",
        title="钱江新城观景台诡异事件（测试）",
        synopsis="你是一名特检院工程师，深夜被派往钱江新城观景台调查异常电磁信号...",
        characters=[
            {
                "name": "特检院工程师",
                "is_protagonist": True,
                "description": "主角，专业工程师"
            },
            {
                "name": "夜班保安",
                "is_protagonist": False,
                "description": "观景台夜班保安"
            }
        ],
        dialogue_trees={
            "特检院工程师": {
                "root": {
                    "node_id": "root",
                    "scene": "S1",
                    "narrative": "深夜，你站在钱江新城观景台...",
                    "choices": [
                        {
                            "choice_id": "A",
                            "choice_text": "检查设备",
                            "next_node_id": "node_001"
                        },
                        {
                            "choice_id": "B",
                            "choice_text": "寻找保安",
                            "next_node_id": "node_002"
                        }
                    ]
                },
                "node_001": {
                    "node_id": "node_001",
                    "scene": "S1",
                    "narrative": "你开始检查频谱仪..."
                },
                "node_002": {
                    "node_id": "node_002",
                    "scene": "S1",
                    "narrative": "你决定先找保安了解情况..."
                }
            },
            "夜班保安": {
                "root": {
                    "node_id": "root",
                    "scene": "S1",
                    "narrative": "又是一个漫长的夜晚..."
                }
            }
        },
        metadata={
            "estimated_duration": 5,  # 测试数据，时间短
            "total_nodes": 3,
            "max_depth": 2,
            "cost": 0.50,
            "total_tokens": 1000,
            "generation_time": 60,
            "model": "test-model"
        }
    )
    print(f"   故事 ID: {story_id}")
    print()

    # 查询城市
    print("4️⃣  查询所有城市...")
    cities = db.get_cities()
    for city in cities:
        print(f"   - {city.name}：{city.story_count} 个故事")
    print()

    # 查询故事
    print("5️⃣  查询杭州的故事...")
    stories = db.get_stories_by_city(city_id)
    for story in stories:
        print(f"   - {story.title}")
        print(f"     时长：{story.estimated_duration_minutes} 分钟")
        print(f"     角色数：{story.character_count} 个")
        print(f"     节点数：{story.total_nodes} 个")
    print()

    # 查询角色
    print("6️⃣  查询故事的角色...")
    characters = db.get_characters_by_story(story_id)
    for char in characters:
        protagonist_mark = "⭐" if char.is_protagonist else "  "
        print(f"   {protagonist_mark} {char.name} - {char.description}")
    print()

    # 加载对话树
    print("7️⃣  加载对话树...")
    char_id = characters[0].id  # 主角
    tree = db.load_dialogue_tree(story_id, char_id)
    print(f"   对话树节点数：{len(tree)} 个")
    print(f"   根节点：{tree['root']['node_id']}")
    print(f"   开场叙事：{tree['root']['narrative'][:30]}...")
    print()

    # 关闭数据库
    print("8️⃣  关闭数据库...")
    db.close()
    print()

    print("=" * 70)
    print("✅ 数据库测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    test_database()

