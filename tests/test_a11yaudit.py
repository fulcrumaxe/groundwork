"""Tests for the a11y-audit exercise (type 52, F-29)."""
import unittest
from types import SimpleNamespace

from groundwork import a11yaudit as mod


def make_concept(name="signup page"):
    return SimpleNamespace(node_id="c", name=name, kind="page",
                           file="page.html", line=3)


FULL = ["<html>", "<body>", "<h2>News</h2>", '<img src="pic.png">',
        '<input type="text" id="q">', '<div onclick="go()">Click me</div>',
        '<a href="/x"></a>', "</body>", "</html>"]

CLEAN = ["<html lang=\"en\">", "<body>", "<h1>News</h1>",
         '<img src="pic.png" alt="">',
         '<label for="q">Search</label><input type="text" id="q">',
         '<div role="button" tabindex="0">Click me</div>',
         '<a href="/x" aria-label="close">x</a>',
         "</body>", "</html>"]


def answer_for(e):
    return "\n".join(f"{it['id']}={it['rule']}"
                     for it in e["payload"]["checklist"])


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex52", make_concept(), FULL, {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (52, "a11y-audit", "analyse"))
        self.assertTrue(e["front"])

    def test_closed_rule_set(self):
        e = mod.generate("ex52", make_concept(), FULL, {})
        rules = [it["rule"] for it in e["payload"]["checklist"]]
        self.assertEqual(rules, list(mod.RULES))
        self.assertTrue(e["payload"]["grounded"])

    def test_false_positive_guards(self):
        self.assertIsNone(mod.generate("ex52", make_concept(), CLEAN, {}))

    def test_escaped_entities_not_flagged(self):
        e = mod.generate("ex52", make_concept(),
                         ["<p>&lt;img src=x&gt; &lt;div onclick=y&gt;</p>"],
                         {})
        self.assertIsNone(e)

    def test_no_surface_returns_none(self):
        self.assertIsNone(mod.generate("ex52", make_concept(),
                                       ["<p>just text</p>"], {}))

    def test_never_raises(self):
        for ex_id, concept, snippet, ctx in [
                ("x", None, None, None), (None, None, [], {}),
                ("x", make_concept(), None, None)]:
            try:
                mod.generate(ex_id, concept, snippet, ctx)
            except Exception as exc:  # noqa: BLE001
                self.fail(f"generate raised {exc!r}")

    def test_deterministic(self):
        a = mod.generate("ex52", make_concept(), FULL, {})
        b = mod.generate("ex52", make_concept(), FULL, {})
        self.assertEqual(a["back"], b["back"])


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex52", make_concept(), FULL, {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_plain_words_accept(self):
        e = mod.generate("ex52", make_concept(), FULL, {})
        r = mod.grade(e, "missing alt text\nno label\nclickable div\n"
                         "missing lang\nempty link\nskipped heading")
        self.assertTrue(r["pass"])

    def test_partial_credit(self):
        e = mod.generate("ex52", make_concept(), FULL, {})
        keep = [it for it in e["payload"]["checklist"][:5]]
        r = mod.grade(e, "\n".join(f"{it['id']}={it['rule']}" for it in keep))
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 1.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex52", make_concept(), FULL, {})
        for bad_ex, bad_sub in [({}, "0=img-missing-alt"), (e, None),
                                (e, ""), (e, "drop table; --"),
                                (e, "<script>alert(1)</script>"),
                                (e, "&lt;img&gt;"), (None, None),
                                ({"payload": {}}, "alt")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex52", make_concept(), FULL, {})
        body = mod.render(e)
        self.assertIn("<ol>", body)
        self.assertIn("name='answer'", body)
        self.assertIn("0=img-missing-alt", body)
        self.assertIn("page.html:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex52", make_concept(name="<b>"), FULL, {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b9-a11yaudit'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "a11y-audit")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b9-a11yaudit")


if __name__ == "__main__":
    unittest.main()
