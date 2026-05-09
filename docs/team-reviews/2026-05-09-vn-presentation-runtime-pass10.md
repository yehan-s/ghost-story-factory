# 评审团报告: VN 演出契约进入运行时 Pass 10

日期: 2026-05-09
任务: `TASK_VN_PRESENTATION_RUNTIME_PASS10`
决议: 修改后放行

---

## 1. Chief Editor

结论:放行,但必须收窄范围。

这轮真正要修的是“已有演出数据不可见”。不要借题发挥成完整 VN 引擎。玩家现在看不到 `presentation`,所以剧本再补 `camera / cg_intent / transition_intent` 也只是在 JSON 里自嗨。先让运行时显示出来。

---

## 2. State Architect

结论:放行。

不得新增状态字段,不得碰 DB schema。`presentation` 是节点元数据,不参与 `State.meets()`、`resolve_next()` 或成就判定。最小实现应是纯格式化函数,旧节点没有 `presentation` 时返回空列表。

---

## 3. Meta-Game Designer

结论:修改后放行。

演出提示必须服务周目反馈,不能变成调试噪音。正式树每个节点都有 `presentation`,如果每步打印 6 行,玩家会烦。建议压成一行基础演出、一行镜头 / CG 意图,并允许环境变量关闭文本 fallback。

---

## 4. UX Designer

结论:修改后放行。

CLI 里显示要轻,放在 narrative 前,让玩家先感知“场景变了”。TUI 要复用同一套文本,但必须转义 Rich markup。资产 label 里如果出现 `[` `]`,Textual 不能被打碎。

---

## 5. Lore Keeper

结论:放行。

资产 label 比裸 id 更适合玩家阅读。杭州剧本的灵异感靠“湖水、汽笛、电话亭、B3 灯管”这些稳定意象回收,运行时应该把这些意象露出来。

---

## 6. Topology Designer

结论:放行。

地图节点也应该显示演出提示。不要只在普通 narrative 节点显示,否则 hub / 地标入口会继续像菜单,不是现场。

---

## 7. QA / Path Tester

结论:修改后放行。

测试不要启动完整 `play()`。应测试纯 formatter、stdout 封装、无 presentation 静默、缺省字段不输出 `None`、TUI 转义。审计测试继续管数据契约,渲染测试只管玩家可见输出。

---

## 8. 风险清单

- 输出噪音:用 1-2 行压缩;
- 旧树兼容:没有 `presentation` 时必须静默;
- Rich markup 注入:TUI 输出前 escape;
- 范围膨胀:本轮不做真实图片和音频。

---

## 9. 决议

修改后放行。

执行顺序:
1. 新增 Task / Issue / milestone;
2. 实现共享 formatter;
3. 接入 CLI 和 TUI;
4. 新增测试并挂入统一测试入口;
5. 跑审计和完整测试;
6. 回写 Task / Issue / PR。

