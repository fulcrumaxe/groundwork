"""Tests for the regex-authoring exercise (type 54, F-31)."""
import unittest
from types import SimpleNamespace

from groundwork import regexex as mod


def make_concept(name="validator"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="validate.py", line=3)


GENERIC_CTX = {"runnable": "x", "expected_output": "x", "tests": "x",
               "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex54", make_concept(), ["x"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (54, "regex-authoring", "apply"))
        self.assertTrue(e["front"])

    def test_payload_suite_stored(self):
        e = mod.generate("ex54", make_concept(), ["x"], {})
        p = e["payload"]
        self.assertTrue(p["grounded"])
        self.assertTrue(p["positives"] and p["negatives"])
        self.assertLessEqual(len(p["positives"]) + len(p["negatives"]),
                             mod.MAX_CASES)
        self.assertTrue(p["reference"])
        # Reference is measured green on its own suite, not invented.
        self.assertTrue(mod.grade(e, p["reference"])["pass"])

    def test_deterministic_family(self):
        a = mod.generate("ex54", make_concept(), ["x"], {})
        b = mod.generate("ex54", make_concept(), ["other"], GENERIC_CTX)
        self.assertEqual(a["payload"], b["payload"])

    def test_fallback_never_raises(self):
        e = mod.generate("ex54", None, None, None)
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_tolerates_suite_ctx(self):
        e = mod.generate("ex54", make_concept(), ["x"], GENERIC_CTX)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_reference_accept(self):
        e = mod.generate("ex54", make_concept(), ["x"], {})
        r = mod.grade(e, e["payload"]["reference"])
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_loose_pattern_reject(self):
        # `.*` matches the positives but also every negative: must fail.
        e = mod.generate("ex54", make_concept(), ["x"], {})
        r = mod.grade(e, ".*")
        self.assertFalse(r["pass"])
        self.assertLess(r["score"], 1.0)
        self.assertIn("cases green", r["feedback"])

    def test_partial_credit_names_first_miss(self):
        e = mod.generate("ex54", make_concept(), ["x"], {})
        ref = e["payload"]["reference"]
        r = mod.grade(e, ref[:-1] + "+")  # widened tail: likely leaks
        if not r["pass"]:
            self.assertGreater(r["score"], 0.0)
            self.assertIn("First miss", r["feedback"])

    def test_slash_delimiters_tolerated(self):
        e = mod.generate("ex54", make_concept(), ["x"], {})
        r = mod.grade(e, "/" + e["payload"]["reference"] + "/")
        self.assertTrue(r["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex54", make_concept(), ["x"], {})
        bad_subs = [None, "", "   ", "([", "(?P<>", "a" * 500,
                    "(a+)+$", "drop table; --"]
        for sub in bad_subs:
            r = mod.grade(e, sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)
        for bad_ex in [{}, None, {"payload": {}},
                       {"payload": {"positives": [], "negatives": []}}]:
            r = mod.grade(bad_ex, ".*")
            self.assertFalse(r["pass"])


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex54", make_concept(), ["x"], {})
        body = mod.render(e)
        self.assertIn("<textarea name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("fullmatched", body)
        self.assertIn("validate.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex54", make_concept(name="<b>"), ["x"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b9-regexex'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "regex-authoring")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b9-regexex")


if __name__ == "__main__":
    unittest.main()
