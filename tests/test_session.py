"""Session-end summary (I-47)."""
import unittest

from groundwork import session as sessmod


class SummarizeTest(unittest.TestCase):
    def test_counts_and_accuracy(self):
        rows = [{"grade": 5, "due": "2026-09-21T00:00:00"},
                {"grade": 2, "due": "2026-09-20T00:00:00"},
                (4, "2026-09-22T00:00:00"),
                {"grade": "bad"}]
        s = sessmod.summarize(rows)
        self.assertEqual(s["answered"], 3)
        self.assertEqual(s["correct"], 2)
        self.assertEqual(s["accuracy"], 67)
        self.assertEqual(s["next_due"], "2026-09-20T00:00:00")

    def test_empty(self):
        s = sessmod.summarize([])
        self.assertEqual(s, {"answered": 0, "correct": 0,
                             "accuracy": 0, "next_due": ""})

    def test_html_renders(self):
        body = sessmod.summary_html(sessmod.summarize([{"grade": 5}]))
        self.assertIn("id='session'", body)
        self.assertIn("1 answered", body)


if __name__ == "__main__":
    unittest.main()
