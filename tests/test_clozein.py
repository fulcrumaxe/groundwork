"""Inline cloze blanks inside rendered code (I-178)."""
import json
import re
import unittest

from groundwork import cards as cardsmod
from groundwork import clozein as mod

PAYLOAD = {"template": "def ___(0)(xs):\n    return ___(1)(xs)",
           "blanks": [{"id": 0, "answers": ["total"]},
                      {"id": 1, "answers": ["sum"]}],
           "answers": ["total", "sum"]}


def legacy_body(payload, conf="CONF"):
    """Verbatim copy of the cards.answer_widget etype-2 branch."""
    blanks = payload.get("blanks") or [{"id": 0, "answers": payload.get("answers", [])}]
    fields = " ".join(
        f"<label>___({b['id']}) <input name='b{b['id']}' size='12'></label>"
        for b in blanks)
    return f"{fields} {conf}<button>Check blanks</button>"


def names_of(html_text):
    return sorted(re.findall(r"name='(b\d+)'", html_text))


class HasDataTest(unittest.TestCase):
    def test_template_plus_blanks(self):
        self.assertTrue(mod.has_inline_data(PAYLOAD))

    def test_card_with_json_payload(self):
        self.assertTrue(mod.has_inline_data({"payload": json.dumps(PAYLOAD)}))

    def test_no_template_no_inline(self):
        self.assertFalse(mod.has_inline_data({"blanks": PAYLOAD["blanks"]}))

    def test_template_without_markers_no_inline(self):
        self.assertFalse(mod.has_inline_data({"template": "plain code", "blanks": []}))

    def test_garbage_is_not_inline(self):
        for bad in ({}, {"payload": "not-json{"}, {"payload": []}, None, "x"):
            self.assertFalse(mod.has_inline_data(bad))

    def test_legacy_answers_shape_counts(self):
        self.assertTrue(mod.has_inline_data(
            {"template": "use ___(0) here", "answers": ["total"]}))


class RenderCodeTest(unittest.TestCase):
    def test_inputs_replace_markers(self):
        out = mod.render_code(PAYLOAD["template"], {0: {"id": 0, "answers": ["total"]},
                                                   1: {"id": 1, "answers": ["sum"]}})
        self.assertIn("name='b0'", out)
        self.assertIn("name='b1'", out)
        self.assertNotIn("___(0)", out.replace("placeholder='___(0)'", ""))

    def test_code_html_escaped_inputs_live(self):
        out = mod.render_code("a <b> & ___(0)", {0: {"id": 0, "answers": ["z"]}})
        self.assertIn("&lt;b&gt;", out)
        self.assertIn("&amp;", out)
        self.assertIn("<input name='b0'", out)

    def test_unknown_marker_stays_literal(self):
        self.assertEqual(mod.render_code("x = ___(9)", {0: {}}), "x = ___(9)")

    def test_locked_blank_readonly_filled(self):
        out = mod.render_code(PAYLOAD["template"],
                              {0: {"id": 0, "answers": ["total"]},
                               1: {"id": 1, "answers": ["sum"]}},
                              {0: "total"}, {0})
        self.assertIn("readonly", out)
        self.assertIn("value='total'", out)
        self.assertEqual(out.count("name='b0'"), 1)  # posts once, no twin

    def test_string_ids_tolerated(self):
        out = mod.render_code(PAYLOAD["template"],
                              {0: {"id": 0, "answers": ["total"]}},
                              {"0": "total"}, ["0"])
        self.assertIn("readonly", out)

    def test_values_escaped(self):
        out = mod.render_code("___(0)", {0: {"id": 0, "answers": ["a"]}},
                              {0: "'><script>"})
        self.assertNotIn("'><script>", out)
        self.assertIn("&#x27;&gt;&lt;script&gt;", out)


class CallerEffectTest(unittest.TestCase):
    def test_due_cloze_card_gains_inline_inputs(self):
        """Behavioral effect: template cards get inputs inside <pre>."""
        body = mod.enhance(PAYLOAD, legacy_body(PAYLOAD))
        self.assertIn("<pre class='cloze-code'>", body)
        pre = body.split("<pre class='cloze-code'>")[1].split("</pre>")[0]
        self.assertIn("name='b0'", pre)
        self.assertIn("name='b1'", pre)
        self.assertNotIn("<label>___(", body)

    def test_same_posted_field_names_as_legacy(self):
        """Grade-compat: inline posts the identical b<id> shape."""
        self.assertEqual(names_of(mod.enhance(PAYLOAD, legacy_body(PAYLOAD))),
                         names_of(legacy_body(PAYLOAD)))

    def test_legacy_card_byte_identical(self):
        """No-data fallback: template-less payload keeps legacy body."""
        payload = {"blanks": PAYLOAD["blanks"]}
        legacy = legacy_body(payload)
        self.assertEqual(mod.enhance(payload, legacy), legacy)
        self.assertEqual(mod.inline_widget(payload), "")

    def test_real_caller_pins_legacy_today(self):
        """Real cards.answer_widget still renders separate fields w/o template."""
        card = {"id": "c-legacy", "exercise_type": "2",
                "payload": json.dumps({"blanks": PAYLOAD["blanks"]})}
        out = cardsmod.answer_widget(card)
        self.assertIn("<label>___(0)", out)
        self.assertNotIn("cloze-code", out)

    def test_answer_widget_renders_inline_with_template(self):
        """Post-wire proof: template cards render inline via the caller."""
        card = {"id": "c-inline", "exercise_type": "2",
                "payload": json.dumps(PAYLOAD)}
        out = cardsmod.answer_widget(card)
        self.assertIn("cloze-code", out)
        self.assertIn("name='b0'", out)


class DemoTest(unittest.TestCase):
    def test_section_anchored_with_demo(self):
        out = mod.section_html()
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", out)
        self.assertIn("cloze-code", out)

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("inline-cloze-blanks", "improvement",
                          "/status", mod.STATUS_ANCHOR))


if __name__ == "__main__":
    unittest.main()
