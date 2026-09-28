"""Weekend/light mode: reduced load on chosen days (I-206)."""
import copy
import unittest
from datetime import date

from groundwork import lightdays as lmod

from test_web import handler_for, make_module


def _card(cid, due, attempts=2):
    return {"id": cid, "due": due, "attempts": attempts}


def _mixed():
    # 4 reviews (even ids) + 4 new (odd ids), most-overdue-first order.
    return [_card(f"c{i:02d}", f"2026-09-{10 + i:02d}T00:00:00Z",
                  attempts=2 if i % 2 == 0 else 0)
            for i in range(8)]


class ParseDaysTest(unittest.TestCase):
    def test_weekend_preset(self):
        self.assertEqual(lmod.parse_days("weekend"), {5, 6})

    def test_names_case_insensitive(self):
        self.assertEqual(lmod.parse_days("Sat, SUN"), {5, 6})
        self.assertEqual(lmod.parse_days("monday"), {0})

    def test_ints_and_single_int(self):
        self.assertEqual(lmod.parse_days("5,6"), {5, 6})
        self.assertEqual(lmod.parse_days(5), {5})
        self.assertEqual(lmod.parse_days(9), frozenset())

    def test_ranges(self):
        self.assertEqual(lmod.parse_days("sat-sun"), {5, 6})
        self.assertEqual(lmod.parse_days("1-3"), {1, 2, 3})

    def test_absent_and_off_is_empty(self):
        for v in (None, "", "  ", "off", "none", "never"):
            self.assertEqual(lmod.parse_days(v), frozenset())

    def test_garbage_fails_closed(self):
        self.assertEqual(lmod.parse_days("junk"), frozenset())
        self.assertEqual(lmod.parse_days("sat,junk"), {5})

    def test_list_input(self):
        self.assertEqual(lmod.parse_days(["sat", 6]), {5, 6})


class ParseFractionTest(unittest.TestCase):
    def test_absent_is_default_half(self):
        self.assertEqual(lmod.parse_fraction(None), 0.5)
        self.assertEqual(lmod.parse_fraction(""), 0.5)

    def test_valid_values(self):
        self.assertEqual(lmod.parse_fraction("0.5"), 0.5)
        self.assertEqual(lmod.parse_fraction(0.25), 0.25)
        self.assertEqual(lmod.parse_fraction(0), 0.0)
        self.assertEqual(lmod.parse_fraction("50%"), 0.5)

    def test_garbage_is_none(self):
        for v in ("junk", -1, float("nan"), True, [1]):
            self.assertIsNone(lmod.parse_fraction(v))

    def test_full_or_more_clamps_to_keep_all(self):
        self.assertEqual(lmod.parse_fraction(1.0), 1.0)
        self.assertEqual(lmod.parse_fraction(2.5), 1.0)


class LightDayTest(unittest.TestCase):
    def test_weekday_ints(self):
        self.assertEqual(lmod.weekday_of(5), 5)
        self.assertIsNone(lmod.weekday_of(9))

    def test_iso_strings(self):
        iso = "2026-09-26"
        self.assertEqual(lmod.weekday_of(iso),
                         date(2026, 9, 26).weekday())
        self.assertIsNone(lmod.weekday_of("junk"))

    def test_none_is_a_real_weekday(self):
        self.assertIn(lmod.weekday_of(None), range(7))

    def test_is_light_day(self):
        self.assertTrue(lmod.is_light_day("weekend", 5))
        self.assertTrue(lmod.is_light_day("sat,sun", 6))
        self.assertFalse(lmod.is_light_day("weekend", 2))
        self.assertFalse(lmod.is_light_day("junk", 5))
        self.assertFalse(lmod.is_light_day(None, 5))


