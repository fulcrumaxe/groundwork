"""Tests for the SQL-authoring exercise (type 55, F-32)."""
import unittest
from types import SimpleNamespace

from groundwork import sqlex as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="orders.py", line=3)


GENERIC_CTX = {"runnable": "x", "expected_output": "x", "tests": "x",
               "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}


def p_ref(e):
    return e["payload"]["reference"]


def rewrite_for(e):
    ref = e["payload"]["reference"]
    return ("WITH x AS (SELECT * FROM items) "
            + ref.replace("FROM items", "FROM x") + ";")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (55, "sql-authoring", "apply"))
        self.assertTrue(e["front"])

    def test_payload_grounded(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        p = e["payload"]
        self.assertTrue(p["grounded"])
        self.assertEqual(len(p["rows"]), 4)
        self.assertTrue(p["expected"])
        self.assertTrue(p["reference"].upper().startswith("SELECT"))
        self.assertIn("checkout", " ".join(r[1] for r in p["rows"]))

    def test_deterministic(self):
        a = mod.generate("ex55", make_concept(), ["x"], {})
        b = mod.generate("ex55", make_concept(), ["x"], {})
        self.assertEqual(a["payload"], b["payload"])

    def test_fallback_never_raises(self):
        e = mod.generate("ex55", None, None, None)
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_tolerates_suite_ctx(self):
        e = mod.generate("ex55", make_concept(), ["x"], GENERIC_CTX)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_reference_accept(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        r = mod.grade(e, p_ref(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_rewrite_accept(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        r = mod.grade(e, rewrite_for(e))
        self.assertTrue(r["pass"])

    def test_select_star_reject(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        r = mod.grade(e, "SELECT * FROM items")
        self.assertFalse(r["pass"])

    def test_order_rule(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        p = e["payload"]
        if len(p["expected"]) < 2:
            self.skipTest("single-row card")
        ref = p["reference"]
        if p["ordered"]:
            bad = ref.replace("ORDER BY name", "ORDER BY name DESC")
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])  # same multiset, wrong order
        else:
            # Order-insensitive specs accept the reference as-is.
            self.assertTrue(mod.grade(e, ref)["pass"])

    def test_nonselect_reject(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        for q in ("UPDATE items SET qty=0",
                  "DELETE FROM items",
                  "INSERT INTO items VALUES (9,'x',9)",
                  "DROP TABLE items",
                  "EXPLAIN SELECT * FROM items",
                  "SELECT 1; DROP TABLE items",
                  "SELECT * FROM items; SELECT * FROM items"):
            r = mod.grade(e, q)
            self.assertFalse(r["pass"], q)
        # Fixture survives: reference still grades after hostile attempts.
        self.assertTrue(mod.grade(e, p_ref(e))["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        for bad_ex, bad_sub in [({}, "SELECT 1"), (e, None), (e, ""),
                                (e, "x" * 9000), (e, "SELECT nope FROM missing"),
                                (None, None), ({"payload": {}}, "SELECT 1")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex55", make_concept(), ["x"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("orders.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex55", make_concept(name="<b>"), ["x"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b9-sqlex'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "sql-authoring")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b9-sqlex")


if __name__ == "__main__":
    unittest.main()
