from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.library_store import LibraryStore


TRACK = {
    "video_id": "abc123",
    "title": "Test Song",
    "artist": "Test Artist",
    "duration": "3:21",
    "thumbnail": "https://example.com/cover.jpg",
}


class LibraryStoreTest(unittest.TestCase):
    def test_liked_tracks_persist_after_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = LibraryStore(tmp)
            store.like_track(TRACK)
            self.assertTrue(store.is_liked("abc123"))
            store.close()

            reopened = LibraryStore(tmp)
            try:
                self.assertTrue(reopened.is_liked("abc123"))
                self.assertEqual(reopened.list_liked_tracks()[0]["title"], "Test Song")
            finally:
                reopened.close()

    def test_playlist_add_remove_and_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = LibraryStore(tmp)
            try:
                playlist_id = store.create_playlist("Road Mix")
                self.assertTrue(store.add_to_playlist(playlist_id, TRACK))
                self.assertFalse(store.add_to_playlist(playlist_id, TRACK))
                self.assertEqual(store.list_playlists()[0]["track_count"], 1)
                self.assertEqual(store.get_playlist_tracks(playlist_id)[0]["video_id"], "abc123")

                store.remove_from_playlist(playlist_id, "abc123")
                self.assertEqual(store.get_playlist_tracks(playlist_id), [])

                self.assertTrue(store.add_to_playlist(playlist_id, TRACK))
                store.delete_playlist(playlist_id)
                self.assertIsNone(store.get_playlist(playlist_id))
                self.assertEqual(store.get_playlist_tracks(playlist_id), [])
            finally:
                store.close()

    def test_download_record_hydrates_and_removes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = LibraryStore(tmp)
            try:
                downloaded_file = Path(tmp) / "downloads" / "abc123.webm"
                downloaded_file.write_text("audio", encoding="utf-8")

                store.mark_downloaded(TRACK, downloaded_file)
                hydrated = store.hydrate_track(TRACK)
                self.assertEqual(hydrated["local_path"], str(downloaded_file.resolve()))
                self.assertEqual(store.list_downloads()[0]["video_id"], "abc123")

                store.remove_download("abc123", delete_file=True)
                self.assertIsNone(store.get_download_path("abc123"))
                self.assertFalse(downloaded_file.exists())
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
