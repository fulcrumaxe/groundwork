"""Explainer open/closed memory (I-121): Study-first panels reopen as left.

Each Study-first ``<details>`` panel carries a ``data-gw-remember``
key; a small footer script restores its ``open`` state from
``localStorage`` and saves toggles. No-JS and first visits keep the
legacy closed panels. Stdlib only (``html``, ``re``); no I/O, never
raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b20-tabmemory"

SUMMARY_HTML = "<summary>Study first — explained your way</summary>"

_KEY_JUNK = re.compile(r"[^a-z0-9]+", re.IGNORECASE)


def normalize_key(key) -> str:
    """Slug for a panel key; "" for missing/hostile input."""
    try:
        if not isinstance(key, str) or not key.strip():
            return ""
        return _KEY_JUNK.sub("-", key.strip().lower()).strip("-")
    except Exception:  # noqa: BLE001 -- normalizing never raises
        return ""


def state_key(key) -> str:
    """localStorage key for a panel; "" when the key is hostile."""
    try:
        slug = normalize_key(key)
        return f"gw-explainer:{slug}" if slug else ""
    except Exception:  # noqa: BLE001
        return ""


def resolve_open(key, stored) -> bool | None:
    """True/False from a stored mapping; None means legacy closed."""
    try:
        slug = normalize_key(key)
        if not slug or not isinstance(stored, dict):
            return None
        value = stored.get(slug, stored.get(f"gw-explainer:{slug}", None))
        if value is True or value == "1" or value == 1:
            return True
        if value is False or value == "0" or value == 0:
            return False
        return None
    except Exception:  # noqa: BLE001
        return None


def details_html(inner: str, key, remembered=None) -> str:
    """Study-first wrapper with its memory key; legacy shape by default.

    ``remembered=True`` adds ``open`` (server-known state, e.g. tests);
    in production the footer script restores openness client-side.
    Never raises.
    """
    try:
        slug = normalize_key(key)
        body = inner if isinstance(inner, str) else ""
        if not slug:
            return f"<details>{SUMMARY_HTML}{body}</details>"
        flag = " open" if remembered is True else ""
        return (f"<details{flag} data-gw-remember='{html.escape(slug)}'>"
                f"{SUMMARY_HTML}{body}</details>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return f"<details>{SUMMARY_HTML}</details>"


def memory_js() -> str:
    """Footer script: restore/save panel openness; no-op without storage."""
    return (
        "<script>(function(){try{"
        "var store=window.localStorage;if(!store)return;"
        "document.querySelectorAll('details[data-gw-remember]').forEach(function(d){"
        "var k='gw-explainer:'+d.getAttribute('data-gw-remember');"
        "try{if(store.getItem(k)==='1')d.open=true;}catch(e){}"
        "d.addEventListener('toggle',function(){"
        "try{store.setItem(k,d.open?'1':'0');}catch(e){}});"
        "});}catch(e){}})();</script>")


def section_html() -> str:
    """Anchored status subsection; joined by the batch20 home module."""
    sample = details_html("<p>Explained your way.</p>", "sample-panel", True)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Explainers remember their state <small>(improvement)</small></h3>"
        "<p>Study-first panels reopen as you left them — open or closed "
        "per panel, remembered in your browser only. "
        "<code>groundwork/tabmemory.py</code> keys each panel on the Due "
        "queue and module rendering paths; without JavaScript the panels "
        "stay closed exactly as before. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "explainer-memory",
        "kind": "improvement",
        "title": "Explainers remember their state",
        "blurb": "Study-first panels reopen as you left them.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
