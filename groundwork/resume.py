"""Resume interrupted sessions from History (I-48).

A "continue session" link on a History attempt row rebuilds the queue
as it was: the session key names the module context plus calendar day,
and the Due page narrows to cards still due from that context.

Pure functions, stdlib only (``html``, ``re``, ``urllib.parse``). No
I/O, no DB/schema changes, no web.py edits. Attempt recording stays
with history.py/results.py; actual queue filtering stays with
queue.py/cards.py — this module only builds the continue link, narrows
an already-fetched due list by module, and renders the resume banner.

WIRES (parent implements, this module only builds strings):
  1. history.py attempt rows: append ``resume.row_link(row)`` per row.
  2. web.py Due handler: read ``?resume=`` via parse_qs, then
     ``due = resume.session_cards(due, key)`` and prepend
     ``resume.resume_box_html(key, ...)``.
  3. status.py page_html + tour.ENTRIES: append ``resume.section_html()``
     and ``resume.tour_entry()``.
"""
from __future__ import annotations

import html
import re
from urllib.parse import quote

DUE = "/due"
STATUS_ANCHOR = "status-b9-resume"

_KEY_RE = re.compile(r"[A-Za-z0-9_-]{1,64}:\d{4}-\d{2}-\d{2}")
_DAY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MOD_OK = re.compile(r"[A-Za-z0-9_-]+")


def _coerce_str(value) -> str:
    """Best-effort str; never raises."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:
        return ""


def _clean_mid(value) -> str:
    """Keep only URL-safe [A-Za-z0-9_-], max 64 chars."""
    return "".join(_MOD_OK.findall(_coerce_str(value).strip()))[:64]


def _day_of(value) -> str:
    """Calendar day (YYYY-MM-DD) of an ISO timestamp-ish value, else ''."""
    text = _coerce_str(value).strip()
    day = text[:10]
    return day if _DAY_RE.match(day) else ""


def session_key(row) -> str:
    """Group one attempt row into its session: ``"<mid>:<YYYY-MM-DD>"``.

    Accepts a dict (``module_id``/``mid``/``module`` + ``reviewed_at``)
    or a ``(module_id, reviewed_at)`` tuple. Anything missing or
    malformed yields ``""``. Never raises.
    """
    try:
        if isinstance(row, dict):
            mid = row.get("module_id", row.get("mid", row.get("module", "")))
            when = row.get("reviewed_at", row.get("day", ""))
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            mid, when = row[0], row[1]
        else:
            return ""
        mid, day = _clean_mid(mid), _day_of(when)
        if not mid or not day:
            return ""
        return f"{mid}:{day}"
    except Exception:
        return ""


def parse_key(key) -> dict:
    """Split a session key into ``{"mid": ..., "day": ...}``.

    Malformed input yields ``{"mid": "", "day": ""}``. Never raises.
    """
    try:
        text = _coerce_str(key).strip()
        if _KEY_RE.fullmatch(text):
            mid, _, day = text.partition(":")
            return {"mid": mid, "day": day}
    except Exception:
        pass
    return {"mid": "", "day": ""}


def continue_url(key=None, row=None) -> str:
    """``/due?resume=<key>`` link for a session; ``/due`` on anything bad.

    Accepts a key string directly, or an attempt row (via ``row=`` or a
    dict passed as ``key``) which is grouped with :func:`session_key`.
    The key must match the ``mid:YYYY-MM-DD`` shape — mirror of
    originguard.py allowlist thinking: only the known ``/due`` page is
    ever targeted, so anything unexpected falls back to ``/due``.
    Never raises.
    """
    try:
        if row is None and isinstance(key, (dict, list, tuple)):
            row, key = key, None
        text = _coerce_str(key).strip() if key is not None else ""
        if not text and row is not None:
            text = session_key(row)
        if _KEY_RE.fullmatch(text):
            return f"{DUE}?resume={quote(text, safe='')}"
    except Exception:
        pass
    return DUE


def row_link(row, label="continue session") -> str:
    """Per-attempt-row "continue session" anchor, or ``""`` when ungroupable."""
    try:
        key = session_key(row)
        if not key:
            return ""
        href = html.escape(continue_url(key), quote=True)
        return (f"<a class='resume-link' href='{href}'>"
                f"{html.escape(_coerce_str(label) or 'continue session')}</a>")
    except Exception:
        return ""


def _card_mid(card) -> str | None:
    """Module id carried by a due card, or None when it carries none."""
    if not isinstance(card, dict):
        return None
    for field in ("module_id", "mid", "module"):
        if card.get(field):
            cleaned = _clean_mid(card[field])
            if cleaned:
                return cleaned
    return None


def session_cards(cards, key) -> list:
    """Due cards still in the resumed session's module context.

    ``cards`` is the already-fetched due list; ``key`` is a session key
    (or an attempt row grouped via :func:`session_key`). A bad key, or
    cards carrying no module field at all, returns the full list —
    fail closed to the normal ``/due`` queue instead of stranding the
    learner on an empty page. Never raises.
    """
    try:
        items = list(cards or [])
    except TypeError:
        return []
    try:
        text = key if isinstance(key, str) else session_key(key)
        parsed = parse_key(text)
        if not parsed["mid"]:
            return items
        if not any(_card_mid(c) is not None for c in items):
            return items
        return [c for c in items if _card_mid(c) == parsed["mid"]]
    except Exception:
        try:
            return list(cards or [])
        except TypeError:
            return []


def resume_box_html(key, count=None, title=None) -> str:
    """Banner for the Due page while a session is being resumed.

    ``count`` is the resumed queue length, ``title`` the module title;
    both are optional. A malformed key yields ``""`` (no banner).
    Never raises.
    """
    try:
        parsed = parse_key(key)
        if not parsed["mid"]:
            return ""
        label = _coerce_str(title).strip() or parsed["mid"]
        noun = ""
        if count is not None:
            try:
                n = int(count)
                noun = f" — {n} card{'s' if n != 1 else ''} still due"
            except (TypeError, ValueError):
                noun = ""
        return (
            "<p class='resume-box' id='resume-box'>Resuming session "
            f"{html.escape(label)} "
            f"<small>{html.escape(parsed['day'])}{html.escape(noun)}</small> · "
            f"<a href='{DUE}'>full queue</a> · "
            "<a href='/reviews'>history</a></p>"
        )
    except Exception:
        return ""


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "continue-session", "kind": "improvement",
            "title": "Continue interrupted sessions",
            "blurb": "History rows offer a continue link that rebuilds "
                     "the queue as it was — cards still due, same module.",
            "path": "/status", "anchor": "status-b9-resume"}


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Continue interrupted sessions "
        "<small>(improvement)</small></h3>"
        "<p>Each History attempt row carries a <code>continue session</code> "
        "link (<code>/due?resume=&lt;module&gt;:&lt;day&gt;</code>) that "
        "narrows the Due queue to cards still due from that session's "
        "module context, with a resume banner linking back to the full "
        "queue. Keys are shape-checked like <code>originguard</code> — "
        "anything unexpected falls back to <code>/due</code>. No DB change. "
        "<code>groundwork/resume.py</code>.</p>"
    )
