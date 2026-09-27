"""Thank-the-author note (F-144): copy-pasteable thanks per module pack.

Groundwork is local-first with no backend and no inbox, and no author
or contact lives anywhere a seed can carry (modules, lessons, and the
share/seed export hold repo + task summary only). So this module does
not send anything: it composes a short thank-you note from the live
module row and renders it with a Copy button plus a manual-copy
fallback. The copy says plainly that Groundwork sends nothing itself.

Caller: Handler.module_html beside the Session provenance line, fed
only the already-fetched module row. Unknown/empty rows render ""
so legacy pages keep their bytes. No DB/schema changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b26-thanks"
BOX_ANCHOR = "thanks"


def _str(v) -> str:
    try:
        return v if isinstance(v, str) else ("" if v is None else str(v))
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def _field(row, key: str) -> str:
    """One text field off a sqlite3 Row or a dict; "" when absent."""
    try:
        if row is None:
            return ""
        if isinstance(row, dict):
            return _str(row.get(key, "")).strip()
        try:
            return _str(row[key]).strip()
        except (KeyError, IndexError, TypeError):
            return ""
    except Exception:  # noqa: BLE001 -- reads must never raise
        return ""


def note_for(module) -> str:
    """Thank-you note naming the pack; "" when the row holds nothing."""
    try:
        mid = _field(module, "id")
        repo = _field(module, "repo")
        summary = " ".join(_field(module, "task_summary").split())
        if not (mid or repo or summary):
            return ""
        title = summary or ("module " + mid)
        where = repo or "this Groundwork pack"
        return "\n".join([
            'Thank you for the "%s" module pack.' % title,
            "Pack: %s (module %s)." % (where, mid or "unknown"),
            "It helped my learning - a Groundwork learner",
        ])
    except Exception:  # noqa: BLE001 -- compose must never raise
        return ""


def thanks_box_html(module) -> str:
    """Copy-note box for the module page; "" when there is no note."""
    try:
        note = note_for(module)
        if not note:
            return ""
        safe = html.escape(note, quote=False)
        return (
            f"<section id='{BOX_ANCHOR}'><h2>Thank the author</h2>"
            "<p>Groundwork sends nothing itself - copy this note, then "
            "paste it wherever you reach the pack author "
            "(chat, email, review thread):</p>"
            f"<textarea id='thanks-note' readonly rows='4'>{safe}</textarea>"
            "<p><button type='button' id='thanks-copy'>Copy note</button> "
            "<small id='thanks-done'></small></p>"
            "<script>(function () {"
            "var b = document.getElementById('thanks-copy');"
            "var t = document.getElementById('thanks-note');"
            "var s = document.getElementById('thanks-done');"
            "if (!b || !t) return;"
            "function done(m) { if (s) s.textContent = m; }"
            "b.addEventListener('click', function () {"
            "if (navigator.clipboard && navigator.clipboard.writeText) {"
            "navigator.clipboard.writeText(t.value).then("
            "function () { done('Copied - paste it to the author.'); },"
            "function () { t.select();"
            "done('Copy failed - text selected, press Ctrl+C.'); });"
            "} else { t.select();"
            "done('Text selected - press Ctrl+C to copy.'); }"
            "});"
            "})();</script></section>"
        )
    except Exception:  # noqa: BLE001 -- box must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the thank-the-author note."""
    return {"id": "thank-author", "kind": "feature",
            "title": "Thank the author",
            "blurb": ("Copy a ready-made thank-you note for the pack "
                      "author - Groundwork sends nothing itself."),
            "path": "/modules/{mid}", "anchor": BOX_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by the batch26 home module."""
    sample = note_for({"id": "abc123", "repo": "example/repo",
                       "task_summary": "Sample pack"})
    return (f"<h3 id='{STATUS_ANCHOR}'>Thank the author <small>(feature)</small></h3>"
            "<p>Each module page carries a copy-pasteable thank-you note "
            "naming the pack. <code>groundwork/thanks.py</code> provides "
            "<code>note_for()</code> and <code>thanks_box_html()</code>, "
            "grafted onto <code>Handler.module_html</code> beside the "
            "Session provenance line; there is no inbox and no mailto "
            "because seeds carry no author contact, so the copy says "
            "plainly that Groundwork sends nothing itself. Example note:</p>"
            f"<pre>{html.escape(sample, quote=False)}</pre>")
