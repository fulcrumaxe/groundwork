"""Curriculum mapping: library modules crossed with course outcomes (F-174).

A curriculum spec is a shareable JSON doc naming course outcomes and the
concept names each outcome needs: {"format": "groundwork-curriculum/1",
"title": str, "outcomes": [{"id": str, "title": str, "concepts": [names]}]}.
It travels in the ?curriculum= library link -- the ?quest= (F-130),
?assign= (F-164), ?scope= (F-162) precedent: the teacher's spec rides the
URL, so no accounts, no rosters, no stored outcomes. Coverage derives from
the learner's own owned proofs already in the DB, in the library page's own
owned/total vocabulary. Pure functions, stdlib only, read-only DB access,
never raises. No spec renders "" (legacy bytes); completion-based, never
ranked.
"""
from __future__ import annotations

import html as htmlmod
import json

STATUS_ANCHOR = "status-b28-curricmap"
BOX_ANCHOR = "curricmap"
FORMAT = "groundwork-curriculum/1"


def _name(v) -> str:
    try:
        return v.strip() if isinstance(v, str) and v.strip() else ""
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def _num(v) -> int:
    try:
        return max(0, int(v or 0))
    except (TypeError, ValueError):
        return 0


def parse_spec(value) -> dict:
    """{"title": str, "outcomes": [{"id","title","concepts"}]}; garbage -> empty."""
    try:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return {"title": "", "outcomes": []}
        if not isinstance(value, dict):
            return {"title": "", "outcomes": []}
        outcomes = []
        raw = value.get("outcomes", [])
        if isinstance(raw, (list, tuple)):
            for o in raw:
                if not isinstance(o, dict):
                    continue
                concepts, seen = [], set()
                cnames = o.get("concepts", [])
                if isinstance(cnames, (list, tuple)):
                    for c in cnames:
                        n = _name(c)
                        if n and n not in seen:
                            seen.add(n)
                            concepts.append(n)
                if not concepts:
                    continue
                oid = _name(o.get("id")) or f"outcome-{len(outcomes) + 1}"
                outcomes.append({"id": oid, "title": _name(o.get("title")),
                                 "concepts": concepts})
        return {"title": _name(value.get("title")), "outcomes": outcomes}
    except Exception:  # noqa: BLE001 -- parse must never raise
        return {"title": "", "outcomes": []}


def library_index(db_path):
    """({name: [(mid, owned)]}, {mid: title}); ({}, {}) on error."""
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id, task_summary FROM modules").fetchall()
            rows = con.execute(
                "SELECT id, name, module_id FROM concepts").fetchall()
            owned_ids = set()
            for m in mods:
                omap = ownmod.owned_map(con, m["id"])
                for cid, (_a, o) in omap.items():
                    if o:
                        owned_ids.add(cid)
        finally:
            con.close()
        titles = {m["id"]: (m["task_summary"] or m["id"]) for m in mods}
        index: dict = {}
        for r in rows:
            n = _name(r["name"])
            if n:
                index.setdefault(n, []).append(
                    (r["module_id"], r["id"] in owned_ids))
        return index, titles
    except Exception:  # noqa: BLE001 -- index must never raise
        return {}, {}


def matrix_view(spec, concept_index, module_titles) -> dict:
    """Per-outcome coverage in teacher order; missing names flagged."""
    try:
        p = parse_spec(spec)
        index = concept_index if isinstance(concept_index, dict) else {}
        titles = module_titles if isinstance(module_titles, dict) else {}
        out_rows = []
        owned_n = total_n = 0
        for o in p["outcomes"]:
            cells, per_mod = [], {}
            for cname in o["concepts"]:
                hits = index.get(cname) or []
                if not isinstance(hits, (list, tuple)):
                    hits = []
                found = owned = False
                for h in hits:
                    if not isinstance(h, (list, tuple)) or len(h) < 2:
                        continue
                    try:
                        mid, flag = h[0], bool(h[1])
                        hash(mid)
                    except Exception:  # noqa: BLE001 -- skip hostile hits
                        continue
                    found = True
                    d = per_mod.setdefault(mid, [0, 0])
                    d[1] += 1
                    if flag:
                        d[0] += 1
                        owned = True
                cells.append({"name": cname, "found": found, "owned": owned})
            owned = sum(1 for c in cells if c["owned"])
            total = len(cells)
            owned_n += owned
            total_n += total
            mods = sorted(
                ((mid, titles.get(mid, mid), v[0], v[1])
                 for mid, v in per_mod.items()),
                key=lambda t: str(t[1]).lower())
            nxt = next((c["name"] for c in cells if not c["owned"]), None)
            out_rows.append({"id": o["id"], "title": o["title"],
                             "concepts": cells, "owned": owned, "total": total,
                             "complete": bool(cells) and owned == total,
                             "next": nxt, "modules": mods})
        return {"title": p["title"], "outcomes": out_rows,
                "owned": owned_n, "total": total_n,
                "complete": bool(out_rows) and all(
                    r["complete"] for r in out_rows)}
    except Exception:  # noqa: BLE001 -- view must never raise
        return {"title": "", "outcomes": [], "owned": 0, "total": 0,
                "complete": False}


