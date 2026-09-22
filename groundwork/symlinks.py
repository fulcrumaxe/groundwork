"""Symbol-mention lesson links (I-104): every symbol a lesson names links
to its own lesson section, or carries its file line when it has none.

Pure post-pass over already-escaped HTML: splits on tags so tag names
and attributes are never matched, skips text already inside links or
glossary tooltips, matches longest names first, and caps links per
fragment. Unknown names render as plain text (legacy fallback).
Stdlib only (`html`, `re`); never raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b19-symlinks"
MAX_SYMLINKS = 20


def slug(text: str) -> str:
    """URL-fragment-safe anchor slug; mirrors lessons.slug."""
    try:
        out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(text))
        out = "-".join(filter(None, out.split("-")))
        return out or "lesson"
    except Exception:  # noqa: BLE001 -- slugging never raises
        return "lesson"


def lesson_anchor(concept) -> str:
    """`lesson-<slug>` section id for a concept name or dict."""
    try:
        name = concept.get("name", "") if isinstance(concept, dict) else concept
        return f"lesson-{slug(name)}"
    except Exception:  # noqa: BLE001
        return "lesson-lesson"


def build_index(entries, module_id: str = "") -> dict:
    """Concept rows -> {lower-name: {module_id, anchor, file, line}}.

    First writer wins on collision; unusable rows skipped; never raises.
    """
    index = {}
    try:
        scope = str(module_id or "")
        for e in entries or []:
            if not isinstance(e, dict):
                continue
            name = str(e.get("name") or "")
            if not name or name.lower() in index:
                continue
            mid = str(e.get("module_id") or scope)
            if not mid:
                continue
            try:
                line = int(e.get("line") or 0)
            except (TypeError, ValueError):
                line = 0
            index[name.lower()] = {
                "module_id": mid,
                "anchor": f"lesson-{slug(name)}",
                "file": str(e.get("file") or ""),
                "line": line,
            }
    except Exception:  # noqa: BLE001 -- indexing never raises
        return index
    return index


def symbol_href(symbol: str, module_id: str, index: dict) -> str:
    """Deep link for one symbol mention, or "" when none is safe.

    Same-module lesson anchor first, owner-module anchor next, bare
    owner module page when no lesson anchor applies. Never a dead
    #anchor; never raises.
    """
    try:
        if not isinstance(index, dict) or not index:
            return ""
        key = str(symbol or "").lower()
        if not key or not module_id:
            return ""
        hit = index.get(key)
        if not isinstance(hit, dict):
            return ""
        mid = str(hit.get("module_id") or "")
        if not mid:
            return ""
        return f"/modules/{mid}#{hit['anchor']}" if hit.get("anchor") else f"/modules/{mid}"
    except Exception:  # noqa: BLE001
        return ""


def _flavor(hit: dict) -> str:
    try:
        loc = str(hit.get("file") or "")
        if hit.get("line"):
            loc = f"{loc}:{hit['line']}"
        return loc or "lesson"
    except Exception:  # noqa: BLE001
        return "lesson"


def link_symbols(fragment: str, index: dict, module_id: str = "",
                 budget: int = MAX_SYMLINKS) -> str:
    """Escaped HTML fragment -> fragment with known mentions linked.

    Unknown symbols pass through untouched; empty index returns the
    input unchanged (byte-identical legacy path); never raises.
    """
    try:
        if fragment is None:
            return ""
        if not isinstance(fragment, str):
            fragment = str(fragment)
        if not fragment or not isinstance(index, dict) or not index or not module_id:
            return fragment
        try:
            left = int(budget)
        except (TypeError, ValueError):
            return fragment
        if left <= 0:
            return fragment
        names = sorted(index.keys(), key=len, reverse=True)
        if not names:
            return fragment
        pattern = re.compile(
            r"(?<!\w)(" + "|".join(re.escape(n) for n in names) + r")(?!\w)",
            re.IGNORECASE)
        parts = re.split(r"(<[^>]*>)", fragment)
        skip = [False]
        cell = [left]
        for i in range(len(parts)):
            if i % 2 == 1:
                tag = parts[i].lower()
                if tag.startswith("<a ") or tag == "<a>":
                    skip[0] = True
                elif tag.startswith("</a"):
                    skip[0] = False
                elif "class='gloss'" in tag or 'class="gloss"' in tag:
                    skip[0] = True
                elif tag.startswith("</dfn"):
                    skip[0] = False
                continue
            if skip[0]:
                continue
            parts[i] = pattern.sub(
                lambda m: _wrap(m, index, str(module_id), cell), parts[i])
            if cell[0] <= 0:
                break
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- markup never raises
        try:
            return fragment if isinstance(fragment, str) else str(fragment)
        except Exception:  # noqa: BLE001
            return ""


def _wrap(match, index: dict, module_id: str, cell: list) -> str:
    word = match.group(1)
    if cell[0] <= 0:
        return word
    hit = index.get(word.lower())
    if not isinstance(hit, dict):
        return word
    href = symbol_href(word, module_id, index)
    if not href:
        return word
    cell[0] -= 1
    return (f"<a class='symlink' href='{href}' "
            f"title='{html.escape(_flavor(hit), quote=True)}'>{word}</a>")


def index_for_lessons(study: dict, cards: list, module_id: str = "") -> dict:
    """Per-group Due index from stored lesson dicts; never raises."""
    entries = []
    try:
        for c in cards or []:
            if not isinstance(c, dict):
                continue
            hit = (study or {}).get(c.get("id"))
            ld = hit[0] if isinstance(hit, (list, tuple)) and hit else None
            if not isinstance(ld, dict):
                continue
            entries.append({"name": ld.get("name") or "",
                            "module_id": module_id,
                            "file": ld.get("file") or "",
                            "line": ld.get("line") or 0})
    except Exception:  # noqa: BLE001
        return {}
    return build_index(entries, module_id)


def annotate_code(code_escaped_lines: str, index: dict, module_id: str = "") -> str:
    """Apply link_symbols to already-escaped code lines; never raises."""
    try:
        return link_symbols(code_escaped_lines, index, module_id)
    except Exception:  # noqa: BLE001
        try:
            return code_escaped_lines if isinstance(code_escaped_lines, str) else ""
        except Exception:  # noqa: BLE001
            return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch19 home module."""
    sample = link_symbols(
        "grade totals via render_levels", build_index([
            {"name": "grade", "module_id": "m1", "file": "calc.py", "line": 12},
            {"name": "render_levels", "module_id": "m1",
             "file": "lessons.py", "line": 14},
        ], "m1"), "m1")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Symbol-mention lesson links <small>(improvement)</small></h3>"
        "<p>Every function and symbol a lesson names links to its own lesson "
        "section — or carries its file line when it has none. "
        "<code>groundwork/symlinks.py</code> runs as a post-pass over finished "
        "HTML on the lesson rendering path (<code>lessons.render_levels</code>); "
        "unknown names render as plain text. A live sample renders below.</p>"
        f"<p>{sample}</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "symbol-links",
        "kind": "improvement",
        "title": "Symbol mentions link to lessons",
        "blurb": "Every function and symbol a lesson names links to its own "
                 "lesson — or its file line when it has none.",
        "path": "/modules/{mid}",
        "anchor": "{lesson}",
    }
