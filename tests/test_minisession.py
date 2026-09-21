"""One-click 5-minute session (I-46)."""
import copy
import unittest

from groundwork import minisession as mmod


def _card(cid, due, attempts=2):
    return {"id": cid, "due": due, "attempts": attempts}


class EstimateTest(unittest.TestCase):
    def test_new_costs_30_review_costs_20(self):
        self.assertEqual(mmod.estimate_for({"attempts": 0}), 30.0)
        self.assertEqual(mmod.estimate_for({"tries": 3}), 20.0)

    def test_unknown_attempts_errs_new(self):
        self.assertEqual(mmod.estimate_for({"id": "c1"}), 30.0)

    def test_estimate_fn_overrides(self):
        c = _card("c1", "2026-09-20T00:00:00Z")
        self.assertEqual(mmod.estimate_for(c, lambda card: 45), 45.0)

    def test_bad_estimate_fn_falls_back(self):
        c = _card("c1", "2026-09-20T00:00:00Z", attempts=5)
        self.assertEqual(mmod.estimate_for(c, lambda card: "junk"), 20.0)


class PickCardsTest(unittest.TestCase):
    def _due(self, n=10):
        return [_card(f"c{i:02d}", f"2026-09-{20 - i // 24:02d}T{i % 24:02d}:00:00Z")
                for i in range(n)]

    def test_budget_fill(self):
        due = self._due(10)
        picks = mmod.pick_cards(due, minutes=5, estimate_fn=lambda c: 60)
        self.assertEqual(len(picks), 5)

    def test_most_overdue_first(self):
        due = self._due(4)
        picks = mmod.pick_cards(list(reversed(due)), minutes=5,
                                estimate_fn=lambda c: 20)
        self.assertEqual([c["id"] for c in picks],
                         [c["id"] for c in due])

    def test_deterministic_regardless_of_input_order(self):
        due = self._due(8)
        a = mmod.pick_cards(due, minutes=5, estimate_fn=lambda c: 60)
        b = mmod.pick_cards(list(reversed(due)), minutes=5,
                            estimate_fn=lambda c: 60)
        self.assertEqual([c["id"] for c in a], [c["id"] for c in b])

    def test_never_mutates_input(self):
        due = list(reversed(self._due(6)))
        before = copy.deepcopy(due)
        picks = mmod.pick_cards(due, minutes=5, estimate_fn=lambda c: 60)
        self.assertEqual(due, before)
        self.assertIsNot(picks, due)

    def test_empty_queue(self):
        self.assertEqual(mmod.pick_cards([]), [])
        self.assertEqual(mmod.pick_cards(None), [])

    def test_guarantees_one_card(self):
        due = self._due(3)
        picks = mmod.pick_cards(due, minutes=5, estimate_fn=lambda c: 9999)
        self.assertEqual(len(picks), 1)
        # Guarantee keeps the single most-overdue card (c00), not the last.
        self.assertEqual(picks[0], min(due, key=mmod._due_key))
        self.assertEqual(picks[0]["id"], "c00")

    def test_bad_minutes_falls_back(self):
        due = self._due(10)
        picks = mmod.pick_cards(due, minutes="junk", estimate_fn=lambda c: 60)
        self.assertEqual(len(picks), 5)


class BannerTest(unittest.TestCase):
    def test_banner_copy_and_button(self):
        due = [_card(f"c{i}", "2026-09-20T00:00:00Z", attempts=1)
               for i in range(10)]
        body = mmod.session_box_html(due, minutes=5,
                                     estimate_fn=lambda c: 60)
        self.assertIn("id='minisession'", body)
        self.assertIn("About 5 cards, ~5 min", body)
        self.assertIn("id='mini-start'", body)
        self.assertIn("Start 5-minute session", body)

    def test_empty_renders_all_clear_without_button(self):
        body = mmod.session_box_html([])
        self.assertIn("id='minisession'", body)
        self.assertIn("All clear", body)
        self.assertNotIn("mini-start", body)

    def test_status_section_anchor(self):
        body = mmod.section_html()
        self.assertIn("id='status-b9-minisession'", body)
        self.assertIn("groundwork/minisession.py", body)


if __name__ == "__main__":
    unittest.main()
