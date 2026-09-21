"""Tests for the backfill-script exercise (type 67, F-44)."""
import unittest
from types import SimpleNamespace

from groundwork import backfill as mod


def make_concept(name="orders"):
    return SimpleNamespace(node_id="c", name=name, kind="record",
                           file="records.py", line=5)


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


def runner():
    from groundwork import sandbox as sbmod
    return sbmod.SandboxRunner()


LOOP_VARIANT = (
    "def backfill(rows):\n"
    "    out = []\n"
    "    for r in rows:\n"
    "        try:\n"
    "            score = int(r.get(\"score\", 0))\n"
    "        except (ValueError, TypeError):\n"
    "            score = 0\n"
    "        out.append({\"id\": r.get(\"id\"), "
    "\"title\": r.get(\"label\", \"untitled\"), "
    "\"score\": score, \"status\": r.get(\"status\", \"active\")})\n"
    "    return out\n"
)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (67, "backfill-script", "modify"))
        self.assertTrue(e["front"] and e["back"])
        self.assertTrue(e["payload"]["grounded"])

    def test_never_none(self):
        for args in [(None, None, None, None),
                     ("ex67", None, [], {}),
                     ("ex67", make_concept(), ["x = 1"], fixture_ctx())]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])

    def test_deterministic(self):
        a = mod.generate("ex67", make_concept(), ["x = 1"], {})
        b = mod.generate("ex67", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["old_rows"], b["payload"]["old_rows"])
        self.assertEqual(a["payload"]["expected"], b["payload"]["expected"])
        rows = a["payload"]["old_rows"]
        self.assertEqual(len(rows), 3)
        self.assertNotIn("label", rows[1])
        self.assertIsInstance(rows[2]["score"], str)

    def test_payload_fixtures(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        for key in ("func", "old_rows", "expected", "reference",
                    "retired", "grounded"):
            self.assertIn(key, e["payload"])
        self.assertEqual(len(e["payload"]["old_rows"]),
                         len(e["payload"]["expected"]))


class GradeTest(unittest.TestCase):
    def test_accept_reference(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["reference"], runner())
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_accept_loop_variant(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        r = mod.grade(e, LOOP_VARIANT, runner())
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_row_lost_fails(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        bad = LOOP_VARIANT.replace("    return out\n", "    return out[:2]\n")
        r = mod.grade(e, bad, runner())
        self.assertFalse(r["pass"])
        self.assertIn("count", r["feedback"])

    def test_missing_default_fails(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        bad = LOOP_VARIANT.replace('"untitled"', '""')
        r = mod.grade(e, bad, runner())
        self.assertFalse(r["pass"])

    def test_retired_field_fails(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        bad = LOOP_VARIANT.replace(
            "out.append({\"id\": r.get(\"id\"), ",
            "out.append({\"id\": r.get(\"id\"), \"legacy\": r.get(\"legacy\", \"\"), ")
        r = mod.grade(e, bad, runner())
        self.assertFalse(r["pass"])
        self.assertIn("legacy", r["feedback"])

    def test_wrong_name_fails(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        bad = LOOP_VARIANT.replace("def backfill(rows):",
                                   "def migrate(rows):")
        r = mod.grade(e, bad, runner())
        self.assertFalse(r["pass"])
        self.assertIn("backfill", r["feedback"])

    def test_no_runner_fails_closed(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["reference"], None)
        self.assertFalse(r["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        big = "def backfill(rows):\n" + "#" * 30000
        for bad_ex, bad_sub in [({}, "x"), (e, None), (e, ""),
                                (e, "x = 1"), (e, big), (None, None)]:
            r = mod.grade(bad_ex, bad_sub, runner())
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex67", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("records.py:5", body)
        self.assertIn("def backfill(rows):", body)

    def test_render_escapes(self):
        e = mod.generate("ex67", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-backfill'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "backfill-script", "kind": "feature",
                          "title": "Backfill script",
                          "blurb": "Write a backfill function that migrates old rows to the new shape — sandbox-executed over fixtures.",
                          "path": "/status", "anchor": "status-b11-backfill"})


if __name__ == "__main__":
    unittest.main()
