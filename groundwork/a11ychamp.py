"""Accessibility-champions track: audit practice per frontend (F-191).

One scoped practice track over a frontend's live audit cards: every
type-52 a11y-audit card (frontend practice by construction -- its front
is rendered HTML) plus the type-53 i18n cards whose concept is honestly
UI-facing (a UI word in the concept name or file). Weakest mastery
first, stalest due date breaks ties, concept id breaks the rest -- the
interviewprep ordering. Progress counts owned proofs (ownership model)
over the track's concepts.

Frontend scope rides the existing ?scope= path prefix (ramppack
precedent): no new query param, no schema changes. Unscoped shows every
frontend; ?scope=groundwork/web narrows to one. Unknown scope renders ""
(the queue banner already explains it). Empty pool renders "" so legacy
Due bytes survive.

Caller: Handler.due_html beside the interview-prep track. Never raises;
never mutates inputs. Stdlib only at import; sibling reads (db,
ownership, ramppack, lessons) are lazy.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b29-a11ychamp"
TRACK_ANCHOR = "a11ychamp-track"
A11Y_TYPE = "52"
I18N_TYPE = "53"
DEFAULT_SIZE = 5
MAX_SIZE = 12
_MISSING_DUE = "\uffff"

FRONTEND_EXTS = (".html", ".css", ".js", ".jsx", ".tsx", ".vue", ".svelte")
FRONTEND_DIRS = ("frontend", "templates", "static", "public", "assets",
                 "components", "pages", "styles")
UI_WORDS = ("css", "html", "page", "render", "view", "template", "web",
            "ui", "screen", "style", "empty")


def _tokens(text) -> set:
    """Lowercase underscore-separated words; hostile input yields empty."""
    try:
        bits = str(text or "").replace("/", "_").replace(".", "_")
        bits = bits.replace("-", "_")
        return {b for b in bits.lower().split("_") if b}
    except Exception:  # noqa: BLE001 -- tokenize never raises
        return set()


def is_frontend(name, file) -> bool:
    """True when the concept lives on a frontend surface.

    A frontend extension, a frontend directory in the path, or a UI word
    in the concept name or file stem. Never raises.
    """
    try:
        f = str(file or "").strip().replace("\\", "/")
        low = f.lower()
        if any(low.endswith(e) for e in FRONTEND_EXTS):
            return True
        if any(p in FRONTEND_DIRS for p in low.split("/")):
            return True
        stem = low.rsplit("/", 1)[-1].split(".", 1)[0]
        return bool(UI_WORDS and ((_tokens(name) | _tokens(stem)) & set(UI_WORDS)))
    except Exception:  # noqa: BLE001 -- gate never raises
        return False


def in_track(exercise_type, name, file) -> bool:
    """True when a card belongs in the champions pool.

    Type 52 always qualifies (an audit card IS frontend practice);
    type 53 qualifies only when honestly UI-facing. Never raises.
    """
    try:
        t = str(exercise_type or "")
        if t == A11Y_TYPE:
            return True
        if t == I18N_TYPE:
            return is_frontend(name, file)
        return False
    except Exception:  # noqa: BLE001 -- gate never raises
        return False


def _mastery(row) -> float:
    try:
        m = float((row or {}).get("mastery") or 0.0)
        return m if m == m else 0.0  # NaN is weakest, never crashes sort
    except (TypeError, ValueError):
        return 0.0


def _size_of(size) -> int:
    try:
        return max(0, min(int(size), MAX_SIZE))
    except (TypeError, ValueError):
        return DEFAULT_SIZE


def pick_track(rows, scope="", size=DEFAULT_SIZE) -> list:
    """Up to `size` track picks, weakest mastery first.

    Each pick: {concept_id, card_id, name, file, module_id, mastery,
    due, exercise_type, reason}. One row per concept (earliest dated
    due wins); scope narrows by file prefix (ramppack.match). Empty or
    hostile input yields []. Never raises; never mutates inputs.
    """
    try:
        from . import ramppack as _rampmod
    except Exception:  # noqa: BLE001 -- scope unverifiable below
        _rampmod = None
    try:
        want = _size_of(size)
        s = str(scope or "")

        def _match(f) -> bool:
            if _rampmod is None:
                return not s
            try:
                return bool(_rampmod.match(s, f))
            except Exception:  # noqa: BLE001 -- one bad row skips
                return not s

        best: dict = {}
        for r in (rows or []):
            if not isinstance(r, dict):
                continue
            cid = r.get("concept_id")
            cid = str(cid).strip() if cid is not None else ""
            if not cid:
                continue
            if not in_track(r.get("exercise_type"), r.get("name"),
                            r.get("file")):
                continue
            if not _match(r.get("file") or ""):
                continue
            d = r.get("due")
            d = d if isinstance(d, str) and d else ""
            prev = best.get(cid)
            if prev is not None and not (
                    d and (not prev["due"] or d < prev["due"])):
                continue
            m = _mastery(r)
            reason = f"mastery {m:.2f}" + (f" \u00b7 due {d[:10]}" if d else "")
            best[cid] = {"concept_id": cid,
                         "card_id": str(r.get("card_id") or ""),
                         "name": str(r.get("name") or cid),
                         "file": str(r.get("file") or ""),
                         "module_id": str(r.get("module_id") or ""),
                         "mastery": m, "due": d,
                         "exercise_type": str(r.get("exercise_type") or ""),
                         "reason": reason}
        pool = sorted(best.values(),
                      key=lambda p: (p["mastery"],
                                     p["due"] or _MISSING_DUE,
                                     p["concept_id"]))
        return pool[:want]
    except Exception:  # noqa: BLE001 -- picker never raises
        return []


def track_rows(db_path) -> list:
    """Live type-52/53 card-concept rows; [] on error. Never raises."""
    try:
        from . import db as dbmod
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.id AS card_id,"
                " cards.exercise_type AS exercise_type, cards.due AS due,"
                " concepts.id AS concept_id, concepts.name AS name,"
                " concepts.file AS file, concepts.module_id AS module_id,"
                " concepts.mastery AS mastery FROM cards"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE cards.exercise_type IN ('52','53')"
                " AND cards.stale = 0").fetchall()
        finally:
            con.close()
        return [dict(r) for r in rows]
    except Exception:  # noqa: BLE001 -- live read never raises
        return []


def progress(db_path, picks) -> dict:
    """{owned, total} owned proofs over the track's concepts."""
    out = {"owned": 0, "total": 0}
    try:
        ids = sorted({str(p.get("concept_id"))
                      for p in (picks or [])
                      if isinstance(p, dict) and p.get("concept_id")})
        out["total"] = len(ids)
        if not ids:
            return out
        from . import db as dbmod
        from . import ownership as ownmod
        con = dbmod.connect(db_path)
        try:
            mids = {r["module_id"] for r in con.execute(
                "SELECT DISTINCT module_id FROM concepts WHERE id IN "
                f"({','.join('?' * len(ids))})", ids).fetchall()}
            owned = set()
            for mid in mids:
                for cid, (_, o) in ownmod.owned_map(con, mid).items():
                    if o:
                        owned.add(cid)
        finally:
            con.close()
        out["owned"] = len(set(ids) & owned)
    except Exception:  # noqa: BLE001 -- progress never raises
        pass
    return out


