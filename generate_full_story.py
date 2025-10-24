#!/usr/bin/env python3
"""
Ghost Story Factory - 完整故事生成器

按照templates定义的流程（阶段1→2→3→4）自动生成完整的灵异故事。
读取templates文件夹中的 .prompt.md 作为提示词，生成 .example.md 样式的正文。

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

# templates目录
TEMPLATE_DIR = Path(__file__).parent / "templates"


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
        """加载templates中的prompt文件"""
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

    # ==================== 阶段4: 支线故事 ====================

    def _extract_branch_roles(self, protagonist: str) -> list:
        """从角色分析中提取支线角色

        Args:
            protagonist: 角色分析文本

        Returns:
            支线角色列表，每个元素为 {"name": "角色名", "type": "支线类型"}
        """
        import re

        branch_roles = []

        # 查找"最终建议"部分推荐的主角
        main_role_match = re.search(r'(?:最终建议|最终推荐|主角线)[：:]\s*[*\*]*([^\n*]+)[*\*]*', protagonist, re.IGNORECASE)
        main_role = main_role_match.group(1).strip() if main_role_match else None

        print(f"📌 识别到主角: {main_role}")

        # 查找支线角色分类（如"惊悚体验支线"、"舆论/资料支线"等）
        # 模式：匹配类似 "- 夜班保安、登山女跑者 → **惊悚体验支线**" 的行
        # 也匹配 "- 值班经理 → **对抗阻力Boss**" 这种不以"支线"结尾的
        branch_lines = re.findall(
            r'[-–]\s*([^→\n]+?)\s*(?:→|->)\s*[*\*]*([^*\n]+?(?:支线|Boss|boss|线))[*\*]*',
            protagonist
        )

        for roles_part, branch_type in branch_lines:
            # 分割多个角色（可能用顿号、逗号分隔）
            role_names = re.split(r'[、,，]', roles_part.strip())
            for role_name in role_names:
                role_name = role_name.strip()
                if role_name and role_name != main_role:
                    branch_roles.append({
                        "name": role_name,
                        "type": branch_type.strip()
                    })

        # 如果没有找到明确的支线分类，则查找所有评估的角色
        if not branch_roles:
            print("⚠️ 未找到明确的支线分类，尝试从角色评估中提取...")
            # 匹配"### N. 角色名"形式的标题
            all_roles = re.findall(r'###\s*\d+\.\s*([^\n]+)', protagonist)
            for role in all_roles:
                role = role.strip()
                if role and role != main_role:
                    branch_roles.append({
                        "name": role,
                        "type": "支线"
                    })

        print(f"🌿 识别到 {len(branch_roles)} 个支线角色: {[r['name'] for r in branch_roles]}")
        return branch_roles

    def generate_branch(self, role_info: dict, role_index: int, lore_v2: str, main_gdd: str, protagonist: str):
        """生成支线故事

        Args:
            role_info: 角色信息 {"name": "角色名", "type": "支线类型"}
            role_index: 支线编号（从1开始）
            lore_v2: 世界书2.0
            main_gdd: 主线GDD（用于确保支线与主线关联）
            protagonist: 完整的角色分析文本
        """
        role_name = role_info["name"]
        branch_type = role_info["type"]

        print("\n" + "="*60)
        print(f"阶段4-{role_index}: 生成支线 - {role_name}（{branch_type}）")
        print("="*60)

        # 使用通用的支线生成提示词
        prompt = f"""
[SYSTEM]
你是一位"首席游戏系统设计师"（Lead Game Systems Designer）。
你的任务是为支线角色"{role_name}"设计一份详细的"AI导演任务简报（GDD）"。

[输入资料]
【世界书2.0】
{lore_v2}

【角色分析报告】
{protagonist}

【主线GDD（用于关联）】
{main_gdd}

[严格指令]
1. **[核心] 角色与目标：**
   * 基于【角色分析报告】中对"{role_name}"的评估，确定其核心目标和动机。
   * 严格限制其"访问权"（Agency）在角色分析报告中定义的范围内。

