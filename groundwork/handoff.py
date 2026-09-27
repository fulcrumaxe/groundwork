"""Handoff packs: export your owned map for a successor (F-160).

A leaving dev's hard-won ownership map usually walks out the door
with them. This module builds a handoff pack: the module's share
document verbatim plus a ``handoff`` block of owned proofs (concept,
attempts, owned) and numbered successor steps. The pack IS a valid
share doc -- ``share.import_module`` reads only
format/module/concepts/cards and ignores the extra key -- so the
successor runs the existing ``import-module`` path unchanged: teaching
content lands with fresh scheduling, review rows never cross the
wire, and the handoff block stays human-readable evidence (not
imported, not trusted blindly).

Caller: ``history.history_html`` lead block renders every module's
pack with its proof table and copy-paste JSON. No owned concepts
anywhere renders an anchor-stable placeholder. Stdlib only
(``json``, ``html``, ``datetime``) plus lazy sibling reads (``db``,
``share``, ``ownership``); section builders never raise.
"""
from __future__ import annotations

import html
import json
from datetime import datetime, timezone

STATUS_ANCHOR = "status-b27-handoff"
BOX_ANCHOR = "handoff"
FORMAT = "groundwork-handoff/1"


def successor_steps(owned_count: int, total: int) -> list:
    """Numbered successor steps as data (rendered, never executed)."""
    try:
        o = int(owned_count)
    except (TypeError, ValueError):
        o = 0
    try:
        t = int(total)
    except (TypeError, ValueError):
        t = 0
    return [
        "Save the pack JSON below as handoff.json.",
        "Run: python3 -m groundwork import-module --in handoff.json",
        (f"The {o}/{t} owned/proof claims are readable evidence of what "
         "the leaver proved -- reviews never transfer, scheduling "
         "restarts fresh."),
        "Re-prove each claim by drilling: owned status is earned, not given.",
    ]


def build_pack(db_path, mid: str) -> dict:
    """Share doc verbatim plus the ``handoff`` evidence block.

    Raises KeyError for an unknown module (inherited from
    ``share.export_module``).
    """
    from . import db as dbmod
    from . import ownership as ownmod
    from . import share as sharemod
    pack = sharemod.export_module(db_path, mid)
    con = dbmod.connect(db_path)
    try:
        names = {r["id"]: r["name"] for r in con.execute(
            "SELECT id, name FROM concepts WHERE module_id=?", (mid,))}
        omap = ownmod.owned_map(con, mid)
    finally:
        con.close()
    rows = [{"concept": names.get(cid, cid), "attempts": a,
             "owned": bool(o)} for cid, (a, o) in sorted(omap.items())]
    owned_n = sum(1 for r in rows if r["owned"])
    pack["handoff"] = {
        "format": FORMAT,
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "owned": rows,
        "owned_count": owned_n,
        "total": len(rows),
        "steps": successor_steps(owned_n, len(rows)),
    }
    return pack


def pack_json(pack) -> str:
    """Stable JSON text for copy-paste; "" when hostile."""
    try:
        return json.dumps(pack, indent=2, sort_keys=True)
    except Exception:  # noqa: BLE001
        return ""


def is_pack(doc) -> bool:
    """True for a share doc carrying a handoff block."""
    try:
        from . import share as sharemod
        return (isinstance(doc, dict) and doc.get("format") == sharemod.FORMAT
                and isinstance(doc.get("handoff"), dict)
                and doc["handoff"].get("format") == FORMAT)
    except Exception:  # noqa: BLE001
        return False


def packs(db_path) -> list:
    """Light per-module summaries; [] on error. Never raises."""
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id, task_summary FROM modules"
                " ORDER BY created_at DESC").fetchall()
            out = []
            for m in mods:
                omap = ownmod.owned_map(con, m["id"])
                owned_n = sum(1 for _, o in omap.values() if o)
                out.append({"mid": m["id"],
                            "title": m["task_summary"] or m["id"],
                            "owned": owned_n, "total": len(omap)})
            return out
        finally:
            con.close()
    except Exception:  # noqa: BLE001
        return []


def _pack_block(db_path, summary: dict) -> str:
    """One module's proof table + pack JSON + steps; "" on error."""
    try:
        pack = build_pack(db_path, summary["mid"])
        hand = pack["handoff"]
        rows = "".join(
            f"<tr><td>{html.escape(str(r['concept']))}</td>"
            f"<td>{r['attempts']}</td>"
            f"<td>{'[x]' if r['owned'] else '[ ]'}</td></tr>"
            for r in hand["owned"])
        steps = "".join(f"<li>{html.escape(s)}</li>"
                        for s in hand["steps"])
        return (
            f"<h3>{html.escape(summary['title'])}</h3>"
            f"<p>Owned {hand['owned_count']}/{hand['total']}</p>"
            "<table class='log'><tr><th>Concept</th><th>Attempts</th>"
            f"<th>Owned</th></tr>{rows}</table>"
            f"<details><summary>Pack JSON</summary><pre>"
            f"{html.escape(pack_json(pack))}</pre></details>"
            f"<ol>{steps}</ol>")
    except Exception:  # noqa: BLE001
        return ""


def section_html(db_path) -> str:
    """History-page handoff packs; anchor-stable placeholder when empty."""
    try:
        mods = packs(db_path)
        blocks = "".join(_pack_block(db_path, m) for m in mods)
        if not blocks:
            inner = ("<p>No owned concepts yet -- answer cards first, "
                     "then export a handoff pack for your successor.</p>")
        else:
            inner = blocks
        return (f"<section id='{BOX_ANCHOR}'><h2>Handoff packs</h2>"
                f"{inner}</section>")
    except Exception:  # noqa: BLE001 -- caller keeps legacy bytes
        return ""


def status_html(db_path) -> str:
    """Anchored status subsection with live packable counts."""
    try:
        mods = packs(db_path)
        owned_n = sum(m["owned"] for m in mods)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Handoff packs "
            "<small>(feature)</small></h3>"
            "<p>Leaving? Export your owned-concepts map plus proofs as "
            "one file your successor imports with the existing "
            "<code>import-module</code> path -- progress transfers, "
            "private reviews stay behind. "
            f"Live: {len(mods)} modules, {owned_n} owned concepts "
            "packable. See <a href='/reviews#handoff'>History</a>. "
            "<code>groundwork/handoff.py</code>.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Handoff packs</h3>"
                "<p>Handoff packs temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "handoff-packs",
        "kind": "feature",
        "title": "Handoff packs",
        "blurb": ("Leaving? Export your owned-concepts map plus proofs as "
                  "one file your successor imports with the existing "
                  "import-module path -- progress transfers, private "
                  "reviews stay behind."),
        "path": "/reviews",
        "anchor": BOX_ANCHOR,
    }
