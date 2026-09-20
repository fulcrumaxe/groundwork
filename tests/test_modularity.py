"""Modularity rule: capabilities live in focused modules, web.py never grows."""
import unittest

from groundwork import modularity as modularitymod


class ModularityGuardrailTest(unittest.TestCase):
    def test_no_ceiling_violations(self):
        self.assertEqual(modularitymod.check(), [])

    def test_web_ceiling_only_moves_down(self):
        counts = modularitymod.sizes()
        self.assertLessEqual(counts["web.py"], modularitymod.WEB_CEILING)

    def test_registered_areas_exist_within_cap(self):
        counts = modularitymod.sizes()
        for area, rel in modularitymod.AREAS.items():
            with self.subTest(area=area):
                self.assertIn(rel, counts)
                self.assertLessEqual(counts[rel], modularitymod.AREA_CAP)

    def test_status_table_lists_every_area(self):
        body = modularitymod.status_rows()
        for rel in ["web.py", *modularitymod.AREAS.values()]:
            self.assertIn(rel, body)


if __name__ == "__main__":
    unittest.main()
