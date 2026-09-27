"""Reference runtime on code-card results (I-182): measured ms only."""
import json
import sqlite3
import unittest
from types import SimpleNamespace

from groundwork import refms as refmod
from groundwork import results as resmod

from test_web import make_module

REF = "def add(a, b):\n    return a + b"
HARNESS = ("_out = repr(add(2, 3))\n"
           "assert _out == '5', f'FAIL: {_out}'\nprint('OK')")


def _ok(code_seen=None):
    def _run(code):
        if code_seen is not None:
            code_seen.append(code)
        return SimpleNamespace(ok=True, stdout="5\n", stderr="")
    return SimpleNamespace(run=_run)


def _fail():
    return SimpleNamespace(
        run=lambda c: SimpleNamespace(ok=False, stdout="", stderr="boom"))


class ReferenceCodeTest(unittest.TestCase):
    def test_type8_snippet(self):
        self.assertEqual(
            refmod.reference_code(8, {"code": "print(1)"}), "print(1)")

    def test_harness_types_join_reference_and_tests(self):
        for t in (12, 19, 23, 20):
            self.assertEqual(
                refmod.reference_code(
                    t, {"reference": REF, "tests": HARNESS}),
                REF + "\n" + HARNESS)

    def test_type14_fixed_plus_tests(self):
        self.assertEqual(
            refmod.reference_code(
                14, {"fixed": REF, "tests": HARNESS}),
            REF + "\n" + HARNESS)

    def test_type11_solution_lines_plus_tests(self):
        self.assertEqual(
            refmod.reference_code(
                11, {"solution": ["a = 1", "print(a)"], "tests": "print(1)"}),
            "a = 1\nprint(a)\nprint(1)")

    def test_missing_half_is_no_data(self):
        self.assertEqual(refmod.reference_code(8, {}), "")
        self.assertEqual(
            refmod.reference_code(12, {"reference": REF}), "")
        self.assertEqual(
            refmod.reference_code(19, {"tests": HARNESS}), "")
        self.assertEqual(
            refmod.reference_code(14, {"fixed": REF}), "")
        self.assertEqual(
            refmod.reference_code(11, {"solution": ["print(1)"]}), "")

    def test_non_execution_and_hostile_is_empty(self):
        for t in (1, 2, 5, 9, 10, 99):
            self.assertEqual(
                refmod.reference_code(t, {"code": "print(1)"}), "")
        self.assertEqual(refmod.reference_code(None, {}), "")
        self.assertEqual(refmod.reference_code("bogus", {}), "")
        self.assertEqual(refmod.reference_code(8, None), "")
        self.assertEqual(refmod.reference_code(8, "x"), "")

    def test_text_exercise_type_coerced(self):
        self.assertEqual(
            refmod.reference_code("8", {"code": "print(1)"}), "print(1)")


class MeasureMsTest(unittest.TestCase):
    def test_measures_wall_clock_of_exact_code(self):
        seen = []
        ms = refmod.measure_ms(_ok(seen), "print(1)")
        self.assertIsInstance(ms, int)
        self.assertGreaterEqual(ms, 0)
        self.assertEqual(seen, ["print(1)"])

    def test_unmeasurable_is_none(self):
        self.assertIsNone(refmod.measure_ms(_fail(), "print(1)"))
        self.assertIsNone(refmod.measure_ms(None, "print(1)"))
        self.assertIsNone(refmod.measure_ms(object(), "print(1)"))
        self.assertIsNone(refmod.measure_ms(
            SimpleNamespace(run=lambda c: None), "print(1)"))

        def _raise(code):
            raise RuntimeError("sandbox down")
        self.assertIsNone(
            refmod.measure_ms(SimpleNamespace(run=_raise), "print(1)"))
        seen = []
        self.assertIsNone(refmod.measure_ms(_ok(seen), ""))
        self.assertIsNone(refmod.measure_ms(_ok(seen), None))
        self.assertEqual(seen, [])  # nothing unrunnable is executed


class MeasureForTest(unittest.TestCase):
    def test_end_to_end_with_stub(self):
        ms = refmod.measure_for(
            12, {"reference": REF, "tests": HARNESS}, _ok())
        self.assertIsInstance(ms, int)
        self.assertGreaterEqual(ms, 0)

    def test_none_when_no_reference_or_no_runner(self):
        self.assertIsNone(refmod.measure_for(12, {}, _ok()))
        self.assertIsNone(refmod.measure_for(
            12, {"reference": REF, "tests": HARNESS}, None))
        self.assertIsNone(refmod.measure_for(2, {"answers": ["x"]}, _ok()))


