"""Contractor ramp packs: the Due queue scoped to one work area (F-162).

A contractor ramping on one subsystem should study only that area.
A scope is a normalized ``concepts.file`` path prefix (a directory, a
file, or a file stem); ``?scope=<prefix>`` on /due narrows the queue
plus progress to matching concepts. The "contractor" is the local
learner with a scope filter -- everything derives from existing
local data, no teams, no accounts.

Caller: ``Handler.due_html`` filters right after the due fetch and
prepends the pack banner. Empty scope returns the list untouched and
renders "" (legacy bytes); unknown scope (valid syntax, zero
concepts match) shows the full queue with an honest notice. Stdlib
only (``html``) plus lazy sibling reads (``db``, ``ownership``,
``sched``); never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b27-ramppack"
BOX_ANCHOR = "ramppack-pack"


def normalize_scope(raw) -> str:
    """Canonical scope prefix; "" when missing/hostile."""
    try:
        if not isinstance(raw, str):
            return ""
        cleaned = raw.strip().replace("\\", "/")
        while cleaned.startswith("./"):
            cleaned = cleaned[2:]
        cleaned = cleaned.strip("/")
        return cleaned
    except Exception:  # noqa: BLE001
        return ""


def match(scope, file) -> bool:
    """True when a concept file falls inside the scope.

    Empty scope matches all (unscoped queue). Otherwise the file must
    equal the scope or extend it at a boundary: a subdirectory, or a
    file extension on a stem (``groundwork/cards`` covers
    ``groundwork/cards.py`` but ``groundwork/card`` does not).
    """
    try:
        s = normalize_scope(scope)
        f = normalize_scope(file)
        if not s:
            return True
        if not f:
            return False
        if f == s:
            return True
        if f.startswith(s + "/"):
            return True
        return f.startswith(s) and f[len(s):].startswith(".")
    except Exception:  # noqa: BLE001
        return False


def filter_due(due, files_by_concept, scope):
    """Due rows narrowed to the scope; the list untouched when empty."""
    try:
        s = normalize_scope(scope)
        if not s:
            return due
        if not isinstance(files_by_concept, dict):
            return due
        return [c for c in (due or [])
                if match(s, files_by_concept.get(c.get("concept_id", ""), ""))]
    except Exception:  # noqa: BLE001
        return due


def files_for(db_path, concept_ids) -> dict:
    """{concept_id: file} for the ids; {} on error. Never raises."""
    try:
        from . import db as dbmod
        ids = [c for c in (concept_ids or []) if c]
        if not ids:
            return {}
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                f"SELECT id, file FROM concepts WHERE id IN "
                f"({','.join('?' * len(ids))})", ids).fetchall()
        finally:
            con.close()
        return {r["id"]: r["file"] or "" for r in rows}
    except Exception:  # noqa: BLE001
        return {}


def _all_files(db_path) -> dict:
    """{concept_id: file} for every concept; {} on error."""
    try:
        from . import db as dbmod
        con = dbmod.connect(db_path)
        try:
            rows = con.execute("SELECT id, file FROM concepts").fetchall()
        finally:
            con.close()
        return {r["id"]: r["file"] or "" for r in rows}
    except Exception:  # noqa: BLE001
        return {}


def scope_due(db_path, due, scope):
    """Due rows in scope; full queue for empty/unknown scopes."""
    try:
        s = normalize_scope(scope)
        if not s:
            return due
        files = _all_files(db_path)
        if not any(match(s, f) for f in files.values()):
            return due  # unknown scope: full queue + notice in banner
        return filter_due(due, files, s)
    except Exception:  # noqa: BLE001
        return due


def scope_stats(db_path, scope) -> dict:
    """{concepts, due, owned} inside the scope; zeros on error."""
    out = {"concepts": 0, "due": 0, "owned": 0}
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        from . import sched as schedmod
        s = normalize_scope(scope)
        files = _all_files(db_path)
        in_scope = {cid for cid, f in files.items() if match(s, f)} if s else set(files)
        out["concepts"] = len(in_scope)
        if not in_scope:
            return out
        con = dbmod.connect(db_path)
        try:
            now = schedmod.iso(schedmod.utcnow())
            ids = sorted(in_scope)
            out["due"] = con.execute(
                "SELECT COUNT(*) FROM cards WHERE concept_id IN "
                f"({','.join('?' * len(ids))})"
                " AND due <= ? AND stale = 0",
                ids + [now]).fetchone()[0] or 0
            mids = {r["module_id"] for r in con.execute(
                f"SELECT DISTINCT module_id FROM concepts WHERE id IN "
                f"({','.join('?' * len(ids))})", ids).fetchall()}
            for mid in mids:
                omap = ownmod.owned_map(con, mid)
                out["owned"] += sum(1 for cid, (_, o) in omap.items()
                                    if o and cid in in_scope)
        finally:
            con.close()
    except Exception:  # noqa: BLE001
        pass
    return out


def top_areas(db_path, limit=6) -> list:
    """[(top-level dir, due count)] busiest first; [] on error."""
    try:
        from . import db as dbmod
        from . import sched as schedmod
        con = dbmod.connect(db_path)
        try:
            now = schedmod.iso(schedmod.utcnow())
            rows = con.execute(
                "SELECT concepts.file AS f FROM cards"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE cards.due <= ? AND cards.stale = 0",
                (now,)).fetchall()
        finally:
            con.close()
        counts: dict = {}
        for r in rows:
            f = normalize_scope(r["f"] or "")
            area = f.split("/", 1)[0] if f else ""
            if area:
                counts[area] = counts.get(area, 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        try:
            n = max(1, int(limit))
        except (TypeError, ValueError):
            n = 6
        return ranked[:n]
    except Exception:  # noqa: BLE001
        return []


def pack_html(db_path, scope, due=None) -> str:
    """Scoped-queue banner; "" when unscoped. Never raises."""
    try:
        s = normalize_scope(scope)
        if not s:
            return ""
        files = _all_files(db_path)
        known = any(match(s, f) for f in files.values())
        areas = "".join(
            f" <a href='/due?scope={html.escape(a, quote=True)}'>"
            f"{html.escape(a)}</a> ({n})"
            for a, n in top_areas(db_path))
        clear = " <a href='/due'>Clear scope</a>"
        if not known:
            return (
                f"<p id='{BOX_ANCHOR}'><small>Unknown scope "
                f"<b>{html.escape(s)}</b> -- showing the full queue."
                f"{areas}{clear}</small></p>")
        stats = scope_stats(db_path, s)
        names = sorted({html.escape(f.rsplit('/', 1)[-1])
                        for cid, f in files.items() if match(s, f)})
        shown = ", ".join(names[:8])
        more = f" +{len(names) - 8} more" if len(names) > 8 else ""
        return (
            f"<p id='{BOX_ANCHOR}'>Ramp pack: <b>{html.escape(s)}</b> -- "
            f"{stats['due']} due, {stats['owned']}/{stats['concepts']} owned"
            f"<br><small>{shown}{more}{areas}{clear}</small></p>")
    except Exception:  # noqa: BLE001
        return ""


def section_html(db_path="") -> str:
    """Status home with live top-area links; static fallback w/o DB."""
    try:
        areas = top_areas(db_path) if db_path else []
        if areas:
            links = "".join(
                f"<li><a href='/due?scope={html.escape(a, quote=True)}'>"
                f"{html.escape(a)}</a> -- {n} due</li>"
                for a, n in areas)
            demo = f"<ul>{links}</ul>"
        else:
            demo = ("<p><small>Study only your work area: open the Due "
                    "queue with <code>?scope=&lt;path-prefix&gt;</code> "
                    "to narrow cards and progress to one subsystem."
                    "</small></p>")
        return (
            f"<section id='{STATUS_ANCHOR}'><h3>Contractor ramp packs "
            "<small>(feature)</small></h3>"
            "<p>A scoped Due queue with scoped progress for ramping on "
            "one subsystem. <code>groundwork/ramppack.py</code>.</p>"
            f"{demo}</section>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<section id='{STATUS_ANCHOR}'><h3>Contractor ramp packs"
                "</h3><p>Ramp packs temporarily unavailable.</p></section>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "ramppack-pack",
        "kind": "feature",
        "title": "Contractor ramp packs",
        "blurb": ("Study only your work area: a scoped Due queue with "
                  "scoped progress for ramping on one subsystem."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
