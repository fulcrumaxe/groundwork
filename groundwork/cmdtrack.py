"""Incident-commander certification track (F-186).

Three gated stages over existing card types \u2014 replay (incident-replay,
type 77) -> diagnose (pressure-drill, type 76) -> decide (rollback-plan,
type 48, grounded on live concept names). Stage N+1 unlocks on owned
proofs of stage N: two passing reviews (grade >= 4) on stage-N cards,
the pass-plus-return-visit shape of the owned rule (ownership.py).
State renders from live reviews and concepts.mastery \u2014 no DB or schema
changes, no new storage.

One delegation (decision 283): ``apply_track(db_path, due)`` returns the
(queue, banner) pair \u2014 locked-stage track cards withheld, unlocked
track cards stage-ordered first, every other row untouched \u2014 plus the
checklist banner with its honest lock notice. A single delegation keeps
the filter and its notice consistent by construction.

Caller (parent wires; same-line joins, no new lines): web.Handler.due_html.
Status home + tour entry below; the parent joins both.
"""

from __future__ import annotations

import html

STATUS_ANCHOR = "status-b29-cmdtrack"
SECTION_ANCHOR = "commander-track"

# Key, title, exercise_type, proofs to clear, blurb. Types cite their
# owners: incident.TYPE_NUM (77), pressure.TYPE_NUM (76),
# rollback.TYPE_NUM (48).
STAGES = (
    {"key": "replay", "title": "Replay", "type": "77", "need": 2,
     "blurb": "replay a past outage (incident-replay)"},
    {"key": "diagnose", "title": "Diagnose", "type": "76", "need": 2,
     "blurb": "name the root cause on a 90s clock (pressure-drill)"},
    {"key": "decide", "title": "Decide", "type": "48", "need": 2,
     "blurb": "order the rollback from live data (rollback-plan)"},
)

_ORDER = {s["type"]: i for i, s in enumerate(STAGES)}


def _placeholders(n: int) -> str:
    return ",".join("?" * max(1, n))


def _proofs(db_path: str) -> dict:
    """{stage type: passing-review count}; {} on error."""
    try:
        from . import db as dbmod
        types = list(_ORDER)
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.exercise_type AS t, COUNT(*) AS n"
                " FROM reviews JOIN cards ON cards.id = reviews.card_id"
                f" WHERE reviews.grade >= 4 AND cards.exercise_type IN"
                f" ({_placeholders(len(types))}) GROUP BY t",
                types).fetchall()
        finally:
            con.close()
        return {str(r["t"]): int(r["n"] or 0) for r in rows}
    except Exception:  # noqa: BLE001 -- stats never raise
        return {}


def _mastery(db_path: str) -> dict:
    """{stage type: avg concepts.mastery over practiced concepts}."""
    try:
        from . import db as dbmod
        types = list(_ORDER)
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.exercise_type AS t,"
                " AVG(concepts.mastery) AS m FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " JOIN concepts ON concepts.id = cards.concept_id"
                f" WHERE cards.exercise_type IN"
                f" ({_placeholders(len(types))}) GROUP BY t",
                types).fetchall()
        finally:
            con.close()
        out = {}
        for r in rows:
            try:
                out[str(r["t"])] = float(r["m"]) if r["m"] is not None else None
            except (TypeError, ValueError):
                continue
        return out
    except Exception:  # noqa: BLE001 -- stats never raise
        return {}


def _track_card_count(db_path: str) -> int:
    """Stage-type cards in the library; 0 on error."""
    try:
        from . import db as dbmod
        types = list(_ORDER)
        con = dbmod.connect(db_path)
        try:
            return int(con.execute(
                "SELECT COUNT(*) FROM cards WHERE exercise_type IN"
                f" ({_placeholders(len(types))})", types).fetchone()[0] or 0)
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- stats never raise
        return 0


def track_state(db_path: str) -> dict:
    """Gated stage states from live reviews + mastery; never raises."""
    try:
        proof_map, mast_map = _proofs(db_path), _mastery(db_path)
        stages = []
        prev_cleared = True
        for i, s in enumerate(STAGES):
            n = int(proof_map.get(s["type"], 0) or 0)
            cleared = n >= s["need"]
            if cleared:
                status = "cleared"
            elif prev_cleared:
                status = "open"
            else:
                status = "locked"
            stages.append({"key": s["key"], "title": s["title"],
                           "type": s["type"], "proofs": n,
                           "need": s["need"], "status": status,
                           "mastery": mast_map.get(s["type"]),
                           "opener": STAGES[i - 1]["title"] if i else ""})
            prev_cleared = cleared
        signal = any(s["proofs"] for s in stages) or _track_card_count(db_path) > 0
        return {"stages": stages,
                "certified": all(s["status"] == "cleared" for s in stages),
                "signal": bool(signal)}
    except Exception:  # noqa: BLE001 -- state never raises
        return {"stages": [{"key": s["key"], "title": s["title"],
                            "type": s["type"], "proofs": 0,
                            "need": s["need"], "status": "locked",
                            "mastery": None, "opener": ""} for s in STAGES],
                "certified": False, "signal": False}


