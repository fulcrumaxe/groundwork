"""Scratch runs: execute a draft without recording an attempt (I-185).

Code cards grade on every submit, so learners cannot probe the sandbox
-- every experiment costs an attempt. This module adds a "Run without
submitting" button beside the editor on code cards (types 12/14/19/20/
23): the same form posts to ``POST /cards/<id>/scratch`` via the
button's ``formaction`` (no JavaScript), the draft runs in the existing
sandbox, and the result page shows the output plus the draft prefilled
for a real submit. Nothing is recorded: no review row, no grade, no
scheduling change.

Call sites: ``cards.answer_widget`` appends the button (``enhance``,
identity for non-code cards); the ``/scratch`` POST route delegates to
``page_for``. Unknown cards 404 like the review route. Stdlib only
(``html``) plus lazy sibling reads (``db``, ``sandbox``); never raises
except through the documented None return.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b27-scratchrun"

#: Code-writing cards whose answer posts a single `answer` field.
CODE_ETYPES = ("12", "14", "19", "20", "23")


def _etype_of(card) -> str:
    """Exercise type as text; "" when unreadable."""
    try:
        if isinstance(card, dict):
            return str(card.get("exercise_type", ""))
        return str(card["exercise_type"])
    except Exception:  # noqa: BLE001 -- probing never raises
        return ""


def is_code_card(card) -> bool:
    """True when the card can scratch-run (single-answer code card)."""
    try:
        return _etype_of(card) in CODE_ETYPES
    except Exception:  # noqa: BLE001
        return False


def button_html(card_id) -> str:
    """Run-without-submitting button; "" for unusable ids."""
    try:
        if card_id is None:
            return ""
        cid = str(card_id)
        if not cid:
            return ""
        safe = html.escape(cid, quote=True)
        return ("<button type='submit' formaction="
                f"'/cards/{safe}/scratch'>Run without submitting</button>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def enhance(card, card_id, body_html: str) -> str:
    """Body plus the scratch button on code cards; legacy bytes else.

    The button must sit inside the answer form (it overrides the
    form's action), so the caller nests this around its post-dispatch
    body. Non-code cards get the identical object back.
    """
    try:
        if not is_code_card(card):
            return body_html
        btn = button_html(card_id)
        if not btn:
            return body_html
        return f"{body_html} {btn}"
    except Exception:  # noqa: BLE001 -- enhance never raises
        return body_html


def output_html(res) -> str:
    """Rendered stdout/stderr block; honest empties, never raises."""
    try:
        out = getattr(res, "stdout", "") or ""
        err = getattr(res, "stderr", "") or ""
        if not isinstance(out, str):
            out = str(out)
        if not isinstance(err, str):
            err = str(err)
        if not out and not err:
            return "<pre class='scratch-out'>(no output)</pre>"
        parts = ""
        if out:
            parts += f"<pre class='scratch-out'>{html.escape(out[:2000])}</pre>"
        if err:
            parts += (f"<pre class='scratch-err'>"
                      f"{html.escape(err[:2000])}</pre>")
        return parts
    except Exception:  # noqa: BLE001 -- markup never raises
        return "<pre class='scratch-out'>(no output)</pre>"


def page_for(db_path, card_id, code, origin: str = "/due",
             confidence: int = 3, raw: str = ""):
    """Scratch-result body; None when the card is unknown.

    Runs ``code`` in the existing sandbox and renders the output with
    the draft prefilled for a real submit. Records nothing.
    """
    try:
        from . import db as dbmod
        from . import sandbox as sbmod
    except Exception:  # noqa: BLE001 -- imports must exist
        return None
    try:
        cid = str(card_id)
        draft = code if isinstance(code, str) else ""
        try:
            con = dbmod.connect(db_path)
            try:
                row = con.execute("SELECT id FROM cards WHERE id=?",
                                  (cid,)).fetchone()
            finally:
                con.close()
        except Exception:  # noqa: BLE001 -- unreadable DB reads unknown
            return None
        if row is None:
            return None
        try:
            conf_i = int(confidence)
        except (TypeError, ValueError):
            conf_i = 3
        res = sbmod.SandboxRunner().run_python(draft)
        safe_origin = html.escape(origin if isinstance(origin, str) else "/due",
                                  quote=True)
        safe_cid = html.escape(cid, quote=True)
        from . import scratchhint as scratchhintmod
        prior = scratchhintmod.parse_count(raw)
        hint_block = scratchhintmod.unlock_html(db_path, cid, prior)
        again = (scratchhintmod.again_html(
            cid, draft, origin if isinstance(origin, str) else "/due",
            conf_i, prior) if hint_block else "")
        return (
            "<h2>Scratch run</h2>"
            "<p><small>Not recorded: no grade, no scheduling change. "
            "Submit below to grade this draft for real.</small></p>"
            f"{output_html(res)}"
            f"{hint_block}"
            f"<form method='post' action='/cards/{safe_cid}/review'>"
            f"<textarea name='answer' rows='12' cols='70'>"
            f"{html.escape(draft)}</textarea><br>"
            f"<input type='hidden' name='confidence' value='{conf_i}'>"
            f"<input type='hidden' name='origin' value='{safe_origin}'>"
            "<button>Submit for real</button></form>"
            f"{again}"
            f"<p><a class='btn' href='{safe_origin}'>Back to card</a></p>")
    except Exception:  # noqa: BLE001 -- scratch never crashes the route
        return None


def section_html() -> str:
    """Anchored status subsection; joined by the batch27 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Run without submitting "
        "<small>(improvement)</small></h3>"
        "<p>Code cards grade on every submit -- until now, every "
        "experiment cost an attempt. <code>groundwork/scratchrun.py</code> "
        "adds a Run-without-submitting button that posts the draft to "
        "<code>/cards/&lt;id&gt;/scratch</code> (same form, "
        "<code>formaction</code>, no JavaScript): the existing sandbox "
        "runs it, the output shows with the draft prefilled, and nothing "
        "is recorded -- no review row, no grade, no scheduling change.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "scratch-runs",
        "kind": "improvement",
        "title": "Run without submitting",
        "blurb": "Code cards gain a scratch run: execute the draft, see the output, record nothing.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
