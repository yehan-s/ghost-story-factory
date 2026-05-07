# linmou_1985 Act 1 Implementation Plan(P0 — 双向联动)

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 linmou_1985 的 Act 1(投湖前 6 小时,~5000 字 / 50 节点 / 4 ending),作为第二可玩角色。**双向联动** — linmou 通关 → G-273 节点 narrative 切档;G-273 已通关 → linmou Act 1 节点叙述者口吻切档(玩家"已知答案的回响")。

**Architecture:** 三柱:① **State 极简**(Linus 反加法者)— 0 新字段,1 新 clause `ending_seen`,复用 `endings_seen[杭州_v7]: list[ending_id]`。② **Lore 详尽 setting**(1985-10-18 23:40 / 杭州二轻物资 / 西湖锦带桥 / 12 红线)。③ **QA 必死不变量**(`audit_paths_linmou.py` 4 不变量固化 lore canon)。

**Tech Stack:** Python 3.11+ / pytest / 现有 v5 player.py + v7 save_manager.py + reaction 机制(ADR-008)

**评审依据**:`docs/team-reviews/2026-05-07-linmou-arc.md`(决议:修改后放行)

---

## 关键决议(评审固化)

| 议题 | 决议 |
|---|---|
| 新字段 | **0 新字段**(复用 `endings_seen`),拒绝 `character_played` / `linmou_ending` |
| 新 clause | **1 个 `ending_seen`**(支持 `*` 通配) |
| story_id | **同一 `杭州_v7`** — linmou 是杭州故事的角色周目 |
| ending 数 | **4 个**:`E_LINMOU_GRIEVANCE/REGRET/RELEASE/EXPOSED` |
| Act 1 必死 | **lore canon 红线**,audit 不变量 INV-1~4 强制 |
| Fragment | 新建 `_fragment_v7_linmou_1985.json`,前缀 `n_l1985_*` |
| 拓扑 | picker hub + 4 地标 × ~10 节点(算盘房/锅炉房/档案室/湖边凉亭) |
| 双向联动 | linmou ↔ G-273 都查同一 `ending_seen` clause(零额外开销) |
| 主菜单 | 三态 `locked / unlockable / playable` + 锁定提示(诱饵不空槽) |
| 投湖呈现 | 三段式静默(对白渐隐 → 黑屏 → 水声 ASCII → 黑屏 → 主菜单) |
| Lore canon | 1985-10-18 23:40 / 二轻物资财务科 / 西湖锦带桥 / 12 红线 |

---

## File Structure

**Create**:
- `stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json` — 50 节点 fragment(picker hub + 4 地标 × 10 + 4 ending + entry)
- `tools/audit_paths_linmou.py` — 必死不变量 INV-1~4 检查
- `tests/test_ending_seen.py` — `_meets_clause` 新条件 6 用例
- `tests/test_audit_paths_linmou.py` — 不变量测试
- `tests/snapshots/linmou_act1_paths.json` — Act 1 路径快照(P1 防回归)
- `docs/architecture/ADR-009-linmou-arc-canon.md` — 1985 lore canon 固化
- `data/linmou_act1_lore.json` — Act 1 物件 / 声音 / 气味清单(机器查表)

**Modify**:
- `src/ghost_story_factory/v5/player.py:199-300` — `_meets_clause` 加 `ending_seen` 分支(参数 `story_id` + `ending_id`,通配 `*`)
- `src/ghost_story_factory/v5/player.py:694-720` — `_select_character` 三态化(查 `save_manager.unlocked_characters`,显示锁定提示)
- `src/ghost_story_factory/v7/tui_player.py` — TUI 端同步三态主菜单
- `src/ghost_story_factory/v7/save_manager.py` — 加 `record_ending` 时把 `E_LINMOU_*` 同样写入 `endings_seen`(已有,但要确认 list 顺序保留)
- `src/ghost_story_factory/v7/save_manager.py:CHARACTER_ROSTER` — `linmou_1985` entry 加 `start_node: "n_l1985_entry"`
- `tools/merge_fragments.py:STORY_META.characters` — `linmou_1985` 加 `start_node` + `initial_inv`(蓝布人造革账册包) + `initial_flags`
- `tools/audit_all.sh` — 加第 5 项 `audit_paths_linmou`
- `stories/hangzhou_yebanbaoan/_fragment_v7_shared.json` — 选 3-5 个 G-273 节点的 narrative_variants 加 linmou ending 反应(双向 b)

---

## Phase 1:引擎扩展(`ending_seen` clause)

### Task 1.1:`_meets_clause` 加 `ending_seen` 分支

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py` _meets_clause(在 reaction 三条件后)
- Test: `tests/test_ending_seen.py`(新建)

- [ ] **Step 1: 写失败测试(6 用例)**

```python
# tests/test_ending_seen.py
"""ending_seen clause:跨周目 ending 查询条件。

形式: {"ending_seen": {"story_id": "...", "ending_id": "..." | "*"}}
list ANY 语义不适用(单条 ending);需要多 ending 用 all_of/any_of 组合。
"""
from __future__ import annotations
from ghost_story_factory.v5.player import State


