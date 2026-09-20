"""Name-that-smell tests (F-2, type 15). Stdlib unittest."""
import unittest
from types import SimpleNamespace

from groundwork import smell as smellmod


def concept(name="calc", file="calc.py", line=1):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file=file, line=line)


SAMPLES = {
    "long-function": "def big():\n" + "".join(
        f'    handle("step{i:02d}")\n' for i in range(25)),
    "long-parameter-list": ("def plan(a, b, c, d, e):\n"
                            "    return (a, b, c, d, e)\n"),
    "deep-nesting": ("def run(items):\n"
                     "    for it in items:\n"
                     "        if it:\n"
                     "            while it.wait():\n"
                     "                with lock:\n"
                     "                    handle(it)\n"),
    "duplicated-code": ("def settle(price, rate, fee):\n"
                        "    total = price * rate + fee  # settle up\n"
                        "    total = price * rate + fee  # settle up\n"
                        "    total = price * rate + fee  # settle up\n"
                        "    return total\n"),
    "magic-numbers": ("def fee(p):\n"
                      "    return p * 0.07 + 32 - 1.5\n"),
    "broad-except": ("try:\n"
                     "    run()\n"
                     "except Exception:\n"
                     "    pass\n"),
}
CLEAN = "def add(a, b):\n    return a + b\n"


class DetectTest(unittest.TestCase):
    def test_each_detector_fires_on_its_sample(self):
        for sid, code in SAMPLES.items():
            with self.subTest(smell=sid):
                scores = smellmod.detect_all(code)
                self.assertGreater(scores[sid], 0)
                entry, strength = smellmod.choose(code)
                self.assertEqual(entry["id"], sid)
                self.assertGreater(strength, 0)

    def test_clean_code_scores_zero_everywhere(self):
        self.assertTrue(all(v == 0 for v in
                            smellmod.detect_all(CLEAN).values()))

    def test_broken_code_never_raises(self):
        self.assertEqual(sum(smellmod.detect_all("def (:").values()), 0)


class GenerateTest(unittest.TestCase):
    def test_shape_and_choices(self):
        e = smellmod.generate("ex15", concept(),
                              SAMPLES["magic-numbers"].splitlines(), {})
        self.assertEqual(e["type"], 15)
        self.assertEqual(e["type_name"], "name-that-smell")
        self.assertEqual(e["bloom"], "analyse")
        self.assertTrue(e["front"])
        self.assertEqual(len(e["payload"]["choices"]), 3)
        self.assertIn("Magic Numbers", e["payload"]["choices"])
        self.assertEqual(e["payload"]["answer"], "Magic Numbers")
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(len(e["hints"]), 3)

    def test_clean_snippet_falls_back_ungrounded(self):
        e = smellmod.generate("ex15", concept(), CLEAN.splitlines(), {})
        self.assertTrue(e["front"])
        self.assertFalse(e["payload"]["grounded"])
        self.assertIn(e["payload"]["answer"], e["payload"]["choices"])

    def test_ctx_smell_forces_answer(self):
        e = smellmod.generate("ex15", concept(), CLEAN.splitlines(),
                              {"smell": "deep-nesting"})
        self.assertEqual(e["payload"]["smell"], "deep-nesting")
        self.assertEqual(e["payload"]["answer"], "Deep Nesting")
        self.assertTrue(e["payload"]["grounded"])

    def test_ctx_smell_accepts_title_and_bad_value_ignored(self):
        e = smellmod.generate("ex15", concept(), CLEAN.splitlines(),
                              {"smell": "Duplicated Code"})
        self.assertEqual(e["payload"]["smell"], "duplicated-code")
        e = smellmod.generate("ex15", concept(), CLEAN.splitlines(),
                              {"smell": "not-a-smell"})
        self.assertFalse(e["payload"]["grounded"])


class GradeTest(unittest.TestCase):
    def payload(self):
        return {"choices": ["Long Function", "Magic Numbers",
                            "Deep Nesting"],
                "answer": "Magic Numbers"}

    def test_accepts_exact_answer(self):
        e = {"id": "x", "type": 15, "payload": self.payload()}
        self.assertTrue(smellmod.grade(e, "Magic Numbers")["pass"])

    def test_whitespace_forgiven_case_matters(self):
        # Same contract as central types 7/16/18: exact answer text.
        e = {"id": "x", "type": 15, "payload": self.payload()}
        self.assertTrue(smellmod.grade(e, "  Magic Numbers  ")["pass"])
        self.assertFalse(smellmod.grade(e, "magic numbers")["pass"])

    def test_rejects_wrong_and_blank(self):
        e = {"id": "x", "type": 15, "payload": self.payload()}
        self.assertFalse(smellmod.grade(e, "Deep Nesting")["pass"])
        self.assertFalse(smellmod.grade(e, "")["pass"])
        self.assertFalse(smellmod.grade(e, "   ")["pass"])

    def test_needs_no_runner(self):
        e = {"id": "x", "type": 15, "payload": self.payload()}
        self.assertTrue(smellmod.grade(e, "Magic Numbers",
                                       runner=None)["pass"])


class RenderTest(unittest.TestCase):
    def test_choices_form_and_hints(self):
        e = smellmod.generate("ex15", concept(),
                              SAMPLES["broad-except"].splitlines(), {})
        body = smellmod.render(e)
        self.assertIn("<form", body)
        self.assertEqual(body.count('type="radio"'), 3)
        self.assertIn("Overly Broad Except", body)
        self.assertIn("Hint 1", body)


class StatusTest(unittest.TestCase):
    def test_section_anchor(self):
        body = smellmod.section_html("")
        self.assertIn("id='status-b6-smell'", body)
        self.assertIn("groundwork/smell.py", body)


if __name__ == "__main__":
    unittest.main()
