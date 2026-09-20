"""Queue status chips: new vs due vs overdue (I-219)."""
import unittest
from datetime import timedelta

from groundwork import cards as cardsmod
from groundwork import queue as qmod
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


class ModuleGroupsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("queue mod")

    def test_single_module_single_group(self):
        due = self.server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertTrue(due)
        groups = qmod.groups(self.db, due)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]["cards"]), len(due))
        self.assertIn("queue mod", groups[0]["title"])

    def test_missing_concept_goes_to_tail_group(self):
        due = self.server.tool_list_due_reviews({"limit": 20})["due"]
        ghost = dict(due[0])
        ghost["concept_id"] = "nope:gone"
        groups = qmod.groups(self.db, due + [ghost])
        self.assertEqual(groups[-1]["title"], "Unknown module")
        self.assertEqual(groups[-1]["cards"], [ghost])

    def test_due_page_renders_group_sections(self):
        h = handler_for(self.db)
        out = h.due_html()
        self.assertIn("id='queue-groups'", out)
        self.assertIn("<details open><summary", out)


class OneCardTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("one mod")

    def test_link_present_by_default(self):
        out = handler_for(self.db).due_html()
        self.assertIn("id='one-card'", out)
        self.assertIn("/due?mode=one", out)

    def test_one_mode_shows_single_card(self):
        h = handler_for(self.db)
        full = h.due_html()
        one = h.due_html(one=True)
        self.assertIn("id='one-card-note'", one)
        self.assertLess(one.count("<article"), full.count("<article"))
        self.assertEqual(one.count("<article"), 1)


if __name__ == "__main__":
    unittest.main()
