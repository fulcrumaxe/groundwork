"""Lesson-facing renderers: leveled explainers and purpose notes.

Pure HTML builders over lesson dicts — no HTTP, no page chrome.
The web Handler calls these so lesson UI never lives in web.py.
"""
from __future__ import annotations

import html


def render_levels(lesson: dict, mastery: float, attempts: int,
                    level_override: str, base_path: str) -> str:
    """Leveled explainer with tabs; auto-places from mastery by default."""
    from . import explain as explainmod
    levels = explainmod.levels_for(lesson)
    if level_override in ("1", "2", "3", "4"):
        active = int(level_override)
    else:
        active = explainmod.auto_level(mastery or 0.0, attempts)
    tabs = []
    for n in ("auto", "1", "2", "3", "4"):
        label = "Auto" if n == "auto" else explainmod.LEVEL_TITLES[int(n)]
        mark = " <b>(you are here)</b>" if (
            (n == "auto" and level_override not in ("1", "2", "3", "4")) or
            (n != "auto" and int(n) == active and
             level_override in ("1", "2", "3", "4"))) else ""
        tabs.append(f"<a href='{base_path}?level={n}'>{label}</a>{mark}")
    out = [f"<p><small>Explain it {'simply' if active <= 2 else 'technically'}: "
           f"{' · '.join(tabs)}</small></p>"]
    lv = next(L for L in levels if L["n"] == active)
    out.append(f"<h4>{html.escape(lv['title'])}</h4>")
    for blk in lv["blocks"]:
        body = html.escape(blk["b"])
        if blk.get("pre"):
            out.append(f"<h5>{html.escape(blk['h'])}</h5><pre>{body}</pre>")
        else:
            out.append(f"<h5>{html.escape(blk['h'])}</h5>"
                       f"<p>{body.replace(chr(10), '<br>')}</p>")
    if lv.get("code") and not any(b.get("pre") for b in lv["blocks"]):
        out.append(f"<details><summary>Show me the code</summary>"
                   f"<pre>{html.escape(lv['code'])}</pre></details>")
    return "".join(out)


def why_html(card) -> str:
    from . import cards as cardsmod
    from . import pipeline as pipelinemod
    why = cardsmod._payload(card).get("why", "")
    if not why:
        return ""
    if why == pipelinemod.UNSTATED_WHY:
        return (f"<p class='unstated'><small><b>Why this matters:</b> "
                f"{html.escape(why)}</small></p>")
    return f"<p><small><b>Why this matters:</b> {html.escape(why)}</small></p>"


def slug(text: str) -> str:
    """URL-fragment-safe anchor slug for a lesson section."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    out = "-".join(filter(None, out.split("-")))
    return out or "lesson"


def submissions_html(entries: list[dict]) -> str:
    """Submission history beneath a lesson's exercises."""
    if not entries:
        return "<p><small>No attempts yet — your tries will appear here.</small></p>"
    items = []
    for e in entries[:10]:
        good = (e.get("grade") or 0) >= 4
        cls = "ok" if good else "stale"
        mark = "✓" if good else "✗"
        sub = (e.get("submission") or "").strip()
        excerpt = html.escape(sub[:200] + ("…" if len(sub) > 200 else ""))
        if not sub:
            excerpt = "<i>no text recorded</i>"
        items.append(
            f"<p class='{cls}'><small>{mark} grade {e.get('grade')}/5,"
            f" confidence {e.get('confidence')}/5,"
            f" {html.escape(e.get('reviewed_at') or '')}<br>"
            f"tried: <code>{excerpt}</code></small></p>")
    more = (f"<p><small>…and {len(entries) - 10} more.</small></p>"
            if len(entries) > 10 else "")
    return ("<details><summary>Past attempts "
            f"({len(entries)})</summary>{''.join(items)}{more}</details>")
