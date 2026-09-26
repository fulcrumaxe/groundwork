"""Line-comment UI for code-review cards (I-168).

Type-21 cards render snippet lines with clickable gutters; each line
takes a note. Notes serialize as `L{n}: text` lines into the SAME
`answer` field the legacy textarea posts, so exercises.grade needs no
changes: rubric substrings match over the whole text and the first
integer token (the first L number) is the accused line.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b25-linecomment"
_NOTE_RE = re.compile(r"^\s*[Ll]\s*(\d+)\s*[:\-.)]?\s*(.*?)\s*$")
_NUMD_RE = re.compile(r"^\s*(\d+)\s*[:|]\s?(.*)$")
_INT_RE = re.compile(r"-?\d+")
_LEGACY_HINT = "Explain in your own words…"


def _s(v) -> str:
    try:
        return v if isinstance(v, str) else ("" if v is None else str(v))
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def parse_notes(sub) -> list:
    """`L3: note` lines -> [(3, 'note')]; legacy text -> []. Never raises."""
    out = []
    try:
        for ln in _s(sub).splitlines():
            m = _NOTE_RE.match(ln)
            if m and m.group(2):
                out.append((int(m.group(1)), m.group(2)))
    except Exception:  # noqa: BLE001 -- parse must never raise
        return []
    return out


def serialize_notes(notes) -> str:
    """[(3,'x')] -> 'L3: x', one per line; unusable -> ''. Never raises."""
    try:
        rows = []
        for n in (notes or []):
            l, t = int(n[0]), _s(n[1]).replace("\n", " ").strip()
            if l > 0 and t:
                rows.append(f"L{l}: {t}")
        return "\n".join(rows)
    except Exception:  # noqa: BLE001 -- serialize must never raise
        return ""


def accused_line(sub):
    """First integer in text, mirroring the t21 grader's regex."""
    try:
        m = _INT_RE.search(_s(sub))
        return int(m.group(0)) if m else None
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return None


def snippet_lines(snippet) -> list:
    """Payload snippet -> [(lineno, code)]; strips 'N:' prefixes."""
    try:
        raw = _s(snippet).splitlines() or []
        if raw and all(_NUMD_RE.match(l) for l in raw if l.strip()):
            return [(int(m.group(1)), m.group(2)) for l in raw
                    for m in [_NUMD_RE.match(l)] if m]
        return [(i + 1, l) for i, l in enumerate(raw)]
    except Exception:  # noqa: BLE001 -- split must never raise
        return []


def review_html(snippet, field="answer") -> str:
    """Clickable lines + per-line note inputs syncing into `field`."""
    try:
        rows = snippet_lines(snippet)
        if not rows:
            return ""
        lis = "".join(
            f"<div class='lc-row'><button type='button' class='lc-gut' data-l='{n}'"
            f" title='Comment on line {n}'>{n}</button>"
            f"<code>{html.escape(c) or '&nbsp;'}</code>"
            f"<input class='lc-note' data-l='{n}' size='30' placeholder='Note…'></div>"
            for n, c in rows)
        return (f"<div class='lc-review'>{lis}</div>"
                f"<label>Review notes (one L-numbered line each):<br><textarea name='{field}'"
                f" rows='4' cols='70' class='lc-sync'"
                f" placeholder='L3: off-by-one…'></textarea></label>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def review_js() -> str:
    """Sync note inputs -> textarea (append/refresh L-lines); degrades."""
    return ("<script>if(!window.__lcInit){window.__lcInit=true;document.addEventListener"
            "('input',function(e){var t=e.target;if(!t.classList||!t.classList.contains('lc-note')"
            ")return;var f=t.closest('form');var a=f&&f.querySelector('textarea.lc-sync');"
            "if(!a)return;var m={};a.value.split('\\n').forEach(function(l){if(!/^\\s*[Ll]\\s*\\d+"
            "/.test(l)&&l.trim())m['#'+l]=l});f.querySelectorAll('input.lc-note').forEach("
            "function(i){if(i.value.trim())m['L'+i.getAttribute('data-l')]='L'+"
            "i.getAttribute('data-l')+': '+i.value.trim()});a.value=Object.keys(m).map("
            "function(k){return m[k]}).join('\\n')})}</script>")


def legacy_body(conf: str) -> str:
    """Byte-identical shared-branch body for etype 21 (no snippet)."""
    return (f"<textarea name='answer' rows='5' cols='70' "
            f"placeholder='{_LEGACY_HINT}'></textarea><br>"
            f"{conf}<button>Submit explanation</button>")


def branch_html(card, payload) -> str:
    """Full etype-21 body: line comments when snippeted, else legacy."""
    try:
        from . import cards as cardsmod  # lazy: cards.py calls this branch
        conf = cardsmod._confidence()
        snippet = payload.get("snippet", "") if isinstance(payload, dict) else ""
        box = review_html(snippet)
        if not box:
            return legacy_body(conf)
        return box + f"{conf}<button>Submit explanation</button>" + review_js()
    except Exception:  # noqa: BLE001 -- branch must never raise
        try:
            from . import cards as cardsmod
            return legacy_body(cardsmod._confidence())
        except Exception:  # noqa: BLE001 -- legacy must never raise
            return "<textarea name='answer' rows='5' cols='70'></textarea>"


def tour_entry() -> dict:
    """Tour registry entry for line comments on code review."""
    return {"id": "line-comments", "kind": "improvement",
            "title": "Line comments on code review",
            "blurb": "Click a line number to pin a note, like real review.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    try:
        return (f"<h3 id='{STATUS_ANCHOR}'>Line comments on review "
                "<small>(improvement)</small></h3><p>Type-21 review cards render each snippet "
                "line with a clickable gutter (<code>groundwork/linecomment.py</code>); notes "
                "serialize as <code>L{n}: text</code> into the existing answer field, so the "
                "legacy grader reads them unchanged.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Line comments</h3>"
