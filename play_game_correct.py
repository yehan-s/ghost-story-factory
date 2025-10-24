#!/usr/bin/env python3
"""Ghost Story Factory - 北高峰·空厢夜行（真实剧情版）"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ghost_story_factory.engine import (
    GameState,
    Choice,
    ChoiceType,
    IntentMappingEngine,
    EndingSystem,
)
from ghost_story_factory.ui import GameCLI

# 初始化
cli = GameCLI(use_rich=True)
intent_engine = IntentMappingEngine()
ending_system = EndingSystem()

# 显示欢迎
cli.display_title("杭州·北高峰", "特检院工程师 - 顾栖迟")

print("""
╔══════════════════════════════════════════════════════════════════╗
║           北高峰·空厢夜行 | Ghost Story Factory              ║
║                                                                  ║
║  📋 身份：浙江省特检院 索道与游乐设施事业部 一级检验师         ║
║  🎯 任务：完成停运索道安全复核，夜间空载运行试验               ║
║  ⚠️  规则：雨停 + 东风 + 0:00-4:00 = "空厢夜行"开始            ║
║                                                                  ║
║  💡 提示：这是基于真实都市传说改编的互动恐怖游戏               ║
║  🎮 操作：输入选项编号 | /save 保存 | /quit 退出               ║
╚══════════════════════════════════════════════════════════════════╝
""")

input("\n按 Enter 开始你的检验任务...\n")

# 初始化游戏状态
state = GameState(
    PR=5,  # 职业理性 Buff +5
    GR=0,
    WF=0,
    current_scene="S0",
    timestamp="23:50",
    inventory=["频谱仪", "高速红外相机", "公务平板", "共振锤"],
    flags={"特检院证件": True}
)

# 游戏场景数据
scenes = {
    "S0": {
        "title": "【S0】23:50 | 灵隐支路尽头 - 你的车",
        "narrative": """
你把车停在灵隐支路尽头，关掉发动机，世界像被拔掉了电源。

雨刚停，树叶还在滴水，一滴，两滴，落在车顶——频率恰好 **1.6 秒**。

你愣了半秒，职业本能抬手看表：**23:50**。

还有10分钟，"空厢夜行"就要开始了。

你是顾栖迟，浙江省特检院的索道检验师。
今晚的任务：**北高峰停运索道安全复核** - 夜间空载运行试验。

后备箱里整齐摆放着：
- 📊 **频谱仪** - 捕获异常声波
- 📷 **高速红外相机** - 记录夜间影像
- 💻 **公务平板** - 实时记录数据
- 🔨 **共振锤** - 测试避雷针锚点

你看了眼前方：
山路尽头是观景台入口，铁门虚掩。
夜风带着雨后的土腥味，还有...电视塔的臭氧味。

像一根冰做的镊子，钻进鼻腔。
""",
        "choices": [
            {
                "choice_id": "S0_C1",
                "choice_text": "📱 先检查工作群，看看有没有其他同事也在附近",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["谨慎", "社交"],
                "consequences": {"PR": "+2", "flags": {"检查工作群": True}},
                "next_scene": "S0_CHECK_PHONE"
            },
            {
                "choice_id": "S0_C2",
                "choice_text": "🎒 拿起设备，直接前往观景台开始任务",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["专业", "效率"],
                "consequences": {"PR": "+3", "timestamp": "00:00"},
                "next_scene": "S1"
            },
            {
                "choice_id": "S0_C3",
                "choice_text": "🚬 抽根烟冷静一下，回想一下工作流程",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["准备"],
                "consequences": {"PR": "+1", "flags": {"回想流程": True}},
                "next_scene": "S0_REVIEW"
            }
        ]
    },

    "S0_CHECK_PHONE": {
        "title": "【S0.1】23:52 | 工作群消息",
        "narrative": """
你打开手机，工作群"索道检验三组"里很安静。