def matrix_table(view) -> str:
    """Outcome x module coverage table; "" when no outcome rows."""
    try:
        if not isinstance(view, dict):
            return ""
        rows = view.get("outcomes") or []
        if not isinstance(rows, (list, tuple)) or not rows:
            return ""
        title = htmlmod.escape(str(view.get("title") or "Curriculum map"))
        trs = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            owned, total = _num(r.get("owned")), _num(r.get("total"))
            pct = int(round(100 * owned / total)) if total else 0
            mods = []
            for m in r.get("modules") or []:
                if not isinstance(m, (list, tuple)) or len(m) < 4:
                    continue
                try:
                    mid, mtitle = m[0], m[1]
                    mo, mt = _num(m[2]), _num(m[3])
                except Exception:  # noqa: BLE001 -- skip hostile cells
                    continue
                mods.append(
                    f"<a href='/modules/{htmlmod.escape(str(mid), quote=True)}'>"
                    f"{htmlmod.escape(str(mtitle))}</a> {mo}/{mt}")
            missing = sorted({str(c.get("name")) for c in (r.get("concepts") or [])
                              if isinstance(c, dict) and not c.get("found")
                              and c.get("name")})
            miss = (f"<br><small>Not in library: "
                    f"{htmlmod.escape(', '.join(missing))}</small>"
                    if missing else "")
            nxt = r.get("next")
            nxt_txt = (f"<small>Next: {htmlmod.escape(str(nxt))}</small>"
                       if nxt else "<small>Complete</small>")
            label = htmlmod.escape(str(r.get("title") or r.get("id", "")))
            trs.append(
                f"<tr><td><b>{label}</b>"
                f"<br><small>{htmlmod.escape(str(r.get('id', '')))}</small></td>"
                f"<td>{owned}/{total} owned"
                f"<div class='bar' aria-hidden='true'>"
                f"<i style='width:{pct}%'></i></div></td>"
                f"<td>{'<br>'.join(mods) if mods else '<small>no covering module</small>'}{miss}</td>"
                f"<td>{nxt_txt}</td></tr>")
        if not trs:
            return ""
        flag = " -- curriculum complete" if view.get("complete") else ""
        return (
            f"<section id='{BOX_ANCHOR}'><h2>{title}</h2>"
            f"<p><small>{_num(view.get('owned'))} of {_num(view.get('total'))} "
            f"outcome concepts owned{flag}.</small></p>"
            "<table class='log'><tr><th>Outcome</th><th>Coverage</th>"
            "<th>Modules</th><th>Next</th></tr>"
            f"{''.join(trs)}</table></section>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def matrix_html(db_path, spec) -> str:
    """Coverage matrix for a ?curriculum= spec; "" without one."""
    try:
        if not parse_spec(spec)["outcomes"]:
            return ""
        index, titles = library_index(db_path)
        return matrix_table(matrix_view(spec, index, titles))
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection with live demo; db-free."""
    try:
        demo = matrix_table(matrix_view(
            {"format": FORMAT, "title": "Sample: serving 101",
             "outcomes": [
                 {"id": "O1", "title": "Serve the queue",
                  "concepts": ["Read lessons", "Grade cards"]},
                 {"id": "O2", "title": "Own the loop",
                  "concepts": ["Serve the queue"]}]},
            {"Read lessons": [("m1", True)], "Grade cards": [("m1", False)]},
            {"m1": "Serving 101"}))
        return (f"<h3 id='{STATUS_ANCHOR}'>Curriculum mapping <small>(feature)</small></h3>"
                "<p>Course outcomes crossed with library modules: a shared "
                "<code>?curriculum=</code> link renders per-outcome coverage from the "
                "learner's own owned proofs -- completion-based, never ranked. "
                "<code>groundwork/curricmap.py</code> renders on "
                "<code>Handler.modules_html</code>.</p>" f"{demo}")
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Curriculum mapping</h3>"


def tour_entry() -> dict:
    """Tour registry entry for curriculum mapping."""
    return {"id": "curricmap-matrix", "kind": "feature",
            "title": "Curriculum mapping",
            "blurb": ("Course outcomes crossed with your library: "
                      "per-outcome coverage from your own owned proofs -- "
                      "complete, never ranked."),
            "path": "/status", "anchor": STATUS_ANCHOR}