class FakeSave:
    def __init__(self, endings_seen=None):
        self.endings_seen_data = endings_seen or {}
    def is_deduction_resolved(self, sid, did): return False
    def is_foreshadow_resolved(self, sid, fid): return False
    def get_resolved_foreshadows(self, sid): return set()

    @property
    def endings_seen(self):
        # 兼容现有 SaveManager(返回 list);新结构是 dict[story_id, list]
        return self.endings_seen_data


def _state_with(endings):
    """endings: dict[story_id, list[ending_id]]"""
    sm = FakeSave(endings_seen={k: list(v) for k, v in endings.items()})
    return State({}, save_manager=sm, story_id="杭州_v7")


def test_ending_seen_exact_match():
    s = _state_with({"杭州_v7": ["E_LINMOU_RELEASE"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}) is True


def test_ending_seen_story_mismatch():
    s = _state_with({"杭州_v7": ["E_TRUTH"]})
    assert s.meets({"ending_seen": {"story_id": "其他故事", "ending_id": "E_TRUTH"}}) is False


def test_ending_seen_ending_mismatch():
    s = _state_with({"杭州_v7": ["E_TRUTH"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}) is False


def test_ending_seen_wildcard_ending_any_match():
    """ending_id='*' → 任意该 story 的 ending 都满足。"""
    s = _state_with({"杭州_v7": ["E_TRUTH"]})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "*"}}) is True


def test_ending_seen_wildcard_ending_empty_fails():
    """ending_id='*' + 该 story 0 ending → False。"""
    s = _state_with({"杭州_v7": []})
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "*"}}) is False


def test_ending_seen_no_save_manager_returns_false():
    s = State({})  # 无 save_manager
    assert s.meets({"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_TRUTH"}}) is False
```

- [ ] **Step 2: 跑测试验证失败**

```bash
pytest tests/test_ending_seen.py -v
# Expected: 6 FAIL
```

- [ ] **Step 3: 加 _meets_clause 分支**

在 `src/ghost_story_factory/v5/player.py::_meets_clause()` 的 `theme_resolved` 分支之后插入:

```python
        if "ending_seen" in require:
            sm = self.save_manager
            if sm is None:
                return False
            spec = require["ending_seen"] or {}
            sid = spec.get("story_id")
            eid = spec.get("ending_id")
            if not sid or not eid:
                return False
            seen = sm.data.get("endings_seen") or []
            # 兼容现状:endings_seen 是 list,linmou ending 也写到同 list
            # 后续若改 dict[story_id, list],下面需要按 sid 取
            if isinstance(seen, list):
                if eid == "*":
                    return len(seen) > 0
                return eid in seen
            elif isinstance(seen, dict):
                story_eds = seen.get(sid) or []
                if eid == "*":
                    return len(story_eds) > 0
                return eid in story_eds
            return False
```

注:**SaveManager 现状**是 `endings_seen: list[ending_id]`(全局)。本期 schema 升级先保持兼容(同 list 也能查)。如果后续要严格按 story_id 分桶,改 SaveManager 的 schema 升级 + 测试。

- [ ] **Step 4: 测试通过**

```bash
pytest tests/test_ending_seen.py -v
# Expected: 6 PASS
```

- [ ] **Step 5: Commit**

```bash
git add src/ghost_story_factory/v5/player.py tests/test_ending_seen.py
git commit -m "feat(engine): _meets_clause 加 ending_seen 条件(支持 * 通配)"
```

---

### Task 1.2:`endings_seen` schema 升级到 dict per story_id(可选,推荐)

> ⚠️ 评审 QA 决议:`ending_seen` 必须当一等公民。当前 SaveManager `endings_seen: list[ending_id]` 是全局 list,无法区分 G-273 vs linmou_1985 两个角色周目。**强烈建议升级**到 `dict[story_id, list[ending_id]]`。

**Files:**
- Modify: `src/ghost_story_factory/v7/save_manager.py:DEFAULT_SAVE` + `load()` + `record_ending()` + property
- Modify: `tests/test_save_manager_query.py` 加迁移测试

- [ ] **Step 1: 写迁移兼容测试**

```python
# 加到 tests/test_save_manager_query.py
def test_endings_seen_legacy_list_migrates_to_dict():
    """旧版 list 自动迁移到 dict[story_id]。"""
    sm = _save_with({
        "version": 4,
        "endings_seen": ["E_TRUTH", "E_NEUTRAL"],  # 旧版 list
    })
    # 迁移后应为 dict
    es = sm.data.get("endings_seen")
    assert isinstance(es, dict)
    # 旧 list → 默认归入 "杭州_v7"
    assert "E_TRUTH" in es.get("杭州_v7", [])

def test_endings_seen_already_dict_preserved():
    sm = _save_with({
        "version": 5,
        "endings_seen": {"杭州_v7": ["E_TRUTH"]},
    })
    es = sm.data["endings_seen"]
    assert es == {"杭州_v7": ["E_TRUTH"]}
```

- [ ] **Step 2: 跑测试验证失败**

- [ ] **Step 3: 改 SaveManager(SAVE_VERSION → 5)**

```python
# DEFAULT_SAVE
"endings_seen": {},   # was: []

# load() 兼容:
es_raw = raw.get("endings_seen")
if isinstance(es_raw, list):
    # 旧版 list → 迁移到 杭州_v7
    self.data["endings_seen"] = {"杭州_v7": list(es_raw)} if es_raw else {}
