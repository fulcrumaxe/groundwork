"""Decision-context quote beside design-rationale choices (I-176)."""
import json
import sqlite3
import unittest

from groundwork import cards as cardsmod
from groundwork import ratquote as ratquotemod


def _card(etype="7", **payload):
    return {"id": "c1", "exercise_type": etype,
            "payload": json.dumps(payload)}


def _row(etype="7", **payload):
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT ? AS id, ? AS exercise_type, ? AS payload",
                      ("c1", etype, json.dumps(payload)))
    return cur.fetchone()


GROUNDED = {"choices": ["signed token", "raw JSON blob"],
            "answer": "signed token",
            "reason": "Unsigned blobs are forgeable.",
            "grounded": True}


class DecisionQuoteTest(unittest.TestCase):
    def test_returns_stripped_reason(self):
        self.assertEqual(
            ratquotemod.decision_quote(
                {"reason": "  why this way\n", "grounded": True}),
            "why this way")

    def test_empty_without_reason(self):
        self.assertEqual(ratquotemod.decision_quote({}), "")
        self.assertEqual(
            ratquotemod.decision_quote({"reason": "   "}), "")
        self.assertEqual(
            ratquotemod.decision_quote({"reason": None}), "")

    def test_explicitly_ungrounded_is_no_data(self):
        self.assertEqual(
            ratquotemod.decision_quote(
                {"reason": "stale?", "grounded": False}), "")

    def test_non_dict_is_no_data(self):
        self.assertEqual(ratquotemod.decision_quote("nope"), "")
        self.assertEqual(ratquotemod.decision_quote(None), "")


class QuoteHtmlTest(unittest.TestCase):
    def test_chose_over_shape_with_escaped_text(self):
        body = ratquotemod.quote_html(_card(**{
            "choices": ["<b>", "other"], "answer": "<b>",
            "reason": "safer <here>", "grounded": True}))
        self.assertIn("<blockquote class='ratquote'>", body)
        self.assertIn("Chose <b>&lt;b&gt;</b> over other", body)
        self.assertIn("safer &lt;here&gt;", body)
        self.assertNotIn("<b>", body.replace(
            "<blockquote class='ratquote'>", "").replace(
            "<b>&lt;b&gt;</b>", ""))

    def test_reason_only_without_answer(self):
        body = ratquotemod.quote_html(
            _card(reason="just the why", grounded=True))
        self.assertIn("<blockquote class='ratquote'>", body)
        self.assertIn("just the why", body)
        self.assertNotIn("Chose", body)

    def test_non_seven_etype_is_empty(self):
        self.assertEqual(
            ratquotemod.quote_html(_card("4", **GROUNDED)), "")
        self.assertEqual(
            ratquotemod.quote_html(_card("1", **GROUNDED)), "")

    def test_legacy_fallback_is_empty_string(self):
        self.assertEqual(ratquotemod.quote_html(_card()), "")
        self.assertEqual(
            ratquotemod.quote_html(_card(choices=["a", "b"])), "")
        self.assertEqual(ratquotemod.quote_html({}), "")

    def test_row_cards_resolve(self):
        body = ratquotemod.quote_html(_row(**GROUNDED))
        self.assertIn("Chose <b>signed token</b>", body)
        self.assertEqual(ratquotemod.quote_html(_row()), "")

    def test_long_reason_truncated(self):
        body = ratquotemod.quote_html(
            _card(reason="y" * 900, answer="a", grounded=True))
        self.assertIn("...", body)
        self.assertLess(len(body), 900)

    def test_never_raises(self):
        self.assertEqual(ratquotemod.quote_html(None), "")
        self.assertEqual(
            ratquotemod.quote_html({"payload": "{broken"}), "")


class StatusSectionTest(unittest.TestCase):
    def test_anchored_subsection(self):
        body = ratquotemod.section_html()
        self.assertIn(f"id='{ratquotemod.STATUS_ANCHOR}'", body)
        self.assertIn("groundwork/ratquote.py", body)
        self.assertIn("ratquote", body)

    def test_tour_entry_shape(self):
        e = ratquotemod.tour_entry()
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], ratquotemod.STATUS_ANCHOR)
        self.assertEqual(e["path"], "/status")


class EffectTest(unittest.TestCase):
    def test_caller_widget_quotes_beside_choices(self):
        body = cardsmod.answer_widget(_card(**GROUNDED))
        self.assertIn("signed token", body)
        self.assertIn("<blockquote class='ratquote'>", body)
        self.assertIn("Unsigned blobs are forgeable.", body)

    def test_live_shape_cards_byte_identical(self):
        live = {"id": "c9", "exercise_type": "7",
                "payload": json.dumps({"hints": []})}
        self.assertEqual(ratquotemod.quote_html(live), "")
        body = cardsmod.answer_widget(live)
        self.assertNotIn("ratquote", body)
        self.assertNotIn("<blockquote", body)


if __name__ == "__main__":
    unittest.main()