class ApplyEffectTest(unittest.TestCase):
    def test_light_day_halves_mixed_queue(self):
        due = _mixed()
        kept = lmod.apply_light_days(due, "sat", 0.5, 5)
        self.assertEqual([c["id"] for c in kept],
                         ["c00", "c02", "c04", "c06"])

    def test_reviews_always_survive_even_over_target(self):
        due = _mixed()
        kept = lmod.apply_light_days(due, "weekend", 0.1, 6)
        self.assertEqual([c["id"] for c in kept],
                         ["c00", "c02", "c04", "c06"])

    def test_gentler_fraction_keeps_first_new_cards(self):
        due = _mixed()
        kept = lmod.apply_light_days(due, "sat", 0.75, 5)
        self.assertEqual([c["id"] for c in kept],
                         ["c00", "c01", "c02", "c03", "c04", "c06"])

    def test_zero_fraction_is_reviews_only(self):
        due = _mixed()
        kept = lmod.apply_light_days(due, "sun", 0, 6)
        self.assertEqual([c["id"] for c in kept],
                         ["c00", "c02", "c04", "c06"])

    def test_tried_map_overrides_card_fields(self):
        due = [_card("r", "2026-09-10T00:00:00Z", attempts=5),
               _card("n", "2026-09-11T00:00:00Z", attempts=0)]
        kept = lmod.apply_light_days(due, "sat", 0.5, 5,
                                     tried={"r": 0, "n": 4})
        self.assertEqual([c["id"] for c in kept], ["n"])

    def test_guarantees_one_card(self):
        due = [_card(f"n{i}", "2026-09-10T00:00:00Z", attempts=0)
               for i in range(3)]
        kept = lmod.apply_light_days(due, "sat", 0, 5)
        self.assertEqual(len(kept), 1)
        self.assertIs(kept[0], due[0])

    def test_never_mutates_input(self):
        due = _mixed()
        before = copy.deepcopy(due)
        kept = lmod.apply_light_days(due, "sat", 0.5, 5)
        self.assertEqual(due, before)
        self.assertIsNot(kept, due)

    def test_never_raises(self):
        due = [{"id": 1}]
        self.assertIs(lmod.apply_light_days(due, object(), object(),
                                            object()),
                      due)


class FallbackPinTest(unittest.TestCase):
    """Legacy full queue: inactive light mode returns due identical."""

    def test_no_days_returns_identical(self):
        for days in (None, "", "off", "junk"):
            due = _mixed()
            self.assertIs(lmod.apply_light_days(due, days, 0.5, 5), due)

    def test_bad_fraction_returns_identical(self):
        due = _mixed()
        self.assertIs(lmod.apply_light_days(due, "sat", "junk", 5), due)

    def test_non_light_weekday_returns_identical(self):
        due = _mixed()
        self.assertIs(lmod.apply_light_days(due, "sat", 0.5, 2), due)

    def test_empty_queue_returns_identical(self):
        due = []
        self.assertIs(lmod.apply_light_days(due, "weekend", 0.5, 5), due)

    def test_non_list_returns_identical(self):
        self.assertIsNone(lmod.apply_light_days(None, "sat", 0.5, 5))
        self.assertEqual(lmod.apply_light_days("nope", "sat", 0.5, 5),
                         "nope")


class DueCallerTest(unittest.TestCase):
    # Real caller proof: Handler.due_html honors ?light=/ ?lightfrac=.

    def test_due_html_light_day_trims_new(self):
        tmp, db, server, out = make_module("lightdays caller")
        h = handler_for(db)
        base = h.due_html()
        light = h.due_html(light="everyday", lightfrac="0")
        self.assertEqual(base.count("<article"), 2)
        self.assertEqual(light.count("<article"), 1)
        self.assertIn("id='lightdays'", light)
        self.assertIn("due reviews always stay", light)

    def test_due_html_box_always_renders(self):
        tmp, db, server, out = make_module("lightdays box")
        h = handler_for(db)
        self.assertIn("id='lightdays'", h.due_html())

    def test_due_html_off_is_default_box(self):
        tmp, db, server, out = make_module("lightdays off")
        h = handler_for(db)
        self.assertEqual(h.due_html(light="off", lightfrac="0.5"),
                         h.due_html(light="", lightfrac=""))


class BoxTest(unittest.TestCase):
    def test_control_links_and_anchor(self):
        body = lmod.light_box_html("weekend", 0.5)
        self.assertIn("id='lightdays'", body)
        self.assertIn("Light days", body)
        self.assertIn("/due?light=weekend", body)
        self.assertIn("(light)", body)
        self.assertIn("due reviews always stay", body)

    def test_mode_preserved(self):
        body = lmod.light_box_html("", None, "one")
        self.assertIn("mode=one", body)

    def test_off_explains_full_queue(self):
        body = lmod.light_box_html()
        self.assertIn("full queue every day", body)

    def test_status_section_anchor(self):
        body = lmod.section_html()
        self.assertIn("id='status-b29-lightdays'", body)
        self.assertIn("groundwork/lightdays.py", body)
        self.assertIn("apply_light_days", body)

    def test_tour_entry_shape(self):
        e = lmod.tour_entry()
        self.assertEqual(e["id"], "light-days")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["path"], "/due")
        self.assertEqual(e["anchor"], lmod.SECTION_ANCHOR)


if __name__ == "__main__":
    unittest.main()
