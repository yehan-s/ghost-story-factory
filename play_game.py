#!/usr/bin/env python3
"""Ghost Story Factory - 交互式游戏（真正可玩！）"""

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
cli.display_title("杭州", "保安 - 阿明")

print("""
╔══════════════════════════════════════════════════════════════════╗
║  欢迎来到 Ghost Story Factory - 杭州·灵异故事                  ║
║                                                                  ║
║  ⚠️  警告：这是一个恐怖游戏                                     ║
║  💡 提示：请在安静的环境中游玩以获得最佳体验                    ║
║  🎮 操作：输入选项编号进行选择                                  ║
║  💾 命令：输入 /save 保存，/load 加载，/quit 退出               ║
╚══════════════════════════════════════════════════════════════════╝
""")

input("\n按 Enter 开始游戏...\n")

# 初始化游戏状态
state = GameState(
    PR=5,
    GR=0,
    WF=0,
    current_scene="S1",
    timestamp="00:00",
    inventory=["手电筒", "对讲机"],
    flags={}
)

# 游戏场景数据
scenes = {
    "S1": {
        "title": "【场景 1】交接班 - 中控室",
        "narrative": """
**00:00 AM - 中控室**

张叔递给你一串钥匙和一本发黄的保安手册。

"阿明，今晚的夜班就交给你了。"他欲言又止地看着你，
"记住...五楼那边，别待太久。"

你想问为什么，但张叔已经背起包，匆匆离开了。

中控室只剩下你一个人。
墙上的九宫格监控屏幕闪烁着惨白的光。
荧光灯发出'嗡——'的电流声。

你需要决定接下来做什么...
""",
        "choices": [
            {
                "choice_id": "S1_C1",
                "choice_text": "📖 翻看保安手册，看看有什么注意事项",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["调查", "谨慎"],
                "consequences": {"PR": "+5", "flags": {"手册_已阅读": True}},
                "next_scene": "S1_READ_MANUAL"
            },
            {
                "choice_id": "S1_C2",
                "choice_text": "📺 检查监控屏幕，查看各楼层情况",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["调查", "主动"],
                "consequences": {"PR": "+3", "flags": {"监控_已检查": True}},
                "next_scene": "S1_CHECK_MONITOR"
            },
            {
                "choice_id": "S1_C3",
                "choice_text": "🚶 直接开始巡逻，先去五楼看看",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冒险", "主动"],
                "consequences": {"PR": "+10", "timestamp": "01:30"},
                "next_scene": "S2"
            }
        ]
    },

    "S1_READ_MANUAL": {
        "title": "【场景 1.1】阅读手册",
        "narrative": """
你拿起那本发黄的保安手册。
纸张很旧，边缘已经磨损。

**【夜班保安守则】**

1. 每小时巡逻一次，按顺序：一楼 → 二楼 → 三楼 → 四楼
2. **五楼暂时关闭，请勿进入**
3. 如遇异常情况，立即联系主管
4. 04:00 前完成所有巡逻

第2条被人用红笔重重地画了三道线。

你注意到手册的最后一页，有人用潦草的字迹写着：

*"别去五楼。*
*别在04:44时出现在五楼。*
*如果听到拍皮球的声音，不要回应。"*

你的后颈有点发凉...
""",
        "choices": [
            {
                "choice_id": "S1_1_C1",
                "choice_text": "📺 继续检查监控屏幕",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["谨慎"],
                "consequences": {"flags": {"监控_已检查": True}},
                "next_scene": "S1_CHECK_MONITOR"
            },
            {
                "choice_id": "S1_1_C2",
                "choice_text": "🚶 开始巡逻，去五楼看看",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冒险"],
                "consequences": {"PR": "+5", "timestamp": "01:30"},
                "next_scene": "S2"
            }
        ]
    },

    "S1_CHECK_MONITOR": {
        "title": "【场景 1.2】检查监控",
        "narrative": """
你盯着九宫格监控屏幕。

一楼：大厅空荡荡，自动门紧闭。
二楼：货架整齐，没有异常。
三楼：餐饮区关灯，只有安全指示灯。
四楼：电影院区域漆黑一片。

**五楼：画面一片雪花。**

你试着切换频道，但五楼的监控始终无法显示。
屏幕上只有白色的噪点和刺耳的'滋——滋——'声。

你感到一阵不安...
""",
        "choices": [
            {
                "choice_id": "S1_2_C1",
                "choice_text": "🔧 尝试修理五楼的监控",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["调查"],
                "consequences": {"PR": "+5", "flags": {"监控修理_失败": True}},
                "next_scene": "S1_FIX_MONITOR"
            },
            {
                "choice_id": "S1_2_C2",
                "choice_text": "🚶 直接去五楼看看",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冒险"],
                "consequences": {"PR": "+8", "timestamp": "01:30"},
                "next_scene": "S2"
            }
        ]
    },

    "S1_FIX_MONITOR": {
        "title": "【场景 1.3】修理监控",
        "narrative": """
你拿起对讲机上的工具包，试着调整五楼监控的接线。

但无论你怎么调试，画面依然是雪花。

就在你准备放弃时——

画面突然清晰了一瞬间。

你看到五楼的走廊里...
站着一个小女孩。
她背对着摄像头，
一动不动。

然后画面又变成雪花。

你的手在颤抖...
""",
        "choices": [
            {
                "choice_id": "S1_3_C1",
                "choice_text": "🚶 立刻去五楼查看",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冒险", "紧急"],
                "consequences": {"PR": "+15", "timestamp": "01:30", "flags": {"看到_小女孩": True}},
                "next_scene": "S2"
            },
            {
                "choice_id": "S1_3_C2",
                "choice_text": "📞 先联系主管确认",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["谨慎"],
                "consequences": {"PR": "+3", "flags": {"主管_未接通": True}},
                "next_scene": "S1_CALL_MANAGER"
            }
        ]
    },

    "S1_CALL_MANAGER": {
        "title": "【场景 1.4】联系主管",
        "narrative": """
你拿起电话拨通主管的号码。

'嘟——嘟——嘟——'

没人接。

你又试了一遍。

还是没人接。

你看了看时间：00:20 AM

这个时间点，主管应该还没睡...
为什么不接电话？

你只能自己决定了。
""",
        "choices": [
            {
                "choice_id": "S1_4_C1",
                "choice_text": "🚶 去五楼查看情况",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["果断"],
                "consequences": {"PR": "+10", "timestamp": "01:30"},
                "next_scene": "S2"
            },
            {
                "choice_id": "S1_4_C2",
                "choice_text": "🪑 待在中控室，继续观察",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["保守"],
                "consequences": {"PR": "+2", "timestamp": "01:00", "flags": {"待在中控室": True}},
                "next_scene": "S1_STAY"
            }
        ]
    },

    "S1_STAY": {
        "title": "【场景 1.5】待在中控室",
        "narrative": """
你决定先待在中控室观察。

时间一分一秒过去。

01:00 AM...

你盯着监控屏幕。
五楼的画面依然是雪花。

突然——

对讲机里传来一阵杂音：

*"滋——...救...我...滋滋——...五楼...滋——"*

是个女孩的声音！

然后就断了。

你必须做出决定。
""",
        "choices": [
            {
                "choice_id": "S1_5_C1",
                "choice_text": "🚶 立刻冲去五楼",
                "choice_type": ChoiceType.CRITICAL,
                "tags": ["救援", "紧急"],
                "consequences": {"PR": "+20", "timestamp": "01:30", "flags": {"听到求救": True}},
                "next_scene": "S2"
            }
        ]
    },

    "S2": {
        "title": "【场景 2】第一次巡逻 - 五楼中庭",
        "narrative": """
**{timestamp} - 五楼中庭**

你推开通往五楼的防火门。

一股土腥味扑面而来，混杂着潮湿的霉味。

荧光灯闪烁着，发出'嗡——'的电流声。
五楼很安静，安静得让你不安。

走廊两边是关闭的店铺。
地面上有一层薄薄的灰尘。

然后，你听到了...

*'啪嗒...啪嗒...啪嗒...'*

拍皮球的声音。

从走廊深处传来。

但这栋楼里，除了你，不应该有其他人。
""",
        "choices": [
            {
                "choice_id": "S2_C1",
                "choice_text": "🚶 走过去检查声音来源",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["调查", "冒险"],
                "consequences": {"PR": "+15", "flags": {"皮球_已接触": True}},
                "next_scene": "S2_APPROACH"
            },
            {
                "choice_id": "S2_C2",
                "choice_text": "📺 返回中控室查看监控",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["保守", "谨慎"],
                "consequences": {"PR": "+5", "flags": {"皮球_监控无画面": True}},
                "next_scene": "S2_MONITOR"
            },
            {
                "choice_id": "S2_C3",
                "choice_text": "🧍 站在原地观察，不要靠近",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["观察", "等待"],
                "consequences": {"PR": "+8", "flags": {"皮球_观察": True}},
                "next_scene": "S2_OBSERVE"
            },
            {
                "choice_id": "S2_C4",
                "choice_text": "💡 用手电筒照向声音方向",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["试探"],
                "preconditions": {"items": ["手电筒"]},
                "consequences": {"PR": "+10", "flags": {"用手电筒": True}},
                "next_scene": "S2_FLASHLIGHT"
            }
        ]
    },

    "S2_APPROACH": {
        "title": "【场景 2.1】接近声音",
        "narrative": """
你小心翼翼地朝声音走去。

*'啪嗒...啪嗒...啪嗒...'*

越来越近了。

声音来自走廊尽头的一家玩具店门口。

你走近了...

地上有一个红色的皮球，
在自己弹跳。

**没有人。**

皮球在地上弹了几下，
然后...

停了。

整个五楼变得死一般寂静。

你感觉背后有什么东西在看着你...
""",
        "choices": [
            {
                "choice_id": "S2_1_C1",
                "choice_text": "🏃 立刻离开五楼",
                "choice_type": ChoiceType.CRITICAL,
                "tags": ["逃跑"],
                "consequences": {"PR": "+5", "flags": {"第一次逃跑": True}},
                "next_scene": "S3_ESCAPE"
            },
            {
                "choice_id": "S2_1_C2",
                "choice_text": "🎾 捡起皮球检查",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["调查", "危险"],
                "consequences": {"PR": "+20", "inventory": ["红色皮球"], "flags": {"拿起皮球": True}},
                "next_scene": "S2_PICK_BALL"
            },
            {
                "choice_id": "S2_1_C3",
                "choice_text": "🔦 进入玩具店查看",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冒险"],
                "consequences": {"PR": "+25", "flags": {"进入玩具店": True}},
                "next_scene": "S2_TOY_STORE"
            }
        ]
    },

    "S2_MONITOR": {
        "title": "【场景 2.2】查看监控",
        "narrative": """
你快步返回中控室，盯着五楼的监控画面——

**什么都没有。**

没有人。
没有皮球。
只有空荡荡的走廊，荧光灯在闪烁。

但你刚才...明明听到了声音。

你调出回放，看刚才五楼的画面。

还是什么都没有。

监控像是在说谎。

你盯着屏幕，屏幕里的走廊空无一物。

但你知道，有什么东西在那里。
""",
        "choices": [
            {
                "choice_id": "S2_2_C1",
                "choice_text": "🚶 再次去五楼确认",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["果断"],
                "consequences": {"PR": "+8"},
                "next_scene": "S2_RETURN"
            },
            {
                "choice_id": "S2_2_C2",
                "choice_text": "📝 记录异常情况，继续观察",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["谨慎"],
                "consequences": {"PR": "+3", "flags": {"记录异常": True}},
                "next_scene": "GAME_OVER_INCOMPLETE"
            }
        ]
    },

    "S2_OBSERVE": {
        "title": "【场景 2.3】观察等待",
        "narrative": """
你站在原地，屏住呼吸。

*'啪嗒...啪嗒...啪嗒...'*

声音还在继续。

你看向走廊深处。

在昏暗的灯光下，你隐约看到...

走廊尽头，一个小小的身影。

是个小女孩，背对着你。

她在拍皮球。

但她的动作...很僵硬。

不像活人。

她突然停下了。

慢慢地...

转过头来。

你看不清她的脸，但你能感觉到——

**她在看着你。**
""",
        "choices": [
            {
                "choice_id": "S2_3_C1",
                "choice_text": "🏃 立刻逃离",
                "choice_type": ChoiceType.CRITICAL,
                "tags": ["逃跑"],
                "consequences": {"PR": "+10", "flags": {"看到女孩": True}},
                "next_scene": "S3_ESCAPE"
            },
            {
                "choice_id": "S2_3_C2",
                "choice_text": "🗣️ '你是谁？'",
                "choice_type": ChoiceType.CRITICAL,
                "tags": ["对话", "危险"],
                "consequences": {"PR": "+30", "flags": {"与女孩对话": True}},
                "next_scene": "S2_TALK"
            }
        ]
    },

    "S2_FLASHLIGHT": {
        "title": "【场景 2.4】用手电筒照射",
        "narrative": """
你打开手电筒，照向声音传来的方向。

光束穿过昏暗的走廊。

*'啪嗒...啪嗒...啪...'*

声音停了。

在手电筒的光圈里，你看到：

一个红色的皮球，
静静地躺在地上。

**没有人。**

你把光束向上移动，照向走廊尽头——

一个小女孩站在那里。

她穿着白色的连衣裙，
长发凌乱地垂在脸前。

她一动不动。

你的手电筒开始闪烁...

'滋——滋——'

然后灭了。

一片黑暗。

在黑暗中，你听到：

*脚步声。*

越来越近。
""",
        "choices": [
            {
                "choice_id": "S2_4_C1",
                "choice_text": "🏃 拼命逃跑",
                "choice_type": ChoiceType.CRITICAL,
                "tags": ["逃跑", "紧急"],
                "consequences": {"PR": "+15", "WF": "+1"},
                "next_scene": "S3_ESCAPE_URGENT"
            },
            {
                "choice_id": "S2_4_C2",
                "choice_text": "🔧 试图修理手电筒",
                "choice_type": ChoiceType.NORMAL,
                "tags": ["冷静"],
                "consequences": {"PR": "+25"},
                "next_scene": "S2_FIX_LIGHT"
            }
        ]
    },

    "GAME_OVER_INCOMPLETE": {
        "title": "【结局】未完成的巡逻",
        "narrative": """
你决定不再去五楼。

整晚，你都待在中控室里。

盯着那片雪花的监控屏幕。

偶尔，对讲机里会传来一些杂音。

像是有人在说话。

但你听不清。

06:00 AM，早班的同事来了。

"昨晚怎么样？"他问。

"还...还好。"你说。

但你知道，你没有完成巡逻。
你没有去查明真相。

五楼的秘密，依然是秘密。

而你...

做了一个整晚的噩梦。

在梦里，有个小女孩一直在拍皮球。

*啪嗒...啪嗒...啪嗒...*

---

**【结局：旁观者】**

- 你选择了安全，但也选择了无知
- PR: {PR}/100
- 真相：未知
""",
        "is_ending": True
    },

    "S3_ESCAPE": {
        "title": "【场景 3】逃离",
        "narrative": """
你转身就跑！

冲向防火门！

身后传来...

*'啪嗒...啪嗒...啪嗒...'*

越来越快！

你冲出防火门，疯狂按下电梯按钮。

电梯太慢了！

你选择楼梯，一路狂奔到一楼。

冲进中控室，反锁房门。

你气喘吁吁，心跳如雷。

监控屏幕上，五楼的画面依然是雪花。

但你知道...

**它还在那里。**

你度过了一个不眠之夜。

---

**【结局：逃避者】**

- 你活了下来，但真相依然未知
- PR: {PR}/100
- 心理阴影：永久
""",
        "is_ending": True
    }
}

