"""Lesson audio summaries via speech synthesis (I-141)."""
import unittest

from groundwork import audiosum as mod

from test_web import handler_for, make_module


def _lesson():
    return {"summary": "Loops repeat work until done.",
            "how": ["A for loop walks each item once.",
                    "A while loop repeats while true."]}


class SummaryTest(unittest.TestCase):
    def test_truncates_at_word_boundary(self):
        lesson = {"summary": " ".join(f"w{i}" for i in range(100))}
        self.assertEqual(len(mod.summary_text(lesson).split()), 60)

    def test_combines_summary_and_first_how_step(self):
        text = mod.summary_text(_lesson())
        self.assertIn("Loops repeat", text)
        self.assertIn("for loop walks", text)
        self.assertNotIn("while loop", text)

    def test_empty_lesson_gives_empty_block(self):
        self.assertEqual(mod.summary_text({}), "")
        self.assertEqual(mod.summary_text(None), "")
        self.assertEqual(mod.block_html({}), "")

    def test_hostile_input_never_raises(self):
        self.assertEqual(mod.summary_text("nope"), "")
        self.assertEqual(mod.block_html([1, 2]), "")


class BlockTest(unittest.TestCase):
    def test_block_has_button_and_transcript(self):
        body = mod.block_html(_lesson())
        self.assertIn(f"class='{mod.BUTTON_CLASS}'", body)
        self.assertIn(mod.BUTTON_LABEL, body)
        self.assertIn("Loops repeat", body)

    def test_transcript_escaped(self):
        body = mod.block_html({"summary": "<b>bold</b>"})
        self.assertNotIn("<b>bold</b>", body)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", body)

    def test_script_guards_speech(self):
        js = mod.script_js()
        self.assertIn("data-audiosum", js)
        self.assertIn("if(!('speechSynthesis' in window))return;", js)
        self.assertIn("cancel()", js)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_module_page_shows_listen(self):
        _tmp, db, _s, out = make_module("audiosum caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn(mod.BUTTON_LABEL, body)

    def test_page_carries_wire(self):
        from groundwork import web as webmod
        raw = webmod.page("T", "<p>x</p>").decode()
        self.assertIn("data-audiosum", raw)


if __name__ == "__main__":
    unittest.main()