elif isinstance(es_raw, dict):
    self.data["endings_seen"] = {k: list(v) for k, v in es_raw.items() if isinstance(v, list)}
else:
    self.data["endings_seen"] = {}

# record_ending:
sc = self.data.setdefault("endings_seen", {})
story_eds = sc.setdefault(story_id, [])
if ending_type not in story_eds:
    story_eds.append(ending_type)

# 兼容旧 property
@property
def endings_seen(self) -> List[str]:
    """所有 story 的 ending 合并扁平 list(向后兼容)。"""
    out = []
    for v in self.data.get("endings_seen", {}).values():
        out.extend(v)
    return out
```

- [ ] **Step 4: 改 _meets_clause 的 ending_seen 分支(去掉 isinstance 兜底,只走 dict)**

- [ ] **Step 5: 跑全套回归 + commit**

```bash
pytest tests/ -q
./tools/audit_all.sh
git add ...
git commit -m "refactor(save): endings_seen list → dict[story_id, list],版本 v5

向后兼容:旧版 list 自动迁移归入 杭州_v7。property endings_seen 仍返回扁平 list。"
```

---

## Phase 2:工具守门(必死不变量 + cross-character contract)

### Task 2.1:`audit_paths_linmou.py`(INV-1~4 必死不变量)

**Files:**
- Create: `tools/audit_paths_linmou.py`
- Test: `tests/test_audit_paths_linmou.py`(新建)
- Modify: `tools/audit_all.sh` 加第 5 项

- [ ] **Step 1: 测试(假 fragment)**

```python
# tests/test_audit_paths_linmou.py
import json, tempfile
from pathlib import Path
from tools.audit_paths_linmou import audit


def _write(tree):
    p = Path(tempfile.mkdtemp()) / "tree.json"
    p.write_text(json.dumps(tree, ensure_ascii=False))
    return p


def test_inv1_terminal_must_be_in_4_endings():
    """INV-1: 所有 linmou 周目终态 ∈ 4 ending 集合。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "go", "next": "n_dead_end"}]},
            "n_dead_end": {"choices": []},  # 不在 4 ending,FAIL
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    assert any(p["code"] == "INV1_TERMINAL_NOT_IN_ENDINGS" for p in report["problems"])


def test_inv2_no_edge_to_act23():
    """INV-2: linmou 子图无边通向 Act 2/3 节点(防逃出生天)。"""
    # 当前 Act 2/3 不存在 → trivial pass
    pass


def test_inv4_endings_have_must_die_canon():
    """INV-4: 4 ending 节点的 _lore_canon must_die: true。"""
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "go", "next": "E_LINMOU_RELEASE"}]},
            "E_LINMOU_RELEASE": {"choices": []},  # 缺 _lore_canon
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    assert any(p["code"] == "INV4_MISSING_MUST_DIE_CANON" for p in report["problems"])


def test_clean_act1_passes():
    tree = {
        "start_node": "n_intro",
        "nodes": {
            "n_l1985_entry": {"choices": [{"text": "go", "next": "E_LINMOU_RELEASE"}]},
            "E_LINMOU_RELEASE": {"choices": [], "_lore_canon": {"must_die": True}},
        },
        "characters": {"linmou_1985": {"start_node": "n_l1985_entry"}},
    }
    report = audit(_write(tree))
    blockers = [p for p in report["problems"] if p["code"].startswith("INV")]
    assert blockers == []
```

- [ ] **Step 2: 实现 audit_paths_linmou.py**

```python
"""tools/audit_paths_linmou.py — linmou 周目必死不变量(INV-1~4)。

INV-1: 所有 linmou 周目终态(choices=[])∈ 4 ending 白名单
INV-2: 无边从 linmou 子图通向 Act 2/3 节点(本期 Act 2/3 不存在,trivial)
INV-3: 投湖节点 n_l1985_lake_jump 后置必为 ending,无中间 narrative
INV-4: 4 ending 节点必须有 _lore_canon.must_die: true

