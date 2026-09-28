"""Security-champions track (F-190): threat-model + scan types per area.

One work area's threat-model, secret-scan, and input-validation cards
gathered weakest-first, with progress proven by owned concepts. Scope
rides the existing ``?scope=`` file prefix (ramppack boundary rule),
so no new param or schema is needed: the box narrows what the queue
already narrowed. (Batch note: ``?service=`` is the repo dimension,
owned by F-185's on-call packs per decision 298; this track scopes by
file area, like F-191.)

Cards with no attempts surface first at 0.0 (unknown is weakest);
average grade, then due date, then card id break ties. Unscoped (or
an empty pool) renders "" so legacy bytes survive. Stdlib only
(``html``) plus lazy sibling reads; no DB/schema changes. Caller:
Handler.due_html beside the other track joins. Never raises; never
mutates inputs.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b29-secchamp"
TRACK_ANCHOR = "secchamp-track"
SEC_TYPES = ("49", "50", "51")
TYPE_LABELS = {"49": "threat-model", "50": "secret-scan",
               "51": "input-validation"}
DEFAULT_SIZE = 8
MAX_SIZE = 16
_MISSING_DUE = "\uffff"


def normalize_scope(raw) -> str:
    """Canonical scope prefix; "" when missing/hostile."""
    try:
        if not isinstance(raw, str):
            return ""
        cleaned = raw.strip().replace("\\", "/")
        while cleaned.startswith("./"):
            cleaned = cleaned[2:]
        return cleaned.strip("/")
    except Exception:  # noqa: BLE001
        return ""


def match(scope, file) -> bool:
    """True when a concept file falls inside the scope.

    Ramppack boundary rule: the file must equal the scope or extend
    it at a boundary -- a subdirectory, or a file extension on a stem
    (``payments/api`` covers ``payments/api.py`` but ``payments/ap``
    does not). Empty scope matches all (unscoped track).
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


def _size_of(size) -> int:
    try:
        return max(0, min(int(size), MAX_SIZE))
    except (TypeError, ValueError):
        return DEFAULT_SIZE


def pick_track(db_path, scope, size=DEFAULT_SIZE) -> list:
    """Up to `size` security-card picks in `scope`, weakest first.

    Each pick: {card_id, concept_id, name, module_id, exercise_type,
    type_name, due, attempts, avg, reason}. Cards with no attempts
    surface first at 0.0 (unknown is weakest); due date then card id
    break ties. Empty or hostile input yields []. Never raises; never
    mutates inputs.
    """
    try:
        from . import db as dbmod
        want = _size_of(size)
        files = _all_files(db_path)
        if not files:
            return []
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.id AS cid, cards.concept_id AS concept_id,"
                " concepts.name AS name, concepts.module_id AS mid,"
                " cards.exercise_type AS etype, cards.due AS due,"
                " COUNT(reviews.id) AS n, AVG(reviews.grade) AS g"
                " FROM cards JOIN concepts ON concepts.id = cards.concept_id"
                " LEFT JOIN reviews ON reviews.card_id = cards.id"
                " WHERE cards.stale = 0"
                " GROUP BY cards.id").fetchall()
        finally:
            con.close()
        pool = []
        for r in rows:
            etype = str(r["etype"] if r["etype"] is not None else "")
            cid = r["concept_id"] or ""
            if etype not in SEC_TYPES or not match(scope, files.get(cid, "")):
                continue
            n = r["n"] or 0
            try:
                avg = float(r["g"]) if n else 0.0
            except (TypeError, ValueError):
                avg = 0.0
            avg = avg if avg == avg else 0.0  # NaN is weakest, never crashes sort
            due = r["due"] if isinstance(r["due"], str) and r["due"] else ""
            pool.append((avg, due or _MISSING_DUE, str(r["cid"]), {
                "card_id": str(r["cid"]), "concept_id": str(cid),
                "name": str(r["name"] or cid),
                "module_id": str(r["mid"] or ""),
                "exercise_type": etype, "type_name": TYPE_LABELS[etype],
                "due": due, "attempts": n, "avg": avg}))
        pool.sort(key=lambda t: (t[0], t[1], t[2]))
        out = []
        for _, _, _, p in pool[:want]:
            if p["attempts"]:
                p["reason"] = f"avg {p['avg']:.1f} over {p['attempts']}"
            else:
                p["reason"] = "no attempts yet"
            if p["due"]:
                p["reason"] += f" \u00b7 due {p['due'][:10]}"
            out.append(p)
        return out
    except Exception:  # noqa: BLE001 -- picker never raises
        return []


