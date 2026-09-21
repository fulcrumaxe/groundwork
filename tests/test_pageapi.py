"""Tests for the page-retrofit exercise (type 68, F-45)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import pageapi as mod


def make_concept(name="orders"):
    return SimpleNamespace(node_id="c", name=name, kind="endpoint",
                           file="api.py", line=10)


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


def answer_for(e, page):
    rows = e["payload"]["rows"]
    n = e["payload"]["per_page_default"]
    total = e["payload"]["total"]
    start = (page - 1) * n
    return json.dumps({"items": rows[start:start + n], "page": page,
                       "per_page": n, "total": total})


def good_sub(e):
    return (f"page1={answer_for(e, 1)}\npage2={answer_for(e, 2)}\n"
            f"page99={answer_for(e, 99)}\n")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (68, "page-retrofit", "apply"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_never_none(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])

    def test_never_none_never_raises(self):
        e = mod.generate(None, None, None, None)
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])

    def test_fixture_deterministic(self):
        a = mod.generate("ex68", make_concept(), ["x = 1"], {})
        b = mod.generate("ex68", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["rows"], b["payload"]["rows"])
        self.assertEqual(a["payload"]["total"], len(a["payload"]["rows"]))
        self.assertEqual(a["payload"]["total"], 23)

    def test_default_per_page(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        self.assertEqual(e["payload"]["per_page_default"], 5)
        self.assertEqual(e["payload"]["per_page_max"], 20)


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        r = mod.grade(e, good_sub(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_page2_overlap_fails(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        bad = (f"page1={answer_for(e, 1)}\npage2={answer_for(e, 1)}\n"
               f"page99={answer_for(e, 99)}\n")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_missing_total_fails(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        rows = e["payload"]["rows"]
        page1 = json.dumps({"items": rows[0:5], "page": 1, "per_page": 5})
        bad = (f"page1={page1}\npage2={answer_for(e, 2)}\n"
               f"page99={answer_for(e, 99)}\n")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_inconsistent_total_fails(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        rows = e["payload"]["rows"]
        page2 = json.dumps({"items": rows[5:10], "page": 2,
                            "per_page": 5, "total": 99})
        bad = (f"page1={answer_for(e, 1)}\npage2={page2}\n"
               f"page99={answer_for(e, 99)}\n")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_unstable_order_fails(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        rows = e["payload"]["rows"]
        flipped = list(reversed(rows[5:10]))
        page2 = json.dumps({"items": flipped, "page": 2,
                            "per_page": 5, "total": 23})
        bad = (f"page1={answer_for(e, 1)}\npage2={page2}\n"
               f"page99={answer_for(e, 99)}\n")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_out_of_range_wrap_fails(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        rows = e["payload"]["rows"]
        last = json.dumps({"items": rows[20:23], "page": 99,
                           "per_page": 5, "total": 23})
        bad = (f"page1={answer_for(e, 1)}\npage2={answer_for(e, 2)}\n"
               f"page99={last}\n")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_no_partial_credit(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        rows = e["payload"]["rows"]
        last = json.dumps({"items": rows[20:23], "page": 99,
                           "per_page": 5, "total": 23})
        bad = (f"page1={answer_for(e, 1)}\npage2={answer_for(e, 2)}\n"
               f"page99={last}\n")
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", None, "hello"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "page1={}"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex68", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("page1", body)
        self.assertIn("page99", body)
        self.assertIn("How grading works", body)
        self.assertIn("api.py:10", body)
        self.assertIn("orders", body)

    def test_render_escapes(self):
        e = mod.generate("ex68", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-pageapi'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "page-the-endpoint", "kind": "feature",
                          "title": "Page the endpoint",
                          "blurb": "Retrofit paging onto a list endpoint — slices, total, and stable order checked.",
                          "path": "/status", "anchor": "status-b11-pageapi"})


if __name__ == "__main__":
    unittest.main()
