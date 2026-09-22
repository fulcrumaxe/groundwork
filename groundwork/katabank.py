"""Refactoring kata library (F-87): one smell, many repos, spaced.

Kata tracks group short buggy snippets by smell id (the same six ids
``smell.detect_all`` reports). ``pick_kata`` deals the weakest due
track that is not the last-dealt smell; ``order_due`` ranks Due-queue
cards by their track so the weakest smell surfaces first. Empty or
missing history returns the input order untouched — the legacy
default. Stdlib only (``html``, ``json``); no I/O, never raises.
"""
from __future__ import annotations

import html
import json

STATUS_ANCHOR = "status-b20-katabank"

DUE_DAYS = 7
PASS_GRADE = 3

TRACKS = (
    {"id": "long-function",
     "katas": ({"code": "def report(rows):\n    out = []\n    for r in rows:\n        x = r.strip()\n        if x:\n            out.append(x.upper())\n    total = len(out)\n    print(total)\n    return out",
                "fix": "extract one helper per job"},
               {"code": "def handle(req):\n    body = req.read()\n    data = parse(body)\n    check(data)\n    save(data)\n    notify(data)\n    return ok(data)",
                "fix": "one function per stage"})},
    {"id": "long-parameter-list",
     "katas": ({"code": "def plot(x, y, color, width, style, label, ax):\n    pass",
                "fix": "bundle related params into one object"},)},
    {"id": "deep-nesting",
     "katas": ({"code": "def f(a, b, c, d):\n    if a:\n        if b:\n            if c:\n                if d:\n                    return 1\n    return 0",
                "fix": "guard-clause or extract the inner block"},)},
    {"id": "duplicated-code",
     "katas": ({"code": "total = price * 1.2\ntax = price * 1.2\nfinal = price * 1.2",
                "fix": "extract it once and call it"},)},
    {"id": "magic-numbers",
     "katas": ({"code": "if code == 3:\n    retry(5)\nelse:\n    wait(30)",
                "fix": "name each constant where it is defined"},)},
    {"id": "broad-except",
     "katas": ({"code": "try:\n    save(row)\nexcept Exception:\n    pass",
                "fix": "catch the narrowest error you can handle"},)},
)
TRACK_IDS = tuple(t["id"] for t in TRACKS)


def _today() -> str:
    try:
        from datetime import date
        return date.today().isoformat()
    except Exception:  # noqa: BLE001
        return ""


def _days_since(last, now: str = "") -> float | None:
    try:
        if not isinstance(last, str) or not last.strip():
            return None
        day = last.strip()[:10]
        end = (now.strip()[:10] if isinstance(now, str) and now.strip()
               else _today())
        from datetime import date
        return (date.fromisoformat(end) - date.fromisoformat(day)).days
    except Exception:  # noqa: BLE001
        return None


def is_due(state, now: str = "") -> bool:
    """True when a track was never tried or its last try is 7+ days old."""
    try:
        if not isinstance(state, dict):
            return True
        elapsed = _days_since(state.get("last", ""), now)
        if elapsed is None:
            return True
        return elapsed >= DUE_DAYS
    except Exception:  # noqa: BLE001
        return True


def _fail_rate(state) -> float:
    try:
        fails = int(state.get("fails", 0) or 0)
        passes = int(state.get("passes", 0) or 0)
        total = fails + passes
        return (fails / total) if total else 0.0
    except (TypeError, ValueError, AttributeError):
        return 0.0


def _stats(history, smell: str) -> dict:
    try:
        got = (history or {}).get(smell, {})
        return got if isinstance(got, dict) else {}
    except (AttributeError, TypeError):
        return {}


def pick_kata(history, tracks=None, last_smell: str = "", now: str = ""):
    """Weakest due track that is not the last smell; None when none due.

    ``history`` maps smell id to {"passes", "fails", "last"}. Never raises.
    """
    try:
        ids = list(tracks) if tracks is not None else list(TRACK_IDS)
        ids = [t for t in ids if isinstance(t, str)]
        cands = [(smell, _fail_rate(_stats(history, smell)))
                 for smell in ids if is_due(_stats(history, smell), now)]
        cands = [(s, r) for s, r in cands if s != last_smell]
        if not cands:
            return None
        cands.sort(key=lambda kv: (-kv[1], ids.index(kv[0])))
        return cands[0][0]
    except Exception:  # noqa: BLE001
        return None


