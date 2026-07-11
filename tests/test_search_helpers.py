import unittest

import wavelink

from bot.music.search import fallback_sources, is_url, normalize_source


class SearchHelperTests(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(is_url("https://youtube.com/watch?v=abc"))
        self.assertTrue(is_url(" HTTP://example.com/track"))
        self.assertFalse(is_url("never gonna give you up"))

    def test_source_normalization(self):
        self.assertEqual(normalize_source("ytsearch"), wavelink.TrackSource.YouTube)
        self.assertEqual(normalize_source("ytmsearch:"), wavelink.TrackSource.YouTubeMusic)
        self.assertEqual(normalize_source("scsearch"), wavelink.TrackSource.SoundCloud)
        self.assertEqual(normalize_source("spsearch"), "spsearch")

    def test_fallback_sources_are_unique_and_preferred_first(self):
        sources = fallback_sources("ytsearch")
        self.assertEqual(sources[0], wavelink.TrackSource.YouTube)
        self.assertEqual(len(sources), len({getattr(s, "value", str(s)) for s in sources}))
        self.assertIn(wavelink.TrackSource.YouTubeMusic, sources)
        self.assertIn(wavelink.TrackSource.SoundCloud, sources)


if __name__ == "__main__":
    unittest.main()