def champ_html(db_path, scope="") -> str:
    """Due-page champions box; "" when the pool is empty (legacy fallback)."""
    try:
        picks = pick_track(track_rows(db_path), scope)
        if not picks:
            return ""
        try:
            from . import lessons as lesmod
            slug = lesmod.slug
        except Exception:  # noqa: BLE001 -- study links degrade to /modules
            slug = None
        prog = progress(db_path, picks)
        lis = []
        for p in picks:
            mid, name = p["module_id"], p["name"]
            href = (f"/modules/{mid}#lesson-{slug(name)}"
                    if (mid and slug) else "/modules")
            tag = "a11y" if p["exercise_type"] == A11Y_TYPE else "i18n"
            lis.append(
                f"<li>{html.escape(name)} <small>[{tag}] "
                f"{html.escape(p['reason'])}</small> \u2014 "
                f"<a href='{html.escape(href, True)}'>Study</a></li>")
        s = str(scope or "").strip()
        head = (f"Accessibility champions: <b>{html.escape(s)}</b> \u2014 "
                if s else "Accessibility champions \u2014 ")
        clear = " <a href='/due'>Clear scope</a>" if s else ""
        n = len(picks)
        return (
            f"<section id='{TRACK_ANCHOR}'><h2>{head}"
            f"{prog['owned']}/{prog['total']} owned</h2>"
            f"<p>{n} audit card{'s' if n != 1 else ''}, shakiest first \u2014 "
            f"practice this frontend's access barriers.{clear}</p>"
            f"<ol>{''.join(lis)}</ol></section>")
    except Exception:  # noqa: BLE001 -- box never breaks Due
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the champions track."""
    # Parent fix (Batch 19/F-178 precedent): the live box only
    # renders with audit cards in the library, so the tour points at
    # the always-rendered Status section instead of /due (the tour
    # gate renders audit-less fixtures).
    return {"id": "a11ychamp-track", "kind": "feature",
            "title": "Accessibility champions track",
            "blurb": ("Weakest-first audit practice per frontend \u2014 a11y "
                      "cards plus UI-honest i18n cards, scoped by ?scope=."),
            "path": "/status",
            "anchor": STATUS_ANCHOR}


def section_html(db_path="") -> str:
    """Anchored status subsection; live counts when db_path is given."""
    try:
        live = ""
        if db_path:
            rows = track_rows(db_path)
            n52 = sum(1 for r in rows
                      if str(r.get("exercise_type")) == A11Y_TYPE)
            n53 = sum(1 for r in rows
                      if str(r.get("exercise_type")) == I18N_TYPE
                      and is_frontend(r.get("name"), r.get("file")))
            live = (f"<p><small>Live now: {n52} audit cards plus {n53} "
                    f"UI-facing i18n cards in the champions pool.</small></p>")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Accessibility champions "
            "<small>(feature)</small></h3>"
            "<p>Weakest-first audit practice per frontend: every type-52 "
            "card plus the UI-honest type-53s, scoped by the existing "
            "?scope= prefix, progress from owned proofs. "
            "<code>groundwork/a11ychamp.py</code> provides "
            "<code>pick_track()</code> and <code>champ_html()</code> "
            "(empty pool renders nothing, legacy bytes survive).</p>" + live)
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Accessibility champions</h3>"
                "<p>Champions track temporarily unavailable.</p>")