退出:0=全绿, 2=有 INV 违规
"""
from __future__ import annotations
import argparse, json, sys
from collections import deque
from pathlib import Path

LINMOU_ENDINGS = {"E_LINMOU_GRIEVANCE", "E_LINMOU_REGRET",
                  "E_LINMOU_RELEASE", "E_LINMOU_EXPOSED"}


def _bfs(nodes, start):
    seen = {start}; q = deque([start])
    while q:
        cur = q.popleft()
        for ch in (nodes.get(cur) or {}).get("choices") or []:
            nxt = ch.get("next")
            if nxt and nxt in nodes and nxt not in seen:
                seen.add(nxt); q.append(nxt)
    return seen


def audit(tree_path: Path):
    tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
    nodes = tree.get("nodes") or {}
    chars = tree.get("characters") or {}
    linmou = chars.get("linmou_1985") or {}
    start = linmou.get("start_node")
    problems = []
    if not start or start not in nodes:
        # 无 linmou 周目 → trivial pass
        return {"tree": str(tree_path), "problems": []}

    reachable = _bfs(nodes, start)

    # INV-1: 终态 ∈ 4 endings
    for nid in reachable:
        node = nodes[nid]
        if not (node.get("choices") or []):
            if nid not in LINMOU_ENDINGS:
                problems.append({
                    "code": "INV1_TERMINAL_NOT_IN_ENDINGS",
                    "node": nid,
                    "msg": f"{nid} choices=[] 但不在 4 ending 集合 {LINMOU_ENDINGS}",
                })

    # INV-3: 投湖后置必为 ending
    if "n_l1985_lake_jump" in nodes:
        node = nodes["n_l1985_lake_jump"]
        for ch in (node.get("choices") or []):
            nxt = ch.get("next")
            if nxt and nxt not in LINMOU_ENDINGS:
                problems.append({
                    "code": "INV3_LAKE_JUMP_NOT_TO_ENDING",
                    "node": "n_l1985_lake_jump",
                    "msg": f"投湖出口指向 {nxt!r},不在 4 ending",
                })

    # INV-4: 4 ending 必须有 _lore_canon.must_die
    for eid in LINMOU_ENDINGS:
        if eid in reachable:
            node = nodes[eid]
            canon = node.get("_lore_canon") or {}
            if not canon.get("must_die"):
                problems.append({
                    "code": "INV4_MISSING_MUST_DIE_CANON",
                    "node": eid,
                    "msg": f"{eid} 缺 _lore_canon.must_die: true",
                })

    return {"tree": str(tree_path), "problems": problems}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tree", type=Path)
    args = ap.parse_args()
    report = audit(args.tree)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(2 if report["problems"] else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 更新 audit_all.sh 加第 5 项**

```bash
echo "=== 5/5 audit_paths_linmou(linmou 必死不变量 ADR-009)==="
python tools/audit_paths_linmou.py "$TREE" > /dev/null
echo "  必死不变量审计通过"
```

- [ ] **Step 4: 跑测试 + audit + commit**

```bash
pytest tests/test_audit_paths_linmou.py -v
./tools/audit_all.sh  # 当前 linmou 周目不存在 → trivial pass
git add tools/audit_paths_linmou.py tests/test_audit_paths_linmou.py tools/audit_all.sh
git commit -m "feat(audit): audit_paths_linmou.py 必死不变量 INV-1~4"
```

---

### Task 2.2:audit_reactions cross-character contract 扩展

**Files:**
- Modify: `tools/audit_reactions.py` 加 cross-character 检测

**目的**:任何 G-273 节点的 narrative_variants 引用 `ending_seen: {story_id: 杭州_v7, ending_id: E_LINMOU_*}`,该 ending 必须在某 fragment 的 ending 节点定义中存在(否则就是 DEAD reference)。

- [ ] **Step 1: 写测试**

```python
# 加到 tests/test_audit_reactions.py
def test_cross_character_dead_ending_seen():
    """variant require ending_seen 但该 ending 不在节点表 → DEAD_REACTION。"""
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {"narrative_variants": [
                {"if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_GHOST"}}, "text": "..."},
                {"text": "default"},
            ], "choices": []},
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    assert any(p["code"] == "DEAD_ENDING_SEEN" and "E_GHOST" in p["msg"]
               for p in report["problems"])


def test_cross_character_existing_ending_seen_passes():
    tree = {
        "start_node": "n1",
        "nodes": {
            "n1": {"narrative_variants": [
                {"if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}}, "text": "..."},
                {"text": "default"},
            ], "choices": [{"text": "x", "next": "E_LINMOU_RELEASE"}]},
            "E_LINMOU_RELEASE": {"choices": [], "_lore_canon": {"must_die": True}},
        },
        "reaction_contracts": {"deductions": {}, "foreshadows": {}, "themes": {}},
    }
    report = audit(_write_tree(tree))
    blockers = [p for p in report["problems"]
                if p["code"] in ("DEAD_REACTION", "DEAD_ENDING_SEEN")]
    assert blockers == []
```

- [ ] **Step 2: 改 audit_reactions.py — 在 _walk_reaction_keys 之后扫 ending_seen**

在 `audit()` 内,扫所有 require 收集 ending_seen 引用:

```python
# 加在 problems 收集逻辑后
ending_node_ids = set(nodes.keys())
for nid, node in nodes.items():
    for ctx, req in _walk_requires(node):
        for spec in _walk_ending_seen(req):
            sid = spec.get("story_id")
            eid = spec.get("ending_id")
            if eid and eid != "*" and eid not in ending_node_ids:
                problems.append({
                    "code": "DEAD_ENDING_SEEN",
                    "node": nid,
                    "ctx": ctx,
                    "msg": f"ending_seen ending_id={eid!r} 不在节点表",
                })


def _walk_ending_seen(req):
    if not isinstance(req, dict):
        return
    if "ending_seen" in req:
        yield req["ending_seen"] or {}
    for sub in req.get("any_of") or []:
        yield from _walk_ending_seen(sub)
    for sub in req.get("all_of") or []:
        yield from _walk_ending_seen(sub)
    if "not" in req:
        yield from _walk_ending_seen(req["not"])
```

- [ ] **Step 3: 测试 + commit**

---

## Phase 3:Lore + ADR-009

### Task 3.1:`data/linmou_act1_lore.json`(物件 / 声音 / 气味清单)

**Files:**
- Create: `data/linmou_act1_lore.json`
- Test: `tests/test_lore_data.py`(append)

```json
{
  "_comment": "Act 1 必出现 lore 元素清单。Phase 4 内容创作必须查表替换,禁止自由发挥。",
  "_source": "docs/team-reviews/2026-05-07-linmou-arc.md § 6",
  "version": 1,
  "setting": {
    "date": "1985-10-18",
    "time_window": "20:00 → 02:00(末班船 22:30 后 6 小时空窗)",
    "weather": "深秋,无月(农历九月初五),气温 12-15℃,微风,西湖夜雾",
    "location_unit": "杭州市第二轻工业局物资供应公司财务科('二轻物资')",
    "location_lake": "西湖北山街锦带桥东侧水域,水温约 15℃",
    "lake_jump_time": "1985-10-18 23:40 前后"
  },
  "objects": {
    "must_appear": [
      "搪瓷缸(白底红字'劳动光荣')",
      "铝制饭盒",
      "的确良衬衫",
      "蓝布人造革黑包(里装 26 联签拨款单复印件)",
      "蓝色中山装",
      "煤油应急灯",
      "手摇电话",
      "《浙江日报》1985-10-17 期",
      "二八式永久自行车",
      "半导体收音机(中央人民广播电台对台广播)",
      "大前门 / 利群烟"
    ]
  },
  "audio": [
    "更夫梆子(罕见但二轻仓库区还有)",
    "远处 104 厂夜班汽笛",
    "桂花落地前的最后蝉鸣残响",
    "保温瓶塞拔出'噗'声"
  ],
  "scent": [
    "煤球炉余烬",
    "来苏儿消毒水",
    "隔夜冷饭",
    "雾里的湖水腥味",
    "廉价烟丝"
  ],
  "text_anchors": [
    "二轻物资 1985 年第三季度采购清单",
    "26 人联签拨款单复印件",
    "'调拨'两字红章"
  ],
  "redlines_vocab": [
    "矿泉水", "塑料瓶", "私家车", "手机", "BP机", "商品房",
    "股票", "外卖", "快递", "超市", "微信", "支付",
    "打卡机", "监控摄像头", "电脑", "U盘", "打印机"
  ],
  "redlines_values": [
    "不得出现'下海'/'创业'/'先富起来'的正面叙事",
    "林某要死在'集体主义信念被 26 个签字撕裂'的语境,不是'看不开经济转型'"
  ],
  "redlines_objects": [
    "不锈钢保温杯(用搪瓷)",
    "一次性筷子",
    "彩色塑料(只有蓝灰绿黑白)",
    "合成洗涤剂广告(用肥皂)"
  ]
}
```

- [ ] **Step 1: 写文件 + schema 测试**

```python
# tests/test_lore_data.py(append)
def test_linmou_act1_lore_schema():
    p = Path("data/linmou_act1_lore.json")
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    for k in ("setting", "objects", "audio", "scent", "text_anchors",
              "redlines_vocab", "redlines_values", "redlines_objects"):
        assert k in data, f"缺 {k}"
    s = data["setting"]
    assert s["date"] == "1985-10-18"
    assert "西湖北山街锦带桥" in s["location_lake"]
```

- [ ] **Step 2: 跑测试 + commit**

---

### Task 3.2:ADR-009 — linmou 角色周目契约

**Files:**
- Create: `docs/architecture/ADR-009-linmou-arc-canon.md`

写入完整 1985 setting + 4 ending canonical name + 必死不变量 INV-1~4 + Phase 拆分 P0/P1 + 双向联动语义。模板参考 ADR-008。

- [ ] **Step 1: 写 ADR(提纲见 plan 评审报告 § 9)**

- [ ] **Step 2: Commit**

```bash
git add docs/architecture/ADR-009-linmou-arc-canon.md data/linmou_act1_lore.json tests/test_lore_data.py
git commit -m "docs(adr): ADR-009 linmou_1985 周目契约 + Act 1 lore 清单"
```

---

## Phase 4:内容创作(50 节点 fragment)

> ⚠️ **本 Phase 是 plan 中工作量最大的部分**(~5000 字剧本)。建议**单独一会话/单独 day** 集中创作,每完成 1 地标 = 1 commit + 1 audit pass,避免后期积压。

### 节点预算 50 = picker 1 + 4 地标 × 10 + 收束 4 + endings 4 + entry 1

### 命名规范 `n_l1985_<area>_<seq>`

### Task 4.1:Fragment 骨架 + entry + picker hub

**Files:**
- Create: `stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json`

- [ ] **Step 1: 写骨架(只含 entry + picker + 4 ending 占位 + 4 地标 placeholder)**

```json
{
  "_comment": "linmou_1985 角色周目 Act 1 — 1985-10-18 投湖前 6 小时。50 节点。",
  "fragment_owner": "linmou_1985_act1",
  "schema_version": "1.0-act1-frozen",
  "_dispatch_notes": "通过 STORY_META.characters['linmou_1985'].start_node = 'n_l1985_entry' 进入。",
  "nodes": {
    "n_l1985_entry": {
      "scene": "INTRO",
      "narrative": "1985 年 10 月 18 日,星期五,晚上 20:00。\n\n二轻物资财务科办公室。\n\n你姓林,叫林志诚,人称林副科长。\n\n窗外是杭州深秋,梧桐落叶贴在窗玻璃上。\n\n你刚锁完档案柜。胸袋里装着 26 联签拨款单的复印件——是你今天傍晚偷偷复印的。\n\n你今晚要去一个地方。\n\n但下班路上,你还有几件事要做。",
      "show_hud": true,
      "choices": [
        {"text": "走出办公室,先去算盘房交班。", "next": "n_l1985_landmark_picker"}
      ]
    },
    "n_l1985_landmark_picker": {
      "scene": "MAP",
      "_is_map_picker": true,
      "narrative": "你站在二轻物资大院的过道。\n\n夜班的灯还没全开,只有几盏煤油应急灯亮着。\n\n远处 104 厂的汽笛响了第一声。\n\n你今晚,还有 4 个地方要去。",
      "show_hud": true,
      "choices": [
        {"text": "[01] 算盘房 — 交班 + 取最后一份拨款单。", "next": "n_l1985_abacus_01",
         "require": {"not": {"flags": {"l_visited_abacus": true}}}},
        {"text": "[02] 锅炉房 — 烧掉一些东西。", "next": "n_l1985_boiler_01",
         "require": {"not": {"flags": {"l_visited_boiler": true}}}},
        {"text": "[03] 档案室 — 查 26 个签字人。", "next": "n_l1985_archive_01",
         "require": {"not": {"flags": {"l_visited_archive": true}}}},
        {"text": "[04] 湖边凉亭 — 见一个老朋友。", "next": "n_l1985_pavilion_01",
         "require": {"not": {"flags": {"l_visited_pavilion": true}}}},
        {"text": "[05] 直接去湖边。", "next": "n_l1985_lake_jump",
         "require": {"shifts_completed_min": 2}}
      ]
    },
    "n_l1985_lake_jump": {
      "scene": "ENDING_TRANSITION",
      "narrative": "(投湖瞬间 — 由 player.py 渲染三段式静默,本节点不应被玩家'看到'文字)",
      "choices": [
        {"text": "(自动)", "next": "E_LINMOU_RELEASE",
         "require": {"flags": {"l_intent_release": true}}},
        {"text": "(自动)", "next": "E_LINMOU_REGRET",
         "require": {"flags": {"l_intent_regret": true}}},
        {"text": "(自动)", "next": "E_LINMOU_GRIEVANCE",
         "require": {"flags": {"l_intent_grievance": true}}},
        {"text": "(自动)", "next": "E_LINMOU_EXPOSED",
         "require": {"flags": {"l_exposed": true}}}
      ]
    },
    "E_LINMOU_RELEASE": {
      "scene": "ENDING",
      "_lore_canon": {"must_die": true},
      "ending_type": "E_LINMOU_RELEASE",
      "narrative": "(释结局 — 林某带着释然投湖,执念变量 = release。Phase 4 后续填充。)",
      "choices": []
    },
    "E_LINMOU_REGRET": {
      "scene": "ENDING",
      "_lore_canon": {"must_die": true},
      "ending_type": "E_LINMOU_REGRET",
      "narrative": "(悔结局)",
      "choices": []
    },
    "E_LINMOU_GRIEVANCE": {
      "scene": "ENDING",
      "_lore_canon": {"must_die": true},
      "ending_type": "E_LINMOU_GRIEVANCE",
      "narrative": "(冤结局)",
      "choices": []
    },
    "E_LINMOU_EXPOSED": {
      "scene": "ENDING",
      "_lore_canon": {"must_die": true},
      "ending_type": "E_LINMOU_EXPOSED",
      "narrative": "(曝光结局 — 隐藏路线,被发现报警)",
      "choices": []
    }
  }
}
```

- [ ] **Step 2: 在 STORY_META.characters 加 linmou_1985**

```python
# tools/merge_fragments.py STORY_META.characters
"linmou_1985": {
    "label": "林副科长 · 1985-10-18 投湖前夜",
    "start_node": "n_l1985_entry",
    "initial_inv": ["蓝布人造革账册包", "26 联签拨款单复印件"],
    "initial_flags": {},
    "_description": "1985 年杭州二轻物资财务科副科长。投湖前 6 小时(20:00 → 02:00)。"
},
```

- [ ] **Step 3: merge + audit + commit**

```bash
python tools/merge_fragments.py
./tools/audit_all.sh
# audit_paths_linmou: INV-1 (entry → 占位 endings 全部 _lore_canon.must_die=true) 应通过
git add stories/hangzhou_yebanbaoan/_fragment_v7_linmou_1985.json tools/merge_fragments.py stories/hangzhou_yebanbaoan/tree.json
git commit -m "feat(linmou): Act 1 fragment 骨架(entry + picker + 4 ending 占位)"
```

---

### Task 4.2:算盘房地标(10 节点)

**Files:**
- Modify: `_fragment_v7_linmou_1985.json` 加 `n_l1985_abacus_01..10`

**剧本要点**(Lore Keeper 钦定):
- 接班同事(老李,16 年工龄,搪瓷缸抽烟)
- 算盘"啪"一声响,听到 26 个签字人之一(王某)在隔壁锅炉房咳嗽
- 关键选择点 1:**告诉老李拨款单的事 → l_intent_grievance**(冤,他会去举报但来不及)
- 关键选择点 2:**藏起拨款单 → l_intent_release**(释,你独自承担)
- 关键选择点 3:**塞进老李抽屉 → l_intent_regret**(悔,你后悔牵连他)
- 关键选择点 4:**让老李撞见复印件 → l_exposed**(曝光,被举报)
- 双向联动:`ending_seen: {杭州_v7, E_TRUTH}` → 老李说一句"前任的录音里听过你的名字"(玩家"已知答案的回响")

- [ ] **Step 1: 写 10 节点(参考 G-273 的 s1 fragment 节奏)**
- [ ] **Step 2: 加 n_l1985_abacus_01 入边到 picker(已有)**
- [ ] **Step 3: merge + audit_all + commit**

```bash
git commit -m "content(linmou): 算盘房地标 10 节点(老李交班 + 4 执念分支锚点)"
```

---

### Task 4.3:锅炉房地标(10 节点)

**剧本要点**:
- 王某在烧账本(他是 26 联签人之一)
- 关键选择:阻止 / 旁观 / 一起烧 / 报警
- Lore 锚:煤球炉余烬 + 来苏儿消毒水 + 廉价烟丝
- 双向联动:`ending_seen: E_BAD_DROWN` → 王某低声说"听说 1986 年钱塘江会沉一艘船"(玩家"已知未来")

- [ ] (3 step,同 4.2 模式)

---

### Task 4.4:档案室地标(10 节点)

**剧本要点**:
- 26 个签字人名单 + 各自身份
- 关键选择:复印 / 焚毁 / 偷一份 / 留原位
- Lore 锚:《浙江日报》1985-10-17 + 调拨红章 + 蓝布账册包
- 双向联动:`ending_seen: E_TRUTH` → 档案柜上有一个 G-273 的工牌(玩家见过的图标)

- [ ] (3 step)

---

### Task 4.5:湖边凉亭地标(10 节点)

**剧本要点**:
- 老朋友 = 张某(他是 26 联签的"内部人",真凶)
- 关键选择:对峙 / 分开喝酒 / 求他一同自首 / 殴打
- Lore 锚:雷峰塔风铃 + 雾里湖水腥味 + 末班船汽笛
- 双向联动:`ending_seen: E_DATA` → 张某身后影子像现代人(玩家见过)

- [ ] (3 step)

---

### Task 4.6:4 ending narrative 填充

**Files:**
- Modify: `_fragment_v7_linmou_1985.json` E_LINMOU_* 节点 narrative

每个 ending ~200-400 字,定调"鬼魂带着什么执念离开":
- **E_LINMOU_RELEASE(释)**:接受集体信念已死,独自抵账
- **E_LINMOU_REGRET(悔)**:把账册塞进老李抽屉,牵连他
- **E_LINMOU_GRIEVANCE(冤)**:拨款单被烧/被夺,带恨
- **E_LINMOU_EXPOSED(曝光)**:被同事举报,被抓后湖边自尽

- [ ] **Step 1-3: 填 4 ending,每个 commit**

---

### Task 4.7:投湖瞬间三段式静默(player.py 引擎)

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py` — 检测 `ending_type == "E_LINMOU_*"` 时,渲染三段静默

UX 决议(评审 § 5):
```
T+0.0s  对白逐字打完
T+0.3s  文字渐隐(每行 fade 100ms)
T+1.5s  纯黑屏
T+2.0s  水声 ASCII 涟漪
T+4.3s  「1985 年 10 月 18 日 · 西湖」 琥珀色
T+5.3s  返回主菜单
```

- [ ] **Step 1: 写测试(mock time.sleep + 截 stdout)**
- [ ] **Step 2: 加 `_render_lake_jump_silence()` helper**
- [ ] **Step 3: ending 渲染入口判断 ending_type 前缀 → 调 helper**
- [ ] **Step 4: commit**

---

## Phase 5:集成(主菜单三态 + 双向反向)

### Task 5.1:`_select_character` 三态化

**Files:**
- Modify: `src/ghost_story_factory/v5/player.py:694-720`
- Test: `tests/test_select_character.py`(新建)

- [ ] **Step 1: 改签名加 save_manager 参数**

```python
def _select_character(characters, save_manager=None):
    """v8 三态主菜单:locked / unlockable / playable。"""
    # ...
    keys = list(characters.keys())
    unlocked = set(save_manager.unlocked_characters) if save_manager else set(keys)
    seen_endings = save_manager.endings_seen if save_manager else []

    print(bold(magenta("\n  可玩角色:")))
    for i, k in enumerate(keys, start=1):
        cdef = characters[k]
        label = cdef.get("label", k)
        if k in unlocked:
            # playable 或 unlockable
            stars = sum(1 for e in seen_endings if e.startswith(f"E_{k.upper().replace('-', '_')}_"))
            badge = "★" * stars if stars else "  ! 新解锁"
            print(f"  {green(str(i))}. {label}  {dim(badge)}")
        else:
            # locked
            unlock_hint = cdef.get("unlock_hint", "")
            print(f"  {dim(str(i))}. {dim('???' + ' ' * 4)}  {dim('🔒 ' + unlock_hint)}")
    # 选择逻辑:锁定的不能选,提示
    # ...
```

- [ ] **Step 2: 调用点改(play() 内传 save_manager)**

- [ ] **Step 3: 测试 + commit**

---

### Task 5.2:G-273 → linmou 反向影响(双向联动 a)

**Files:**
- Modify: `_fragment_v7_linmou_1985.json` 4 个地标各加 1 条反应 variant

每个地标 1 个节点(共 4 节点)的 `narrative_variants` 数组开头插:

```json
{
  "if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_TRUTH"}},
  "text": "(玩家通关 G-273 E_TRUTH 后回来玩 linmou 的回响 — 此处 narrative 增加'已知答案'的隐喻)..."
}
```

- [ ] **Step 1-4: 4 节点各加 1 反应 variant**
- [ ] merge + audit + commit

---

### Task 5.3:linmou → G-273 反向影响(双向联动 b)

**Files:**
- Modify: `_fragment_v7_shared.json` 选 3-5 个 G-273 节点加 linmou ending 反应

候选节点(评审 § 5 决议):**字体从灰转琥珀** — 但 CLI/TUI 实现简化为额外 narrative_variant。

例如 `n_npc_corrosion_face` 加:
```json
{
  "if": {"ending_seen": {"story_id": "杭州_v7", "ending_id": "E_LINMOU_RELEASE"}},
  "text": "铜锈侧脸这次没有抬头。\n\n他坐在湖边,你认得那个轮廓——\n\n是 1985-10-18 那一夜的林副科长。\n\n他对你说:'小赵,我那一夜是带着释然走的。\n\n你今晚可以走得更早。'"
}
```

3-5 节点候选:`n_npc_corrosion_face` / `n_scene_lost_archive` / `n_npc_predecessor_voice` / `n_landmark_picker` / `n_scene_red_telephone`

- [ ] **Step 1-3: 3 节点各加 1 反应 variant**
- [ ] **Step 4: 在 STORY_META.reaction_contracts.foreshadows 加 cross-character contract**(若 audit_reactions 要求)
- [ ] merge + audit + commit

---

### Task 5.4:端到端验收

- [ ] **Step 1: 全套审计 5/5 全绿**
```bash
./tools/audit_all.sh
```

- [ ] **Step 2: 全套测试 PASS**
```bash
pytest tests/ -q
```

- [ ] **Step 3: 手测 1 — 锁定主菜单**
- 删 ~/.ghost_save.json
- 启动游戏 → 主菜单 → 应该只有 G-273 可选,linmou 显示 🔒

- [ ] **Step 4: 手测 2 — 解锁 + 玩 linmou**
- 命令行注入 save:`echo '{"version":5,"unlocked_characters":["G-273","linmou_1985"]}' > ~/.ghost_save.json`
- 启动 → linmou 显示 "! 新解锁"
- 选 linmou → 进入 1985 财务科 → 玩到任一 ending
- 投湖三段静默应正确播放

- [ ] **Step 5: 手测 3 — 双向联动**
- 玩 linmou → 通关 E_LINMOU_RELEASE
- 重启,玩 G-273 → 进 n_npc_corrosion_face → 应看到林某反应 variant
- 删 save 重启,玩 G-273 通关 E_TRUTH → 玩 linmou → 算盘房应有"已知回响"

- [ ] **Step 6: 生成快照(QA 决议)**
```bash
python tools/path_explorer.py --story-scope linmou_1985 --hash > tests/snapshots/linmou_act1_paths.json
git add tests/snapshots/
git commit -m "chore(snapshot): linmou Act 1 路径快照(防 P1 回归)"
```

---

## Validation Checklist(P0 完成判定)

| 项 | 验证 |
|---|---|
| `ending_seen` clause | `pytest tests/test_ending_seen.py` 6 PASS |
| `endings_seen` schema 升级 | 旧 list 自动迁移到 dict[杭州_v7] |
| `audit_paths_linmou` | INV-1~4 全过 |
| `audit_reactions` cross-character | DEAD_ENDING_SEEN 检测可用 |
| Lore canon 固化 | `data/linmou_act1_lore.json` + ADR-009 |
| linmou Act 1 内容 | 50 节点 / 4 ending / 必死铁律不变 |
| 三段式投湖 | 手测正确播放 |
| 主菜单三态 | locked / unlockable / playable 正确 |
| 双向联动 a | G-273 通关 → linmou 节点切档 |
| 双向联动 b | linmou 通关 → G-273 节点切档 |
| Act 1 快照 | tests/snapshots/linmou_act1_paths.json 生成 |

---

## 风险 & 回滚

- **风险 1**:Phase 4 内容创作工作量大(~5000 字),容易疲劳
  - **缓解**:每地标 = 1 commit,可中途暂停
- **风险 2**:`endings_seen` schema 升级可能破坏现有玩家存档
  - **缓解**:Task 1.2 的迁移测试是必跑;旧 list 自动转 dict[杭州_v7]
- **风险 3**:三段式静默动画在 TUI 模式可能不工作
  - **缓解**:Task 4.7 先做 CLI,TUI 端单独 follow-up
- **风险 4**:audit_paths_linmou INV-2 在 P0 是 trivial(Act 2/3 不存在),P1 上线时要立刻补
  - **缓解**:Task 4.7 完成后立即把 INV-2 真实化

---

## 后续(P1 — Act 2/3,本 plan 范围之外)

- Act 2 鬼身补票(1986-08-17 沉船,~4000 字)
- Act 3 执念结局扩展(每 ending ~1000 字补充)
- 第三角色(沈玉茹 — Meta 提议) / yeh_1991(已存 roster)
- 收集本三 Tab 架构(横向 [G-273] [林某] [沈玉茹])
- 周目计数器 UI(右上角 Loop 1/3)
