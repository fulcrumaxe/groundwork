"""Answer history diff on results (I-197): prior answer shown on change."""
import unittest

from groundwork import answerhist as ahmod
from groundwork import results as resmod

from test_web import make_module


class ChangedTest(unittest.TestCase):
    def test_differing_answers(self):
        self.assertTrue(ahmod.changed("Paris", "Lyon"))

    def test_identical_is_quiet(self):
        self.assertFalse(ahmod.changed("Paris", "Paris"))

    def test_whitespace_only_is_quiet(self):
        self.assertFalse(ahmod.changed("  Paris  ", "Paris"))
        self.assertFalse(ahmod.changed("New\nYork", "New York"))

    def test_case_counts_as_change(self):
        self.assertTrue(ahmod.changed("Paris", "paris"))

    def test_blank_or_hostile_is_quiet(self):
        for bad in ("", "   ", None, 5, True, ["x"], {"a": 1}):
            self.assertFalse(ahmod.changed(bad, "Paris"))
            self.assertFalse(ahmod.changed("Paris", bad))
            self.assertFalse(ahmod.changed(bad, bad))


class DiffLineTest(unittest.TestCase):
    def test_exact_line(self):
        self.assertEqual(ahmod.diff_line("Paris", "Lyon"),
                         'Last time you wrote "Paris".')

    def test_long_prior_truncates(self):
        line = ahmod.diff_line("x" * 200, "y")
        self.assertEqual(line, 'Last time you wrote "' + "x" * 160 + '...".')

    def test_boundary_160_chars_verbatim(self):
        line = ahmod.diff_line("x" * 160, "y")
        self.assertEqual(line, 'Last time you wrote "' + "x" * 160 + '".')

    def test_quiet_cases(self):
        self.assertEqual(ahmod.diff_line("", "Lyon"), "")
        self.assertEqual(ahmod.diff_line("Paris", ""), "")
        self.assertEqual(ahmod.diff_line("Paris", "Paris"), "")
        self.assertEqual(ahmod.diff_line(None, None), "")
        self.assertEqual(ahmod.diff_line(5, ["x"]), "")


class LineHtmlTest(unittest.TestCase):
    def test_escaped_line(self):
        self.assertEqual(
            ahmod.line_html("Paris", "Lyon"),
            "<p><small>Last time you wrote &quot;Paris&quot;.</small></p>")

    def test_stored_markup_cannot_break_out(self):
        body = ahmod.line_html("<b>hi</b>", "other")
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;hi&lt;/b&gt;", body)

    def test_quiet_without_change(self):
        for prior, cur in (("", "x"), ("x", ""), ("x", "x"),
                           (None, "x"), ("x", None), (5, 6)):
            self.assertEqual(ahmod.line_html(prior, cur), "")


class AttachTest(unittest.TestCase):
    def test_adds_key_only_on_change(self):
        res = {"pass": False, "score": 0.0, "feedback": "Try again."}
        self.assertIs(ahmod.attach(res, "Paris", "Lyon"), res)
        self.assertIn("Last time you wrote", res["answer_hist"])
        self.assertIn("Paris", res["answer_hist"])

    def test_unchanged_keeps_legacy_shape(self):
        res = {"pass": True, "score": 1.0, "feedback": "Good."}
        ahmod.attach(res, "Paris", "Paris")
        self.assertNotIn("answer_hist", res)
        self.assertEqual(res["feedback"], "Good.")
        ahmod.attach(res, "", "Lyon")
        self.assertNotIn("answer_hist", res)

    def test_non_dict_passthrough_never_raises(self):
        self.assertEqual(ahmod.attach([1], "a", "b"), [1])
        self.assertIsNone(ahmod.attach(None, None, None))


class CallerEffectTest(unittest.TestCase):
    # Behavioral-effect: real submit_review attaches the diff on a
    # changed repeat; real render_result displays it; first attempts
    # keep the legacy shape and render legacy-identical.

    def test_first_attempt_has_no_key(self):
        tmp, db, server, out = make_module("answerhist first")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        out = server.submit_review(card["id"], "Paris", 3)
        self.assertNotIn("answer_hist", out["result"])

    def test_changed_repeat_carries_prior(self):
        tmp, db, server, out = make_module("answerhist live")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "Paris", 3)
        second = server.submit_review(card["id"], "Lyon", 3)
        line = second["result"]["answer_hist"]
        self.assertIn("Last time you wrote", line)
        self.assertIn("Paris", line)
        self.assertNotIn("Lyon", line)  # current answer is not repeated

    def test_identical_repeat_stays_quiet(self):
        tmp, db, server, out = make_module("answerhist repeat")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "Paris", 3)
        second = server.submit_review(card["id"], "Paris", 3)
        self.assertNotIn("answer_hist", second["result"])

    def test_render_result_shows_history_line(self):
        body = resmod.render_result(
            True, "good", "why", "2030-01-01",
            "/due", "m", 0,
            answer_hist=ahmod.line_html("Paris", "Lyon"))
        self.assertIn("Last time you wrote", body)
        self.assertIn("Paris", body)

    def test_render_result_legacy_byte_identical(self):
        args = (True, "good", "why", "2030-01-01", "/due", "m", 0)
        self.assertEqual(resmod.render_result(*args),
                         resmod.render_result(*args, answer_hist=""))
        self.assertNotIn("Last time", resmod.render_result(*args))


class StatusTourAsciiTest(unittest.TestCase):
    def test_anchor_and_tour(self):
        self.assertIn(f"id='{ahmod.STATUS_ANCHOR}'",
                      ahmod.section_html())
        e = ahmod.tour_entry()
        self.assertEqual(e["id"], "answer-history")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], ahmod.STATUS_ANCHOR)

    def test_user_strings_ascii_only(self):
        blob = (ahmod.diff_line("Paris", "Lyon")
                + ahmod.diff_line("x" * 200, "y")
                + ahmod.line_html("a", "b") + ahmod.section_html()
                + ahmod.tour_entry()["blurb"])
        blob.encode("ascii")


if __name__ == "__main__":
    unittest.main()