最后一条消息是下午5点，组长老刘发的：
> "小顾，北高峰那单你独自复核没问题吧？空载试验记得录全程视频。"

你回复了个"👌"。

没人回。

你往上翻，看到一周前的讨论：

**老刘**（15:30）：
> "北高峰索道那边...有点邪门。之前去的小王说夜里听到怪声。"

**小王**（15:32）：
> "我就是觉得那钢索声音不对劲，像...像有人在敲。"
> "1.6秒一次，特别规律。"
> "但监控什么都拍不到。"

**老刘**（15:35）：
> "别瞎说，吓到新来的。顾工是专业的，没问题。"

聊天记录到此为止。

你关掉手机，雨后的夜空特别静。

只有树叶滴水的声音。

*滴答...滴答...滴答...*

**1.6秒。**
""",
        "choices": [
            {
                "choice_id": "S0_1_C1",
                "choice_text": "📱 给老刘打电话确认一下",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["谨慎"],
                "consequences": {"PR": "+2", "flags": {"联系老刘": True}},
                "next_scene": "S0_CALL_LIU"
            },
            {
                "choice_id": "S0_1_C2",
                "choice_text": "🎒 不用管这些，专心做检验",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["专业"],
                "consequences": {"PR": "+5", "timestamp": "00:00"},
                "next_scene": "S1"
            }
        ]
    },

    "S0_CALL_LIU": {
        "title": "【S0.2】23:55 | 未接通",
        "narrative": """
你拨通老刘的电话。

*嘟——嘟——嘟——*

没人接。

又试了一遍。

还是没人接。

奇怪，老刘这个时间应该还没睡...

手机屏幕突然闪了一下，显示"信号微弱"。

你看了看信号格：只有一格。

这里信号一向不好。

不管了，按流程来就行。

你是工程师，不是都市传说调查员。

**00:00 AM**

手表震动了一下。

零点整。

"空厢夜行"开始了。
""",
        "choices": [
            {
                "choice_id": "S0_2_C1",
                "choice_text": "🎒 开始任务",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["专业"],
                "consequences": {"timestamp": "00:00"},
                "next_scene": "S1"
            }
        ]
    },

    "S0_REVIEW": {
        "title": "【S0.3】23:55 | 工作流程回顾",
        "narrative": """
你点燃一支烟，靠在车门上，回想今晚的任务流程：

**【停运索道安全复核 - 夜间空载运行试验】**

1. **S1 观景台** - 钢索声波检测
   - 使用频谱仪捕获运行频率
   - 高速相机记录索道运行状态
   - 生成【校准日志】

2. **S2 值班室** - 监控系统检查
   - 调阅历史监控记录
   - 核对运行日志
   - 出具监控评估报告

3. **S3 避雷针锚点** - 结构安全测试
   - 共振锤测试拉线张力
   - 记录0.8Hz共振数据
   - 评估电气安全

4. **完成报告** - 0400前提交

流程很清楚，没什么问题。

但你总觉得...有什么不对劲。

是雨后的空气太安静？
还是那个1.6秒的滴水声？

你掐灭烟头。

**00:00 AM**

开始工作。
""",
        "choices": [
            {
                "choice_id": "S0_3_C1",
                "choice_text": "🎒 前往观景台",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["专业"],
                "consequences": {"timestamp": "00:00"},
                "next_scene": "S1"
            }
        ]
    },

    "S1": {
        "title": "【S1】00:00 | 观景台 - 雨夜校准",
        "narrative": """
**00:00 AM - 北高峰观景台**

你推开虚掩的铁门。

观景台只有一盏25W白炽灯，灯罩破了个洞，光像坏掉的蛋黄。

钢索在黑暗里绷成一条笔直的刀口。
没有车厢，索道已经停运三个月了。

但你听到——

*"眶——眶——"*

像有人在敲击空心的铁桶。

**每1.6秒一次。**

你打开频谱仪，屏幕上立刻跳出一条竖线：

**65 Hz**

像心电图里突然冒出的早搏。

