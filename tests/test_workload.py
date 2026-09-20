"""Workload forecast: 30-day due buckets (I-204)."""
import unittest

from groundwork import workload as workloadmod

from test_web import handler_for, make_module


class WorkloadBucketsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("workload mod")
        self.h = handler_for(self.db)

    def test_thirty_days_starting_today(self):
        import datetime
        rows = workloadmod.buckets(self.db)
        self.assertEqual(len(rows), 30)
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        self.assertEqual(rows[0][0], today)
        self.assertTrue(all(n >= 0 for _, n in rows))

    def test_due_cards_land_in_buckets(self):
        total = sum(n for _, n in workloadmod.buckets(self.db))
        self.assertGreater(total, 0)

    def test_history_shows_forecast(self):
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)
        body = self.h.history_html()
        self.assertIn("id='workload'", body)
        self.assertIn("Workload forecast", body)
        self.assertIn("30 days", body)


if __name__ == "__main__":
    unittest.main()
