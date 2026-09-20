"""Unique page titles (I-1)."""
import unittest

from groundwork import titles as titlesmod


class PageTitleTest(unittest.TestCase):
    def test_page_and_context(self):
        t = titlesmod.page_title("Due", "3 cards")
        self.assertIn("Due", t)
        self.assertIn("3 cards", t)
        self.assertIn("Groundwork", t)

    def test_page_only(self):
        self.assertEqual(titlesmod.page_title("History"), "History | Groundwork")

    def test_blank_falls_back_to_site(self):
        self.assertEqual(titlesmod.page_title("", ""), "Groundwork")
        self.assertEqual(titlesmod.page_title(None, None), "Groundwork")

    def test_whitespace_collapsed(self):
        self.assertEqual(titlesmod.page_title("  Due\n", None), "Due | Groundwork")


if __name__ == "__main__":
    unittest.main()
