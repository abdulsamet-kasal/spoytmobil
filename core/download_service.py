"""Threaded yt-dlp downloader without Qt dependencies."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from core.stream_service import DEFAULT_AUDIO_FORMAT


ProgressCallback = Callable[[str, int, str], None]
CompletedCallback = Callable[[str, str], None]
FailedCallback = Callable[[str, str], None]


class DownloadService:
    def __init__(self, download_dir: str | Path) -> None:
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self._threads: dict[str, threading.Thread] = {}
        self._cancelled: set[str] = set()
        self._lock = threading.Lock()

    def is_downloading(self, video_id: str) -> bool:
        with self._lock:
            return video_id in self._threads

    def active_video_ids(self) -> set[str]:
        with self._lock:
            return set(self._threads)

    def start_download(
        self,
        track: dict[str, Any],
        on_progress: ProgressCallback,
        on_completed: CompletedCallback,
        on_failed: FailedCallback,
    ) -> bool:
        video_id = track.get("video_id")
        if not video_id:
            return False

        with self._lock:
            if video_id in self._threads:
                return False
            self._cancelled.discard(video_id)

        thread = threading.Thread(
            target=self._download_worker,
            args=(dict(track), on_progress, on_completed, on_failed),
            daemon=True,
        )
        with self._lock:
            self._threads[video_id] = thread
        thread.start()
        return True

    def cancel_all(self) -> None:
        with self._lock:
            self._cancelled.update(self._threads)

    def _download_worker(
        self,
        track: dict[str, Any],
        on_progress: ProgressCallback,
        on_completed: CompletedCallback,
        on_failed: FailedCallback,
    ) -> None:
        video_id = track["video_id"]
        url = f"https://www.youtube.com/watch?v={video_id}"
        output_template = str(self.download_dir / f"{video_id}.%(ext)s")

        def progress_hook(info: dict[str, Any]) -> None:
            if self._is_cancelled(video_id):
                raise RuntimeError("Download cancelled.")
            status = info.get("status")
            if status == "downloading":
                total = info.get("total_bytes") or info.get("total_bytes_estimate") or 0
                downloaded = info.get("downloaded_bytes") or 0
                percent = int((downloaded / total) * 100) if total else 0
                on_progress(video_id, max(0, min(99, percent)), "Downloading")
            elif status == "finished":
                on_progress(video_id, 100, "Finalizing")

        options = {
            "format": DEFAULT_AUDIO_FORMAT,
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "retries": 3,
            "socket_timeout": 12,
            "progress_hooks": [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.extract_info(url, download=True)
            if self._is_cancelled(video_id):
                return
            downloaded_file = self._find_downloaded_file(video_id)
            if downloaded_file is None:
                on_failed(video_id, "Downloaded file was not found.")
                return
            on_completed(video_id, str(downloaded_file.resolve()))
        except Exception as exc:
            if not self._is_cancelled(video_id):
                on_failed(video_id, str(exc))
        finally:
            with self._lock:
                self._threads.pop(video_id, None)
                self._cancelled.discard(video_id)

    def _is_cancelled(self, video_id: str) -> bool:
        with self._lock:
            return video_id in self._cancelled

    def _find_downloaded_file(self, video_id: str) -> Path | None:
        candidates = [
            path
            for path in self.download_dir.glob(f"{video_id}.*")
            if path.is_file() and path.suffix not in {".part", ".ytdl"}
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)
