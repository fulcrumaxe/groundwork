"""Real code editor for code-writing cards (I-154).

Code-writing cards (exercise types 12, 14, 19, 20, 23) post their
work from a plain proportional textarea where Tab moves focus away
and lines carry no numbers. This module upgrades that box in place:
monospace type, a line-number gutter, and Tab-to-indent — while the
posting field keeps its name and form action, so grading and the
review POST are unchanged.

Pure HTML/CSS/JS builders over posted text — no HTTP, no DB/schema
changes, no web.py edits. The caller is ``cards.answer_widget``,
which swaps its code-branch textarea for ``editor_html()``; page
CSS joins once via the head wire, and ``editor_js()`` rides inline
per code branch (guarded, repeat-safe). Every helper fails closed
and never raises.

Legacy no-data fallback: the editor IS a real textarea (never
contenteditable), so with JavaScript disabled it is exactly the old
plain box; with CSS disabled the gutter is a plain number column
beside readable code. Empty and non-string input render an empty
editor; nothing raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b24-codeedit"

CODE_TYPES = ("12", "14", "19", "20", "23")

_INDENT = "  "

_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


def _safe_text(value) -> str:
    """Best-effort str(); empty string for anything unusable, never raises."""
    try:
        if isinstance(value, str):
            return value
        if value is None:
            return ""
        return str(value)
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def _safe_name(value) -> str:
    """Field name restricted to a safe token; 'answer' fallback."""
    try:
        text = _safe_text(value)
        if _NAME_RE.fullmatch(text):
            return text
        return "answer"
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return "answer"


def _safe_int(value, default: int) -> int:
    """Positive int or default; never raises."""
    try:
        n = int(value)
        return n if n > 0 else default
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return default


def is_code_type(etype) -> bool:
    """True when the exercise type posts code from the large textarea."""
    try:
        return str(etype) in CODE_TYPES
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return False


def line_count(text) -> int:
    """Number of lines in a code string; 0 for empty input, never raises."""
    try:
        body = _safe_text(text)
        if not body:
            return 0
        return body.count("\n") + 1
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return 0


def _gutter(n) -> str:
    """One gutter number per line; empty string for n < 1, never raises."""
    try:
        count = _safe_int(n, 0)
        if count < 1:
            return ""
        return "".join(f"<span>{i}</span>" for i in range(1, count + 1))
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def editor_html(code=None, *, name: str = "answer", rows: int = 12,
                cols: int = 70, placeholder: str = "Write your code here",
                editor_id: str = "") -> str:
    """Code editor: gutter + real textarea posting field, never raises.

    The textarea keeps ``name`` (default ``'answer'``) so the review
    POST and grading contract are unchanged. ``editor_id`` adds an
    ``id`` to the wrapper for tour anchoring; empty means no id.
    """
    try:
        body = _safe_text(code)
        field = _safe_name(name)
        rows_n = _safe_int(rows, 12)
        cols_n = _safe_int(cols, 70)
        hint = _safe_text(placeholder)
        ident = _safe_text(editor_id)
        id_attr = (f" id='{html.escape(ident, quote=True)}'"
                   if ident else "")
        return (
            f"<div class='codeedit'{id_attr}>"
            f"<div class='codeedit-gutter' aria-hidden='true'>"
            f"{_gutter(line_count(body) or 1)}</div>"
            f"<textarea class='codeedit-input' name='{field}' "
            f"rows='{rows_n}' cols='{cols_n}' "
            f"placeholder='{html.escape(hint, quote=True)}' "
            f"spellcheck='false' autocapitalize='off' "
            f"autocomplete='off'>{html.escape(body)}</textarea>"
            f"</div>"
        )
    except Exception:  # noqa: BLE001 -- status/queue pages must never break
        return "<textarea name='answer' rows='12' cols='70'></textarea>"


def editor_css() -> str:
    """Style rules: mono type, gutter, scroll lock-step. Never raises.

    Rules only, no <style> wrapper: the caller concatenates this into
    the single head stylesheet (a nested <style> element would close
    the sheet early and dump later CSS into <body> as text).
    """
    try:
        return (
            ".codeedit{display:flex;gap:0;border:1px solid #ccc;border-radius:4px;overflow:hidden}"
            ".codeedit-gutter{padding:4px 6px;text-align:right;background:#f4f4f4;color:#888;"
            "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
            "font-size:13px;line-height:1.5;user-select:none;overflow:hidden}"
            ".codeedit-gutter span{display:block}"
            ".codeedit-input{flex:1;border:0;outline:none;resize:vertical;padding:4px 8px;"
            "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
            "font-size:13px;line-height:1.5;white-space:pre;overflow:auto;tab-size:4}"
        )
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def editor_js() -> str:
    """Behavior: Tab indents, Shift-Tab outdents, gutter syncs. Never raises.

    No-JS fallback is the plain textarea above: Tab then moves focus
    as before and the gutter stays at its server-rendered count.
    """
    try:
        return (
            "<script>"
            "if (!window.__codeeditInit) { window.__codeeditInit = true;"
            "function codeeditSync(box) {"
            "  var ta = box.querySelector('.codeedit-input');"
            "  var g = box.querySelector('.codeedit-gutter');"
            "  if (!ta || !g) return;"
            "  var n = ta.value.split('\\n').length;"
            "  var cur = g.childNodes.length;"
            "  if (cur === n) return;"
            "  var h = '';"
            "  for (var i = 1; i <= n; i++) h += '<span>' + i + '</span>';"
            "  g.innerHTML = h;"
            "  g.scrollTop = ta.scrollTop;"
            "}"
            "function codeeditIndent(ta, out) {"
            "  var s = ta.selectionStart, e = ta.selectionEnd, v = ta.value;"
            "  var a = v.lastIndexOf('\\n', s - 1) + 1;"
            "  var b = e; var z = v.indexOf('\\n', e);"
            "  b = (z < 0) ? v.length : z;"
            "  var block = v.slice(a, b); var lines = block.split('\\n');"
            "  var next;"
            "  if (out) {"
            "    next = lines.map(function (l) {"
            "      return l.indexOf('  ') === 0 ? l.slice(2) : l; }).join('\\n');"
            "  } else {"
            "    next = '  ' + lines.join('\\n  ');"
            "  }"
            "  ta.value = v.slice(0, a) + next + v.slice(b);"
            "  ta.selectionStart = a; ta.selectionEnd = a + next.length;"
            "}"
            "document.addEventListener('DOMContentLoaded', function () {"
            "  Array.prototype.forEach.call("
            "    document.querySelectorAll('.codeedit'), function (box) {"
            "    var ta = box.querySelector('.codeedit-input');"
            "    var g = box.querySelector('.codeedit-gutter');"
            "    if (!ta) return;"
            "    codeeditSync(box);"
            "    ta.addEventListener('input', function () { codeeditSync(box); });"
            "    ta.addEventListener('scroll', function () {"
            "      if (g) g.scrollTop = ta.scrollTop; });"
            "    ta.addEventListener('keydown', function (e) {"
            "      if (e.key !== 'Tab' || e.ctrlKey || e.metaKey || e.altKey) return;"
            "      e.preventDefault();"
            "      codeeditIndent(ta, e.shiftKey);"
            "      codeeditSync(box);"
            "    });"
            "  });"
            "});"
            "}"
            "</script>"
        )
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Real code editor "
            f"<small>(improvement)</small></h3>"
            "<p>Code-writing cards now answer in a real editor from "
            "<code>groundwork/codeedit.py</code>: monospace type, a "
            "line-number gutter, and Tab-to-indent (Shift-Tab outdents) — "
            "no web.py edits. The posting field keeps "
            "<code>name='answer'</code> and the same form action, so "
            "grading and the review POST are unchanged; "
            "<code>is_code_type()</code> names the five code branches, "
            "<code>editor_html()</code> renders gutter plus textarea, and "
            "<code>editor_css()</code> / <code>editor_js()</code> ship the "
            "style and behavior once per page. Without JavaScript the box "
            "is exactly the legacy plain textarea; without CSS the gutter "
            "is a plain number column beside readable code.</p>"
        )
    except Exception:  # noqa: BLE001 -- status page must never break
        return f"<h3 id='{STATUS_ANCHOR}'>Real code editor</h3>"
