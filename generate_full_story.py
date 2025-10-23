#!/usr/bin/env python3
"""
Ghost Story Factory - 完整故事生成器

按照范文定义的流程（阶段1→2→3→4）自动生成完整的灵异故事。
读取范文文件夹中的 .prompt.md 作为提示词，生成 .example.md 样式的正文。

使用方法：
    python generate_full_story.py --city 武汉 --output deliverables/程序-武汉/

流程：
    阶段1: lore-v1 (世界书1.0)
    阶段2: protagonist (角色分析) + lore-v2 (世界书2.0)
    阶段3: GDD (AI导演简报) + main-thread (主线故事)
    阶段4: (可选) choice-points (选择点设计)
"""

import argparse
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 范文目录
TEMPLATE_DIR = Path(__file__).parent / "范文"


class StoryGenerator:
    """完整故事生成器"""

    def __init__(self, city: str, output_dir: Optional[str] = None):
        self.city = city
        self.output_dir = Path(output_dir) if output_dir else Path(f"deliverables/程序-{city}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 构建LLM
        self.llm = self._build_llm()

        # 创建Agent
        self.researcher = self._create_researcher()
        self.analyst = self._create_analyst()
        self.writer = self._create_writer()

        # 存储生成的内容
        self.artifacts = {}

    def _build_llm(self) -> LLM:
        """构建LLM（优先Kimi，fallback到OpenAI）"""
        kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        if kimi_key:
            base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
            model = os.getenv("KIMI_MODEL", "kimi-k2-0905-preview")
            return LLM(
                model=model,
                api_key=kimi_key,
                api_base=base,
                custom_llm_provider="openai",
                max_tokens=16000,
            )

        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            base = os.getenv("OPENAI_BASE_URL")
            model = os.getenv("OPENAI_MODEL", "gpt-4o")
            return LLM(
                model=model,
                api_key=openai_key,
                base_url=base,
                max_tokens=16000,
            )

        raise RuntimeError("未检测到 KIMI_API_KEY 或 OPENAI_API_KEY")

    def _create_researcher(self) -> Agent:
        """创建研究员Agent"""
        from langchain_community.tools import GoogleSearchRun
        google_enabled = bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID"))

        return Agent(
            role='灵异故事调查员',
            goal=f'搜集关于{self.city}的灵异故事、都市传说和民间鬼故事',
            backstory='你是一位对中国都市传说了如指掌的专家，擅长从互联网和文献中提取高质量素材。',
            tools=[GoogleSearchRun()] if google_enabled else [],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _create_analyst(self) -> Agent:
        """创建分析师Agent"""
        return Agent(
            role='世界观与剧本设计师',
            goal='将原始素材转化为结构化的世界观、角色设定和剧情框架',
            backstory='你是专业的游戏设计师和剧本架构师，擅长构建自洽的世界观和引人入胜的剧情结构。',
            tools=[],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _create_writer(self) -> Agent:
        """创建写作Agent"""
        return Agent(
            role='恐怖故事作家',
            goal='将结构化框架扩写成引人入胜的长篇故事文案',
            backstory='你是B站百万粉丝的恐怖故事UP主，擅长营造氛围、塑造细节、讲述引人入胜的故事。',
            tools=[],
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
        )

    def _load_prompt(self, module_name: str) -> str:
        """加载范文中的prompt文件"""
        prompt_file = TEMPLATE_DIR / f"{module_name}.prompt.md"
        if not prompt_file.exists():
            raise FileNotFoundError(f"未找到提示词文件: {prompt_file}")
        return prompt_file.read_text(encoding='utf-8')

    def _save_artifact(self, name: str, content: str, format: str = "md"):
        """保存生成的产物"""
        filename = f"{self.city}_{name}.{format}"
        filepath = self.output_dir / filename
        filepath.write_text(content, encoding='utf-8')
        print(f"✅ 已保存: {filepath}")
        self.artifacts[name] = content

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """尝试从文本中解析JSON"""
        # 直接解析
        try:
            return json.loads(text)
        except:
            pass

        # 提取JSON块
        match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass

        # 提取裸JSON
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            blob = match.group(0)
            # 修正中文引号
            blob = blob.replace('"', '"').replace('"', '"')
            blob = blob.replace(''', "'").replace(''', "'")
            try:
                return json.loads(blob)
            except:
                pass

        return None

    # ==================== 阶段0: 收集原始素材 ====================

    def gather_raw_materials(self):
        """收集原始素材"""
        print("\n" + "="*60)
        print("阶段0: 收集原始素材")
        print("="*60)

        # 使用researcher搜集城市的灵异故事素材
        task = Task(
            description=f"""
收集关于城市【{self.city}】的灵异故事、都市传说的原始素材。

要求：
1. 搜集至少3-5个不同的传说或故事
2. 包含地点、事件、时间线等细节
3. 整合成一份完整的原始素材文档
4. Markdown格式输出

注：不需要结构化，只需要原始文本即可。
""",
            expected_output="关于城市的原始灵异故事素材（Markdown长文）",
            agent=self.researcher,
        )

        crew = Crew(
            agents=[self.researcher],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={"city": self.city}))
        self._save_artifact("raw_materials", result, "md")
        return result

    # ==================== 阶段1: Lore v1 (世界书1.0) ====================

    def generate_lore_v1(self, raw_materials: str):
        """生成世界书1.0（高保真地基）"""
        print("\n" + "="*60)
        print("阶段1: 生成世界书1.0（高保真地基）")
        print("="*60)

        prompt = self._load_prompt("lore-v1")

        task = Task(
            description=prompt,
            expected_output="Markdown格式的世界书1.0，包含事件、地点、实体、形而上学等章节",
            agent=self.analyst,
        )

        crew = Crew(
            agents=[self.analyst],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "city": self.city,
            "raw_text_from_agent_a": raw_materials
        }))
        self._save_artifact("lore_v1", result, "md")

        # 也保存JSON版本（如果能解析）
        json_data = self._try_parse_json(result)
        if json_data:
            self._save_artifact("lore_v1", json.dumps(json_data, ensure_ascii=False, indent=2), "json")

        return result

    # ==================== 阶段2: Protagonist + Lore v2 ====================

    def generate_protagonist(self, lore_v1: str):
        """生成角色分析"""
        print("\n" + "="*60)
        print("阶段2A: 生成角色分析")
        print("="*60)

        prompt = self._load_prompt("protagonist")

        task = Task(
            description=prompt,
            expected_output="角色分析报告，包含角色身份、访问权、动机、限制等",
            agent=self.analyst,
        )

        crew = Crew(
            agents=[self.analyst],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "city": self.city,
            "lore_v1": lore_v1
        }))

        self._save_artifact("protagonist", result, "md")

        json_data = self._try_parse_json(result)
        if json_data:
            self._save_artifact("protagonist", json.dumps(json_data, ensure_ascii=False, indent=2), "json")

        return result

    def generate_lore_v2(self, lore_v1: str):
        """生成世界书2.0（游戏化规则）"""
        print("\n" + "="*60)
        print("阶段2B: 生成世界书2.0（游戏化规则）")
        print("="*60)

        prompt = self._load_prompt("lore-v2")

        task = Task(
            description=prompt,
            expected_output="世界书2.0，包含共鸣度系统、实体等级、场域规则等",
            agent=self.analyst,
        )

        crew = Crew(
            agents=[self.analyst],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "city": self.city,
            "lore_v1": lore_v1
        }))

        self._save_artifact("lore_v2", result, "md")

        json_data = self._try_parse_json(result)
        if json_data:
            self._save_artifact("lore_v2", json.dumps(json_data, ensure_ascii=False, indent=2), "json")

        return result

    # ==================== 阶段3: GDD + Main Thread ====================

    def generate_gdd(self, protagonist: str, lore_v2: str):
        """生成AI导演任务简报"""
        print("\n" + "="*60)
        print("阶段3: 生成AI导演任务简报（GDD）")
        print("="*60)

        prompt = self._load_prompt("GDD")

        # 提取角色名
        role_match = re.search(r'角色.*?[:：]\s*(.+)', protagonist)
        role = role_match.group(1).strip() if role_match else "主角"

        task = Task(
            description=prompt,
            expected_output="AI导演任务简报，包含场景流程、触发条件、分支设计",
            agent=self.analyst,
        )

        crew = Crew(
            agents=[self.analyst],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "city": self.city,
            "role": role,
            "protagonist": protagonist,
            "lore_v2": lore_v2
        }))

        self._save_artifact("gdd", result, "md")

        json_data = self._try_parse_json(result)
        if json_data:
            self._save_artifact("gdd", json.dumps(json_data, ensure_ascii=False, indent=2), "json")

        return result

    def generate_main_thread(self, gdd: str, lore_v2: str):
        """生成主线故事"""
        print("\n" + "="*60)
        print("阶段3: 生成主线故事（完整文案）")
        print("="*60)

        prompt = self._load_prompt("main-thread")

        task = Task(
            description=prompt,
            expected_output="完整的主线故事，1500-3000字，Markdown格式，UP主风格",
            agent=self.writer,
        )

        crew = Crew(
            agents=[self.writer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        result = str(crew.kickoff(inputs={
            "city": self.city,
            "gdd": gdd,
            "lore_v2": lore_v2
        }))

        self._save_artifact("story", result, "md")

        return result

    # ==================== 主流程 ====================

    def generate_all(self):
        """执行完整的生成流程"""
        print(f"\n🎬 开始为【{self.city}】生成完整故事...")
        print(f"📁 输出目录: {self.output_dir}")

        # 阶段0: 收集原始素材
        raw_materials = self.gather_raw_materials()

        # 阶段1: Lore v1
        lore_v1 = self.generate_lore_v1(raw_materials)

        # 阶段2: Protagonist + Lore v2
        protagonist = self.generate_protagonist(lore_v1)
        lore_v2 = self.generate_lore_v2(lore_v1)

        # 阶段3: GDD + Main Thread
        gdd = self.generate_gdd(protagonist, lore_v2)
        story = self.generate_main_thread(gdd, lore_v2)

        # 生成README
        self._generate_readme()

        print("\n" + "="*60)
        print("✅ 完整故事生成完毕！")
        print("="*60)
        print(f"\n📁 所有文件已保存至: {self.output_dir}")
        print("\n生成的文件：")
        for artifact in self.artifacts.keys():
            print(f"  - {self.city}_{artifact}.*")
        print(f"  - README.md")

    def _generate_readme(self):
        """生成README说明文件"""
        readme = f"""# {self.city} - 灵异故事完整生成

本目录包含使用"Ghost Story Factory"自动生成的完整故事内容。

## 📁 文件说明

### 阶段1: 地基层
- `{self.city}_lore_v1.md` - 世界书1.0（高保真地基）
  - 包含：传说事件、地点描述、实体设定、形而上学规则

### 阶段2: 逻辑层
- `{self.city}_protagonist.md` - 角色分析
  - 包含：角色身份、访问权、动机、行为限制
- `{self.city}_lore_v2.md` - 世界书2.0（游戏化规则）
  - 包含：共鸣度系统、实体等级、场域规则、道具系统

### 阶段3: 故事层
- `{self.city}_gdd.md` - AI导演任务简报
  - 包含：场景流程、关键节点、分支设计
- `{self.city}_story.md` - 主线故事（完整文案）⭐
  - 1500-3000字的引人入胜的灵异故事

## 🎯 如何阅读

**如果您只想看故事：**
→ 直接阅读 `{self.city}_story.md`

**如果您想了解设计过程：**
1. 先看 `lore_v1.md`（传说素材）
2. 再看 `lore_v2.md`（游戏规则）
3. 最后看 `gdd.md`（剧情设计）

**如果您想二次创作：**
- 所有的 `.json` 文件都是结构化数据，可以用于游戏开发、互动小说等

## 📖 生成信息

- **城市：** {self.city}
- **生成工具：** Ghost Story Factory v3.1
- **架构版本：** 选项交互式
- **生成日期：** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

*本内容由AI自动生成，基于"范文"设计模式库的专业提示词。*
"""
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme, encoding='utf-8')
        print(f"✅ 已生成: {readme_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Ghost Story Factory - 完整故事生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    # 生成武汉的完整故事
    python generate_full_story.py --city 武汉

    # 指定输出目录
    python generate_full_story.py --city 广州 --output deliverables/程序-广州/
        """
    )

    parser.add_argument(
        "--city",
        type=str,
        required=True,
        help="目标城市名称"
    )

    parser.add_argument(
        "--output",
        type=str,
        help="输出目录（默认: deliverables/程序-<城市>/）"
    )

    args = parser.parse_args()

    # 生成故事
    generator = StoryGenerator(city=args.city, output_dir=args.output)
    generator.generate_all()


if __name__ == "__main__":
    main()

