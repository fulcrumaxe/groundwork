"""Unsaved-textarea guard (I-29)."""
import unittest

from groundwork import answerguard as agmod
from groundwork import unsaved as umod


class DirtyTest(unittest.TestCase):
    def test_empty_is_clean(self):
        for clean in ("", "   ", "\n\t ", None):
            self.assertFalse(umod.is_dirty(clean))

    def test_text_is_dirty(self):
        self.assertTrue(umod.is_dirty("half an answer"))
        self.assertTrue(umod.is_dirty("  x  "))

    def test_non_string_coerced(self):
        self.assertFalse(umod.is_dirty(None))
        self.assertTrue(umod.is_dirty(123))


class GuardJsTest(unittest.TestCase):
    def test_beforeunload_and_dirty_check(self):
        js = umod.guard_js()
        self.assertIn("beforeunload", js)
        self.assertIn("textarea", js)
        self.assertIn("querySelectorAll", js)

    def test_submitted_flag_never_blocks_submits(self):
        js = umod.guard_js()
        self.assertIn("submit", js)
        self.assertIn("SUBMITTED", js)
        self.assertIn("returnValue", js)

    def test_targets_card_forms(self):
        self.assertIn("/cards/", umod.guard_js())

    def test_no_duplicate_of_answerguard(self):
        js = umod.guard_js()
        self.assertNotIn("guard-warn", js)
        self.assertNotIn("looks empty", js)
        self.assertNotIn(agmod.guard("")["warning"], js)


class SectionTest(unittest.TestCase):
    def test_anchor(self):
        body = umod.section_html()
        self.assertIn("id='status-b7-unsaved'", body)
        self.assertIn("groundwork/unsaved.py", body)


if __name__ == "__main__":
    unittest.main()
