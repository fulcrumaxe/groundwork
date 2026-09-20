"""Type-17 rename-symbol exercise (F-3)."""
import unittest

from groundwork import renameex as rx
from groundwork import select as selectmod


def _concept():
    return selectmod.ScoredConcept("f", "add", "function", "calc.py",
                                   1, 1.0, 1.0, 1.0, 1.0)


SNIPPET = ["def add(a=2, b=3):", "    x = a + b", "    return x"]


def _ex(**kw):
    c = _concept()
    e = rx.generate("ex17", c, SNIPPET, kw.get("ctx", {}))
    e["payload"].update(kw.get("payload", {}))
    return e


class RenameGenerateTest(unittest.TestCase):
    def test_registry_constants(self):
        self.assertEqual((rx.TYPE_NUM, rx.TYPE_NAME, rx.BLOOM),
                         (17, "rename-symbol", "analyse"))

    def test_generate_picks_weak_local(self):
        e = rx.generate("ex17", _concept(), SNIPPET, {})
        self.assertEqual(e["type"], 17)
        self.assertTrue(e["front"])
        self.assertEqual(e["payload"]["target"], "x")
        self.assertEqual(e["payload"]["kind"], "variable")
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(len(e["hints"]), 3)

    def test_generate_override(self):
        e = rx.generate("ex17", _concept(), SNIPPET,
                        {"rename_target": "tmp"})
        self.assertEqual(e["payload"]["target"], "tmp")
        self.assertTrue(e["payload"]["grounded"])

    def test_generate_clean_fallback_ungrounded(self):
        e = rx.generate("ex17", _concept(),
                        ["def add(total):", "    return total"], {})
        self.assertTrue(e["front"])
        self.assertFalse(e["payload"]["grounded"])


class RenameGradeTest(unittest.TestCase):
    def test_accept_good_name_and_reason(self):
        e = _ex()
        got = rx.grade(e, "total add variable calc.py")
        self.assertTrue(got["pass"], got["feedback"])
        self.assertEqual(got["score"], 1.0)

    def test_reject_same_name(self):
        self.assertFalse(rx.grade(_ex(), "x x variable")["pass"])

    def test_reject_conventions(self):
        e = _ex()
        for bad in ("Total", "AB", "x2", "for", "list"):
            with self.subTest(bad=bad):
                got = rx.grade(e, f"{bad} add variable calc.py")
                self.assertFalse(got["pass"], bad)

    def test_reject_thin_justification(self):
        got = rx.grade(_ex(), "grand_total unrelated words here")
        self.assertFalse(got["pass"])
        self.assertIn("0/3", got["feedback"])

    def test_reject_empty(self):
        got = rx.grade(_ex(), "   ")
        self.assertFalse(got["pass"])
        self.assertEqual(got["score"], 0.0)


class RenameRenderStatusTest(unittest.TestCase):
    def test_render_escapes_and_single_answer(self):
        e = _ex()
        body = rx.render(e)
        self.assertIn("<article>", body)
        self.assertIn("name='answer'", body)
        self.assertNotIn("<script>", body)

    def test_section_anchor(self):
        self.assertIn("id='status-b6-renameex'", rx.section_html())

    def test_standalone_no_groundwork_import(self):
        with open("groundwork/renameex.py", encoding="utf-8") as fh:
            src = fh.read()
        top = [l for l in src.splitlines()
               if (l.startswith("import ") or l.startswith("from "))
               and "groundwork" in l]
        self.assertEqual(top, [])


if __name__ == "__main__":
    unittest.main()
