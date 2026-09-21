"""Tests for the containerize exercise (type 64, F-41)."""
import unittest
from types import SimpleNamespace

from groundwork import containerize as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="app.py", line=3)


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


def good_for(e):
    port = e["payload"]["port"]
    entry = e["payload"]["entrypoint"]
    return (f"FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\n"
            f"EXPOSE {port}\nUSER appuser\n"
            f'CMD ["python", "{entry}"]\n')


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (64, "containerize", "create"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_never_none(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])

    def test_port_deterministic(self):
        a = mod.generate("ex64", make_concept(), ["x = 1"], {})
        b = mod.generate("ex64", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["port"], b["payload"]["port"])
        self.assertTrue(8000 <= a["payload"]["port"] <= 8999)

    def test_no_surface_returns_none(self):
        self.assertIsNone(mod.generate("ex64", None, [], {}))
        self.assertIsNone(mod.generate("ex64", None, None, None))

    def test_never_raises(self):
        self.assertIsNone(mod.generate(None, None, None, None))
        e = mod.generate("ex64", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        r = mod.grade(e, good_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_latest_fails(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        bad = good_for(e).replace("python:3.12-slim", "python:latest")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_no_user_fails(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        bad = "\n".join(l for l in good_for(e).splitlines()
                        if not l.startswith("USER"))
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_add_for_files_fails(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        bad = good_for(e).replace("COPY . .", "ADD . /app")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_env_secret_fails(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        bad = good_for(e) + 'ENV API_KEY=hunter2\n'
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_wrong_expose_fails(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        bad = good_for(e).replace(f"EXPOSE {e['payload']['port']}",
                                  "EXPOSE 1234")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_shell_form_cmd_fails(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        bad = good_for(e).replace(
            f'CMD ["python", "{e["payload"]["entrypoint"]}"]',
            "CMD python app.py")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_no_partial_credit(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        # Everything right except USER: most points earned, still 0.0.
        bad = "\n".join(l for l in good_for(e).splitlines()
                        if not l.startswith("USER"))
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None, "FROM\n"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None), (e, ""),
                                ({"payload": {}}, "FROM x"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex64", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("app.py:3", body)
        self.assertIn(str(e["payload"]["port"]), body)

    def test_render_escapes(self):
        e = mod.generate("ex64", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b10-containerize'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t, {"id": "containerize-it", "kind": "feature",
                             "title": "Containerize it",
                             "blurb": "Write a Dockerfile for a small service — static build gate, no partial credit.",
                             "path": "/status", "anchor": "status-b10-containerize"})


if __name__ == "__main__":
    unittest.main()
