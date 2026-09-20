"""Char/line counts (I-153)."""
import unittest

from groundwork import charcount as ccmod


class CountMetaTest(unittest.TestCase):
    def test_counts(self):
        self.assertEqual(ccmod.count_meta("hi\nthere you"),
                         {"chars": 12, "lines": 2, "words": 3})

    def test_empty_and_none(self):
        self.assertEqual(ccmod.count_meta(""), {"chars": 0, "lines": 0, "words": 0})
        self.assertEqual(ccmod.count_meta(None), {"chars": 0, "lines": 0, "words": 0})

    def test_hint_renders(self):
        body = ccmod.textarea_hint("a b")
        self.assertIn("chars", body)
        self.assertIn("lines", body)


if __name__ == "__main__":
    unittest.main()