def _card_type(card) -> str | None:
    """Stage type of a Due row, else None (pass-through); never raises."""
    try:
        t = str(card.get("exercise_type", "") or "") if isinstance(card, dict) else ""
    except Exception:  # noqa: BLE001 -- hostile rows pass through
        return None
    return t if t in _ORDER else None


def apply_track(db_path, due):
    """(queue, banner): stage-gated Due queue plus its checklist banner.

    Locked-stage track cards are withheld, unlocked track cards lead in
    stage order, every other row keeps its relative order and content.
    Legacy fallback: (due, "") with no track signal, hostile inputs, or
    an unreadable DB \u2014 Due never breaks. Never raises.
    """
    try:
        if not isinstance(due, list):
            return due, ""
        state = track_state(db_path)
        if not state.get("signal"):
            return due, ""
        unlocked = {s["type"] for s in state["stages"]
                    if s["status"] in ("open", "cleared")}
        kept, rest, withheld = [], [], 0
        for c in due:
            t = _card_type(c)
            if t is None:
                rest.append(c)
            elif t in unlocked:
                kept.append(c)
            else:
                withheld += 1
        kept.sort(key=lambda c: _ORDER[_card_type(c)])
        return kept + rest, banner_html(db_path, withheld)
    except Exception:  # noqa: BLE001 -- gate must never raise
        return due, ""


def banner_html(db_path: str, withheld: int = 0) -> str:
    """Checklist banner for the Due queue; "" with no signal."""
    try:
        state = track_state(db_path)
        if not state.get("signal"):
            return ""
        items = []
        for s in state["stages"]:
            bits = f"{s['proofs']}/{s['need']} proofs"
            if s["mastery"] is not None:
                bits += f" \u00b7 mastery {s['mastery']:.0%}"
            if s["status"] == "cleared":
                items.append(f"<li>{s['title']} - cleared ({bits})</li>")
            elif s["status"] == "open":
                items.append(f"<li>{s['title']} - open ({bits})</li>")
            else:
                items.append(f"<li>{s['title']} - locked "
                             f"(opens when {s['opener']} clears)</li>")
        cert = ("<p><b>Incident-commander certified</b> \u2014 replay, "
                "diagnose, and decide all cleared.</p>"
                if state["certified"] else "")
        note = ""
        try:
            n = max(0, int(withheld))
        except (TypeError, ValueError):
            n = 0
        locked = [s for s in state["stages"] if s["status"] == "locked"]
        if n and locked:
            note = (f"<p><small>{n} locked card"
                    f"{'s' if n != 1 else ''} withheld from this queue "
                    f"until {locked[0]['title']} opens.</small></p>")
        return (
            f"<section id='{SECTION_ANCHOR}'>"
            "<h2>Incident-commander track</h2>"
            "<p>Replay, diagnose, then decide \u2014 each stage opens on two "
            "passing proofs from the last.</p>"
            f"<ol>{''.join(items)}</ol>{cert}{note}</section>")
    except Exception:  # noqa: BLE001 -- banner must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; the parent joins it into batch29 home."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Incident-commander track "
        "<small>(feature)</small></h3>"
        "<p>Replay, diagnose, then decide \u2014 a gated certification track over "
        "incident-replay, pressure-drill, and rollback-plan cards. Each stage "
        "opens on two passing proofs from the last; the Due queue withholds "
        "locked-stage cards and leads with the open stage. "
        "<code>groundwork/cmdtrack.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    # Parent fix (Batch 19/F-178 precedent): the live banner only
    # renders with track cards in the library, so the tour points at
    # the always-rendered Status section instead of /due (the tour
    # gate renders trackless fixtures).
    return {
        "id": "commander-track",
        "kind": "feature",
        "title": "Incident-commander track",
        "blurb": ("Replay, diagnose, then decide \u2014 gated commander stages "
                  "over live reviews and mastery."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