2. **[核心] 参考：**
   * 必须指定《世界书2.0》为"规则引擎"。
   * 必须参考角色分析报告中对该角色的"访问权"、"交集点"、"动机"评估。

3. **[核心] 游戏流程（Key Scenes & Flow）：**
   * 设计3-4个关键场景，聚焦于该角色在角色分析中被识别的"交集点"。
   * 场景必须符合角色的访问权限制。

4. **[核心] 主线关联（Mainline Association）：**
   * **必须**包含至少一个"主线关联"场景。
   * 让该角色通过某种方式（目击、听闻、间接感知）与主线事件产生联系。
   * 设计该关联的"余波"（Backlash）：主线事件如何影响到这条支线。

5. **[核心] 后果树：**
   * 基于该角色的动机类型（主动调查 vs 被动逃跑），设计2-3个分支结局。

6. **支线类型定位：** 本支线属于"{branch_type}"，确保设计符合这一定位。

[USER]
请基于以上输入，为"{role_name}"撰写一份完整的支线GDD。
"""

        task = Task(
            description=prompt,
            expected_output=f"支线{role_index}（{role_name}）的AI导演任务简报",
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
            "role_name": role_name,
            "branch_type": branch_type,
            "lore_v2": lore_v2,
            "main_gdd": main_gdd,
            "protagonist": protagonist
        }))

        # 保存时使用角色名而非编号
        safe_role_name = re.sub(r'[^\w\u4e00-\u9fff]+', '_', role_name)
        self._save_artifact(f"branch_{role_index}_{safe_role_name}_gdd", result, "md")

        json_data = self._try_parse_json(result)
        if json_data:
            self._save_artifact(f"branch_{role_index}_{safe_role_name}_gdd", json.dumps(json_data, ensure_ascii=False, indent=2), "json")

        # 生成支线故事文案
        return self.generate_branch_story(role_info, role_index, result, lore_v2)

    def generate_branch_story(self, role_info: dict, role_index: int, branch_gdd: str, lore_v2: str):
        """生成支线故事文案"""
        role_name = role_info["name"]
        branch_type = role_info["type"]

        print("\n" + "="*60)
        print(f"阶段4-{role_index}: 生成支线 {role_index} 故事文案 - {role_name}")
        print("="*60)

        prompt = f"""
你是一位恐怖故事作家。

基于以下内容，写一个引人入胜的支线故事：

【世界书2.0】
{lore_v2}

【支线{role_index} GDD - {role_name}】
{branch_gdd}

你的任务：
1. 将支线GDD扩写成完整的故事（1500-3000字）
2. 保持B站恐怖故事UP主的文风（第二人称、沉浸式、音效提示）
3. 确保故事与主线有联动点（如GDD中定义）
4. 包含完整的场景、异象、高潮和结局
5. Markdown格式输出

角色定位：{role_name}（{branch_type}）

