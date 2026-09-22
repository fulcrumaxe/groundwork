"""Lesson-facing renderers: leveled explainers and purpose notes.

Pure HTML builders over lesson dicts — no HTTP, no page chrome.
The web Handler calls these so lesson UI never lives in web.py.
"""
from __future__ import annotations

import html

from . import glossary as glossmod
from . import verdicts as verdictsmod


def render_levels(lesson: dict, mastery: float, attempts: int,
                    level_override: str, base_path: str, owned=None,
                    order: str = "definition", symbols=None,
                    sym_mid: str = "", replay_step=None,
                    lesson_commit: str = "",
                    current_commit: str = "", recent=None) -> str:
    """Leveled explainer with tabs; auto-places from mastery by default.

    ``recent`` is an optional oldest-first list of (grade, confidence)
    pairs (I-122, ``explcalib.recent_from_rows``); it nudges the auto
    placement for overconfident/underconfident streaks. ``None``/empty
    keeps the legacy ``explain.auto_level`` placement.

    ``owned`` is an optional list of sibling lesson dicts the learner
    already masters; when two or more are given an elaboration drill
    connects this concept to them (F-59). ``None``/empty renders the
    legacy page with no drill.

    ``symbols`` is an optional per-page symbol index (I-104,
    ``symlinks.build_index``) scoped by ``sym_mid``; known symbol
    mentions link to their lesson sections. Absent/empty renders the
    legacy page byte-identical.
    """
    from . import codelines as codelinesmod
    from . import dualcode as dualmod
    from . import elaboration as elabmod
    from . import explain as explainmod
    from . import explainflip as flipmod
    from . import fading as fadingmod
    from . import predict as predictmod
    from . import selfexplain as semod
    from . import symlinks as symmod
    from . import replay as replaymod
    from . import runinputs as runinputsmod
    from . import srccollapse as srcmod
    from . import tryprompts as trymod
    from . import explcalib as explcalibmod
    from . import lessonver as lessonvermod
    from . import lessondiff as lessondiffmod
    levels = explainmod.levels_for(lesson)
    order = flipmod.normalize_order(order)
    osuffix = "" if order == "definition" else f"&order={order}"
    if level_override in ("1", "2", "3", "4"):
        active = int(level_override)
    else:
        # I-122: recent calibration nudges auto-place; no data = legacy.
        active = explcalibmod.pick_level(mastery or 0.0, attempts, recent)
    tabs = []
    for n in ("auto", "1", "2", "3", "4"):
        label = "Auto" if n == "auto" else explainmod.LEVEL_TITLES[int(n)]
        mark = " <b>(you are here)</b>" if (
            (n == "auto" and level_override not in ("1", "2", "3", "4")) or
            (n != "auto" and int(n) == active and
             level_override in ("1", "2", "3", "4"))) else ""
        tabs.append(f"<a href='{base_path}?level={n}{osuffix}'>{label}</a>{mark}")
    # I-115/I-116: version banner then version diff; "" keeps bytes.
    ver = (lessonvermod.banner_html(
        lessonvermod.lesson_commit_of(lesson, lesson_commit), current_commit)
        + lessondiffmod.lesson_block(lesson))
    out = [ver + f"<p><small>Explain it {'simply' if active <= 2 else 'technically'}: "
           f"{' · '.join(tabs)}</small></p>" + flipmod.toggle_html(base_path, level_override, order)]
    lv = next(L for L in levels if L["n"] == active)
    out.append(f"<h4>{html.escape(lv['title'])}</h4>")
    sym_index = symbols if isinstance(symbols, dict) else {}
    sym_scope = sym_mid if isinstance(sym_mid, str) else ""
    shown = list(flipmod.reorder_blocks(lv["blocks"], order))
    for i, blk in enumerate(shown):
        body = glossmod.gloss_html(blk["b"])
        if blk.get("pre"):
            body = (srcmod.block_html(blk["b"]) or
                    f"<pre>{codelinesmod.numbered_html(blk['b'])}</pre>")
            body = symmod.annotate_code(body, sym_index, sym_scope)
            out.append(f"<h5>{html.escape(blk['h'])}</h5>{body}")
        else:
            body = symmod.link_symbols(body, sym_index, sym_scope)
            out.append(f"<h5>{html.escape(blk['h'])}</h5>"
                       f"<p>{body.replace(chr(10), '<br>')}</p>")
        # I-112: micro-prompt between paragraphs, never after the last.
        if i < len(shown) - 1:
            micro = trymod.block_prompt_html(i, blk)
            if micro:
                out.append(micro)
    # F-60: the generated lesson's key ideas as diagram + trace.
    how = [s for s in (lesson.get("how") or [])
           if isinstance(s, str) and s.strip()]
    dc = lesson.get("dualcode")
    dc = dc if isinstance(dc, dict) else {}
    steps = [s for s in (dc.get("steps") or how)
             if isinstance(s, str) and s.strip()]
    # I-105: stepped replay wins when a measured trace exists; the
    # full pack stays as the legacy branch for traceless lessons.
    replay_block = replaymod.replay_html(lesson, replay_step, base_path)
    if replay_block:
        out.append(replay_block)
    elif steps:
        pack = dualmod.pack_html(
            lesson.get("name") or "",
            (lesson.get("summary") or "").splitlines()[0][:200],
            steps, dc.get("states") or [], wrapper="div")
        if pack:
            out.append(pack)
    if lv.get("code") and not any(b.get("pre") for b in lv["blocks"]):
        # F-64: snippets hide under a predict-then-reveal cover.
        cover = predictmod.cover_html(
            lv["code"], _code_lang(lesson.get("file") or ""))
        if predictmod.is_covered(cover):
            out.append(cover)
        else:
            snippet = lv["code"]
            if srcmod.is_long(snippet):
                out.append(srcmod.block_html(snippet))
            else:
                out.append(
                    f"<details><summary>Show me the code</summary>"
                    f"<pre>{codelinesmod.numbered_html(snippet)}</pre></details>")
    # F-57: support fades with practice — full steps live above, so the
    # faded section only appears once the learner has attempts.
    try:
        tries = int(attempts or 0)
    except (TypeError, ValueError):
        tries = 0
    if how and tries >= 1:
        seq = fadingmod.fade_sequence(how)
        if len(seq) == 3:
            out.append("<h5>Faded recall</h5>"
                       + fadingmod.fading_html([seq[2] if tries >= 3 else seq[1]]))
    # F-58: self-explanation prompts under the worked steps.
    sexplain = semod.prompts_html(semod.selfexplain_prompts(how))
    if sexplain:
        out.append("<h5>Explain it back</h5>" + sexplain)
    # I-106: run the worked example with the learner's own inputs.
    ri = runinputsmod.runinputs_html(lesson)
    if ri:
        out.append("<h5>Try your own inputs</h5>" + ri)
    # F-59: connect this concept to mastered siblings when given.
    try:
        owned_list = [o for o in (owned or []) if isinstance(o, dict)]
    except TypeError:
        owned_list = []
    if owned_list:
        drill = elabmod.elaboration_drill(
            {"name": lesson.get("name") or "",
             "summary": lesson.get("summary") or ""}, owned_list)
        if drill.get("partners"):
            out.append(elabmod.drill_html(drill, wrapper="div"))
    return "".join(out)


def owned_lessons(lesson_map: dict, mastery_of: dict, node: str) -> list:
    """Sibling lessons the learner masters (F-59 elaboration partners).

    Mastery >= 0.85 is the top auto-level tier ("owns it"); those
    siblings feed the elaboration drill for ``node``. Never raises.
    """
    try:
        if not isinstance(lesson_map, dict) or not isinstance(mastery_of, dict):
            return []
        return [lesson_map[n] for n in lesson_map
                if n != node and isinstance(lesson_map[n], dict)
                and (mastery_of.get(n, 0.0) or 0.0) >= 0.85]
    except Exception:  # noqa: BLE001 — partner lookup never raises
        return []


def _code_lang(file: str) -> str:
    """Predict-cover language from a source filename; defaults to python."""
    try:
        ext = (file or "").rsplit(".", 1)[-1].lower() if "." in (file or "") else ""
    except Exception:  # noqa: BLE001 — filename sniffing never raises
        return "python"
    if ext in ("js", "jsx", "ts", "tsx", "mjs", "cjs"):
        return "javascript"
    return "python"


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
        mark = verdictsmod.stamp_html(good)
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
