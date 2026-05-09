# TASK: 正式剧本沙盒化深层迭代 Pass 1

版本: v1.0
状态: Done
关联:
- `docs/architecture/ADR-010-sandbox-topology-contract.md`
- `docs/tasks/TASK_GAMETREE_V1.md`
- GitHub Issue: `#20`

---

## 0. 背景

`stories/hangzhou_yebanbaoan/tree.json` 已经具备 GameTree v1 的运行闭环,但剧本层仍有明显短板:

- 部分可回访节点没有 `narrative_variants`,玩家回访时读到同一段文字;
- 多个灵异事件仍是单点惊吓,地标之间的互相污染不足;
- 玩家拿到的道具/线索没有被足够多的后续节点承认;
- 二周目与跨角色反应已有框架,但文本密度不够;
- `linmou_1985` 前传沙盒骨架已补,但湖边终局节点仍需要更强的意图分化。

这不是引擎问题,是剧本问题。本任务直接修改正式 fragment,重建正式 `tree.json`。

---

## 1. 目标 / 非目标

### 目标

- [x] 为关键可回访节点补 `narrative_variants`,让二次/三次访问有新内容;
- [x] 增强跨地标污染:湖滨账本、柳浪红衣、九溪裂钟、羊血弄、留下小学、联庄井底、B3 终局互相承认;
- [x] 增强道具/线索承认:例如 `林副科长账本残页`、`1986 林字硬币`、`红衣女孩铜锈`、`1991 班级合照`、`27F 铜钥匙`;
- [x] 强化灵异规则感:杭州常数不是随机鬼吓人,而是用年份、工号、地标、档案互相校验玩家;
- [x] 保持开放沙盒:新增文本和选择没有把地标改回单线流程。

### 非目标

- 不新增图形 VN 客户端;
- 不引入外部素材文件;
- 不改 DB schema;
- 不用 LLM 实时生成替代手写剧本;
- 不一次性补完所有角色线。

---

## 2. 第一批剧本切入点

优先改这些节点:

- `n_s1_close_touch`:风衣触摸回访、林某线索承认;
- `n_s1_wet_shoes`:湿鞋与 1986 硬币/联庄沉船互相污染;
- `n_s2_wait_307`:307 阶等待二次访问、红衣女孩对玩家行为记账;
- `n_s2_descend_count`:倒数下山与 S5/1991 线索关联;
- `n_s3_examine_face`:裂钟铜锈根据道具/二周目改变叙述;
- `n_s3_scrape_corrosion`:铜锈片不只是道具,而是被后续地标识别的污染物;
- `n_s3_wait_to_ring`:七下钟与 S6/S7 终局线关联;
- `n_s3_temple_back`:后院井承认八棺/前任/林某;
- `n_s4_examine_sign`:羊血弄匾额承认 `铜锈护符` / 羊公会线;
- `n_s5_open_door`:琴房承认 1991 请假条/班级合照/红衣线;
- `n_s6_look_down`:联庄井底承认 `1986 林字硬币` / 林某前传;
- `n_s7_arrive`:B3 终局承认此前地标收集状态;
- `n_l1985_lake_jump`:林某投湖前按意图分化叙述。

完成情况:

- `redgirl_1996` 统一为 **林晓燕,11 岁,林志诚遗腹女,1996 货梯事故**;
- `n_npc_red_dress_girl` 增加信任选择与跨物件反应,承认 `红衣女孩铜锈`、`十三号湿巾`、`1987 告示残页`、`1991 班级合照`;
- `n_scene_lost_archive` 增加对 `十三号湿巾`、`红衣女孩铜锈`、`浙大钟楼跳绳照片`、`武林门 7 人录音`、`血毛笔` 的档案承认;
- `n_s1_close_touch` / `n_s1_wet_shoes` / `n_s2_wait_307` / `n_s2_descend_count` / `n_s3_*` / `n_s4_examine_sign` / `n_s5_open_door` / `n_s6_look_down` / `n_s7_arrive` 均补充了条件叙述;
- `n_l1985_lake_jump` 按释/悔/冤/暴露四类意图补足投湖瞬间叙述;
- 湖滨终局选择从抽象按钮改为具体行为文本。

---

## 3. 验收标准

- [x] `python3 tools/merge_fragments.py` 能重建正式 `tree.json`;
- [x] `python3 tools/audit_playability.py stories/hangzhou_yebanbaoan/tree.json` 通过;
- [x] `python3 tools/audit_variants.py stories/hangzhou_yebanbaoan/tree.json` 显示 `undifferentiated_revisit_nodes: []`;
- [x] `bash tools/audit_all.sh` 通过;
- [x] `python3 tools/run_all_tests.py` 通过;
- [x] 文档和 GitHub issue 留痕。
