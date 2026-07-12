import sqlite3
import tempfile
import unittest
from pathlib import Path

from bot.database.database import close_connection, get_connection, initialize_database


class DatabaseTests(unittest.TestCase):
    def tearDown(self):
        close_connection()

    def test_initialize_creates_core_and_access_tables(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "musicbot.db"
            conn = initialize_database(str(db_path))

            table_names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }

            expected_tables = {
                "guild_settings",
                "user_favorites",
                "playlists",
                "playlist_tracks",
                "playback_history",
                "approved_users",
                "access_requests",
                "blacklisted_users",
                "audit_logs",
                "bot_settings",
            }
            self.assertTrue(expected_tables.issubset(table_names))
            close_connection(str(db_path))

    def test_connection_cache_is_keyed_by_resolved_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            first_path = Path(tmpdir) / "first.db"
            second_path = Path(tmpdir) / "second.db"

            first = initialize_database(str(first_path))
            first_again = get_connection(str(first_path))
            second = initialize_database(str(second_path))

            self.assertIs(first, first_again)
            self.assertIsNot(first, second)

            first.execute(
                "INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)",
                ("probe", "first"),
            )
            first.commit()

            row = second.execute(
                "SELECT value FROM bot_settings WHERE key = ?",
                ("probe",),
            ).fetchone()
            self.assertIsNone(row)
            close_connection(str(first_path))
            close_connection(str(second_path))

    def test_close_connection_can_close_single_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "musicbot.db"
            conn = initialize_database(str(db_path))
            close_connection(str(db_path))

            with self.assertRaises(sqlite3.ProgrammingError):
                conn.execute("SELECT 1")

            reopened = get_connection(str(db_path))
            self.assertIsNot(conn, reopened)
            self.assertEqual(reopened.execute("SELECT 1").fetchone()[0], 1)
            close_connection(str(db_path))


if __name__ == "__main__":
    unittest.main()