请开始创作这个支线故事。
"""

        task = Task(
            description=prompt,
            expected_output=f"完整的支线{role_index}故事（{role_name}），1500-3000字",
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
            "role_name": role_name,
            "branch_type": branch_type,
            "branch_gdd": branch_gdd,
            "lore_v2": lore_v2,
            "role_index": role_index
        }))

        safe_role_name = re.sub(r'[^\w\u4e00-\u9fff]+', '_', role_name)
        self._save_artifact(f"branch_{role_index}_{safe_role_name}_story", result, "md")

        return result

    # ==================== 主流程 ====================

    def generate_all(self, include_branches: bool = True):
        """执行完整的生成流程

        Args:
            include_branches: 是否生成支线故事（默认True）
        """
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

        # 阶段4: 支线故事（可选）
        branch_roles = []
        if include_branches:
            print("\n" + "="*60)
            print("🌿 开始生成支线故事...")
            print("="*60)

            try:
                # 从角色分析中提取支线角色
                branch_roles = self._extract_branch_roles(protagonist)

                if not branch_roles:
                    print("⚠️ 未识别到支线角色，跳过支线生成")
                else:
                    print(f"📋 将生成 {len(branch_roles)} 条支线故事")

                    # 为每个支线角色生成故事
                    for idx, role_info in enumerate(branch_roles, start=1):
                        try:
                            self.generate_branch(role_info, idx, lore_v2, gdd, protagonist)
                        except Exception as e:
                            print(f"\n⚠️ 支线{idx}（{role_info['name']}）生成失败: {e}")
                            continue

                    print("\n✅ 支线故事生成完成！")
            except Exception as e:
                print(f"\n⚠️ 支线生成出错（已跳过）: {e}")

        # 生成README
        self._generate_readme(include_branches, branch_roles)

        print("\n" + "="*60)
        print("✅ 完整故事生成完毕！")
        print("="*60)
        print(f"\n📁 所有文件已保存至: {self.output_dir}")
        print("\n生成的文件：")
        for artifact in self.artifacts.keys():
            print(f"  - {self.city}_{artifact}.*")
        print(f"  - README.md")

    def _generate_readme(self, include_branches: bool = True, branch_roles: list = None):
        """生成README说明文件

        Args:
            include_branches: 是否包含支线
            branch_roles: 支线角色列表
        """

        branch_section = ""
        branch_reading_guide = ""
        if include_branches and branch_roles:
            branch_lines = []
            branch_names = []
            for idx, role_info in enumerate(branch_roles, start=1):
                role_name = role_info['name']
                branch_type = role_info['type']
                safe_role_name = re.sub(r'[^\w\u4e00-\u9fff]+', '_', role_name)
                branch_lines.append(f"- `{self.city}_branch_{idx}_{safe_role_name}_gdd.md` - 支线{idx} AI导演任务简报（{role_name}）")
                branch_lines.append(f"  - 包含：{role_name}视角的场景流程、与主线的联动点（{branch_type}）")
                branch_lines.append(f"- `{self.city}_branch_{idx}_{safe_role_name}_story.md` - 支线{idx}故事文案 🌿")
                branch_lines.append(f"  - 从{role_name}的视角体验灵异事件")
                branch_names.append(f"`{self.city}_branch_{idx}_{safe_role_name}_story.md`")

            branch_section = f"\n### 阶段4: 支线故事\n" + "\n".join(branch_lines) + "\n"
            branch_reading_guide = f"\n→ 或阅读支线: " + " / ".join(branch_names)
        elif include_branches:
            branch_section = f"""
### 阶段4: 支线故事
*（本次生成未识别到支线角色）*
"""

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
- `{self.city}_gdd.md` - AI导演任务简报（主线）
  - 包含：场景流程、关键节点、分支设计
- `{self.city}_story.md` - 主线故事（完整文案）⭐
  - 1500-3000字的引人入胜的灵异故事
{branch_section}
## 🎯 如何阅读

**如果您只想看故事：**
→ 直接阅读 `{self.city}_story.md`（主线）{branch_reading_guide}

**如果您想了解设计过程：**
1. 先看 `lore_v1.md`（传说素材）
2. 再看 `lore_v2.md`（游戏规则）
3. 然后看 `gdd.md`（主线剧情设计）
4. 最后看支线的 `branch_*_gdd.md`（支线设计）

**如果您想二次创作：**
- 所有的 `.json` 文件都是结构化数据，可以用于游戏开发、互动小说等

## 📖 生成信息

- **城市：** {self.city}
- **生成工具：** Ghost Story Factory v3.1
- **架构版本：** 选项交互式
- **生成日期：** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

*本内容由AI自动生成，基于"templates"设计模式库的专业提示词。*
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
    # 生成武汉的完整故事（包含支线）
    python generate_full_story.py --city 武汉

    # 只生成主线，不生成支线
    python generate_full_story.py --city 武汉 --no-branches

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

    parser.add_argument(
        "--no-branches",
        action="store_true",
        help="不生成支线故事（默认会生成支线1和支线2）"
    )

    args = parser.parse_args()

    # 生成故事
    generator = StoryGenerator(city=args.city, output_dir=args.output)
    generator.generate_all(include_branches=not args.no_branches)


if __name__ == "__main__":
    main()

