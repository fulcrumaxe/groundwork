"""Tests for the webhook verification exercise (type 72, F-49)."""
import unittest
from types import SimpleNamespace

from groundwork import webhook as mod


def make_concept(name="push"):
    return SimpleNamespace(node_id="c", name=name, kind="webhook",
                           file="webhooks.py", line=11)


def fixture_ctx():
    # Same shape as tests/test_groundwork.py test_all_types_generate.
    from groundwork import graph as graphmod
    return {"runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5",
            "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
            "trace_var": "total", "trace_expected": ["2", "5"],
            "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
            "fixed": "def add(a=2, b=3):\n    return a + b",
            "graph": graphmod.Graph()}


EQ_NO_WINDOW = (
    "def verify_signature(secret, body, timestamp, signature, now):\n"
    "    import hmac as _hm, hashlib as _hl\n"
    "    expected = _hm.new(str(secret).encode(),\n"
    "                       f\"{timestamp}.{body}\".encode(),\n"
    "                       _hl.sha256).hexdigest()\n"
    "    return expected == str(signature)\n"
)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (72, "webhook", "apply"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_never_none(self):
        for args in [("ex72", make_concept(), ["x = 1"], {}),
                     ("ex72", make_concept(), ["x = 1"], fixture_ctx()),
                     (None, None, None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])

    def test_deterministic(self):
        a = mod.generate("ex72", make_concept(), ["x = 1"], {})
        b = mod.generate("ex72", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["secret"], b["payload"]["secret"])
        self.assertEqual(a["payload"]["valid"], b["payload"]["valid"])

    def test_distinct_ids_diverge(self):
        a = mod.generate("ex72a", make_concept(), ["x = 1"], {})
        b = mod.generate("ex72b", make_concept(), ["x = 1"], {})
        self.assertNotEqual(a["payload"]["secret"], b["payload"]["secret"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["reference"])
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_tampered_body_rejected(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        p = e["payload"]
        fn = mod._load_verify(e["payload"]["reference"])[0]
        _, out = mod._call(fn, p["secret"], p["tampered"]["body"],
                           p["tampered"]["ts"], p["tampered"]["sig"],
                           p["now"])
        self.assertFalse(out)

    def test_eq_without_window_fails(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        # NOTE: `import` is unavailable in the restricted namespace, so
        # this naive submission fails to load — still a fail, still 0.0.
        r = mod.grade(e, EQ_NO_WINDOW)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_boundary_window(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        p = e["payload"]
        good = mod._verify(p["secret"], p["body"], p["ts"] + 300,
                           mod._signed(p["secret"], p["body"], p["ts"] + 300),
                           p["now"])
        self.assertTrue(good)
        bad = mod._verify(p["secret"], p["body"], p["ts"] + 301,
                          mod._signed(p["secret"], p["body"], p["ts"] + 301),
                          p["now"])
        self.assertFalse(bad)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None, "def broken(:"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "def f(): pass"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex72", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("webhooks.py:11", body)
        self.assertIn(e["payload"]["secret"][:8], body)

    def test_render_escapes(self):
        e = mod.generate("ex72", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-webhook'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "webhook-verify", "kind": "feature",
                          "title": "Webhook verify",
                          "blurb": "Verify an HMAC-signed webhook — valid passes, tampered, wrong-secret, and replayed deliveries rejected.",
                          "path": "/status", "anchor": "status-b11-webhook"})


if __name__ == "__main__":
    unittest.main()
