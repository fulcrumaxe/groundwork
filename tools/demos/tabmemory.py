"""Improvement demo: explainer open/closed memory (I-121).

Full behavior: Study-first panels remember their open state per
panel in localStorage only -- no server state. seed_db forces one
lesson-backed card due solo; the Due beat opens its panel with a
real click, reloads, and polls the restored-open state; the module
beat proves the second caller path keys its own panel.
"""
from __future__ import annotations

import json
import re
import sqlite3

_JUNK = re.compile(r"[^a-z0-9]+", re.IGNORECASE)


def _normalize(key) -> str:
    try:
        if not isinstance(key, str) or not key.strip():
            return ""
        return _JUNK.sub("-", key.strip().lower()).strip("-")
    except Exception:
        return ""


SCENARIO = {
    "id": "tabmemory",
    "kind": "improvement",
    "batch": 20,
    "item": "I-121",
    "title": "Explainers remember their state",
    "blurb": "Study-first panels reopen as you left them.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Improvement I-121",
         "title": "Explainers remember their state",
         "subtitle": "Open or closed per panel -- remembered in your browser only."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-tabmemory",
         "caption": "Status documents the improvement with a live open sample panel.",
         "assert_js": "() => !!document.querySelector('#status-b20-tabmemory') && "
                      "!!document.querySelector(\"details[data-gw-remember='sample-panel'][open]\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Pure rules: keys slug to gw-explainer slugs; stored 1 opens, missing stays legacy-closed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import tabmemory as m; "
              "print(m.state_key('Due:AbC 12')); "
              "print(m.resolve_open('due:x', {'due-x': '1'}), m.resolve_open('due:x', {}), m.resolve_open('due:x', None)); "
              "print(m.details_html('<p>e</p>', 'due:x', True)[:60]); "
              "print('server state:', 'localStorage' in m.memory_js() and 'fetch' not in m.memory_js())"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "focus": "details[data-gw-remember='{seed_slug}']",
         "caption": "Click the panel open, reload -- it restores open from browser memory alone.",
         "js": ["() => { const d = document.querySelector(\"details[data-gw-remember='{seed_slug}']\"); "
                "if (!d) return 'panel-missing'; "
                "try { localStorage.removeItem('gw-explainer:{seed_slug}'); } catch (e) {} "
                "d.open = false; window.__tab_armed = 1; "
                "d.querySelector('summary').click(); "
                "setTimeout(() => location.reload(), 800); return 'armed'; }"],
         "poll_js": "() => window.__tab_armed ? 'waiting-armed' : (() => { "
                    "const d = document.querySelector(\"details[data-gw-remember='{seed_slug}']\"); "
                    "if (!d) return 'waiting-missing'; let v = ''; "
                    "try { v = localStorage.getItem('gw-explainer:{seed_slug}'); } catch (e) {} "
                    "return (d.open && v === '1') ? 'restored-open' : 'waiting-closed'; })()",
         "poll_want": "restored-open",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const d = document.querySelector(\"details[data-gw-remember='{seed_slug}']\"); "
                      "let v = ''; try { v = localStorage.getItem('gw-explainer:{seed_slug}'); } catch (e) {} "
                      "return !!d && d.open && v === '1'; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "details[data-gw-remember='{seed_mod_slug}']",
         "caption": "The module path keys its own panel -- same memory, separate key.",
         "js": ["() => { const d = document.querySelector(\"details[data-gw-remember='{seed_mod_slug}']\"); "
                "if (!d) return 'panel-missing'; "
                "try { localStorage.removeItem('gw-explainer:{seed_mod_slug}'); } catch (e) {} "
                "d.open = false; d.querySelector('summary').click(); return 'clicked'; }"],
         "poll_js": "() => { let v = ''; try { v = localStorage.getItem('gw-explainer:{seed_mod_slug}'); } "
                    "catch (e) {} return v === '1' ? 'saved' : 'waiting'; }",
         "poll_want": "saved",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const d = document.querySelector(\"details[data-gw-remember='{seed_mod_slug}']\"); "
                      "let v = ''; try { v = localStorage.getItem('gw-explainer:{seed_mod_slug}'); } catch (e) {} "
                      "return !!d && d.open && v === '1'; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Left as you left it.",
         "subtitle": "tabmemory.py restores per-panel state -- no-JS keeps legacy-closed panels."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One lesson-backed card due solo; module node for the second path."""
    con = sqlite3.connect(db_path)
    try:
        mods = con.execute("SELECT id, lessons FROM modules").fetchall()
        for mid, raw in mods:
            try:
                lessons = {L["concept_id"]: L for L in json.loads(raw or "[]")}
            except (ValueError, KeyError):
                continue
            if not lessons:
                continue
            rows = con.execute("SELECT id FROM concepts WHERE module_id=?",
                               (mid,)).fetchall()
            backed = [cid for (cid,) in rows
                      if (cid.split(":", 1)[1] if ":" in cid else cid) in lessons]
            if not backed:
                continue
            card = None
            for cid in backed:
                card = con.execute("SELECT id FROM cards WHERE concept_id=?"
                                   " ORDER BY rowid LIMIT 1", (cid,)).fetchone()
                if card:
                    break
            if not card:
                continue
            con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
            con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                        " WHERE id=?", (card[0],))
            con.commit()
            node = backed[0].split(":", 1)[1] if ":" in backed[0] else backed[0]
            return {"seeded": True, "card_id": card[0],
                    "slug": _normalize(f"due:{card[0]}"),
                    "mid": mid, "mod_slug": _normalize(f"mod:{node}")}
        return {"seeded": False, "reason": "no lesson-backed card"}
    finally:
        con.close()
