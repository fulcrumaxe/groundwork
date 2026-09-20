"""Card deep-links (I-7)."""
import unittest

from groundwork import cardlinks as cardmod


class CardLinksTest(unittest.TestCase):
    def test_anchor_prefixes_card_id(self):
        self.assertEqual(cardmod.card_anchor("abc"), "card-abc")

    def test_anchor_blank_renders_empty(self):
        self.assertEqual(cardmod.card_anchor(""), "")
        self.assertEqual(cardmod.card_anchor(None), "")
        self.assertEqual(cardmod.card_anchor(123), "")

    def test_anchor_sanitises_unsafe_chars(self):
        body = cardmod.card_anchor("m1:weird/id here")
        self.assertTrue(body.startswith("card-"))
        self.assertNotIn(" ", body)
        self.assertNotIn("/", body)
        self.assertNotIn(":", body)

    def test_anchor_preserves_case(self):
        self.assertNotEqual(cardmod.card_anchor("AbC"), cardmod.card_anchor("abc"))

    def test_anchor_never_collides_with_lessons(self):
        self.assertFalse(cardmod.card_anchor("x").startswith("lesson-"))

    def test_url_points_at_module_plus_fragment(self):
        self.assertEqual(
            cardmod.card_url("m1", "abc"), "/modules/m1#card-abc")

    def test_url_without_card_falls_back_to_module(self):
        self.assertEqual(cardmod.card_url("m1", ""), "/modules/m1")

    def test_url_escapes_module_id(self):
        body = cardmod.card_url("m'1", "abc")
        self.assertNotIn("m'1", body)

    def test_article_tag_carries_anchor(self):
        body = cardmod.article_open("abc")
        self.assertIn("id='card-abc'", body)
        self.assertTrue(body.startswith("<article"))

    def test_history_link_jumps_to_card(self):
        body = cardmod.history_link("m1", "abc", "My module")
        self.assertIn("href='/modules/m1#card-abc'", body)
        self.assertIn("My module", body)

    def test_history_link_escapes_label(self):
        body = cardmod.history_link("m1", "abc", "<b>x</b>")
        self.assertNotIn("<b>", body)

    def test_status_section_has_stable_anchor(self):
        body = cardmod.section_html()
        self.assertIn("id='status-b6-cardlinks'", body)


if __name__ == "__main__":
    unittest.main()
