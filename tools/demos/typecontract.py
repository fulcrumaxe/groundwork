"""Feature demo: type completeness contract (F-50).

Full behavior: the six-part contract (generator, grader, widget,
disclosure, emission, e2e) audited live over the real registry —
Status renders the live table, and the terminal re-runs the same
audit plus a synthetic gap. Deterministic, db-free.
"""
from __future__ import annotations

SCENARIO = {
    "id": "typecontract",
    "kind": "feature",
    "batch": 12,
    "item": "F-50",
    "title": "Type completeness contract",
    "blurb": "Every exercise type proves six parts -- audited live, gaps fail closed.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-50",
         "title": "Type completeness contract",
         "subtitle": "Six parts or it does not ship."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#status-b12-typecontract",
         "caption": "Status audits every live type against the six-part contract.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-typecontract\"); "
                      "return !!el && document.body.innerText.includes('generator')"
                      " && document.body.innerText.includes('Verdict'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 10,
         "caption": "The same audit, live: full registry plus one synthetic gap.",
         "commands": [
             ["python3", "-c",
              "from groundwork import contractaudit as a, typecontract as m; "
              "rep = a.live_report(); s = m.completeness(rep); "
              "print('live types:', s['total'], 'complete:', s['complete']); "
              "print('gaps:', s['missing_types'][:6] or 'none'); "
              "gap = m.audit_type(99, {'generator': {99}, 'widget': {99}, "
              "'disclosure': {99}, 'emission': {99}}); "
              "print('type 99:', gap['ok'], 'missing:', gap['missing'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/status?tour=type-contract",
         "caption": "Guided tour arrival: banner on top, contract below.",
         "assert_js": "() => { const b = document.querySelector("
                      "'.tour-banner'); return !!b && "
                      "b.innerText.includes('Type completeness contract'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Six parts, proven.",
         "subtitle": "typecontract.py audits the registry -- gaps fail closed."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Db-free feature: no fixture needed, audit runs over live code."""
    return {"seeded": True, "note": "live registry, no fixture"}
