"""Inline form validation errors (I-84): errors beside the field, not silence.

Today an out-of-range confidence on a hand-built review POST is
silently clamped to 3, and server-rendered error paragraphs (journal
save, dispute filing) share no shape with the client-side answer guard.
This module owns the inline-error presentation both sides use: a
``role='alert'`` ``.field-error`` line naming the field and the fix,
plus ``.field-invalid`` highlighting for the offending input.

``confidence_error`` mirrors the server's ``_parse_review_form``
default (missing key means "3", no error); a present-but-unusable
value names the 1–5 range instead of failing silently. The review POST
handler prepends the line to the result body when it fires. Pure
functions, stdlib only (``html``), no I/O, no DB changes.
"""
from __future__ import annotations

import html
from urllib.parse import parse_qs

STATUS_ANCHOR = "status-b13-formerr"

ERROR_CLASS = "field-error"
INVALID_CLASS = "field-invalid"

CONF_MIN = 1
CONF_MAX = 5


def confidence_error(raw) -> str:
    """Message for a bad confidence value, or "" when it parses.

    Missing/None means the server default applies (no error); a
    present value outside 1–5 or not an integer names the fix.
    Never raises.
    """
    try:
        if raw is None:
            return ""
        text = raw.strip() if isinstance(raw, str) else str(raw).strip()
        if text == "":
            return ""
        if int(text) != float(text):
            return ("Confidence must be a whole number "
                    f"{CONF_MIN}–{CONF_MAX}.")
        value = int(text)
        if value < CONF_MIN or value > CONF_MAX:
            return (f"Confidence {value} is out of range — "
                    f"pick {CONF_MIN}–{CONF_MAX}.")
        return ""
    except Exception:  # noqa: BLE001 -- validation must never raise
        return (f"Confidence must be a whole number "
                f"{CONF_MIN}–{CONF_MAX}.")


def review_note(raw: str) -> str:
    """Inline error line for a review POST body, or "" when clean.

    Parses the raw body exactly like the handler (missing key means
    the server default, no error); a present-but-bad confidence
    renders the alert line the result page prepends. Never raises.
    """
    try:
        form = parse_qs(raw or "", keep_blank_values=True)
        msg = confidence_error(form.get("confidence", [None])[0])
        return field_error_html("confidence", msg) if msg else ""
    except Exception:  # noqa: BLE001 -- validation must never raise
        return ""


def field_error_html(field: str, message: str) -> str:
    """Inline error line for one field; escapes both halves."""
    try:
        name = html.escape(str(field or "answer"))
        msg = html.escape(str(message or "Fix this field and retry."))
        return (f"<p class='{ERROR_CLASS}' role='alert'>"
                f"<b>{name}:</b> {msg}</p>")
    except Exception:  # noqa: BLE001 -- error line must never raise
        return (f"<p class='{ERROR_CLASS}' role='alert'>"
                "Fix this field and retry.</p>")


def formerr_css() -> str:
    """Raw CSS declarations only, never ``<style>`` tags."""
    return (
        f".{ERROR_CLASS}{{color:var(--fail);font-weight:700;"
        "margin:.4rem 0;padding:.3rem .6rem;"
        "border-left:3px solid var(--fail);background:var(--paper)}}"
        f".{INVALID_CLASS}{{outline:2px solid var(--fail);outline-offset:2px}}"
        f".{ERROR_CLASS} b{{margin-right:.3rem}}")


def demo_html() -> str:
    """Status-page demo: the line a bad confidence renders."""
    return (
        "<form method='post' action='/cards/demo/review'>"
        "<label>Confidence (1–5): "
        f"<input name='confidence' value='9' class='{INVALID_CLASS}'></label> "
        + field_error_html("confidence",
                           confidence_error("9"))
        + "<button>Check prediction</button></form>")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Inline form errors <small>(improvement)</small></h3>"
        "<p>Out-of-range input now says so beside the field instead of "
        "failing silently: <code>groundwork/formerr.py</code> provides "
        "<code>confidence_error()</code> (present-but-bad 1–5 values name "
        "the fix; a missing key still means the server default) and "
        "<code>field_error_html()</code> (a <code>role='alert'</code> "
        "<code>.field-error</code> line plus <code>.field-invalid</code> "
        "highlight), wired into the review POST path and the head "
        "stylesheet. Helpers fail closed, never raise.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "inline-errors",
        "kind": "improvement",
        "title": "Inline form errors",
        "blurb": "Out-of-range answers fail loudly beside the field — a role=alert line naming the fix, not silence.",
        "path": "/status",
        "anchor": "status-b13-formerr",
    }
