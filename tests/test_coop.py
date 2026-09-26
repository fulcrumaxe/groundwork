"""Co-op card splits (F-127): complementary dealing over the due queue."""
import unittest

from test_web import handler_for, make_module

from groundwork import coop as mod


def _card(cid, concept="loops"):
    return {"id": cid, "concept_id": concept}


class DealTest(unittest.TestCase):
    def test_alternate_deal_is_complementary(self):
        due = [_card(f"c{i}") for i in range(4)]
        a, b = mod.deal(due, ["Ann", "Bo"])
        self.assertEqual([c["id"] for c in a], ["c0", "c2"])
        self.assertEqual([c["id"] for c in b], ["c1", "c3"])
        self.assertTrue(mod.is_complementary(a, b, due))

    def test_odd_queue_covers_every_card(self):
        due = [_card(f"c{i}") for i in range(5)]
        a, b = mod.deal(due, ["Ann", "Bo"])
        self.assertEqual(len(a), 3)
        self.assertEqual(len(b), 2)
        self.assertTrue(mod.is_complementary(a, b, due))

    def test_hands_keep_queue_order(self):
        due = [_card(f"c{i}", f"concept-{i}") for i in range(6)]
        a, b = mod.deal(due, ["Ann", "Bo"])
        self.assertEqual([c["id"] for c in a + b],
                         ["c0", "c2", "c4", "c1", "c3", "c5"])

    def test_solo_or_thin_queue_falls_back_empty(self):
        due = [_card(f"c{i}") for i in range(4)]
        self.assertEqual(mod.deal(due, ["Solo"]), ([], []))
        self.assertEqual(mod.deal(due, ["A", "A"]), ([], []))
        self.assertEqual(mod.deal(due, []), ([], []))
        self.assertEqual(mod.deal([_card("c0")], ["A", "B"]), ([], []))
        self.assertEqual(mod.deal([], ["A", "B"]), ([], []))

    def test_hostile_never_raises(self):
        self.assertEqual(mod.deal(None, None), ([], []))
        self.assertEqual(mod.deal("junk", 123), ([], []))
        self.assertEqual(mod.deal([None, 42, "x"], ["A", "B"]), ([], []))
        self.assertFalse(mod.is_complementary(None, None, None))
        self.assertEqual(mod.split_html(None, None), "")


class DuoTest(unittest.TestCase):
    def test_duo_needs_two_distinct_names(self):
        self.assertEqual(mod.duo(["Ann", "Bo"]), ["Ann", "Bo"])
        self.assertEqual(mod.duo(["Ann", "Ann", " "]), [])
        self.assertEqual(mod.duo(["Solo"]), [])
        self.assertEqual(mod.duo(None), [])
        self.assertEqual(mod.duo(["<b>A</b>", "<b>A</b>"]), [])

    def test_duo_matches_buddyview_rule(self):
        from groundwork import buddyview as buddymod
        for friends in (["Ann", "Bo"], ["x", "x"], [], None):
            mine = [buddymod.clean_name(f) for f in (friends or [])]
            uniq = [m for m in mine if m]
            self.assertEqual(
                [n for n in dict.fromkeys(uniq)][:2]
                if len(uniq) >= 2 and len(set(uniq)) >= 2 else [],
                mod.duo(friends))


class SplitHtmlTest(unittest.TestCase):
    def test_solo_renders_nothing(self):
        due = [_card(f"c{i}") for i in range(3)]
        self.assertEqual(mod.split_html(due, ["Solo"]), "")
        self.assertEqual(mod.split_html([_card("c0")], ["A", "B"]), "")

    def test_duo_renders_both_hands(self):
        due = [_card(f"c{i}") for i in range(4)]
        body = mod.split_html(due, ["Ann", "Bo"])
        self.assertIn("coop-split", body)
        self.assertIn("Ann", body)
        self.assertIn("Bo", body)
        self.assertEqual(body.count("coop-hand"), 2)
        for i in range(4):
            self.assertIn(f"c{i}", body)

    def test_titles_escaped(self):
        due = [_card("<script>", "<i>evil</i>"), _card("c1")]
        body = mod.split_html(due, ["A", "B"])
        self.assertNotIn("<script>", body)
        self.assertNotIn("<i>evil</i>", body)


class CallerEffectTest(unittest.TestCase):
    def test_solo_due_page_has_no_split(self):
        _tmp, db, _s, _out = make_module("coop solo")
        body = handler_for(db).due_html()
        self.assertNotIn("coop-split", body)

    def test_duo_due_page_carries_split(self):
        _tmp, db, _s, _out = make_module("coop duo")
        body = handler_for(db).due_html(buddies=["Ann", "Bo"])
        self.assertIn("coop-split", body)
        self.assertIn("Ann", body)
        self.assertIn("Bo", body)

    def test_split_covers_live_due_shape(self):
        due = [{"id": f"c{i}", "concept_id": f"k{i % 2}"}
               for i in range(6)]
        a, b = mod.deal(due, ["Ann", "Bo"])
        self.assertTrue(mod.is_complementary(a, b, due))
        self.assertEqual(len(a) + len(b), len(due))

    def test_overlapping_hands_fail_audit(self):
        due = [_card(f"c{i}") for i in range(3)]
        a, _b = mod.deal(due, ["Ann", "Bo"])
        self.assertFalse(mod.is_complementary(a, a, due))


class ShapeTest(unittest.TestCase):
    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)
        self.assertTrue(entry["blurb"])


if __name__ == "__main__":
    unittest.main()
