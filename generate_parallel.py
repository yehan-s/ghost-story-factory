#!/usr/bin/env python3
"""
并行生成多个角色的对话树

特性：
- 同时为多个角色生成对话树
- 充分利用多核 CPU
- 显著缩短总生成时间

使用方法：
  python3 generate_parallel.py
"""

import sys
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

# 自动加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, _, value = line.partition('=')
                    os.environ[key.strip()] = value.strip()

from ghost_story_factory.pregenerator.synopsis_generator import StorySynopsis
from ghost_story_factory.pregenerator.tree_builder import DialogueTreeBuilder


# ==================== 配置参数 ====================
CITY = "杭州"
STORY_TITLE = "断桥残血-并行测试"
MAX_WORKERS = min(cpu_count(), 4)  # 最多使用 4 个进程，避免 API 速率限制
TEST_MODE = True  # 测试模式
# ==================================================


def generate_character_tree(args):
    """
    为单个角色生成对话树（用于并行执行）

    Args:
        args: (character_info, gdd_content, lore_content, main_story, test_mode, city, synopsis_text)

    Returns:
        (character_name, dialogue_tree)
    """
    char, gdd, lore, story, test_mode, city, synopsis = args
    char_name = char['name']

    print(f"[{char_name}] 开始生成对话树...")

    try:
        tree_builder = DialogueTreeBuilder(
            city=city,
            synopsis=synopsis,
            gdd_content=gdd,
            lore_content=lore,
            main_story=story,
            test_mode=test_mode
        )

        if test_mode:
            max_depth = 5
            min_main_path = 3
        else:
            max_depth = 20
            min_main_path = 15

        checkpoint_path = f"checkpoints/{city}_{char_name}_tree_parallel.json"

        tree = tree_builder.generate_tree(
            max_depth=max_depth,
            min_main_path_depth=min_main_path,
            checkpoint_path=checkpoint_path
        )

        print(f"[{char_name}] ✅ 对话树生成完成：{len(tree)} 个节点")
        return (char_name, tree)

    except Exception as e:
        print(f"[{char_name}] ❌ 生成失败：{e}")
        import traceback
        traceback.print_exc()
        return (char_name, None)


def extract_characters(city: str):
    """提取角色列表"""
    import json
    import glob

    struct_path = None
    possible_patterns = [
        f"examples/*/{city}_struct.json",
        f"examples/{city}/*_struct.json",
    ]

    for pattern in possible_patterns:
        matches = glob.glob(pattern)
        if matches:
            struct_path = Path(matches[0])
            break

    if struct_path and struct_path.exists():
        with open(struct_path, 'r', encoding='utf-8') as f:
            struct_data = json.load(f)
            potential_roles = struct_data.get('potential_roles', [])

            if potential_roles:
                characters = []
                for idx, role_name in enumerate(potential_roles):
                    characters.append({
                        "name": role_name,
                        "is_protagonist": (idx == 0),
                        "description": f"{city} - {role_name}视角"
                    })
                return characters

    return []


