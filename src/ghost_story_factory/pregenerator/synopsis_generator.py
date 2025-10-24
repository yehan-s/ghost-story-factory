"""
故事简介生成器

根据城市名称，使用 LLM 生成多个故事简介供用户选择
"""

import os
import json
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class StorySynopsis:
    """故事简介数据类"""
    title: str
    synopsis: str
    protagonist: str
    location: str
    estimated_duration: int  # 预计时长（分钟）

    def __str__(self) -> str:
        return f"{self.title}\n{self.synopsis}"


class SynopsisGenerator:
    """故事简介生成器"""

    def __init__(self, city: str):
        """
        初始化生成器

        Args:
            city: 城市名称
        """
        self.city = city
        self.llm = None
        self._init_llm()

    def _init_llm(self):
        """初始化 LLM"""
        try:
            from crewai import LLM

            kimi_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
            kimi_base = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
            kimi_model = os.getenv("KIMI_MODEL_RESPONSE", "kimi-k2-0905-preview")

            if not kimi_key:
                print("⚠️  未找到 KIMI_API_KEY 环境变量")
                return

            self.llm = LLM(
                model=kimi_model,
                api_key=kimi_key,
                base_url=kimi_base,
                temperature=0.9  # 高创意度
            )

            print(f"✅ LLM 初始化完成：{kimi_model}")

        except ImportError:
            print("⚠️  CrewAI 未安装，无法生成简介")

    def generate_synopses(self, count: int = 3) -> List[StorySynopsis]:
        """
        生成多个故事简介

        Args:
            count: 生成简介数量

        Returns:
            故事简介列表
        """
        if not self.llm:
            print("⚠️  LLM 未初始化，返回默认简介")
            return self._get_default_synopses(count)

        print(f"🤖 正在为城市「{self.city}」生成 {count} 个故事简介...")

        try:
            # 构建 Prompt
            prompt = self._build_prompt(count)

            # 调用 LLM
            from crewai import Agent, Task, Crew

            agent = Agent(
                role="恐怖故事编剧",
                goal=f"为城市「{self.city}」创作引人入胜的恐怖灵异故事简介",
                backstory="你是一位擅长都市灵异题材的编剧，精通营造悬疑和恐怖氛围",
                llm=self.llm,
                verbose=False
            )

            task = Task(
                description=prompt,
                agent=agent,
                expected_output=f"JSON 格式的 {count} 个故事简介"
            )

            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            result = crew.kickoff()

            # 解析结果
            synopses = self._parse_result(str(result))

            if synopses:
                print(f"✅ 成功生成 {len(synopses)} 个故事简介")
                return synopses
            else:
                print("⚠️  解析简介失败，返回默认简介")
                return self._get_default_synopses(count)

        except Exception as e:
            print(f"⚠️  生成简介失败：{e}")
            return self._get_default_synopses(count)

    def _build_prompt(self, count: int) -> str:
        """构建生成 Prompt"""
        return f"""为城市「{self.city}」创作 {count} 个恐怖灵异故事的简介。

要求：
1. 每个故事简介 100-150 字
2. 必须包含：主角身份、核心任务、恐怖元素
3. 基于该城市的真实地标或传说
4. 风格：现代都市灵异
5. 每个故事的主角职业和场景必须不同
6. 预计游戏时长：15-25 分钟

参考案例（勿抄袭）：
- 钱江新城观景台诡异事件：你是一名特检院工程师，深夜被派往钱江新城观景台调查异常电磁信号。你发现避雷针系统出现了不明频率共振，而这可能与 15 年前的一起坠楼事件有关...

返回 JSON 格式：
```json
[
  {{
    "title": "故事标题",
    "synopsis": "故事简介（100-150字）",
    "protagonist": "主角身份（如：特检院工程师）",
    "location": "主要场景（如：钱江新城观景台）",
    "estimated_duration": 18
  }},
  ...
]
```

只返回 JSON，不要其他内容。"""

    def _parse_result(self, result: str) -> List[StorySynopsis]:
        """解析 LLM 返回的结果"""
        try:
            # 提取 JSON 部分
            import re

            # 查找 JSON 数组
            json_match = re.search(r'\[\s*\{.*?\}\s*\]', result, re.DOTALL)
            if not json_match:
                print("⚠️  未找到 JSON 数据")
                return []

            json_str = json_match.group(0)

            # 解析 JSON
            data = json.loads(json_str)

            # 转换为 StorySynopsis 对象
            synopses = []
            for item in data:
                synopsis = StorySynopsis(
                    title=item.get('title', '未命名故事'),
                    synopsis=item.get('synopsis', ''),
                    protagonist=item.get('protagonist', '未知'),
                    location=item.get('location', '未知'),
                    estimated_duration=item.get('estimated_duration', 18)
                )
                synopses.append(synopsis)

            return synopses

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON 解析失败：{e}")
            return []
        except Exception as e:
            print(f"⚠️  解析结果失败：{e}")
            return []

    def _get_default_synopses(self, count: int = 3) -> List[StorySynopsis]:
        """
        获取默认故事简介（当 LLM 不可用时）

        Args:
            count: 简介数量

        Returns:
            默认简介列表
        """
        default_synopses = [
            StorySynopsis(
                title=f"{self.city}夜行记",
                synopsis=f"深夜，{self.city}的街道笼罩在诡异的雾气中。作为一名夜班出租车司机，你接到了一个奇怪的订单，乘客要去一个不存在于地图上的地址...",
                protagonist="出租车司机",
                location=f"{self.city}街道",
                estimated_duration=18
            ),
            StorySynopsis(
                title=f"{self.city}地铁传说",
                synopsis=f"你是一名地铁维修工，凌晨三点被叫到{self.city}某条地铁线路进行紧急维修。然而你发现，这条线路在地图上根本不存在...",
                protagonist="地铁维修工",
                location=f"{self.city}地铁",
                estimated_duration=20
            ),
            StorySynopsis(
                title=f"{self.city}古宅探秘",
                synopsis=f"作为一名建筑修复专家，你接到委托前往{self.city}一栋废弃古宅进行勘察。房屋的主人在百年前神秘失踪，而墙壁上的符文似乎在警告什么...",
                protagonist="建筑修复专家",
                location=f"{self.city}古宅",
                estimated_duration=22
            ),
            StorySynopsis(
                title=f"{self.city}医院夜话",
                synopsis=f"你是{self.city}某医院的夜班护士，今晚负责照顾一位昏迷的病人。午夜时分，病房的监控设备显示出诡异的画面...",
                protagonist="夜班护士",
                location=f"{self.city}医院",
                estimated_duration=19
            ),
            StorySynopsis(
                title=f"{self.city}电台之声",
                synopsis=f"作为{self.city}一家深夜电台的主播，你每晚都会收到听众的来电。但今晚，一个声音告诉你，他知道你的秘密...",
                protagonist="电台主播",
                location=f"{self.city}电台",
                estimated_duration=21
            )
        ]

        return default_synopses[:count]

