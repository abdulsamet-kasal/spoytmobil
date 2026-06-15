"""Persistent local library state for Spoyt.

The app stores user-owned state inside the project-level ``data`` folder:
liked songs, playlists, downloads, and recently played tracks.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LibraryStore:
    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir = self.data_dir / "downloads"
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "spoyt.db"

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def close(self) -> None:
        self.conn.close()

    def _init_db(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tracks (
                    video_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    artist TEXT NOT NULL,
                    duration TEXT NOT NULL DEFAULT '',
                    thumbnail TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS liked_tracks (
                    video_id TEXT PRIMARY KEY,
                    liked_at TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES tracks(video_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    playlist_id INTEGER NOT NULL,
                    video_id TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    PRIMARY KEY (playlist_id, video_id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                        ON DELETE CASCADE,
                    FOREIGN KEY (video_id) REFERENCES tracks(video_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS downloads (
                    video_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    downloaded_at TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES tracks(video_id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS recent_tracks (
                    video_id TEXT PRIMARY KEY,
                    played_at TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES tracks(video_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_playlist_tracks_position
                    ON playlist_tracks(playlist_id, position);
                CREATE INDEX IF NOT EXISTS idx_recent_tracks_played_at
                    ON recent_tracks(played_at);
                """
            )

    def ensure_track(self, track: dict[str, Any]) -> None:
        video_id = track.get("video_id")
        if not video_id:
            raise ValueError("Track is missing video_id.")

        timestamp = _now()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO tracks (
                    video_id, title, artist, duration, thumbnail,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    title = excluded.title,
                    artist = excluded.artist,
                    duration = excluded.duration,
                    thumbnail = excluded.thumbnail,
                    updated_at = excluded.updated_at
                """,
                (
                    video_id,
                    track.get("title") or "Bilinmeyen Başlık",
                    track.get("artist") or "Bilinmeyen Sanatçı",
                    track.get("duration") or "",
                    track.get("thumbnail"),
                    timestamp,
                    timestamp,
                ),
            )

    def get_track(self, video_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM tracks WHERE video_id = ?",
            (video_id,),
        ).fetchone()
        return self._track_from_row(row) if row else None

    def toggle_liked(self, track: dict[str, Any]) -> bool:
        if self.is_liked(track["video_id"]):
            self.unlike_track(track["video_id"])
            return False
        self.like_track(track)
        return True

    def like_track(self, track: dict[str, Any]) -> None:
        self.ensure_track(track)
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO liked_tracks (video_id, liked_at)
                VALUES (?, ?)
                """,
                (track["video_id"], _now()),
            )

    def unlike_track(self, video_id: str) -> None:
        with self.conn:
            self.conn.execute(
                "DELETE FROM liked_tracks WHERE video_id = ?",
                (video_id,),
            )

    def is_liked(self, video_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM liked_tracks WHERE video_id = ?",
            (video_id,),
        ).fetchone()
        return row is not None

    def list_liked_tracks(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT t.*
            FROM liked_tracks l
            JOIN tracks t ON t.video_id = l.video_id
            ORDER BY l.liked_at DESC
            """
        ).fetchall()
        return [self.hydrate_track(self._track_from_row(row)) for row in rows]

    def create_playlist(self, name: str) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Çalma listesi adı boş olamaz.")

        try:
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO playlists (name, created_at) VALUES (?, ?)",
                    (clean_name, _now()),
                )
            return int(cursor.lastrowid)
        except sqlite3.IntegrityError as exc:
            raise ValueError("Bu adda bir çalma listesi zaten var.") from exc

    def list_playlists(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT
                p.id,
                p.name,
                p.created_at,
                COUNT(pt.video_id) AS track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]

    def get_playlist(self, playlist_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT
                p.id,
                p.name,
                p.created_at,
                COUNT(pt.video_id) AS track_count
            FROM playlists p
            LEFT JOIN playlist_tracks pt ON pt.playlist_id = p.id
            WHERE p.id = ?
            GROUP BY p.id
            """,
            (playlist_id,),
        ).fetchone()
        return dict(row) if row else None

    def delete_playlist(self, playlist_id: int) -> None:
        with self.conn:
            self.conn.execute(
                "DELETE FROM playlists WHERE id = ?",
                (playlist_id,),
            )

    def add_to_playlist(self, playlist_id: int, track: dict[str, Any]) -> bool:
        self.ensure_track(track)
        existing = self.conn.execute(
            """
            SELECT 1
            FROM playlist_tracks
            WHERE playlist_id = ? AND video_id = ?
            """,
            (playlist_id, track["video_id"]),
        ).fetchone()
        if existing:
            return False

        row = self.conn.execute(
            """
            SELECT COALESCE(MAX(position), 0) AS max_position
            FROM playlist_tracks
            WHERE playlist_id = ?
            """,
            (playlist_id,),
        ).fetchone()
        next_position = int(row["max_position"]) + 1

        with self.conn:
            self.conn.execute(
                """
                INSERT INTO playlist_tracks (
                    playlist_id, video_id, added_at, position
                )
                VALUES (?, ?, ?, ?)
                """,
                (playlist_id, track["video_id"], _now(), next_position),
            )
        return True

    def remove_from_playlist(self, playlist_id: int, video_id: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                DELETE FROM playlist_tracks
                WHERE playlist_id = ? AND video_id = ?
                """,
                (playlist_id, video_id),
            )

    def get_playlist_tracks(self, playlist_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT t.*
            FROM playlist_tracks pt
            JOIN tracks t ON t.video_id = pt.video_id
            WHERE pt.playlist_id = ?
            ORDER BY pt.position ASC, pt.added_at ASC
            """,
            (playlist_id,),
        ).fetchall()
        return [self.hydrate_track(self._track_from_row(row)) for row in rows]

    def mark_downloaded(self, track: dict[str, Any], file_path: str | Path) -> None:
        self.ensure_track(track)
        with self.conn:
            self.conn.execute(
                """
                INSERT OR REPLACE INTO downloads (
                    video_id, file_path, downloaded_at
                )
                VALUES (?, ?, ?)
                """,
                (track["video_id"], str(Path(file_path).resolve()), _now()),
            )

    def remove_download(self, video_id: str, delete_file: bool = True) -> None:
        row = self.conn.execute(
            "SELECT file_path FROM downloads WHERE video_id = ?",
            (video_id,),
        ).fetchone()
        with self.conn:
            self.conn.execute(
                "DELETE FROM downloads WHERE video_id = ?",
                (video_id,),
            )
        if delete_file and row:
            path = Path(row["file_path"])
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass

    def is_downloaded(self, video_id: str) -> bool:
        return self.get_download_path(video_id) is not None

    def get_download_path(self, video_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT file_path FROM downloads WHERE video_id = ?",
            (video_id,),
        ).fetchone()
        if not row:
            return None
        path = Path(row["file_path"])
        if path.exists():
            return str(path)
        return None

    def list_downloads(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT t.*
            FROM downloads d
            JOIN tracks t ON t.video_id = d.video_id
            ORDER BY d.downloaded_at DESC
            """
        ).fetchall()
        return [self.hydrate_track(self._track_from_row(row)) for row in rows]

    def record_played(self, track: dict[str, Any]) -> None:
        self.ensure_track(track)
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO recent_tracks (video_id, played_at)
                VALUES (?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    played_at = excluded.played_at
                """,
                (track["video_id"], _now()),
            )

    def list_recent_tracks(self, limit: int = 8) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT t.*
            FROM recent_tracks r
            JOIN tracks t ON t.video_id = r.video_id
            ORDER BY r.played_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self.hydrate_track(self._track_from_row(row)) for row in rows]

    def get_summary(self) -> dict[str, int]:
        liked = self.conn.execute("SELECT COUNT(*) FROM liked_tracks").fetchone()[0]
        downloads = self.conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        playlists = self.conn.execute("SELECT COUNT(*) FROM playlists").fetchone()[0]
        return {
            "liked": int(liked),
            "downloads": int(downloads),
            "playlists": int(playlists),
        }

    def hydrate_track(self, track: dict[str, Any]) -> dict[str, Any]:
        hydrated = dict(track)
        local_path = self.get_download_path(hydrated["video_id"])
        if local_path:
            hydrated["local_path"] = local_path
        return hydrated

    @staticmethod
    def _track_from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "video_id": row["video_id"],
            "title": row["title"],
            "artist": row["artist"],
            "duration": row["duration"],
            "thumbnail": row["thumbnail"],
        }
