#!/usr/bin/env python3
"""
智能并行生成系统 - 动态工作队列

特性：
- 同时保持 2 个角色在生成（可配置）
- 完成一个立即开始下一个，不浪费时间
- 实时进度显示
- 失败自动重试

使用方法：
  python3 generate_smart_parallel.py
"""

import sys
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import time
from datetime import datetime

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

from ghost_story_factory.pregenerator.tree_builder import DialogueTreeBuilder


# ==================== 配置参数 ====================
CITY = "杭州"
STORY_TITLE = "断桥残血-智能并行测试"

# 并发配置
MAX_CONCURRENT = 2  # 同时生成的角色数量
MAX_RETRIES = 2     # 失败重试次数

# 测试模式
TEST_MODE = True
MAX_DEPTH = 5 if TEST_MODE else 20
MIN_MAIN_PATH = 3 if TEST_MODE else 15

# ==================================================


class SmartParallelGenerator:
    """智能并行生成器 - 动态工作队列"""
    
    def __init__(self, city: str, test_mode: bool = True):
        self.city = city
        self.test_mode = test_mode
        
        # 状态追踪
        self.completed_count = 0
        self.failed_count = 0
        self.total_count = 0
        self.dialogue_trees = {}
        
        # 线程安全
        self.lock = Lock()
        self.start_time = None
        
        # 文档内容（预加载）
        self.gdd_content = None
        self.lore_content = None
        self.main_story = None
        self.synopsis = None
    
    def load_documents(self):
        """预加载文档"""
        print("📄 加载游戏文档...")
        examples_dir = Path(f"examples/hangzhou")
        gdd_path = examples_dir / "杭州_GDD.md"
        lore_path = examples_dir / "杭州_lore_v2.md"
        main_story_path = examples_dir / "杭州_story.md"
        
        for path, name in [(gdd_path, "GDD"), (lore_path, "Lore"), (main_story_path, "Story")]:
            if not path.exists():
                raise FileNotFoundError(f"找不到 {name} 文件: {path}")
        
        with open(gdd_path, 'r', encoding='utf-8') as f:
            self.gdd_content = f.read()
        with open(lore_path, 'r', encoding='utf-8') as f:
            self.lore_content = f.read()
        with open(main_story_path, 'r', encoding='utf-8') as f:
            self.main_story = f.read()
        
        self.synopsis = "午夜时分，西湖断桥上出现白衣女子的身影..."
        print("   ✅ 文档加载完成\n")
    
    def generate_character_tree(self, character: dict, retry_count: int = 0):
        """
        为单个角色生成对话树
        
        Args:
            character: 角色信息
            retry_count: 当前重试次数
        
        Returns:
            (character_name, dialogue_tree) 或 (character_name, None) 如果失败
        """
        char_name = character['name']
        
        # 显示开始信息
        with self.lock:
            self.print_status(f"[{char_name}] 🔄 开始生成...")
        
        try:
            tree_builder = DialogueTreeBuilder(
                city=self.city,
                synopsis=self.synopsis,
                gdd_content=self.gdd_content,
                lore_content=self.lore_content,
                main_story=self.main_story,
                test_mode=self.test_mode
            )
            
            checkpoint_path = f"checkpoints/{self.city}_{char_name}_tree_smart.json"
            
            tree = tree_builder.generate_tree(
                max_depth=MAX_DEPTH,
                min_main_path_depth=MIN_MAIN_PATH,
                checkpoint_path=checkpoint_path
            )
            
            # 成功
            with self.lock:
                self.completed_count += 1
                self.dialogue_trees[char_name] = tree
                self.print_status(f"[{char_name}] ✅ 完成！节点数: {len(tree)}")
            
            return (char_name, tree)
            
        except Exception as e:
            # 失败处理
            if retry_count < MAX_RETRIES:
                with self.lock:
                    self.print_status(f"[{char_name}] ⚠️  失败，重试 {retry_count + 1}/{MAX_RETRIES}...")
                
                time.sleep(2)  # 等待2秒后重试
                return self.generate_character_tree(character, retry_count + 1)
            else:
                with self.lock:
                    self.failed_count += 1
                    self.print_status(f"[{char_name}] ❌ 生成失败：{e}")
                
                return (char_name, None)
    
    def print_status(self, message: str):
        """打印带时间戳的状态信息（线程安全）"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        timestamp = f"[{elapsed:>6.1f}s]"
        progress = f"[{self.completed_count}/{self.total_count}]"
        print(f"{timestamp} {progress} {message}")
    
    def generate_all(self, characters: list):
        """
        使用智能并行策略生成所有角色的对话树
        
        Args:
            characters: 角色列表
        
        Returns:
            dialogue_trees: {角色名: 对话树}
        """
        self.total_count = len(characters)
        self.start_time = time.time()
        
        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║          ⚡ 智能并行生成 - 动态工作队列                        ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        print(f"📊 生成配置：")
        print(f"   总角色数: {self.total_count}")
        print(f"   并发数量: {MAX_CONCURRENT}")
        print(f"   测试模式: {'是' if self.test_mode else '否'}")
        print(f"   深度配置: max={MAX_DEPTH}, min_main={MIN_MAIN_PATH}")
        print()
        print(f"⚡ 策略: 保持 {MAX_CONCURRENT} 个角色同时生成，完成一个立即开始下一个")
        print()
        
        # 使用 ThreadPoolExecutor（IO密集型任务，线程更合适）
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as executor:
            # 提交所有任务
            future_to_char = {
                executor.submit(self.generate_character_tree, char): char['name']
                for char in characters
            }
            
            # 实时收集结果
            for future in as_completed(future_to_char):
                char_name = future_to_char[future]
                try:
                    result_name, tree = future.result()
                    # 结果已经在 generate_character_tree 中处理
                except Exception as e:
                    with self.lock:
                        self.failed_count += 1
                        self.print_status(f"[{char_name}] 💥 异常：{e}")
        
        # 生成完成
        elapsed = time.time() - self.start_time
        
        print()
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║          📊 生成完成                                            ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        print(f"⏱️  总耗时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
        print(f"✅ 成功: {self.completed_count}/{self.total_count}")
        print(f"❌ 失败: {self.failed_count}/{self.total_count}")
        print()
        
        if self.dialogue_trees:
            print("生成详情：")
            total_nodes = 0
            for name, tree in self.dialogue_trees.items():
                nodes = len(tree)
                total_nodes += nodes
                print(f"   • {name}: {nodes} 个节点")
            print(f"\n   总节点数: {total_nodes:,}")
        
        return self.dialogue_trees


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
    print("║          🎯 智能并行生成系统                                    ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()
    
    # 检查环境变量
    if not os.getenv("KIMI_API_KEY"):
        print("❌ 错误：未设置 KIMI_API_KEY 环境变量")
        print("请确保 .env 文件存在并包含 KIMI_API_KEY")
        sys.exit(1)
    
    # 提取角色
    print(f"📋 提取角色列表...")
    characters = extract_characters(CITY)
    
    if not characters:
        print(f"❌ 错误：未找到 {CITY} 的角色配置")
        sys.exit(1)
    
    # 测试模式：限制角色数量
    if TEST_MODE:
        # 可以测试更多角色，看动态队列效果
        characters = characters[:4]  # 测试4个角色，2个并发
        print(f"   ⚡ [测试模式] 生成前 {len(characters)} 个角色")
    
    print(f"   ✅ 找到 {len(characters)} 个角色")
    for char in characters:
        mark = "⭐" if char['is_protagonist'] else "  "
        print(f"   {mark} {char['name']}")
    print()
    
    # 创建生成器
    generator = SmartParallelGenerator(
        city=CITY,
        test_mode=TEST_MODE
    )
    
    # 加载文档
    try:
        generator.load_documents()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 确认开始
    print("准备开始智能并行生成...")
    print()
    input("按 Enter 确认开始...")
    
    # 开始生成
    dialogue_trees = generator.generate_all(characters)
    
    # 保存到数据库
    if dialogue_trees:
        print()
        print("💾 保存到数据库...")
        
        try:
            from ghost_story_factory.database import DatabaseManager
            
            db = DatabaseManager()
            
            total_nodes = sum(len(tree) for tree in dialogue_trees.values())
            
            metadata = {
                "estimated_duration": 5 if TEST_MODE else 20,
                "total_nodes": total_nodes,
                "max_depth": MAX_DEPTH,
                "cost": 0.0,
                "total_tokens": 0,
                "generation_time": time.time() - generator.start_time,
                "model": os.getenv("KIMI_MODEL_RESPONSE", "kimi-k2-0905-preview"),
                "parallel_generation": True,
                "concurrent_workers": MAX_CONCURRENT,
                "generation_strategy": "smart_parallel"
            }
            
            story_id = db.save_story(
                city_name=CITY,
                title=STORY_TITLE,
                synopsis=generator.synopsis,
                characters=[c for c in characters if c['name'] in dialogue_trees],
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
    else:
        print()
        print("❌ 没有成功生成任何角色的对话树")
        sys.exit(1)


if __name__ == "__main__":
    main()

