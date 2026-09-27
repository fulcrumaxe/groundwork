"""Scratch runs unlock hints without touching grades (I-186).

Code cards grade on every submit, so I-185 added scratch runs: the
draft executes in the sandbox and nothing is recorded. But hints
unlock off graded attempts (hints_html shows the 1+attempts prefix),
so a learner who only scratches never unlocks past the nudge. This
module counts scratch runs toward hint unlocking while keeping them
out of grading: the scratch result page renders the card's stored
hints at graded attempts + scratch runs, and a Run-again form carries
the incremented count as a plain `scratches` POST field (no schema
change, no new table) so repeated scratches keep unlocking. The
/review route and submit_review are untouched, so grades, scheduling,
and review rows stay exactly as they were.

Call sites: scratchrun.page_for parses the posted count and appends
the unlock block plus the run-again form; web.py only forwards the
raw POST body (one added argument, zero new lines). SELECT-only DB
reads (graded attempts, payload hints); never writes, never raises
except through the documented "" returns.
"""
from __future__ import annotations

import html
import json
from urllib.parse import parse_qs

STATUS_ANCHOR = "status-b28-scratchhint"

#: POST field carrying scratch runs so far (before the current run).
FIELD = "scratches"

#: Absurd counts clamp here; hint prefixes saturate long before this.
MAX_PRIOR = 99


def _coerce_int(value) -> int:
    """Non-negative int; hostile input fails closed to 0."""
    try:
        if isinstance(value, bool):
            return 0
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def parse_count(raw) -> int:
    """Prior scratch runs from a POST body; 0 when absent or hostile."""
    try:
        if not isinstance(raw, str) or not raw:
            return 0
        form = parse_qs(raw, keep_blank_values=True)
        vals = form.get(FIELD) or []
        if not vals:
            return 0
        return min(MAX_PRIOR, _coerce_int(vals[0]))
    except Exception:  # noqa: BLE001 -- parsing never raises
        return 0


def effective_attempts(graded, prior) -> int:
    """Hint-unlock attempts: graded + prior scratches + this run."""
    try:
        return _coerce_int(graded) + _coerce_int(prior) + 1
    except Exception:  # noqa: BLE001 -- counting never raises
        return 1


def _graded_and_hints(db_path, card_id):
    """(graded attempts, hints list); (0, []) when unreadable."""
    try:
        from . import db as dbmod
    except Exception:  # noqa: BLE001 -- imports must exist
        return 0, []
    try:
        cid = str(card_id)
        con = dbmod.connect(db_path)
        try:
            row = con.execute(
                "SELECT payload FROM cards WHERE id=?", (cid,)).fetchone()
            if row is None:
                return 0, []
            try:
                graded = con.execute(
                    "SELECT COUNT(*) FROM reviews WHERE card_id=?",
                    (cid,)).fetchone()[0]
            except Exception:  # noqa: BLE001 -- pre-migration DBs
                graded = 0
        finally:
            con.close()
        try:
            payload = json.loads(row[0] or "{}")
        except (ValueError, TypeError):
            return _coerce_int(graded), []
        hints = payload.get("hints", []) if isinstance(payload, dict) else []
        if not isinstance(hints, (list, tuple)):
            return _coerce_int(graded), []
        return _coerce_int(graded), list(hints)
    except Exception:  # noqa: BLE001 -- lookup never raises
        return 0, []


def unlock_html(db_path, card_id, prior=0) -> str:
    """Hint block for the scratch result page; "" when nothing unlocks.

    Renders the card's stored hints at graded attempts + scratch runs
    (the run now rendering counts), with an honest run-number note.
    "" when the card has no hints (the scratch page then stays
    byte-identical), the card is unknown, or the DB is unreadable.
    SELECT-only: never writes a review row.
    """
    try:
        from . import hinttiers as hinttiersmod
    except Exception:  # noqa: BLE001 -- imports must exist
        return ""
    try:
        run_no = _coerce_int(prior) + 1
        graded, hints = _graded_and_hints(db_path, card_id)
        if not hints:
            return ""
        eff = graded + run_no
        shown = min(len(hints), 1 + eff)
        body = hinttiersmod.hints_html(hints, eff)
        if not body:
            return ""
        noun = "hint" if len(hints) == 1 else "hints"
        return (
            f"<p><small>Scratch run {run_no} (not graded): "
            f"{shown} of {len(hints)} {noun} unlocked; "
            f"graded attempts still {graded}.</small></p>" + body)
    except Exception:  # noqa: BLE001 -- renderer never raises
        return ""


def again_html(card_id, draft, origin="/due", confidence=3, prior=0) -> str:
    """Run-again form carrying the incremented scratch count.

    Posts back to /scratch with the draft prefilled so repeated
    scratches keep unlocking. "" for unusable ids; never raises.
    """
    try:
        if card_id is None:
            return ""
        cid = str(card_id)
        if not cid:
            return ""
        run_no = _coerce_int(prior) + 1
        text = draft if isinstance(draft, str) else ""
        safe_origin = html.escape(
            origin if isinstance(origin, str) else "/due", quote=True)
        safe_cid = html.escape(cid, quote=True)
        try:
            conf_i = int(confidence)
        except (TypeError, ValueError):
            conf_i = 3
        return (
            f"<form method='post' action='/cards/{safe_cid}/scratch'>"
            f"<textarea name='answer' rows='12' cols='70'>"
            f"{html.escape(text)}</textarea><br>"
            f"<input type='hidden' name='confidence' value='{conf_i}'>"
            f"<input type='hidden' name='origin' value='{safe_origin}'>"
            f"<input type='hidden' name='{FIELD}' value='{run_no}'>"
            "<button>Run again without submitting</button></form>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch28 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Scratch runs unlock hints "
        "<small>(improvement)</small></h3>"
        "<p>Scratch runs record nothing, so they never unlocked hints -- "
        "until now. <code>groundwork/scratchhint.py</code> renders the "
        "card's hints on the scratch result page at graded attempts plus "
        "scratch runs, and a Run-again form carries the count as a plain "
        "POST field (no schema change): each run unlocks the next tier "
        "while grades, scheduling, and review rows stay untouched.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "scratch-hint-unlock",
        "kind": "improvement",
        "title": "Scratch runs unlock hints",
        "blurb": ("Scratch runs stay ungraded, and each one unlocks "
                  "the next hint tier on the result page."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
