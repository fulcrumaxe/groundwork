"""Next-gap forecast: scheduler estimate plus Due rendering (I-203)."""
import unittest

from groundwork import cards as cardsmod
from groundwork import sched as schedmod

from test_web import handler_for, make_module


class ForecastGapTest(unittest.TestCase):
    def test_mirrors_review_interval(self):
        for stab in (0.4, 1.0, 3.0, 9.6):
            with self.subTest(stability=stab):
                gap = schedmod.forecast_gap(stab)
                expect = max(1, round(stab))
                self.assertIn(f"{expect}d", gap)

    def test_bad_input_is_unknown(self):
        self.assertEqual(schedmod.forecast_gap("high"), "unknown")

    def test_due_shows_forecast(self):
        tmp, db, server, out = make_module("forecast mod")
        h = handler_for(db)
        body = h.due_html()
        self.assertIn("id='forecast'", body)
        self.assertIn("Forecast:", body)

    def test_garbage_stability_renders_nothing(self):
        self.assertEqual(cardsmod.forecast_html({"stability": "high"}), "")


if __name__ == "__main__":
    unittest.main()
