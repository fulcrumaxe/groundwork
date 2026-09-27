"""Post-answer "what to review next" list (I-190).

After a review is submitted, the result screen suggests the next due
cards -- the live due queue minus the just-answered card, earliest
due first, each linked back into the queue. Nothing left due renders
"" so the result page stays byte-identical. Stdlib only; never raises.
"""
from __future__ import annotations

import html

from . import whysee as whyseemod

STATUS_ANCHOR = "status-b28-nextup"
SECTION_ANCHOR = "nextup"
DEFAULT_LIMIT = 3
MAX_LIMIT = 5


def _limit_of(limit) -> int:
    try:
        return max(0, min(int(limit), MAX_LIMIT))
    except (TypeError, ValueError):
        return DEFAULT_LIMIT


def _mastery_of(value) -> float:
    try:
        got = float(value or 0.0)
        return got if got == got else 0.0
    except (TypeError, ValueError):
        return 0.0


def _overdue_days(due, now: str = "") -> int | None:
    try:
        if not isinstance(due, str) or not due.strip():
            return None
        from datetime import date
        day = date.fromisoformat(due.strip()[:10])
        if isinstance(now, str) and now.strip():
            today = date.fromisoformat(now.strip()[:10])
        else:
            today = date.today()
        return (today - day).days
    except Exception:  # noqa: BLE001
        return None


def pick_next(db_path, answered_card_id="",
              limit=DEFAULT_LIMIT, now="") -> list:
    """Up to `limit` due cards minus the answered one, earliest first.

    Each pick: {card_id, concept, module_id, due, mastery, reason}.
    Empty store, unknown db, or hostile input yields []. Never raises.
    """
    try:
        want = _limit_of(limit)
        if not want or not db_path:
            return []
        from . import db as dbmod
        from . import sched as schedmod
        stamp = (now if isinstance(now, str) and now.strip()
                 else schedmod.iso(schedmod.utcnow()))
        answered = str(answered_card_id or "")
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.id AS cid, cards.due AS due,"
                " concepts.name AS concept, concepts.mastery AS mastery,"
                " concepts.module_id AS mid FROM cards"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE cards.due <= ? AND cards.stale = 0"
                " AND cards.id != ?"
                " ORDER BY cards.due LIMIT ?",
                (stamp, answered, want)).fetchall()
        finally:
            con.close()
        picks = []
        for r in rows:
            try:
                cid = str(r["cid"] or "")
                if not cid:
                    continue
                due = str(r["due"] or "")
                m = _mastery_of(r["mastery"])
                late = _overdue_days(due, stamp)
                reason = f"due {due[:10]}" if due else "due now"
                if late is not None and late > 0:
                    reason += (f"; {late} day"
                               f"{'s' if late != 1 else ''} overdue")
                reason += f"; mastery {m:.2f}"
                picks.append({"card_id": cid,
                              "concept": str(r["concept"] or cid),
                              "module_id": str(r["mid"] or ""),
                              "due": due, "mastery": m, "reason": reason})
            except Exception:  # noqa: BLE001 -- one bad row skips
                continue
        return picks
    except Exception:  # noqa: BLE001 -- picker never raises
        return []


def box_html(picks) -> str:
    """Result-screen suggestion box; "" when none due (legacy)."""
    try:
        from . import scrollpos as scrollposmod
        rows = [p for p in (picks or []) if isinstance(p, dict)]
        if not rows:
            return ""
        lis = []
        for p in rows[:MAX_LIMIT]:
            cid = str(p.get("card_id", "") or "")
            name = str(p.get("concept", "") or cid or "next card")
            href = f"/due#{scrollposmod.card_anchor(cid)}"
            reason = str(p.get("reason", "") or "")
            why = whyseemod.reason_html(reason)
            tail = f" {why}" if why else ""
            lis.append(f"<li><a href='{html.escape(href, True)}'>"
                       f"{html.escape(name)}</a>"
                       f" <small>{html.escape(reason)}</small>"
                       f"{tail}</li>")
        n = len(lis)
        return (f"<section id='{SECTION_ANCHOR}'><h2>What to review next</h2>"
                f"<p>{n} card{'s' if n != 1 else ''} still due -- "
                f"keep the momentum.</p><ol>{''.join(lis)}</ol></section>")
    except Exception:  # noqa: BLE001 -- box never breaks the result
        return ""


def box_for(db_path, answered_card_id="",
            limit=DEFAULT_LIMIT, now="") -> str:
    """Pick + render for the submit_review caller; "" when none due."""
    try:
        return box_html(pick_next(db_path, answered_card_id, limit, now))
    except Exception:  # noqa: BLE001
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch28 home module."""
    sample = box_html([{"card_id": "ex001", "concept": "add",
                        "module_id": "m1", "due": "2026-09-20T00:00:00Z",
                        "mastery": 0.2,
                        "reason": "due 2026-09-20; mastery 0.20"}])
    return (
        f"<h3 id='{STATUS_ANCHOR}'>What to review next "
        "<small>(improvement)</small></h3>"
        "<p>After each answer, the result screen suggests the next due "
        "cards -- earliest due first, each linked back into the queue. "
        "<code>groundwork/nextup.py</code> queries the live due queue "
        "minus the just-answered card (<code>MCPServer.submit_review</code> "
        "attaches the box); nothing left due renders nothing at all. "
        "A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "what-next",
        "kind": "improvement",
        "title": "What to review next",
        "blurb": ("After each answer, the result screen suggests the next "
                  "due cards with links back into the queue."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
