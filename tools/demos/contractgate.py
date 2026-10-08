"""Feature demo: the gate reads live code (F-50 integration).

Full behavior: contractaudit derives the six-part registry from the
real code -- GENERATORS keys, grade/widget branches, the disclosure
table, the pipeline emission map, the e2e dispatch -- Status eats
the live report, and a bare new type fails all six parts closed.
"""
from __future__ import annotations

SCENARIO = {
    "id": "contractgate",
    "kind": "feature",
    "batch": 17,
    "item": "F-50",
    "title": "The gate reads live code",
    "blurb": "Six parts per type, registry derived from the real code -- a bare new type fails closed.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 17 - Feature F-50",
         "title": "The gate reads live code",
         "subtitle": "Six parts per type, registry derived from the real code -- a bare new type fails closed."},
        {"type": "terminal", "duration": 9,
         "caption": "The live registry in one call: generator, grader, widget, disclosure, emission, e2e -- all derived.",
         "commands": [
             ["python3", "-c",
              "from groundwork import contractaudit as a, "
              "typecontract as m; "
              "reg = a.live_registry(); "
              "print('parts:', "
              "{k: len(v) for k, v in sorted(reg.items())}); "
              "rep = a.live_report(); s = m.completeness(rep); "
              "print('types:', s['total'], '| complete:', s['complete'], "
              "'| gaps:', s['missing_types'][:8])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/status",
         "focus": "#status-b12-typecontract",
         "caption": "Status eats the live report: live rows, six parts each, verdicts attached.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-typecontract\"); "
                      "return !!el && document.body.innerText.includes("
                      "'generator') && document.body.innerText.includes("
                      "'Verdict'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The gate catches a bare type: 999 ships nothing, so all six parts miss.",
         "commands": [
             ["python3", "-c",
              "from groundwork import contractaudit as a, exercises as e, "
              "typecontract as m; "
              "reg = a.live_registry(); types = set(e.TYPES); "
              "g = m.audit_type(999, reg); "
              "print('type 999 ok:', g['ok']); "
              "print('missing:', g['missing']); "
              "print('gen/grader/disclosure complete:', "
              "all(types <= set(reg[p]) "
              "for p in ('generator', 'grader', 'disclosure')))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 17",
         "title": "Derived, not hand-kept.",
         "subtitle": "contractaudit.py derives the registry -- the gate pins the baseline."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Db-free feature: no fixture needed, audit runs over live code."""
    return {"seeded": True, "note": "live registry, no fixture"}