你架好高速红外相机，镜头对准索道。

录制开始。

画面里什么都没有，只有雨后的雾气被声浪推得一起一伏。

可耳机里却出现第二条竖线——

**130 Hz**

倍频。

像有人在钢索背面再敲一下。

这不科学。

停运的索道不应该有任何声音。
""",
        "choices": [
            {
                "choice_id": "S1_C1",
                "choice_text": "📊 继续记录，收集完整数据（职业流程）",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["专业", "数据"],
                "consequences": {"PR": "+10", "flags": {"校准日志_已生成": True}, "inventory": ["校准日志"]},
                "next_scene": "S1_RECORD"
            },
            {
                "choice_id": "S1_C2",
                "choice_text": "🔦 用手电筒照向钢索，看看有什么",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["调查", "主动"],
                "consequences": {"PR": "+8", "flags": {"用手电筒": True}},
                "next_scene": "S1_FLASHLIGHT"
            },
            {
                "choice_id": "S1_C3",
                "choice_text": "📱 立即上报异常，请求支援",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["谨慎", "求助"],
                "consequences": {"PR": "+3", "flags": {"尝试上报": True}},
                "next_scene": "S1_REPORT"
            },
            {
                "choice_id": "S1_C4",
                "choice_text": "🎧 戴上耳机仔细听，分析声音特征",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["专业", "分析"],
                "consequences": {"PR": "+12", "flags": {"深度分析": True}},
                "next_scene": "S1_LISTEN"
            }
        ]
    },

    "S1_RECORD": {
        "title": "【S1.1】00:05 | 数据记录",
        "narrative": """
你深吸一口气，切换到专业模式。

**记录时长：3分钟**

频谱仪数据：
- 基频：65 Hz ±0.3
- 倍频：130 Hz ±0.5
- 间隔：1.6 秒 ±0.02
- 波形：方波（非正弦，异常）

高速相机：
- 帧率：240 fps
- 红外模式：ON
- 拍摄时长：3min 12s

就在快门按下的瞬间——

取景框里闪过一帧高亮。

像有人从内部掀开黑布，又立刻合上。

你立刻回放。

**第3帧，00:00:18**

画面中间，若隐若现的...轮廓。

像一节车厢。

但钢索上什么都没有。

**系统提示**：
✅ 获得道具【校准日志】
✅ PR +10 → 当前 {PR}
✅ 可以前往 S2 值班室

你收好设备。

*眶——眶——*

声音还在继续。

但你已经有足够的数据了。
""",
        "choices": [
            {
                "choice_id": "S1_1_C1",
                "choice_text": "🚶 前往值班室调阅监控",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["推进"],
                "consequences": {"timestamp": "00:30"},
                "next_scene": "S2"
            },
            {
                "choice_id": "S1_1_C2",
                "choice_text": "🔍 留在观景台继续观察",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["谨慎"],
                "consequences": {"PR": "+5"},
                "next_scene": "S1_STAY"
            }
        ]
    },

    "S1_FLASHLIGHT": {
        "title": "【S1.2】00:03 | 手电筒照射",
        "narrative": """
你打开强光手电，照向钢索。

光束穿过雾气，在钢索上留下一道刺眼的白线。

*眶——眶——*

声音没有停。

你把光束慢慢移动，沿着钢索向上...

**突然——**

光束打在了什么东西上。

一个轮廓。

悬在半空。

像是...第三节车厢？

但它不应该在那里。

索道已经停运，所有车厢都停在下站维修。

你眨了眨眼。

光束重新扫过去——

**什么都没有。**

只有雾气和钢索。

你的手在颤抖。

频谱仪显示：65 Hz 突然跳到 **195 Hz**。

三倍频。

手电开始闪烁...

'滋——滋——'

然后灭了。