def track_progress(db_path, scope) -> dict:
    """{total, owned, due} over the scope's security-track concepts.

    Total counts distinct concepts holding a live 49/50/51 card in the
    scope; owned reuses ownership.owned_map proofs per module; due
    counts live track cards past due. Zeros on error. Never raises.
    """
    out = {"total": 0, "owned": 0, "due": 0}
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        from . import sched as schedmod
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.concept_id AS cid, cards.due AS due,"
                " concepts.module_id AS mid, concepts.file AS f"
                " FROM cards JOIN concepts ON concepts.id = cards.concept_id"
                f" WHERE cards.exercise_type IN ({','.join('?' * len(SEC_TYPES))})"
                " AND cards.stale = 0", list(SEC_TYPES)).fetchall()
        finally:
            con.close()
        in_scope = [dict(r) for r in rows
                    if match(scope, (r["f"] or ""))]
        cids = {r["cid"] for r in in_scope}
        out["total"] = len(cids)
        if not cids:
            return out
        now = schedmod.iso(schedmod.utcnow())
        out["due"] = sum(1 for r in in_scope if (r["due"] or "") <= now)
        con2 = dbmod.connect(db_path)
        try:
            for mid in {r["mid"] for r in in_scope if r["mid"]}:
                omap = ownmod.owned_map(con2, mid)
                out["owned"] += sum(1 for cid, (_, o) in omap.items()
                                    if o and cid in cids)
        finally:
            con2.close()
    except Exception:  # noqa: BLE001
        pass
    return out


def track_html(db_path, scope, size=DEFAULT_SIZE) -> str:
    """Due-page track box; "" when unscoped (legacy fallback)."""
    try:
        s = normalize_scope(scope)
        if not s:
            return ""
        files = _all_files(db_path)
        if not files:
            return ""
        if not any(match(s, f) for f in files.values()):
            return (
                f"<p id='{TRACK_ANCHOR}'><small>Unknown scope "
                f"<b>{html.escape(s)}</b> \u2014 no files match. "
                f"<a href='/due'>Clear scope</a></small></p>")
        picks = pick_track(db_path, s, size)
        prog = track_progress(db_path, s)
        if not picks:
            return (
                f"<p id='{TRACK_ANCHOR}'>Security-champions track: "
                f"<b>{html.escape(s)}</b> has no threat-model, secret-scan, "
                f"or input-validation cards yet -- generate some and they "
                f"gather here. <a href='/due'>Clear scope</a></p>")
        from . import lessons as lesmod
        lis = []
        for p in picks:
            mid, name = p["module_id"], p["name"]
            href = (f"/modules/{mid}#lesson-{lesmod.slug(name)}"
                    if mid else "/modules")
            lis.append(
                f"<li>{html.escape(name)} "
                f"<small>{html.escape(p['type_name'])} \u00b7 "
                f"{html.escape(p['reason'])}</small> -- "
                f"<a href='{html.escape(href, True)}'>Study</a></li>")
        n = len(picks)
        return (
            f"<section id='{TRACK_ANCHOR}'><h2>Security-champions track: "
            f"{html.escape(s)}</h2>"
            f"<p>{prog['owned']}/{prog['total']} track concepts owned \u00b7 "
            f"{n} card{'s' if n != 1 else ''} weakest first "
            f"(<a href='/due'>Clear scope</a>)</p>"
            f"<ol>{''.join(lis)}</ol></section>")
    except Exception:  # noqa: BLE001 -- box never breaks Due
        return ""


def section_html(db_path="") -> str:
    """Status home with a live security-card count; static fallback w/o DB."""
    try:
        if db_path:
            from . import db as dbmod
            con = dbmod.connect(db_path)
            try:
                n = con.execute(
                    "SELECT COUNT(*) FROM cards WHERE cards.stale = 0 AND "
                    f"cards.exercise_type IN ({','.join('?' * len(SEC_TYPES))})",
                    list(SEC_TYPES)).fetchone()[0] or 0
            finally:
                con.close()
            demo = (f"<p><small>{n} security card{'s' if n != 1 else ''} "
                    f"across all areas -- open the Due queue with "
                    f"<code>?scope=&lt;path-prefix&gt;</code> to practice "
                    f"one.</small></p>")
        else:
            demo = ("<p><small>Open the Due queue with "
                    "<code>?scope=&lt;path-prefix&gt;</code> to practice one "
                    "area's threat-model, secret-scan, and "
                    "input-validation cards.</small></p>")
        return (
            f"<section id='{STATUS_ANCHOR}'><h3>Security-champions track "
            "<small>(feature)</small></h3>"
            "<p>One area's threat-model, secret-scan, and input-validation "
            "cards gathered weakest-first, with progress proven by owned "
            "concepts. <code>groundwork/secchamp.py</code> provides "
            "<code>pick_track()</code> and <code>track_html()</code> "
            "(unscoped renders nothing, legacy bytes survive).</p>"
            f"{demo}</section>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<section id='{STATUS_ANCHOR}'><h3>Security-champions track"
                "</h3><p>Track temporarily unavailable.</p></section>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "secchamp-track",
        "kind": "feature",
        "title": "Security-champions track",
        "blurb": ("Threat-model plus secret-scan practice per area: your "
                  "area's security cards weakest-first, progress from owned proofs."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
