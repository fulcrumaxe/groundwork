"""Teaching certificates per module pack (F-112).

Own a whole pack and you could teach it: a certificate issues per
module at full owned coverage, dated by the last concept owned,
with a delayed-verified seal once three weeks pass since issue
(retention proved, not just crammed). Partial packs show progress
("3/5 — 2 to go"); empty libraries keep an anchor-stable
to-earn line. Pure reads over existing tables; never raises.
"""
from __future__ import annotations

import html
from datetime import timedelta

STATUS_ANCHOR = "status-b23-teachcert"

DELAY_DAYS = 21


def certificates(db_path: str) -> list:
    """[{pack, summary, owned, total, coverage, issued, delayed}]."""
    try:
        from . import db as dbmod
        from . import milestones as milesmod
        owned = milesmod.owned_dates(db_path)
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id, task_summary FROM modules").fetchall()
            cons = con.execute(
                "SELECT id, module_id FROM concepts").fetchall()
        finally:
            con.close()
        by_mod: dict = {}
        for r in cons:
            by_mod.setdefault(str(r["module_id"]), []).append(str(r["id"]))
        out = []
        for m in mods:
            mid = str(m["id"])
            members = by_mod.get(mid, [])
            if not members:
                continue
            have = [c for c in members if c in owned]
            if not have:
                continue
            issued = max(owned[c] for c in have)
            out.append({"pack": mid,
                        "summary": m["task_summary"] or mid,
                        "owned": len(have), "total": len(members),
                        "coverage": len(have) / len(members),
                        "issued": issued,
                        "delayed": _delayed(issued)})
        return out
    except Exception:  # noqa: BLE001 -- certificates must never raise
        return []


def _delayed(issued: str) -> bool:
    try:
        from . import sched as schedmod
        when = schedmod.parse_iso(str(issued or ""))
        return (schedmod.utcnow() - when) >= timedelta(days=DELAY_DAYS)
    except (ValueError, TypeError):
        return False


def eligible(db_path: str) -> list:
    """Fully-owned packs (coverage == 1.0)."""
    try:
        return [c for c in certificates(db_path) if c["coverage"] >= 1.0]
    except Exception:  # noqa: BLE001 -- eligibility must never raise
        return []


def section_html(db_path: str) -> str:
    """Certificates on History; to-earn line when none."""
    try:
        certs = certificates(db_path)
        if not certs:
            return (f"<h2 id='teaching-certificates'>Teaching "
                    f"certificates</h2><p>No certificates yet — own a "
                    f"whole pack and it certifies you could teach it.</p>")
        bits = []
        for c in certs:
            seal = (" <b>delayed-verified</b>" if c["delayed"]
                    else " <small>(delayed seal pending)</small>")
            if c["coverage"] >= 1.0:
                bits.append(
                    f"<p>Teaching certificate: "
                    f"<a href='/modules/{c['pack']}'>"
                    f"{html.escape(str(c['summary']))}</a> — "
                    f"{c['owned']}/{c['total']} owned, issued "
                    f"{html.escape(str(c['issued'])[:10])}.{seal}</p>")
            else:
                left = c["total"] - c["owned"]
                bits.append(
                    f"<p><a href='/modules/{c['pack']}'>"
                    f"{html.escape(str(c['summary']))}</a> — "
                    f"{c['owned']}/{c['total']} owned, {left} to go.</p>")
        return (f"<h2 id='teaching-certificates'>Teaching "
                f"certificates</h2>{''.join(bits)}")
    except Exception:  # noqa: BLE001 -- section must never raise
        return ("<h2 id='teaching-certificates'>Teaching "
                "certificates</h2><p>Certificates temporarily "
                "unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Teaching certificates "
            "<small>(feature)</small></h3>"
            "<p>Own a whole pack, prove you could teach it — "
            "<code>groundwork/teachcert.py</code> issues a certificate "
            "at full owned coverage with a delayed-verified seal once "
            "three weeks pass since issue.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Teaching certificates</h3>"
                "<p>Certificate help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "teaching-certificates",
        "kind": "feature",
        "title": "Teaching certificates",
        "blurb": ("Own a whole pack — proof you could teach it."),
        "path": "/reviews",
        "anchor": "teaching-certificates",
    }
