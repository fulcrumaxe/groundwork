"""Queue status chips: new vs due vs overdue (I-219)."""
import unittest
from datetime import timedelta

from groundwork import cards as cardsmod
from groundwork import sched as schedmod

from test_web import handler_for, make_module


def _card(due, stability=2.0):
    return {"id": "c1", "due": due, "stability": stability,
            "retrievability": 0.5, "lapses": 0}


class StatusChipTest(unittest.TestCase):
    def test_unattempted_is_new(self):
        self.assertIn(">new<", cardsmod.status_chip(_card(""), 0))

    def test_recent_due_is_due(self):
        due = schedmod.iso(schedmod.utcnow() - timedelta(hours=2))
        self.assertIn(">due<", cardsmod.status_chip(_card(due), 3))

    def test_old_due_is_overdue(self):
        due = schedmod.iso(schedmod.utcnow() - timedelta(days=3))
        body = cardsmod.status_chip(_card(due), 3)
        self.assertIn("3d overdue", body)

    def test_bad_date_falls_back_to_due(self):
        self.assertIn(">due<", cardsmod.status_chip(_card("junk"), 2))

    def test_due_queue_shows_chips(self):
        tmp, db, server, out = make_module("chips mod")
        h = handler_for(db)
        body = h.due_html()
        self.assertIn("id='queue-status'", body)
        self.assertIn(">new<", body)


if __name__ == "__main__":
    unittest.main()