一片黑暗。
""",
        "choices": [
            {
                "choice_id": "S1_2_C1",
                "choice_text": "🏃 立刻离开观景台",
                "choice_type": ChoiceType.CRITICAL,
                "tags": ["逃跑"],
                "consequences": {"PR": "+5", "WF": "+1", "timestamp": "00:10"},
                "next_scene": "S1_ESCAPE"
            },
            {
                "choice_id": "S1_2_C2",
                "choice_text": "🔧 尝试修理手电筒",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冷静"],
                "consequences": {"PR": "+15", "flags": {"修理成功": True}},
                "next_scene": "S1_FIX_LIGHT"
            },
            {
                "choice_id": "S1_2_C3",
                "choice_text": "📊 用频谱仪记录这个异常",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["专业", "冷静"],
                "consequences": {"PR": "+20", "flags": {"记录195Hz": True}},
                "next_scene": "S1_RECORD_ANOMALY"
            }
        ]
    },

    "S2": {
        "title": "【S2】{timestamp} | 值班室 - 监控悖论",
        "narrative": """
**{timestamp} - 索道站值班室**

值班室亮得过分。

六台监控屏排成一排，绿灰色反色，像六口井。

值班经理姓陆，秃顶，手里转着一串钥匙。

**哗啦...哗啦...哗啦...**

节拍——**1.6秒**。

你出示工作证和【校准日志】。

他扫了一眼，目光停在"65 Hz"上。

钥匙声骤停。

"顾工，"他咧嘴笑，但眼角抽了一下，"大半夜一个人？"

"复核任务，夜间空载试验。"你说。

"雨夜的数据，"他压低声音，"最好别往上报。"

你沉默。

他递过来一支烟。

"我需要调阅09通道的监控录像，"你说，"索道下站，00:00-00:30时段。"

他犹豫了几秒。

"可以，"他起身，"但别看太久。容易...眼花。"

他输入密码，屏幕解锁。

**09通道 - 索道下站 - 00:00:00**

画面静止。

时间戳在走，但画面一动不动。

钢索反光却在一帧里突然增亮。

你按下录屏。

进度条每1.6秒卡一次，像被看不见的指甲掐住。

**第3帧，00:00:18**

屏幕右下角——

一个背影。

橘色反光背心，拖把垂在地上，却不见水滴。

**【实体：不存在的清洁工·T1】**

陆经理在你身后咳嗽。

"顾工，别看太久。"

你回头，他正盯着你的屏幕。

但他的瞳孔里...看不见那抹橘色。
""",
        "choices": [
            {
                "choice_id": "S2_C1",
                "choice_text": "📸 截图保存证据",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["证据", "专业"],
                "preconditions": {"flags.校准日志_已生成": True},
                "consequences": {"PR": "+10", "flags": {"1帧证据": True}, "inventory": ["监控截图"]},
                "next_scene": "S2_SCREENSHOT"
            },
            {
                "choice_id": "S2_C2",
                "choice_text": "💾 用U盘拷贝完整监控",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冒险", "全面"],
                "consequences": {"PR": "+5", "flags": {"陆经理_驱逐": True}},
                "next_scene": "S2_COPY"
            },
            {
                "choice_id": "S2_C3",
                "choice_text": "❓ '陆经理，你看到了吗？那个背影'",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["试探"],
                "consequences": {"PR": "+3", "flags": {"陆经理_知情": True}},
                "next_scene": "S2_ASK"
            },
            {
                "choice_id": "S2_C4",
                "choice_text": "🚪 假装什么都没看到，离开",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["保守"],
                "consequences": {"PR": "+2"},
                "next_scene": "S2_LEAVE"
            }
        ]
    },

    "GAME_OVER_INCOMPLETE": {
        "title": "【结局】未完成的检验",
        "narrative": """
**04:00 AM**

你提交了一份"正常"的检验报告。

所有异常数据都被你标记为"设备故障"。

65 Hz？ 雨水滴落。
130 Hz？ 电磁干扰。
监控背影？ 反光异常。

报告通过审核。

索道照常运营。

