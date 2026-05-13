# Pass 24 ── linmou ending 跨周目反咬补完

## 上下文

Pass 23 把 4 个主结局(E_TRUE / E_BROADCAST / E_NEUTRAL / E_HIDDEN)的
跨周目反咬 variant 铺到 G-273 早期节点。linmou 前传线的 4 个 ending
(E_LINMOU_RELEASE / EXPOSED / GRIEVANCE / DUTY)还没有反咬:
玩家通关林某线后,G-273 周目里看不到任何"上一世记忆"的痕迹。

`audit_cross_run_continuity` 在跑过的时候,linmou ending 一律豁免不报
(BAD ending 也豁免),所以 ENDING_NO_CROSS_REFERENCE 为 0 不代表
linmou 真的被反咬过——是它**不在审计范围内**。

## 目标

至少 2 条 linmou ending 在 G-273 主线得到反咬,把"通关林某线" → "G-273
周目里看到 1985 年的物质遗迹"通路打通。

## 实施(已完成)

`stories/hangzhou_yebanbaoan/_fragment_v7_shared.json` 新增 2 条 variant:

1. **n_scene_lost_archive.variant[0]**:`ending_seen.ending_id = E_LINMOU_RELEASE`
   - 文案:1985-12-XX 米黄色牛皮纸袋,"准予恢复夜班岗位",双归档抬头。
   - 语义:林某复职 → 这个档案室真的留下了一份纸质档案,G-273 在 2026 年扒到它。

2. **n_npc_predecessor_voice.variant[0]**:`ending_seen.ending_id = E_LINMOU_EXPOSED`
   - 文案:1980 厂区广播喇叭,"念三遍",前任声音残留。
   - 语义:林某被广播站点名 → 这个声音在 2026 年还在某个角落循环。

两条变体都用 `ending_id` 形式(Pass 23 同款),不是 `.last`(.last 是 Pass 25 的人格惯性范畴,
linmou 是"线性物质遗迹"不是"人格底色")。

## 验收

- `audit_all.sh` 13/13 全绿
- `tools/run_all_tests.py` 7/7 全绿
- 手动通关 linmou RELEASE / EXPOSED 后,G-273 周目相应节点看到新文案

## 状态

✅ Done(2026-05-13)

## 相关

- 前置:Pass 23 主结局反咬(`TASK_SCRIPT_CROSS_RUN_FINALE_PASS23.md`)
- 跨周目契约:ADR-010 第一公理(`endings_seen[story_id]: list`)
