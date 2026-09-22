"""Reading-group mode (F-89): one module, discussion prompts, presence.

A shared lesson carries three deterministic prompts (recall, connect,
challenge); the roster lists who is around via locally synced
presence; the plan shares minutes across lessons. Presence is a plain
mapping (member -> {"done", "at"}) merged last-writer-wins — the sync
channel stays out of scope. With no presence the section omits
itself, so pages render byte-identical legacy HTML. Stdlib only
(``html``); no I/O, never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b20-readgroup"

GENERIC_PROMPTS = ("Restate the lesson's big idea in your own words.",
                   "Connect it to a concept you already own.",
                   "Name one place where it would break.")


def _text(value) -> str:
    try:
        return value.strip() if isinstance(value, str) else ""
    except Exception:  # noqa: BLE001
        return ""


def discussion_prompts(lesson) -> list:
    """Three deterministic prompts; generic trio on thin input."""
    try:
        if not isinstance(lesson, dict):
            return list(GENERIC_PROMPTS)
        summary = _text(lesson.get("summary"))
        how = [s for s in (lesson.get("how") or [])
               if isinstance(s, str) and s.strip()]
        name = _text(lesson.get("name")) or "this lesson"
        if not summary and not how:
            return list(GENERIC_PROMPTS)
        first = summary.split(".")[0][:140] if summary else name
        recall = f"Restate in your own words: {first}."
        connect = (f"Connect this step to something you own: {how[0][:140]}."
                   if how else f"Connect {name} to a concept you own.")
        challenge = f"Where would {name} break? Name one case."
        return [recall, connect, challenge]
    except Exception:  # noqa: BLE001
        return list(GENERIC_PROMPTS)


def session_plan(pairs) -> list:
    """[(name, minutes, share)] minute shares; [] on hostile input."""
    try:
        rows = []
        for pair in pairs or []:
            try:
                name, mins = pair[0], int(pair[1])
            except (TypeError, IndexError, KeyError, ValueError):
                continue
            rows.append((_text(name) or "lesson", max(0, mins)))
        total = sum(m for _, m in rows)
        if not rows or total <= 0:
            return [(n, m, 0) for n, m in rows]
        return [(n, m, round(100 * m / total)) for n, m in rows]
    except Exception:  # noqa: BLE001
        return []


def roster_html(members) -> str:
    """Escaped roster list; "" with no members."""
    try:
        names = [m for m in (members or []) if isinstance(m, str) and m.strip()]
        if not names:
            return ""
        items = "".join(f"<li>{html.escape(m)}</li>" for m in names)
        return f"<ul class='readgroup-roster'>{items}</ul>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def presence_merge(local, peer) -> dict:
    """Last-writer-wins per member on the "at" stamp; {} on garbage."""
    try:
        merged: dict = {}

        def _take(mapping):
            if not isinstance(mapping, dict):
                return
            for member, entry in mapping.items():
                if not isinstance(member, str) or not member.strip():
                    continue
                if not isinstance(entry, dict):
                    continue
                stamp = str(entry.get("at") or "")
                prev = merged.get(member)
                prev_stamp = str((prev or {}).get("at") or "")
                if prev is None or stamp >= prev_stamp:
                    merged[member] = {"done": entry.get("done", 0),
                                      "at": stamp}

        _take(local)
        _take(peer)
        return merged
    except Exception:  # noqa: BLE001
        return {}


def session_html(lesson_map, presence, minutes=None) -> str:
    """Reading-group section; "" without live presence."""
    try:
        if not isinstance(presence, dict) or not presence:
            return ""
        if not isinstance(lesson_map, dict) or not lesson_map:
            return ""
        node = sorted(lesson_map)[0]
        lesson = lesson_map[node]
        prompts = "".join(f"<li>{html.escape(p)}</li>"
                          for p in discussion_prompts(lesson))
        plan = ""
        if isinstance(minutes, dict) and minutes:
            pairs = [(str(n), minutes.get(n, 0)) for n in lesson_map]
            rows = "".join(
                f"<li>{html.escape(n)} — {m} min ({s}%)</li>"
                for n, m, s in session_plan(pairs))
            if rows:
                plan = f"<h5>Plan</h5><ul>{rows}</ul>"
        return (
            f"<section id='readgroup'><h3>Reading group</h3>"
            f"{roster_html(list(presence))}"
            f"<h5>Discuss</h5><ol>{prompts}</ol>{plan}</section>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = session_html({"n:add": {"name": "add",
                                     "summary": "Totals two numbers.",
                                     "how": ["Read the defaults."]}},
                          {"ann": {"done": 1, "at": "2020-01-01"}})
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Reading-group mode <small>(feature)</small></h3>"
        "<p>Study one module together: shared lesson, discussion prompts, "
        "local presence sync. <code>groundwork/readgroup.py</code> appends "
        "a reading-group section on the module rendering path "
        "(<code>Handler.module_html</code>) only when presence is live; "
        "solo visits render exactly as before. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "reading-group",
        "kind": "feature",
        "title": "Reading-group mode",
        "blurb": "Study one module together: shared lesson, discussion "
                 "prompts, local presence sync.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
