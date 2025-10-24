"""
完整故事生成器

整合所有组件，实现不可中断的完整故事生成流程
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

from .synopsis_generator import StorySynopsis
from .tree_builder import DialogueTreeBuilder
from ..database import DatabaseManager


class StoryGeneratorWithRetry:
    """带重试机制的故事生成器"""

    def __init__(self, city: str, synopsis: StorySynopsis, test_mode: bool = False):
        """
        初始化生成器

        Args:
            city: 城市名称
            synopsis: 故事简介
            test_mode: 测试模式（快速生成MVP用于验证）
        """
        self.city = city
        self.synopsis = synopsis
        self.max_retries = 3  # 最大重试次数
        self.test_mode = test_mode  # 测试模式

    def generate_full_story(
        self,
        gdd_path: Optional[str] = None,
        lore_path: Optional[str] = None,
        main_story_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成完整故事（支持断点续传！）

        Args:
            gdd_path: GDD 文件路径
            lore_path: Lore 文件路径
            main_story_path: 主线故事路径

        Returns:
            生成结果
        """
        print("\n")
        print("╔══════════════════════════════════════════════════════════════════╗")
        if self.test_mode:
            print("║              🧪 开始生成测试故事 (MVP)                          ║")
        else:
            print("║              🚀 开始生成完整故事                                ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print("\n")
        print(f"故事标题: {self.synopsis.title}")
        print(f"城市: {self.city}")
        print(f"主角: {self.synopsis.protagonist}")
        print(f"场景: {self.synopsis.location}")
        print(f"预计时长: {self.synopsis.estimated_duration} 分钟")
        print("\n")

        if self.test_mode:
            print("⚡ [测试模式] 预计生成时间: 5-10 分钟")
            print("   • 角色数量: 2 个")
            print("   • 对话树深度: 5 层")
            print("   • 主线深度: 3 层")
        else:
            print("⚠️  [警告] 生成过程预计 2-4 小时")
            print("✅ [支持] 如果中断，下次可以从断点继续！")
        print("\n")

        # 用户确认
        input("按 Enter 确认开始生成...")
        print("\n")

        # 重试循环
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # 1. 生成文档（GDD、Lore、主线故事）
                print("📄 Step 1/4: 生成游戏设计文档...")
                gdd_content, lore_content, main_story = self._generate_documents(
                    gdd_path, lore_path, main_story_path
                )
                print("   ✅ 文档生成完成")
                print("\n")

                # 2. 提取角色列表
                print("👥 Step 2/4: 提取角色列表...")
                characters = self._extract_characters(main_story)

                # 测试模式：只生成前2个角色
                if self.test_mode:
                    print("   ⚡ [测试模式] 只生成前 2 个角色以快速验证")
                    characters = characters[:2]

                print(f"   ✅ 找到 {len(characters)} 个角色")
                for char in characters:
                    mark = "⭐" if char['is_protagonist'] else "  "
                    print(f"   {mark} {char['name']}")
                print("\n")

                # 3. 生成对话树（最耗时）
                print("🌳 Step 3/4: 生成对话树（主要耗时步骤）...")

                # 测试模式：使用更小的深度
                if self.test_mode:
                    max_depth = 5
                    min_main_path = 3
                    print(f"   ⚡ [测试模式] 使用较小深度: max_depth={max_depth}, min_main_path={min_main_path}")
                else:
                    max_depth = 20
                    min_main_path = 15

                dialogue_trees = {}

                # 🔄 尝试加载角色级别的检查点
                char_checkpoint = self._load_character_checkpoint()
                if char_checkpoint:
                    dialogue_trees = char_checkpoint.get("dialogue_trees", {})
                    completed_chars = list(dialogue_trees.keys())
                    print(f"\n✅ 发现角色级检查点！已恢复 {len(completed_chars)} 个角色的对话树")
                    for char_name in completed_chars:
                        print(f"   ✓ {char_name}")
                    print()

                for char in characters:
                    # 跳过已完成的角色
                    if char['name'] in dialogue_trees:
                        print(f"⏩ 跳过已完成的角色「{char['name']}」")
                        continue

                    print(f"\n🔄 正在为角色「{char['name']}」生成对话树...")

                    # 使用角色专属的检查点路径
                    checkpoint_path = f"checkpoints/{self.city}_{char['name']}_tree.json"

                    tree_builder = DialogueTreeBuilder(
                        city=self.city,
                        synopsis=self.synopsis.synopsis,
                        gdd_content=gdd_content,
                        lore_content=lore_content,
                        main_story=main_story,
                        test_mode=self.test_mode
                    )

                    tree = tree_builder.generate_tree(
                        max_depth=max_depth,
                        min_main_path_depth=min_main_path,
                        checkpoint_path=checkpoint_path
                    )

                    dialogue_trees[char['name']] = tree
                    print(f"   ✅ {char['name']} 的对话树生成完成：{len(tree)} 个节点")

                    # 保存角色级检查点（每完成一个角色）
                    self._save_character_checkpoint(
                        characters,
                        dialogue_trees,
                        gdd_content,
                        lore_content,
                        main_story
                    )

                print("\n")
                print("   ✅ 所有对话树生成完成")
                print("\n")

                # 4. 保存到数据库
                print("💾 Step 4/4: 保存到数据库...")
                db = DatabaseManager()

                # 计算元数据
                main_tree = dialogue_trees[characters[0]['name']]  # 主角的树
                metadata = self._calculate_metadata(main_tree, dialogue_trees)

                story_id = db.save_story(
                    city_name=self.city,
                    title=self.synopsis.title,
                    synopsis=self.synopsis.synopsis,
                    characters=characters,
                    dialogue_trees=dialogue_trees,
                    metadata=metadata
                )

                db.close()
                print(f"   ✅ 故事已保存到数据库（ID: {story_id}）")
                print("\n")

                # 🗑️ 清理所有检查点（生成成功）
                self._cleanup_all_checkpoints(characters)

                # 成功！
                self._print_success_summary(metadata)

                return {
                    "story_id": story_id,
                    "title": self.synopsis.title,
                    "metadata": metadata,
                    "characters": characters
                }

            except Exception as e:
                retry_count += 1

                if retry_count >= self.max_retries:
                    print("\n")
                    print("╔══════════════════════════════════════════════════════════════════╗")
                    print("║              ❌ 生成失败                                        ║")
                    print("╚══════════════════════════════════════════════════════════════════╝")
                    print("\n")
                    print(f"错误信息：{e}")
                    print(f"已重试 {self.max_retries} 次，仍然失败。")
                    print("⚠️  请检查配置后重新开始。")
                    raise

                print("\n")
                print(f"⚠️  遇到错误，自动重试 {retry_count}/{self.max_retries}...")
                print(f"   错误信息：{e}")
                print(f"   等待 10 秒后重试...")
                time.sleep(10)

    def _generate_documents(
        self,
        gdd_path: Optional[str],
        lore_path: Optional[str],
        main_story_path: Optional[str]
    ) -> tuple:
        """生成或加载文档"""

        # 如果提供了路径，直接加载
        if gdd_path and Path(gdd_path).exists():
            with open(gdd_path, 'r', encoding='utf-8') as f:
                gdd_content = f.read()
        else:
            gdd_content = self._generate_gdd()

        if lore_path and Path(lore_path).exists():
            with open(lore_path, 'r', encoding='utf-8') as f:
                lore_content = f.read()
        else:
            lore_content = self._generate_lore()

        if main_story_path and Path(main_story_path).exists():
            with open(main_story_path, 'r', encoding='utf-8') as f:
                main_story = f.read()
        else:
            main_story = self._generate_main_story()

        return gdd_content, lore_content, main_story

    def _generate_gdd(self) -> str:
        """生成 GDD（简化版）"""
        return f"""# 游戏设计文档 - {self.synopsis.title}

## 基本信息
- 城市：{self.city}
- 主角：{self.synopsis.protagonist}
- 场景：{self.synopsis.location}

## 游戏机制
- PR（恐惧值）：0-100
- GR（真相值）：0-100
- WF（世界熟悉度）：0-100

## 场景
- S1：{self.synopsis.location}（起始场景）
"""

    def _generate_lore(self) -> str:
        """生成 Lore（简化版）"""
        return f"""# 世界观规则 - {self.synopsis.title}

## 核心规则
1. 恐怖氛围优先
2. 逻辑自洽
3. 伏笔回收

## 故事背景
{self.synopsis.synopsis}
"""

    def _generate_main_story(self) -> str:
        """生成主线故事（简化版）"""
        return f"""# 主线故事 - {self.synopsis.title}

{self.synopsis.synopsis}

主角：{self.synopsis.protagonist}
场景：{self.synopsis.location}
"""

    def _extract_characters(self, main_story: str) -> list:
        """
        提取角色列表

        从 struct.json 中读取所有 potential_roles，
        每个角色都可以作为主角游玩
        """
        import json
        import glob

        # 尝试查找 struct.json 文件
        # 支持拼音和中文两种目录名
        struct_path = None
        possible_patterns = [
            f"examples/*/{self.city}_struct.json",  # 中文文件名
            f"examples/{self.city}/*_struct.json",   # 中文目录名
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
                    # 将所有 potential_roles 转换为角色列表
                    # 第一个角色标记为主角
                    characters = []
                    for idx, role_name in enumerate(potential_roles):
                        characters.append({
                            "name": role_name,
                            "is_protagonist": (idx == 0),  # 第一个角色为默认主角
                            "description": f"{self.synopsis.title} - {role_name}视角"
                        })

                    print(f"   ℹ️  从 {struct_path} 读取到 {len(characters)} 个角色")
                    return characters

        # 如果没有找到 struct.json，使用默认单角色
        print(f"⚠️  警告: 未找到 {self.city} 的 struct.json，使用默认单角色配置")
        return [
            {
                "name": self.synopsis.protagonist,
                "is_protagonist": True,
                "description": f"{self.synopsis.title}的主角"
            }
        ]

    def _calculate_metadata(self, main_tree: Dict, all_trees: Dict) -> Dict[str, Any]:
        """计算元数据"""
        from .time_validator import TimeValidator

        validator = TimeValidator()
        report = validator.get_validation_report(main_tree)

        total_nodes = sum(len(tree) for tree in all_trees.values())

        return {
            "estimated_duration": report['estimated_duration_minutes'],
            "total_nodes": total_nodes,
            "max_depth": report['main_path_depth'],
            "cost": 0.0,  # TODO: 实际计算
            "total_tokens": 0,  # TODO: 实际统计
            "generation_time": 0,  # TODO: 实际计时
            "model": os.getenv("KIMI_MODEL_RESPONSE", "kimi-k2-0905-preview")
        }

    def _print_success_summary(self, metadata: Dict):
        """打印成功总结"""
        print("╔══════════════════════════════════════════════════════════════════╗")
        print("║              ✅ 故事生成完成！                                  ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print("\n")
        print(f"故事名称: {self.synopsis.title}")
        print(f"生成节点: {metadata['total_nodes']:,} 个")
        print(f"主线深度: {metadata['max_depth']} 层")
        print(f"预计游戏时长: {metadata['estimated_duration']} 分钟")
        print("\n")
        print("✅ 已保存到数据库")
        print("\n")
        print("按 Enter 返回主菜单，选择「选择故事」开始游玩...")
        input()

    def _load_character_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        加载角色级检查点

        Returns:
            检查点数据（如果存在）
        """
        import json
        from pathlib import Path

        checkpoint_path = f"checkpoints/{self.city}_characters.json"
        checkpoint_file = Path(checkpoint_path)

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载角色检查点失败：{e}")
            return None

    def _save_character_checkpoint(
        self,
        characters: list,
        dialogue_trees: Dict[str, Any],
        gdd_content: str,
        lore_content: str,
        main_story: str
    ):
        """
        保存角色级检查点

        Args:
            characters: 角色列表
            dialogue_trees: 已完成的对话树
            gdd_content: GDD 内容
            lore_content: Lore 内容
            main_story: 主线故事
        """
        import json
        from pathlib import Path
        from datetime import datetime

        checkpoint_path = f"checkpoints/{self.city}_characters.json"
        checkpoint_file = Path(checkpoint_path)
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        checkpoint = {
            "generated_at": datetime.now().isoformat(),
            "city": self.city,
            "synopsis": self.synopsis.__dict__,
            "characters": characters,
            "dialogue_trees": dialogue_trees,
            "gdd_content": gdd_content,
            "lore_content": lore_content,
            "main_story": main_story,
            "completed_count": len(dialogue_trees),
            "total_count": len(characters)
        }

        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)

        print(f"💾 [角色检查点] 已保存 {len(dialogue_trees)}/{len(characters)} 个角色 → {checkpoint_path}")

    def _cleanup_all_checkpoints(self, characters: list):
        """
        清理所有检查点文件

        Args:
            characters: 角色列表
        """
        import os
        from pathlib import Path

        deleted_count = 0

        # 删除角色级检查点
        char_checkpoint = Path(f"checkpoints/{self.city}_characters.json")
        if char_checkpoint.exists():
            os.remove(char_checkpoint)
            deleted_count += 1

        # 删除每个角色的对话树检查点
        for char in characters:
            tree_checkpoint = Path(f"checkpoints/{self.city}_{char['name']}_tree.json")
            if tree_checkpoint.exists():
                os.remove(tree_checkpoint)
                deleted_count += 1

        if deleted_count > 0:
            print(f"🗑️  已清理 {deleted_count} 个检查点文件")

