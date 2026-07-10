import unittest

from bot.music.queue_manager import LoopMode, QueueManager


class QueueManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = QueueManager()
        self.guild_id = 123

    def test_add_remove_clear_and_cleanup(self):
        first = {"title": "First", "uri": "https://example.com/1"}
        second = {"title": "Second", "uri": "https://example.com/2"}

        self.assertEqual(self.manager.add(self.guild_id, first, requester_id=10), 1)
        self.assertEqual(self.manager.add(self.guild_id, second, requester_id=20), 2)
        self.assertEqual(self.manager.get_length(self.guild_id), 2)
        self.assertEqual(self.manager.get_all(self.guild_id)[0]["requester_id"], 10)

        self.assertIsNone(self.manager.remove(self.guild_id, 0))
        self.assertIsNone(self.manager.remove(self.guild_id, 99))

        removed = self.manager.remove(self.guild_id, 1)
        self.assertEqual(removed["title"], "First")
        self.assertEqual(self.manager.get_length(self.guild_id), 1)

        self.manager.clear(self.guild_id)
        self.assertTrue(self.manager.is_empty(self.guild_id))

        self.manager.add(self.guild_id, {"title": "Temp", "uri": "u"}, requester_id=1)
        self.manager.set_loop(self.guild_id, "queue")
        self.manager.add_history(self.guild_id, {"title": "Temp"})
        self.manager.cleanup(self.guild_id)

        self.assertTrue(self.manager.is_empty(self.guild_id))
        self.assertEqual(self.manager.get_loop(self.guild_id), LoopMode.NONE)
        self.assertEqual(self.manager.get_history(self.guild_id), [])

    def test_loop_none_pops_tracks(self):
        self.manager.add(self.guild_id, {"title": "A", "uri": "u1"}, requester_id=1)
        self.manager.add(self.guild_id, {"title": "B", "uri": "u2"}, requester_id=2)

        self.assertEqual(self.manager.get_next(self.guild_id)["title"], "A")
        self.assertEqual(self.manager.get_next(self.guild_id)["title"], "B")
        self.assertIsNone(self.manager.get_next(self.guild_id))

    def test_loop_queue_rotates_tracks(self):
        self.manager.add(self.guild_id, {"title": "A", "uri": "u1"}, requester_id=1)
        self.manager.add(self.guild_id, {"title": "B", "uri": "u2"}, requester_id=2)
        self.manager.set_loop(self.guild_id, "queue")

        self.assertEqual(self.manager.get_next(self.guild_id)["title"], "A")
        self.assertEqual([t["title"] for t in self.manager.get_all(self.guild_id)], ["B", "A"])
        self.assertEqual(self.manager.get_next(self.guild_id)["title"], "B")
        self.assertEqual([t["title"] for t in self.manager.get_all(self.guild_id)], ["A", "B"])

    def test_loop_validation_and_history_limit(self):
        with self.assertRaises(ValueError):
            self.manager.set_loop(self.guild_id, "invalid")

        for i in range(60):
            self.manager.add_history(self.guild_id, {"title": f"Track {i}"})

        history = self.manager.get_history(self.guild_id, limit=100)
        self.assertEqual(len(history), 50)
        self.assertEqual(history[0]["title"], "Track 10")
        self.assertEqual(history[-1]["title"], "Track 59")


if __name__ == "__main__":
    unittest.main()
