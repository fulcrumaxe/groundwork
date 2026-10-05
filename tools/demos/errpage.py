"""Improvement demo: chrome error pages (I-83).

Full behavior: an unhandled handler exception renders the 500 body
inside the normal page chrome (nav, safe type label, links back)
instead of dropping the connection, and traceback anatomy never
reaches the browser. The 500 path only fires on a real crash, so
Chrome films its 404 sibling (same wrap pattern, same chrome) while
the terminal beats prove the 500 body shape and its page-chrome wrap
directly. No seed needed: nothing is data-dependent.
"""
from __future__ import annotations

SCENARIO = {
    "id": "errpage",
    "kind": "improvement",
    "batch": 13,
    "item": "I-83",
    "title": "Chrome error pages",
    "blurb": "Server errors render inside the normal header and footer -- never a dropped connection.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-83",
         "title": "Chrome error pages",
         "subtitle": "Server errors render inside the normal header and footer -- never a dropped connection."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-errpage",
         "caption": "Status documents the 500 body: safe label, correlation ref, links back.",
         "assert_js": "() => !!document.querySelector('#status-b13-errpage')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: type names pass, traceback anatomy never does.",
         "commands": [
             ["python3", "-c",
              "from groundwork import errpage as m; "
              "print('kind:', m.safe_kind(ValueError('x')), '|', m.safe_kind('Traceback x')); "
              "body = m.server_error_html('ValueError'); "
              "print('links:', all(h in body for h in ('/due', '/modules', '/reviews', '/status'))); "
              "evil = m.server_error_html('Traceback File x.py, line 1'); "
              "print('leak:', any(f in evil for f in ('Traceback', '.py', 'line ')))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/nope-b13-errpage",
         "caption": "The 404 sibling proves the pattern: errors render inside site chrome with somewhere real to go.",
         "assert_js": "() => !!document.querySelector('#sitenav') && !!document.querySelector('#not-found')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The 500 body wrapped for real: nav, safe label, footer -- one page.",
         "commands": [
             ["python3", "-c",
              "from groundwork import errpage as e, web as w; "
              "raw = w.page('Error', e.server_error_html(ValueError('boom')), "
              "counts={'due': 0, 'modules': 0, 'tries': 0}).decode(); "
              "print('chrome:', 'sitenav' in raw, 'server-error' in raw, 'site-footer' in raw)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Crashes keep their chrome.",
         "subtitle": "errpage.py fails closed -- labels, never tracebacks."},
    ],
}
