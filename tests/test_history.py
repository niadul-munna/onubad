import tempfile
import unittest
from pathlib import Path

from onubad.history import History


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "history.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_then_recent_returns_entry(self):
        h = History(self.path)
        h.add("en", "bn", "hello", "হ্যালো")
        recent = h.recent()
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["input"], "hello")
        self.assertEqual(recent[0]["output"], "হ্যালো")
        self.assertEqual(recent[0]["src"], "en")
        self.assertEqual(recent[0]["dst"], "bn")

    def test_recent_is_newest_first(self):
        h = History(self.path)
        h.add("en", "bn", "first", "১")
        h.add("en", "bn", "second", "২")
        recent = h.recent()
        self.assertEqual(recent[0]["input"], "second")
        self.assertEqual(recent[1]["input"], "first")

    def test_capped_at_limit(self):
        h = History(self.path, cap=5)
        for i in range(8):
            h.add("en", "bn", f"in{i}", f"out{i}")
        recent = h.recent(100)
        self.assertEqual(len(recent), 5)
        self.assertEqual(recent[0]["input"], "in7")

    def test_clear_empties(self):
        h = History(self.path)
        h.add("en", "bn", "hello", "হ্যালো")
        h.clear()
        self.assertEqual(h.recent(), [])

    def test_persists_across_instances(self):
        History(self.path).add("en", "bn", "hello", "হ্যালো")
        self.assertEqual(History(self.path).recent()[0]["input"], "hello")

    def test_corrupt_file_recovers_to_empty(self):
        self.path.write_text("{not valid json")
        h = History(self.path)
        self.assertEqual(h.recent(), [])
        h.add("en", "bn", "ok", "ঠিক")
        self.assertEqual(h.recent()[0]["input"], "ok")


if __name__ == "__main__":
    unittest.main()