但每个雨夜，你都会梦到那个1.6秒的节拍。

*眶——眶——眶——*

你知道，有些真相，你选择了无视。

---

**【结局：专业逃避】**

- 你完成了工作，但没有揭开真相
- PR: {PR}/100
- 职业生涯：安全但平庸
- 第三节车厢：依然在运行

**"有些检验，不合格才是正确答案。"**
""",
        "is_ending": True
    }
}

# 主游戏循环
current_scene = "S0"
game_running = True

while game_running:
    # 检查结局
    ending = ending_system.check_ending(state)
    if ending:
        print("\n" + "="*70)
        print("🏆 游戏结束")
        print("="*70 + "\n")
        cli.display_narrative(f"达成结局: {ending.value}\n\n（完整结局叙事需要完整的故事内容）")
        break

    # 获取当前场景
    scene = scenes.get(current_scene)
    if not scene:
        print(f"\n❌ 场景 {current_scene} 未实现（演示版仅包含部分场景）")
        print("💡 提示：完整游戏需要基于 GDD 和 Lore 内容生成")
        break

    # 显示场景
    print("\n" + "="*70)
    print(scene["title"].format(timestamp=state.timestamp))
    print("="*70 + "\n")

    cli.display_state(state)

    # 显示叙事
    narrative = scene["narrative"].format(
        timestamp=state.timestamp,
        PR=state.PR
    )
    cli.display_narrative(narrative)

    # 检查是否是结局场景
    if scene.get("is_ending"):
        narrative_ending = scene["narrative"].format(PR=state.PR)
        cli.display_narrative(narrative_ending)
        print("\n" + "="*70)
        print("✨ 感谢游玩！")
        print("="*70)
        break

    # 创建选择点
    choices = []
    for choice_data in scene["choices"]:
        choice = Choice(
            choice_id=choice_data["choice_id"],
            choice_text=choice_data["choice_text"],
            choice_type=choice_data["choice_type"],
            tags=choice_data.get("tags", []),
            preconditions=choice_data.get("preconditions"),
            consequences=choice_data.get("consequences", {})
        )
        choices.append(choice)

    # 显示选择并获取玩家输入
    while True:
        cli.display_choices(choices, state)

        user_input = input("\n👉 请输入选项编号（或 /save, /quit）: ").strip()

        # 处理命令
        if user_input == "/quit":
            print("\n👋 退出游戏")
            game_running = False
            break
        elif user_input == "/save":
            save_name = input("请输入存档名: ").strip() or "quicksave"
            state.save(f"saves/{save_name}.save")
            print(f"✅ 已保存")
            continue

        # 验证输入
        try:
            choice_num = int(user_input)
            if 1 <= choice_num <= len(choices):
                selected = choices[choice_num - 1]

                # 验证选择
                validation = intent_engine.validate_choice(selected, state)
                if validation.is_valid:
                    # 应用后果
                    state.update(selected.consequences)
                    state.consequence_tree.append(selected.choice_id)

                    # 跳转下一场景
                    next_scene = scene["choices"][choice_num - 1].get("next_scene")
                    if next_scene:
                        current_scene = next_scene
                    break
                else:
                    print(f"\n❌ {validation.reason}\n")
            else:
                print("\n❌ 无效选项\n")
        except ValueError:
            print("\n❌ 请输入数字\n")

print("""
╔══════════════════════════════════════════════════════════════════╗
║                       感谢游玩！                                 ║
║                                                                  ║
║  🎮 北高峰·空厢夜行 | Ghost Story Factory                     ║
║  💡 这是基于真实剧情的演示版                                    ║
║  📖 主角：顾栖迟 - 特检院工程师                                 ║
║  🎯 核心：索道检验 + 65Hz异常 + 第三节车厢                      ║
║                                                                  ║
║  ✨ 完整版本需要加载 GDD 和 Lore 内容动态生成                   ║
╚══════════════════════════════════════════════════════════════════╝
""")

