"""Lesson read times: word-count estimates (I-101)."""
import unittest

from groundwork import readtime as readtimemod

from test_web import handler_for, make_module


class MinutesForTest(unittest.TestCase):
    def test_counts_words_at_200wpm(self):
        lesson = {"summary": " ".join(["word"] * 400)}
        self.assertEqual(readtimemod.minutes_for(lesson), 2)

    def test_minimum_one_minute(self):
        self.assertEqual(readtimemod.minutes_for({}), 1)
        self.assertEqual(readtimemod.minutes_for({"summary": "hi"}), 1)
        self.assertEqual(readtimemod.minutes_for("nope"), 1)

    def test_counts_nested_how_steps(self):
        lesson = {"summary": "",
                  "how": [{"h": "a", "b": " ".join(["w"] * 200)}]}
        self.assertEqual(readtimemod.minutes_for(lesson), 1)

    def test_module_toc_shows_minutes(self):
        tmp, db, server, out = make_module("readtime mod")
        h = handler_for(db)
        body = h.module_html(out["module_id"])
        self.assertIn("id='readtime'", body)
        self.assertIn("min", body)


if __name__ == "__main__":
    unittest.main()
