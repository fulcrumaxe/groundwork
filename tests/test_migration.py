"""F-24 migration authoring (type 47) tests, unittest style."""
import json
import unittest
from types import SimpleNamespace

from groundwork import migration as mod


def make_concept(name="profile"):
    return SimpleNamespace(node_id="m", name=name, kind="function",
                           file="models.py", line=3)


def make_ex(**kw):
    ctx = dict(kw.pop("ctx", {}) or {})
    return mod.generate("ex47", make_concept(kw.pop("name", "profile")),
                        ["x"], ctx)


def sub_of(ex):
    return json.dumps(ex["payload"]["expected"])


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = make_ex()
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (47, "migration-authoring", "modify"))
        self.assertTrue(e["front"] and e["back"] and len(e["hints"]) == 3)

    def test_payload_fixtures(self):
        p = make_ex()["payload"]
        for k in ("func", "old_field", "new_field", "default",
                  "old_rows", "expected", "reference", "grounded"):
            self.assertIn(k, p)
        self.assertTrue(p["grounded"])
        self.assertEqual(len(p["old_rows"]), len(p["expected"]))
        self.assertIn("title", p["expected"][0])

    def test_fallback_concept(self):
        c = SimpleNamespace(node_id="", name="", kind="", file="", line=0)
        e = mod.generate("ex47", c, [], {})
        self.assertTrue(e["payload"]["grounded"])

    def test_tolerates_suite_ctx(self):
        ctx = {"runnable": "x", "expected_output": "x", "tests": "x",
               "trace_var": "v", "trace_expected": ["1"], "buggy": "b",
               "bug_line": 1, "fixed": "f", "graph": None}
        self.assertTrue(mod.generate("ex47", make_concept(), ["x"], ctx)["front"])


class GradeTest(unittest.TestCase):
    def test_accept(self):
        e = make_ex()
        r = mod.grade(e, sub_of(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_reject_old_shape(self):
        e = make_ex()
        r = mod.grade(e, json.dumps(e["payload"]["old_rows"]))
        self.assertFalse(r["pass"])

    def test_reject_copied_field(self):
        # A rename moves the field: keeping both old and new fails.
        e = make_ex()
        rows = [dict(r, name=r.get("title", "")) for r in e["payload"]["expected"]]
        r = mod.grade(e, json.dumps(rows))
        self.assertFalse(r["pass"])
        self.assertIn("name", r["feedback"])

    def test_partial(self):
        e = make_ex()
        rows = [dict(r) for r in e["payload"]["expected"]]
        rows[-1] = dict(rows[-1], title="WRONG")
        r = mod.grade(e, json.dumps(rows))
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)

    def test_reject_count(self):
        e = make_ex()
        r = mod.grade(e, json.dumps(e["payload"]["expected"][:-1] or []))
        self.assertFalse(r["pass"])
        self.assertIn("count", r["feedback"].lower())

    def test_hostile(self):
        e = make_ex()
        for bad in ["", "not json", '{"id": 1}', "__import__('os').system('x')",
                    "x" * 50000, None, "[1, 2", '[{"id": 1}]']:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)

    def test_no_runner_needed(self):
        e = make_ex()
        self.assertTrue(mod.grade(e, sub_of(e), None)["pass"])
        self.assertTrue(mod.grade(e, sub_of(e), object())["pass"])

    def test_never_raises(self):
        for ex, s in [({}, "[]"), (None, None), ({"payload": {}}, "[]")]:
            self.assertFalse(mod.grade(ex, s)["pass"])


class RenderStatusTest(unittest.TestCase):
    def test_render(self):
        body = mod.render(make_ex())
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("models.py:3", body)

    def test_escapes(self):
        e = mod.generate("ex47", make_concept("<b>"), ["x"], {})
        self.assertNotIn("<b>", mod.render(e))

    def test_anchor(self):
        self.assertIn("id='status-b8-migration'", mod.section_html())

    def test_tour(self):
        t = mod.tour_entry()
        self.assertEqual((t["id"], t["kind"], t["path"], t["anchor"]),
                         ("migration-type", "feature", "/status",
                          "status-b8-migration"))


if __name__ == "__main__":
    unittest.main()
