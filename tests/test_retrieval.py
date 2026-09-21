"""Retrieval-first modules (F-63): attempt, then read."""
import unittest

from groundwork import retrieval as rtmod


class RetrievalTest(unittest.TestCase):
    def test_question_first_passes_prose_first_fails(self):
        good = [("question", "What doubles?"), ("prose", "Backoff does.")]
        bad = [("prose", "Backoff does."), ("question", "What doubles?")]
        self.assertTrue(rtmod.check_order(good))
        self.assertFalse(rtmod.check_order(bad))

    def test_vacuous_cases_pass(self):
        self.assertTrue(rtmod.check_order([]))
        self.assertTrue(rtmod.check_order(None))
        self.assertTrue(rtmod.check_order([("prose", "only prose")]))

    def test_enforce_is_stable_reorder(self):
        blocks = [("prose", "p1"), ("question", "q1"),
                  ("prose", "p2"), ("question", "q2")]
        out = rtmod.enforce_template(blocks)
        self.assertEqual([t for _, t in out], ["q1", "q2", "p1", "p2"])
        # Already-ordered input is unchanged.
        ordered = [("question", "q"), ("prose", "p")]
        self.assertEqual(rtmod.enforce_template(ordered), ordered)
        self.assertTrue(rtmod.check_order(out))

    def test_bad_blocks_skipped_never_raise(self):
        blocks = [("prose", "p"), ("aside", "x"), ("question", ""),
                  ("question", None), "junk", None, ("question", "q")]
        out = rtmod.enforce_template(blocks)
        self.assertEqual(out, [("question", "q"), ("prose", "p")])
        self.assertEqual(rtmod.enforce_template(None), [])
        self.assertEqual(rtmod.lesson_html(None),
                         "<article class='retrieval-first'></article>")

    def test_render_prompt_before_prose_escaped(self):
        html = rtmod.lesson_html([("prose", "<b>p</b>"),
                                  ("question", "q < 5?")])
        self.assertLess(html.index("retrieve-q"), html.index("&lt;b&gt;"))
        self.assertNotIn("<b>p</b>", html)
        self.assertIn("q &lt; 5?", html)
        self.assertIn("Recall first:", html)

    def test_section_html_anchor(self):
        html = rtmod.section_html()
        self.assertIn("id='status-b13-retrieval'", html)
        self.assertIn("enforce_template", html)

    def test_tour_entry_shape(self):
        e = rtmod.tour_entry()
        self.assertEqual(e, {
            "id": "retrieval-first",
            "kind": "feature",
            "title": "Retrieval-first lessons",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-retrieval",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "retrieval.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
