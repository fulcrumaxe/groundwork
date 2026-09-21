"""Tests for the CLI UX review exercise (type 57, F-34)."""
import unittest
from types import SimpleNamespace

from groundwork import cliux as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


def answer_for(e):
    return e["payload"]["flaw"]


def wrong_for(e):
    for fid in mod._FLAW_IDS:
        if fid != e["payload"]["flaw"]:
            return fid
    raise AssertionError("taxonomy needs 2+ flaws")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (57, "cli-ux-review", "evaluate"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_grounded_on_fixture_ctx(self):
        # The test_all_types_generate fixture ctx must yield a real card.
        c = SimpleNamespace(node_id="f", name="add", kind="function",
                            file="calc.py", line=1)
        snippet = ["def add(a=2, b=3):", "    total = a + b",
                   "    return total"]
        ctx = {"runnable": "def add(a=2, b=3):\n    return a + b",
               "expected_output": "5",
               "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
               "trace_var": "total", "trace_expected": ["2", "5"],
               "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
               "fixed": "def add(a=2, b=3):\n    return a + b",
               "graph": None}
        e = mod.generate("ex57", c, snippet, ctx)
        self.assertTrue(e["front"])
        self.assertIn(e["payload"]["flaw"], mod._FLAW_IDS)

    def test_keyword_grounds_flaw(self):
        e = mod.generate("ex57", make_concept(),
                         ["def wipe(dry_run=True):", "    delete(path)"],
                         {})
        self.assertEqual(e["payload"]["mode"], "found")
        self.assertEqual(e["payload"]["flaw"], "destructive-default")

    def test_planted_is_deterministic(self):
        a = mod.generate("ex57", make_concept(), ["x = 1"], {})
        b = mod.generate("ex57", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["mode"], "planted")
        self.assertEqual(a["payload"]["flaw"], b["payload"]["flaw"])
        self.assertEqual(a["front"], b["front"])

    def test_exactly_one_flaw_listed_in_help(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        self.assertIn(e["payload"]["help"], e["front"])
        self.assertIn(e["payload"]["label"], e["back"])

    def test_no_surface_returns_none(self):
        self.assertIsNone(mod.generate("ex57", None, [], {}))
        self.assertIsNone(mod.generate("ex57", None, None, None))

    def test_never_raises(self):
        self.assertIsNone(mod.generate(None, None, None, None))


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_label_and_separator_variants_accepted(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        fid = e["payload"]["flaw"]
        _, label, aliases, _, _ = mod._by_id(fid)
        for variant in [label, label.upper(),
                        fid.replace("-", "_"), f"  '{fid}'  "]:
            r = mod.grade(e, variant)
            self.assertTrue(r["pass"], variant)
        r = mod.grade(e, aliases[0])
        self.assertTrue(r["pass"], aliases[0])

    def test_wrong_category_rejected(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        r = mod.grade(e, wrong_for(e))
        self.assertFalse(r["pass"])

    def test_empty_and_garbage_rejected(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "the help is bad", "drop table; --",
                    e["payload"]["help"],
                    f"{answer_for(e)} {wrong_for(e)}"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"], bad[:40])

    def test_hostile_never_raises(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None), (e, ""),
                                (e, "drop table; --"), (None, None),
                                ({"payload": {}}, "1"),
                                ({"payload": {"flaw": "nope"}}, "nope")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex57", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("deploy.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex57", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b10-cliux'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "cli-ux-review")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b10-cliux")


if __name__ == "__main__":
    unittest.main()