def kata_history_from_rows(rows) -> dict:
    """{smell: {passes, fails, last}} from review rows with card payloads.

    Rows are mappings (or tuples) carrying grade, reviewed_at, and the
    card payload JSON (or dict) with a "smell" id. Pass is grade >= 3.
    Never raises.
    """
    out: dict = {}
    try:
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    grade, when, payload = (row.get("grade"),
                                            row.get("reviewed_at"),
                                            row.get("payload"))
                else:
                    grade, when, payload = row[0], row[1], row[2]
            except (TypeError, IndexError, KeyError):
                continue
            try:
                data = json.loads(payload) if isinstance(payload, str) else payload
                smell = (data or {}).get("smell", "")
            except (TypeError, ValueError, AttributeError):
                smell = ""
            if not isinstance(smell, str) or smell not in TRACK_IDS:
                continue
            try:
                passed = float(grade or 0) >= PASS_GRADE
            except (TypeError, ValueError):
                continue
            slot = out.setdefault(smell, {"passes": 0, "fails": 0, "last": ""})
            slot["passes" if passed else "fails"] += 1
            stamp = str(when or "")
            if stamp and stamp >= slot["last"]:
                slot["last"] = stamp
        return out
    except Exception:  # noqa: BLE001
        return {}


def _card_track(card) -> str | None:
    try:
        payload = (card or {}).get("payload", {})
        if isinstance(payload, str):
            payload = json.loads(payload or "{}")
        smell = (payload or {}).get("smell", "")
        return smell if smell in TRACK_IDS else None
    except (TypeError, ValueError, AttributeError):
        return None


def order_due(cards, history=None, now: str = "") -> list:
    """Due cards grouped weakest-track-first; input order back without data.

    Tracks rank by fail rate (ties keep catalog order); the most
    recently dealt track sinks last for variety. Untracked cards keep
    their relative order at the end. Never raises, never mutates input.
    """
    try:
        items = [c for c in (cards or []) if isinstance(c, dict)]
        if not items:
            return []
        if not isinstance(history, dict) or not history:
            return list(items)
        lasts = [(s, str((_stats(history, s).get("last") or "")))
                 for s in TRACK_IDS if _stats(history, s)]
        last_smell = max(lasts, key=lambda kv: kv[1])[0] if lasts else ""
        ranked = sorted(
            TRACK_IDS,
            key=lambda s: (-_fail_rate(_stats(history, s)),
                           TRACK_IDS.index(s)))
        if last_smell in ranked:
            ranked = [s for s in ranked if s != last_smell] + [last_smell]
        pos = {s: i for i, s in enumerate(ranked)}
        tracked = sorted(
            [c for c in items if _card_track(c) is not None],
            key=lambda c: pos.get(_card_track(c), len(ranked)))
        rest = [c for c in items if _card_track(c) is None]
        return tracked + rest
    except Exception:  # noqa: BLE001
        try:
            return list(cards or [])
        except Exception:  # noqa: BLE001
            return []


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = "".join(
        f"<li>{html.escape(t['id'])} — {len(t['katas'])} katas</li>"
        for t in TRACKS)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Refactoring kata library <small>(feature)</small></h3>"
        "<p>Same smell across many repos on a spaced schedule until the "
        "fix sticks. <code>groundwork/katabank.py</code> groups kata "
        "snippets by smell track and ranks the Due queue weakest-first "
        "on the review path (<code>MCPServer.tool_list_due_reviews</code>); "
        "with no kata history the queue keeps its order. Tracks:</p>"
        f"<ul>{sample}</ul>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "refactoring-katas",
        "kind": "feature",
        "title": "Refactoring kata library",
        "blurb": "Same smell across many repos on a spaced schedule "
                 "until the fix sticks.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
