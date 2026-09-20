"""Storage meter: file size plus per-module rows (I-238)."""
import unittest

from groundwork import storage as storagemod

from test_web import handler_for, make_module


class StorageMeterTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("storage mod")
        self.h = handler_for(self.db)

    def test_usage_reports_size_and_rows(self):
        info = storagemod.usage(self.db)
        self.assertGreater(info["bytes"], 0)
        self.assertIn("B", info["human"])
        self.assertEqual(len(info["modules"]), 1)
        m = info["modules"][0]
        self.assertGreater(m["concepts"], 0)
        self.assertGreater(m["cards"], 0)

    def test_human_sizes(self):
        self.assertEqual(storagemod._human(500), "500 B")
        self.assertEqual(storagemod._human(2048), "2.0 KB")
        self.assertEqual(storagemod._human(3 * 1024 * 1024), "3.0 MB")

    def test_status_shows_storage(self):
        body = self.h.status_html()
        self.assertIn("id='status-storage'", body)
        self.assertIn("Database file:", body)


if __name__ == "__main__":
    unittest.main()
