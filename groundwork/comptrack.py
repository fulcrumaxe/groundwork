"""Compliance tracks (F-189): required concepts verified, not checkboxed.

A compliance spec is a shareable JSON doc ({"format": "groundwork-comply/1",
"title": str, "required": [concept names]}) traveling in the ?comply=
module-page link; PASS derives from owned/mastery already in the DB.
Pure functions, stdlib only, no I/O, no DB/schema changes, never raises.
No spec renders "" (legacy bytes); verify state, never self-attested.
"""
from __future__ import annotations

import html as htmlmod
import json

STATUS_ANCHOR = "status-b29-comptrack"
FORMAT = "groundwork-comply/1"
OWNED_MASTERY = 0.85


def _name(v) -> str:
    try:
        return v.strip() if isinstance(v, str) and v.strip() else ""
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def parse_spec(value) -> dict:
    """{"title": str, "required": [...]}; blanks/dupes dropped; garbage -> empty."""
    try:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return {"title": "", "required": []}
        if not isinstance(value, dict):
            return {"title": "", "required": []}
        req, seen = [], set()
        raw = value.get("required", [])
        if isinstance(raw, (list, tuple)):
            for s in raw:
                n = _name(s)
                if n and n not in seen:
                    seen.add(n)
                    req.append(n)
        return {"title": _name(value.get("title")), "required": req}
    except Exception:  # noqa: BLE001 -- parse must never raise
        return {"title": "", "required": []}


def _owned_set(owned, mastery_of, required) -> set:
    done = set()
    try:
        for o in (owned or []):
            n = _name(o)
            if n:
                done.add(n)
    except TypeError:
        pass
    try:
        m = mastery_of if isinstance(mastery_of, dict) else {}
        for s in required:
            try:
                if float(m.get(s, 0.0) or 0.0) >= OWNED_MASTERY:
                    done.add(s)
            except (TypeError, ValueError):
                continue
    except Exception:  # noqa: BLE001 -- set build must never raise
        pass
    return done


def comply_view(spec, owned=None, mastery_of=None) -> dict:
    """Verify state over required order: verified/total/passed/next. Never raises."""
    try:
        p = parse_spec(spec)
        done = _owned_set(owned, mastery_of, p["required"])
        rows = [{"name": s, "verified": s in done} for s in p["required"]]
        n = sum(1 for r in rows if r["verified"])
        nxt = next((r["name"] for r in rows if not r["verified"]), None)
        return {"title": p["title"], "required": rows, "verified": n,
                "total": len(rows),
                "passed": bool(rows) and n == len(rows), "next": nxt}
    except Exception:  # noqa: BLE001 -- view must never raise
        return {"title": "", "required": [], "verified": 0, "total": 0,
                "passed": False, "next": None}


def verify_html(spec, owned=None, mastery_of=None) -> str:
    """Verify/PASS section; "" with no spec/required. Escaped, no <style>."""
    try:
        v = comply_view(spec, owned, mastery_of)
        if not v["required"]:
            return ""
        items = "".join(
            f"<li class='{'comply-verified' if s['verified'] else 'comply-pending'}'>"
            f"{htmlmod.escape(s['name'])}"
            f" \u2014 {'verified' if s['verified'] else 'pending'}</li>"
            for s in v["required"])
        title = htmlmod.escape(v["title"] or "Compliance track")
        flag = " \u2014 PASS" if v["passed"] else ""
        return (f"<section id='comptrack'><h2>{title}</h2>"
                f"<p><small>{v['verified']} of {v['total']} required concepts "
                f"verified{flag}.</small></p>"
                f"<ol class='comply-required'>{items}</ol></section>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for compliance tracks."""
    return {"id": "compliance-track", "kind": "feature",
            "title": "Compliance tracks",
            "blurb": ("Required concepts verified against owned proofs \u2014 "
                      "PASS, never checkboxed."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with live demo; db-free."""
    try:
        demo = verify_html({"format": FORMAT, "title": "Q3: data handling",
                            "required": ["Handle PII", "Log access", "Rotate keys"]},
                           owned={"Handle PII"})
        return (f"<h3 id='{STATUS_ANCHOR}'>Compliance tracks <small>(feature)</small></h3>"
                "<p>Required-concept sets graded by live owned proofs at mastery 0.85: "
                "PASS means demonstrated, not clicked. <code>groundwork/comptrack.py</code> "
                "renders on <code>Handler.module_html</code> with a <code>?comply=</code> "
                "spec; no spec keeps legacy bytes.</p>" f"{demo}")
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Compliance tracks</h3>"