# 主游戏循环
current_scene = "S1"
game_running = True

while game_running:
    # 检查结局
    ending = ending_system.check_ending(state)
    if ending:
        print("\n" + "="*70)
        print("🏆 游戏结束")
        print("="*70 + "\n")
        print(f"达成结局: {ending.value}")
        cli.display_narrative(ending_system.render_ending(ending, state))
        break

    # 获取当前场景
    scene = scenes.get(current_scene)
    if not scene:
        print(f"\n❌ 错误：场景 {current_scene} 不存在")
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

    # 显示选择
    while True:
        cli.display_choices(choices, state)

        # 获取玩家输入
        user_input = input("\n👉 请输入选项编号（或输入 /save, /quit）: ").strip()

        # 处理命令
        if user_input == "/quit":
            print("\n👋 退出游戏")
            game_running = False
            break
        elif user_input == "/save":
            save_name = input("请输入存档名（不含后缀）: ").strip() or "quicksave"
            state.save(f"saves/{save_name}.save")
            print(f"✅ 已保存到 saves/{save_name}.save")
            continue
        elif user_input == "/load":
            save_name = input("请输入存档名: ").strip()
            try:
                state = GameState.load(f"saves/{save_name}.save")
                print(f"✅ 已加载 saves/{save_name}.save")
            except:
                print("❌ 加载失败")
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

                    # 跳转到下一个场景
                    next_scene = scene["choices"][choice_num - 1].get("next_scene")
                    if next_scene:
                        current_scene = next_scene

                    break
                else:
                    print(f"\n❌ {validation.reason}\n")
            else:
                print("\n❌ 无效的选项编号\n")
        except ValueError:
            print("\n❌ 请输入数字编号\n")

print("""
╔══════════════════════════════════════════════════════════════════╗
║                       感谢游玩！                                 ║
║                                                                  ║
║  🎮 Ghost Story Factory - 杭州·灵异故事                        ║
║  💡 这只是一个演示版本，完整版将包含更多场景和结局              ║
║  🌟 你的选择决定了故事的走向                                    ║
╚══════════════════════════════════════════════════════════════════╝
""")