def main():
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          ⚡ 并行生成多角色故事                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    # 检查环境变量
    if not os.getenv("KIMI_API_KEY"):
        print("❌ 错误：未设置 KIMI_API_KEY 环境变量")
        print("请确保 .env 文件存在并包含 KIMI_API_KEY")
        sys.exit(1)

    # 提取角色
    print(f"📋 Step 1: 提取角色列表...")
    characters = extract_characters(CITY)

    if not characters:
        print(f"❌ 错误：未找到 {CITY} 的角色配置")
        sys.exit(1)

    # 测试模式：只生成前2个角色
    if TEST_MODE:
        characters = characters[:2]
        print(f"   ⚡ [测试模式] 只生成前 {len(characters)} 个角色")

    print(f"   ✅ 找到 {len(characters)} 个角色")
    for char in characters:
        mark = "⭐" if char['is_protagonist'] else "  "
        print(f"   {mark} {char['name']}")
    print()

    # 加载文档
    print(f"📄 Step 2: 加载游戏文档...")
    examples_dir = Path("examples/hangzhou")
    gdd_path = examples_dir / "杭州_GDD.md"
    lore_path = examples_dir / "杭州_lore_v2.md"
    main_story_path = examples_dir / "杭州_story.md"

    for path, name in [(gdd_path, "GDD"), (lore_path, "Lore"), (main_story_path, "Story")]:
        if not path.exists():
            print(f"❌ 错误：找不到 {name} 文件: {path}")
            sys.exit(1)

    with open(gdd_path, 'r', encoding='utf-8') as f:
        gdd_content = f.read()
    with open(lore_path, 'r', encoding='utf-8') as f:
        lore_content = f.read()
    with open(main_story_path, 'r', encoding='utf-8') as f:
        main_story = f.read()

    print("   ✅ 文档加载完成")
    print()

    # 配置信息
    synopsis = "午夜时分，西湖断桥上出现白衣女子的身影，外卖骑手被卷入了一场超自然事件..."

    print(f"🚀 Step 3: 并行生成对话树...")
    print(f"   并发进程数: {MAX_WORKERS}")
    print(f"   测试模式: {'是' if TEST_MODE else '否'}")
    if TEST_MODE:
        print(f"   预计时间: 3-5 分钟（并行）vs 5-10 分钟（串行）")
    else:
        print(f"   预计时间: {len(characters) * 2} 小时（串行）→ {max(2, len(characters) * 2 // MAX_WORKERS)} 小时（并行）")
    print()

    input("按 Enter 开始并行生成...")
    print()

    # 准备参数
    args_list = [
        (char, gdd_content, lore_content, main_story, TEST_MODE, CITY, synopsis)
        for char in characters
    ]

    # 并行生成
    dialogue_trees = {}
    failed_chars = []

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_char = {
            executor.submit(generate_character_tree, args): args[0]['name']
            for args in args_list
        }

        # 收集结果
        for future in as_completed(future_to_char):
            char_name = future_to_char[future]
            try:
                result_char_name, tree = future.result()
                if tree:
                    dialogue_trees[result_char_name] = tree
                else:
                    failed_chars.append(result_char_name)
            except Exception as e:
                print(f"[{char_name}] ❌ 异常：{e}")
                failed_chars.append(char_name)

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║          📊 并行生成完成                                        ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    print(f"✅ 成功生成: {len(dialogue_trees)} 个角色")
    for name in dialogue_trees.keys():
        print(f"   • {name}: {len(dialogue_trees[name])} 个节点")

    if failed_chars:
        print(f"\n❌ 失败角色: {len(failed_chars)} 个")
        for name in failed_chars:
            print(f"   • {name}")

    print()
    print("💾 Step 4: 保存到数据库...")

    try:
        from ghost_story_factory.database import DatabaseManager

        db = DatabaseManager()

        # 计算元数据
        total_nodes = sum(len(tree) for tree in dialogue_trees.values())
        main_tree = dialogue_trees[characters[0]['name']] if dialogue_trees else {}

        # 简化的元数据
        metadata = {
            "estimated_duration": 5 if TEST_MODE else 20,
            "total_nodes": total_nodes,
            "max_depth": 5 if TEST_MODE else 20,
            "cost": 0.0,
            "total_tokens": 0,
            "generation_time": 0,
            "model": os.getenv("KIMI_MODEL_RESPONSE", "kimi-k2-0905-preview"),
            "parallel_generation": True,
            "workers": MAX_WORKERS
        }

        story_id = db.save_story(
            city_name=CITY,
            title=STORY_TITLE,
            synopsis=synopsis,
            characters=characters,
            dialogue_trees=dialogue_trees,
            metadata=metadata
        )

        db.close()

        print(f"   ✅ 故事已保存到数据库（ID: {story_id}）")
        print()
        print("🎮 下一步：")
        print("  ./start_pregenerated_game.sh")
        print()
        print(f"  选择故事「{STORY_TITLE}」开始游玩！")

    except Exception as e:
        print(f"   ❌ 保存失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

