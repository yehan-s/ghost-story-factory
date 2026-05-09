"""档案视图渲染 — s 键打开的"剧本元数据档案"。

四张表合并显示:
  1. 伏笔档案(foreshadows + shards)
  2. 推论(deductions)
  3. 时间年表(timeline)
  4. NPC 人物志(npcs)

按"已发现/已解开/未知"区分显示密度,未触达内容显示为 ??? 占位。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _format_shard_progress(
    tree: Dict[str, Any], save_manager, story_id: str, slot_id: str,
) -> str:
    """返回 'N/M' 或空串(若该 foreshadow 没有 shards)。"""
    if not save_manager:
        return ""
    if not hasattr(save_manager, "shard_progress"):
        return ""
    try:
        c, t = save_manager.shard_progress(tree, story_id, slot_id)
    except (KeyError, TypeError, ValueError):
        return ""
    if t == 0:
        return ""
    return f"{c}/{t}"


def render_archive_cli(tree, save_manager, story_id: str) -> None:
    """直接 print 到 stdout(CLI 用)。
    渲染顺序:主题 → 推论 → 伏笔档案 → 时间年表 → NPC 人物志 → 成就。
    """
    from ghost_story_factory.v5.player import (
        bold, cyan, dim, green, red, yellow, blue, magenta,
    )
    foreshadows = (tree or {}).get("foreshadows") or {}
    deductions = (tree or {}).get("deductions") or {}
    timeline = (tree or {}).get("timeline") or []
    npcs = (tree or {}).get("npcs") or {}
    themes = (tree or {}).get("themes") or {}
    achievements = (tree or {}).get("achievements") or {}

    seen_set = set(save_manager.data.get("foreshadows_seen", {}).get(story_id, []))
    resolved_set = set(
        save_manager.data.get("foreshadows_resolved", {}).get(story_id, [])
    )
    deductions_resolved = set(
        save_manager.data.get("deductions_resolved", {}).get(story_id, [])
    )
    achievements_unlocked = set(save_manager.data.get("achievements_unlocked") or [])

    # 颜色映射(主题颜色)
    _color_map = {
        "magenta": magenta, "red": red, "cyan": cyan, "yellow": yellow,
        "blue": blue, "green": green,
    }

    # === 主题宏观进度 ===
    # 反应契约(ADR-008):反向影响索引,通关后玩家可 trace 自己的发现路径
    reaction_contracts = (tree or {}).get("reaction_contracts") or {}
    ded_contracts = reaction_contracts.get("deductions") or {}
    fs_contracts = reaction_contracts.get("foreshadows") or {}
    theme_contracts = reaction_contracts.get("themes") or {}

    if themes:
        print()
        print(bold(yellow("  ── 主题(母题集合) ──")))
        for theme_id, meta in themes.items():
            name = meta.get("name", theme_id)
            icon = meta.get("icon", "·")
            color_fn = _color_map.get(meta.get("color", ""), lambda s: s)
            manifests = meta.get("manifestations") or []
            res = sum(1 for m in manifests if m in resolved_set)
            seen = sum(1 for m in manifests if m in seen_set)
            total = len(manifests)
            if seen == 0:
                print(f"  {dim(icon)} {dim(name)}  {dim(f'(0/{total})')}")
            else:
                bar = color_fn(icon)
                if res == total and total > 0:
                    line = f"  {bar} {bold(color_fn(name))}  {color_fn(f'(✦ 通透 {res}/{total})')}"
                else:
                    line = f"  {bar} {bold(name)}  {dim(f'({seen}/{total} 已发现 · {res}/{total} 已解)')}"
                print(line)
                desc = meta.get("description", "")
                if desc and seen > 0:
                    print(f"    {dim(desc)}")
                # 母题"通透"才显示反向影响节点(避免剧透)
                if res == total and total > 0:
                    th_consumers = (theme_contracts.get(theme_id) or {}).get("consumer_nodes") or []
                    if th_consumers:
                        print(f"    {dim('↳ 影响节点:')} {dim(', '.join(th_consumers))}")

    # === 推论 ===
    if deductions:
        revealed = [d for d in deductions if d in deductions_resolved]
        print()
        print(bold(magenta(
            f"  ── 推论({len(revealed)}/{len(deductions)})── "
            f"两条以上伏笔解开后,会自动合并"
        )))
        for ded_id, meta in deductions.items():
            title = meta.get("title", ded_id)
            if ded_id in deductions_resolved:
                summary = meta.get("summary", "")
                print(f"  {magenta('⟁')} {bold(title)}")
                if summary:
                    print(f"    {dim(summary)}")
                # 反向影响索引:已解开 → 影响哪些节点
                consumers = (ded_contracts.get(ded_id) or {}).get("consumer_nodes") or []
                if consumers:
                    print(f"    {dim('↳ 影响节点:')} {dim(', '.join(consumers))}")
            else:
                # 显示前置伏笔解开了几个
                req = list(meta.get("requires_resolved") or [])
                got = sum(1 for r in req if r in resolved_set)
                print(f"  {dim('⟁')} {dim(title)}  {dim(f'(前置 {got}/{len(req)} 已解)')}")

    # === 伏笔档案 ===
    if foreshadows:
        # 按 year 排序,未发现的折叠
        ordered = sorted(
            foreshadows.items(),
            key=lambda kv: kv[1].get("year", 9999),
        )
        print()
        print(bold(cyan(
            f"  ── 档案 · 伏笔({len(seen_set)}/{len(foreshadows)} 已发现 · "
            f"{len(resolved_set)}/{len(foreshadows)} 已解开)──"
        )))
        for slot_id, meta in ordered:
            title = meta.get("title", slot_id)
            year = meta.get("year")
            theme = meta.get("theme", "")
            year_tag = f"[{year}]" if year else ""
            theme_tag = f"《{theme}》" if theme else ""
            shard_str = _format_shard_progress(tree, save_manager, story_id, slot_id)
            shard_tag = f"  碎片 {shard_str}" if shard_str else ""
            if slot_id in resolved_set:
                summary = meta.get("summary_resolved", "")
                print(f"  {green('✦')} {dim(year_tag)} {bold(title)} {dim(theme_tag)}")
                if summary:
                    print(f"    {dim(summary)}")
                # 反向影响索引(ADR-008):已解开伏笔影响哪些节点
                fs_consumers = (fs_contracts.get(slot_id) or {}).get("consumer_nodes") or []
                if fs_consumers:
                    print(f"    {dim('↳ 影响节点:')} {dim(', '.join(fs_consumers))}")
                # 展示已收的碎片(全 resolved 时)
                shards = meta.get("shards") or []
                if shards:
                    for sh in shards:
                        sh_label = sh.get("label", sh.get("id", ""))
                        sh_text = sh.get("text", "")
                        print(f"    {green('·')} {dim(sh_label)}: {dim(sh_text)}")
            elif slot_id in seen_set:
                summary = meta.get("summary_locked", "")
                print(f"  {cyan('?')} {dim(year_tag)} {bold(title)} {dim(theme_tag)} {dim(shard_tag)}")
                if summary:
                    print(f"    {dim(summary)}")
                # 展示已收的碎片
                got_shards = save_manager.get_shards_collected(story_id, slot_id)
                if got_shards:
                    shards_meta = {s.get("id"): s for s in (meta.get("shards") or [])}
                    for sid in got_shards:
                        sh = shards_meta.get(sid) or {}
                        sh_label = sh.get("label", sid)
                        sh_text = sh.get("text", "")
                        print(f"    {cyan('·')} {dim(sh_label)}: {dim(sh_text)}")
            else:
                # 未发现 — 标题用问号占位 + 年份隐藏
                print(f"  {dim('???')} {dim('???')}")

    # === 时间年表 ===
    if timeline:
        print()
        print(bold(yellow("  ── 时间年表 ──")))
        for entry in timeline:
            year = entry.get("year", "????")
            date = entry.get("date", "")
            event = entry.get("event", "")
            related = entry.get("related_foreshadows") or []
            # 该年事件是否"已知" — 如果 related 里有任意一条 seen,就显示
            shown = (not related) or any(r in seen_set for r in related)
            tags = entry.get("tags") or []
            tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
            if shown:
                date_str = date if date else f"{year}"
                print(f"  {yellow('·')} {bold(str(date_str))}  {event}  {dim(tag_str)}")
            else:
                print(f"  {dim('·')} {dim(str(year))}  {dim('???')}")

    # === 成就 ===
    if achievements:
        print()
        print(bold(yellow(
            f"  ── 成就({len(achievements_unlocked)}/{len(achievements)})──"
        )))
        for ach_id, meta in achievements.items():
            icon = meta.get("icon", "🏆")
            name = meta.get("name", ach_id)
            desc = meta.get("description", "")
            if ach_id in achievements_unlocked:
                print(f"  {yellow(icon)} {bold(name)}")
                if desc:
                    print(f"    {dim(desc)}")
            else:
                print(f"  {dim(icon)} {dim(name)}")
                if desc:
                    print(f"    {dim(desc)}")

    # === NPC 人物志 ===
    if npcs:
        # 玩家见过的 NPC = npc_locations 里的 keys ∪ tree 的 default location
        # 简化:全部 npcs 都列出,但未关联任何 seen foreshadow 的标"未知"
        npc_to_fs: Dict[str, List[str]] = {}
        for slot, meta in foreshadows.items():
            for ref in (meta.get("related_npcs") or []):
                npc_to_fs.setdefault(ref, []).append(slot)
        # 也从 timeline 反向索引
        for entry in timeline:
            for ref in (entry.get("related_npcs") or []):
                npc_to_fs.setdefault(ref, [])
        print()
        print(bold(green("  ── 人物志 ──")))
        for npc_id, info in npcs.items():
            label = info.get("label", npc_id)
            death_year = info.get("death_year")
            real_name = info.get("real_name")
            related_fs = info.get("related_foreshadows") or npc_to_fs.get(npc_id, [])
            relations = info.get("relations") or {}
            # 若有任一 seen,显示;否则隐藏(不剧透 NPC 真名)
            if related_fs and any(r in seen_set for r in related_fs):
                year_str = f"({death_year}†)" if death_year else ""
                rn = f" · 真名: {real_name}" if (real_name and any(r in resolved_set for r in related_fs)) else ""
                print(f"  {green('●')} {bold(label)} {dim(year_str)}{dim(rn)}")
                # 关系图(任一 resolved 才解锁)
                if relations and any(r in resolved_set for r in related_fs):
                    for rel_npc, rel_type in relations.items():
                        rel_label = (npcs.get(rel_npc) or {}).get("label", rel_npc)
                        print(f"      {dim('→')} {dim(rel_type)}: {dim(rel_label)}")
            else:
                print(f"  {dim('○')} {bold(label)}")
        print()


def render_archive_lines_rich(tree, save_manager, story_id: str) -> List[str]:
    """返回 Rich markup 行列表(TUI 用)。"""
    foreshadows = (tree or {}).get("foreshadows") or {}
    deductions = (tree or {}).get("deductions") or {}
    timeline = (tree or {}).get("timeline") or []
    npcs = (tree or {}).get("npcs") or {}
    themes = (tree or {}).get("themes") or {}
    achievements = (tree or {}).get("achievements") or {}

    seen_set = set(save_manager.data.get("foreshadows_seen", {}).get(story_id, []))
    resolved_set = set(
        save_manager.data.get("foreshadows_resolved", {}).get(story_id, [])
    )
    deductions_resolved = set(
        save_manager.data.get("deductions_resolved", {}).get(story_id, [])
    )
    achievements_unlocked = set(save_manager.data.get("achievements_unlocked") or [])

    reaction_contracts = (tree or {}).get("reaction_contracts") or {}
    ded_contracts = reaction_contracts.get("deductions") or {}
    fs_contracts = reaction_contracts.get("foreshadows") or {}
    theme_contracts = reaction_contracts.get("themes") or {}

    rich_color_map = {
        "magenta": "magenta",
        "red": "red",
        "cyan": "cyan",
        "yellow": "yellow",
        "blue": "blue",
        "green": "green",
    }

    out: List[str] = []

    # 主题宏观进度。TUI 必须和 CLI 同步,否则玩家按 s 看到的是半份档案。
    if themes:
        out.append("")
        out.append("[bold yellow]── 主题(母题集合) ──[/]")
        for theme_id, meta in themes.items():
            name = meta.get("name", theme_id)
            icon = meta.get("icon", "·")
            color = rich_color_map.get(meta.get("color", ""), "white")
            manifests = meta.get("manifestations") or []
            resolved_count = sum(1 for m in manifests if m in resolved_set)
            seen_count = sum(1 for m in manifests if m in seen_set)
            total = len(manifests)
            if seen_count == 0:
                out.append(f"  [dim]{icon} {name}  (0/{total})[/]")
                continue
            if resolved_count == total and total > 0:
                out.append(
                    f"  [{color}]{icon}[/] [bold {color}]{name}[/]  "
                    f"[{color}](✦ 通透 {resolved_count}/{total})[/]"
                )
            else:
                out.append(
                    f"  [{color}]{icon}[/] [bold]{name}[/]  "
                    f"[dim]({seen_count}/{total} 已发现 · "
                    f"{resolved_count}/{total} 已解)[/]"
                )
            desc = meta.get("description", "")
            if desc:
                out.append(f"    [dim]{desc}[/]")
            if resolved_count == total and total > 0:
                consumers = (
                    (theme_contracts.get(theme_id) or {}).get("consumer_nodes") or []
                )
                if consumers:
                    out.append(f"    [dim]↳ 影响节点: {', '.join(consumers)}[/]")

    # 推论
    if deductions:
        revealed = [d for d in deductions if d in deductions_resolved]
        out.append("")
        out.append(
            f"[bold magenta]── 推论({len(revealed)}/{len(deductions)})── "
            f"两条以上伏笔解开后,会自动合并[/]"
        )
        for ded_id, meta in deductions.items():
            title = meta.get("title", ded_id)
            if ded_id in deductions_resolved:
                out.append(f"  [magenta]⟁[/] [bold]{title}[/]")
                summary = meta.get("summary", "")
                if summary:
                    out.append(f"    [dim]{summary}[/]")
                consumers = (ded_contracts.get(ded_id) or {}).get("consumer_nodes") or []
                if consumers:
                    out.append(f"    [dim]↳ 影响节点: {', '.join(consumers)}[/]")
            else:
                req = list(meta.get("requires_resolved") or [])
                got = sum(1 for r in req if r in resolved_set)
                out.append(f"  [dim]⟁ {title}  (前置 {got}/{len(req)} 已解)[/]")

    # 伏笔档案
    if foreshadows:
        out.append("")
        out.append(
            f"[bold cyan]── 档案 · 伏笔("
            f"{len(seen_set)}/{len(foreshadows)} 已发现 · "
            f"{len(resolved_set)}/{len(foreshadows)} 已解开)──[/]"
        )
        ordered = sorted(
            foreshadows.items(),
            key=lambda kv: kv[1].get("year", 9999),
        )
        for slot_id, meta in ordered:
            title = meta.get("title", slot_id)
            year = meta.get("year")
            theme = meta.get("theme", "")
            year_tag = f"[{year}]" if year else ""
            theme_tag = f"《{theme}》" if theme else ""
            shard_str = _format_shard_progress(tree, save_manager, story_id, slot_id)
            shard_tag = f"  碎片 {shard_str}" if shard_str else ""
            if slot_id in resolved_set:
                out.append(
                    f"  [green]✦[/] [dim]{year_tag}[/] [bold]{title}[/] [dim]{theme_tag}[/]"
                )
                summary = meta.get("summary_resolved", "")
                if summary:
                    out.append(f"    [dim]{summary}[/]")
                consumers = (fs_contracts.get(slot_id) or {}).get("consumer_nodes") or []
                if consumers:
                    out.append(f"    [dim]↳ 影响节点: {', '.join(consumers)}[/]")
                for shard in meta.get("shards") or []:
                    sh_label = shard.get("label", shard.get("id", ""))
                    sh_text = shard.get("text", "")
                    out.append(f"    [green]·[/] [dim]{sh_label}: {sh_text}[/]")
            elif slot_id in seen_set:
                out.append(
                    f"  [cyan]?[/] [dim]{year_tag}[/] [bold]{title}[/] "
                    f"[dim]{theme_tag} {shard_tag}[/]"
                )
                summary = meta.get("summary_locked", "")
                if summary:
                    out.append(f"    [dim]{summary}[/]")
                if hasattr(save_manager, "get_shards_collected"):
                    got_shards = save_manager.get_shards_collected(story_id, slot_id)
                else:
                    got_shards = []
                shards_meta = {
                    s.get("id"): s for s in (meta.get("shards") or []) if s.get("id")
                }
                for sid in got_shards:
                    shard = shards_meta.get(sid) or {}
                    sh_label = shard.get("label", sid)
                    sh_text = shard.get("text", "")
                    out.append(f"    [cyan]·[/] [dim]{sh_label}: {sh_text}[/]")
            else:
                out.append("  [dim]??? ???[/]")

    # 时间年表
    if timeline:
        out.append("")
        out.append("[bold yellow]── 时间年表 ──[/]")
        for entry in timeline:
            year = entry.get("year", "????")
            date = entry.get("date", "")
            event = entry.get("event", "")
            related = entry.get("related_foreshadows") or []
            shown = (not related) or any(r in seen_set for r in related)
            tags = entry.get("tags") or []
            tag_str = " ".join(f"#{t}" for t in tags) if tags else ""
            if shown:
                date_str = date if date else f"{year}"
                out.append(f"  [yellow]·[/] [bold]{date_str}[/]  {event}  [dim]{tag_str}[/]")
            else:
                out.append(f"  [dim]·  {year}  ???[/]")

    # 成就
    if achievements:
        out.append("")
        out.append(
            f"[bold yellow]── 成就({len(achievements_unlocked)}/"
            f"{len(achievements)})──[/]"
        )
        for ach_id, meta in achievements.items():
            icon = meta.get("icon", "🏆")
            name = meta.get("name", ach_id)
            desc = meta.get("description", "")
            if ach_id in achievements_unlocked:
                out.append(f"  [yellow]{icon}[/] [bold]{name}[/]")
                if desc:
                    out.append(f"    [dim]{desc}[/]")
            else:
                out.append(f"  [dim]{icon} {name}[/]")
                if desc:
                    out.append(f"    [dim]{desc}[/]")

    # NPC 人物志
    if npcs:
        npc_to_fs: Dict[str, List[str]] = {}
        for slot, meta in foreshadows.items():
            for ref in (meta.get("related_npcs") or []):
                npc_to_fs.setdefault(ref, []).append(slot)
        for entry in timeline:
            for ref in (entry.get("related_npcs") or []):
                npc_to_fs.setdefault(ref, [])

        out.append("")
        out.append("[bold green]── 人物志 ──[/]")
        for npc_id, info in npcs.items():
            label = info.get("label", npc_id)
            death_year = info.get("death_year")
            real_name = info.get("real_name")
            related_fs = info.get("related_foreshadows") or npc_to_fs.get(npc_id, [])
            relations = info.get("relations") or {}
            known = bool(related_fs and any(r in seen_set for r in related_fs))
            if known:
                year_str = f"({death_year}†)" if death_year else ""
                show_real_name = real_name and any(r in resolved_set for r in related_fs)
                rn = f" · 真名: {real_name}" if show_real_name else ""
                out.append(f"  [green]●[/] [bold]{label}[/] [dim]{year_str}{rn}[/]")
                if relations and any(r in resolved_set for r in related_fs):
                    for rel_npc, rel_type in relations.items():
                        rel_label = (npcs.get(rel_npc) or {}).get("label", rel_npc)
                        out.append(f"      [dim]→ {rel_type}: {rel_label}[/]")
            else:
                out.append(f"  [dim]○[/] [bold]{label}[/]")

    return out