class FormatLineTest(unittest.TestCase):
    def test_milliseconds(self):
        self.assertEqual(refmod.format_line(42),
                         "Reference runtime: 42 ms (measured).")

    def test_sub_millisecond_is_honest(self):
        self.assertEqual(refmod.format_line(0),
                         "Reference runtime: <1 ms (measured).")

    def test_hostile_is_empty(self):
        for bad in (None, "42", 4.5, -1, True, [42], {"ms": 1}):
            self.assertEqual(refmod.format_line(bad), "")


class LineHtmlTest(unittest.TestCase):
    def test_small_line(self):
        self.assertEqual(
            refmod.line_html(42),
            "<p><small>Reference runtime: 42 ms (measured).</small></p>")

    def test_quiet_without_measurement(self):
        for bad in (None, "", "42", -1, True, 4.5, [], {}):
            self.assertEqual(refmod.line_html(bad), "")


class AttachTest(unittest.TestCase):
    def test_adds_key_only_when_measured(self):
        res = {"pass": True, "score": 1.0, "feedback": "Tests pass."}
        self.assertIs(
            refmod.attach(res, 12, {"reference": REF, "tests": HARNESS},
                          _ok()), res)
        self.assertIsInstance(res["ref_ms"], int)
        self.assertGreaterEqual(res["ref_ms"], 0)

    def test_unmeasurable_keeps_legacy_shape(self):
        res = {"pass": True, "score": 1.0, "feedback": "Tests pass."}
        refmod.attach(res, 12, {"reference": REF, "tests": HARNESS},
                      _fail())
        self.assertNotIn("ref_ms", res)
        self.assertEqual(res["feedback"], "Tests pass.")
        refmod.attach(res, 2, {"answers": ["x"]}, _ok())
        self.assertNotIn("ref_ms", res)

    def test_non_dict_passthrough_never_raises(self):
        self.assertEqual(refmod.attach([1], 8, {"code": "print(1)"}, _ok()),
                         [1])
        self.assertIsNone(refmod.attach(None, None, None, None))


class CallerEffectTest(unittest.TestCase):
    # Behavioral-effect: real submit_review (real sandbox) attaches the
    # measurement; real render_result displays it; legacy stays quiet.

    def _type8_card(self, db, code="print(2 + 3)", expected="5"):
        con = sqlite3.connect(db)
        try:
            row = con.execute(
                "SELECT id, concept_id FROM cards LIMIT 1").fetchone()
            cid = row[0] + ":t8"
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front,"
                " back, payload) VALUES(?,?,?,?,?,?)",
                (cid, row[1], "8", "Predict the output.", "5",
                 json.dumps({"code": code, "expected": expected})))
            con.commit()
        finally:
            con.close()
        return cid

    def test_submit_review_attaches_measured_ref_ms(self):
        tmp, db, server, out = make_module("refms live")
        cid = self._type8_card(db)
        out = server.submit_review(cid, "5", 3)
        res = out["result"]
        self.assertTrue(res["pass"])
        self.assertEqual(res["feedback"], "Prediction matches.")
        self.assertIn("ref_ms", res)
        self.assertIsInstance(res["ref_ms"], int)
        self.assertGreaterEqual(res["ref_ms"], 0)

    def test_submit_review_non_execution_has_no_key(self):
        tmp, db, server, out = make_module("refms legacy")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        out = server.submit_review(card["id"], "5", 4)
        self.assertNotIn("ref_ms", out["result"])

    def test_render_result_shows_measured_line(self):
        body = resmod.render_result(
            True, "Prediction matches.", "why", "2030-01-01",
            "/due", "m", 0, ref_ms=42)
        self.assertIn("Reference runtime: 42 ms (measured).", body)

    def test_render_result_legacy_byte_identical(self):
        args = (True, "good", "why", "2030-01-01", "/due", "m", 0)
        self.assertEqual(resmod.render_result(*args),
                         resmod.render_result(*args, ref_ms=None))
        self.assertNotIn("Reference runtime", resmod.render_result(*args))


class StatusTourAsciiTest(unittest.TestCase):
    def test_anchor_and_tour(self):
        self.assertIn(f"id='{refmod.STATUS_ANCHOR}'",
                      refmod.section_html())
        e = refmod.tour_entry()
        self.assertEqual(e["id"], "reference-runtime")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], refmod.STATUS_ANCHOR)

    def test_user_strings_ascii_only(self):
        blob = (refmod.format_line(42) + refmod.format_line(0)
                + refmod.line_html(7) + refmod.section_html()
                + refmod.tour_entry()["blurb"])
        blob.encode("ascii")


if __name__ == "__main__":
    unittest.main()
