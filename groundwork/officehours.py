"""Office-hours bring-list fed by confusing flags (F-178).

The learner's own confusing flags (I-134) double as their office-hours
agenda: the longest-flagged sections, oldest confusion first, each
linked to its module page so the learner can re-read before asking.
No helper, signup, or queue table: this single-learner app has no
honest source for those, so the shippable core is the prioritized
bring-list, not the helper.

Pure helpers over flag rows plus a thin read of the existing
confusing_flags table (same CREATE TABLE IF NOT EXISTS shape as
confusing.py, no schema change to existing tables).

Caller path (Due queue, never a Status demo): ``Handler.due_html``
appends ``bring_html(db_path)`` to its first parts element (same-line
join). With no flag data every helper returns its legacy value (empty
list, "" markup), so unflagged Due pages render byte-identical.
"""
from __future__ import annotations

import html as htmlmod

from . import db as dbmod

STATUS_ANCHOR = "status-b28-officehours"
BRING_ID = "officehours"
BRING_LIMIT = 5


def _ensure_table(con) -> None:
    """confusing_flags table; identical additive shape, no migration."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS confusing_flags ("
        " section_id TEXT PRIMARY KEY,"
        " flagged_at TEXT NOT NULL DEFAULT"
        " (strftime('%Y-%m-%dT%H:%M:%SZ','now')))")


def parse_section(section) -> tuple:
    """(concept-id, block-slug) for a flag key; ("","") when hostile."""
    try:
        if not isinstance(section, str) or "#" not in section:
            return ("", "")
        cid, block = section.split("#", 1)
        cid, block = cid.strip(), block.strip()
        if not cid or not block or ":" not in cid:
            return ("", "")
        return (cid, block)
    except Exception:  # noqa: BLE001 -- parsing never raises
        return ("", "")


def module_of(section) -> str:
    """Module id owning a flag key; "" when unparsable. Never raises."""
    try:
        cid, _block = parse_section(section)
        return cid.split(":", 1)[0] if cid else ""
    except Exception:  # noqa: BLE001 -- lookup never raises
        return ""


def label_for(section) -> str:
    """Human label for a flag key: block slug as words. Never raises."""
    try:
        _cid, block = parse_section(section)
        if not block:
            return "a flagged section"
        words = block.replace("-", " ").replace("_", " ").strip()
        return words or block
    except Exception:  # noqa: BLE001 -- labeling never raises
        return "a flagged section"


def order_flags(rows) -> list:
    """Flagged section ids, oldest-flagged first. Pure; never raises.

    rows is [(section_id, flagged_at-iso)]; ties break by section id
    so the order is stable. Hostile rows are skipped, hostile input
    yields [] (legacy: nothing queued).
    """
    try:
        if not isinstance(rows, (list, tuple)):
            return []
        good = []
        for row in rows:
            try:
                sid, when = row
            except (TypeError, ValueError):
                continue
            if isinstance(sid, str) and sid.strip():
                good.append((sid, when if isinstance(when, str) else ""))
        good.sort(key=lambda pair: (pair[1], pair[0]))
        return [sid for sid, _when in good]
    except Exception:  # noqa: BLE001 -- queue never raises
        return []


def fetch_flags(db_path: str) -> list:
    """[(section_id, flagged_at)] oldest first; [] when none. Never raises."""
    try:
        con = dbmod.connect(db_path)
        try:
            _ensure_table(con)
            rows = con.execute(
                "SELECT section_id, flagged_at FROM confusing_flags"
                " ORDER BY flagged_at, section_id").fetchall()
        finally:
            con.close()
        return [(r[0], r[1]) for r in rows]
    except Exception:  # noqa: BLE001 -- render path never raises
        return []


def bring_list(db_path: str, limit: int = BRING_LIMIT) -> list:
    """Top-N bring items: {section, mid, cid, block, label}. Never raises."""
    try:
        try:
            cap = int(limit)
        except (TypeError, ValueError):
            cap = BRING_LIMIT
        if cap <= 0:
            return []
        out = []
        for sid in order_flags(fetch_flags(db_path))[:cap]:
            cid, block = parse_section(sid)
            if not cid:
                continue
            out.append({"section": sid, "mid": module_of(sid),
                        "cid": cid, "block": block,
                        "label": label_for(sid)})
        return out
    except Exception:  # noqa: BLE001 -- render path never raises
        return []


def queue_count(db_path: str) -> int:
    """Number of flagged sections awaiting office hours. Never raises."""
    try:
        return len(order_flags(fetch_flags(db_path)))
    except Exception:  # noqa: BLE001 -- counting never raises
        return 0


def bring_html(db_path: str = "", limit: int = BRING_LIMIT) -> str:
    """Bring-list box for the Due page; "" when no flags. Never raises.

    Empty db_path or an empty flags table returns "" so unflagged Due
    pages render byte-identical (legacy no-data fallback).
    """
    try:
        items = bring_list(db_path, limit) if db_path else []
        if not items:
            return ""
        total = queue_count(db_path)
        lines = []
        for pos, item in enumerate(items, 1):
            mid = htmlmod.escape(item["mid"], quote=True)
            label = htmlmod.escape(item["label"])
            lines.append(
                f"<li>{pos}. <a href='/modules/{mid}'>{label}</a></li>")
        extra = ""
        if total > len(items):
            extra = (f"<p><small>...and {total - len(items)} more "
                     f"flagged.</small></p>")
        return (
            f"<div id='{BRING_ID}'><h3>Bring to office hours</h3>"
            f"<p>Your {total} flagged section(s), "
            f"longest-confused first: re-read, then ask.</p>"
            f"<ol>{''.join(lines)}</ol>{extra}</div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch28 home module."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Office-hours queue "
            "<small>(feature)</small></h3>"
            "<p>Your confusing flags become your office-hours agenda: "
            "<code>groundwork/officehours.py</code> lists your "
            "longest-flagged sections first on the Due page, each linked "
            "to its lesson; with no flags the Due page renders exactly "
            "as before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Office-hours queue</h3>"
                "<p>Office-hours help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    # Parent fix (Batch 19 precedent): the live box only renders with
    # flags, so the tour points at the always-rendered Status section
    # instead of /due (the tour gate renders flagless fixtures).
    return {
        "id": "officehours-queue",
        "kind": "feature",
        "title": "Office-hours bring-list",
        "blurb": ("Your flagged sections, longest-confused first -- "
                  "bring these to office hours."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
