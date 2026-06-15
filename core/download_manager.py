"""Background audio downloads for app-internal offline playback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yt_dlp
from PySide6.QtCore import QObject, QThread, Signal


class DownloadThread(QThread):
    progress = Signal(str, int, str)
    completed = Signal(str, str)
    failed = Signal(str, str)

    def __init__(self, track: dict[str, Any], download_dir: str | Path, parent=None) -> None:
        super().__init__(parent)
        self.track = track
        self.video_id = track["video_id"]
        self.download_dir = Path(download_dir)

    def run(self) -> None:
        self.download_dir.mkdir(parents=True, exist_ok=True)
        url = f"https://www.youtube.com/watch?v={self.video_id}"
        output_template = str(self.download_dir / f"{self.video_id}.%(ext)s")

        options = {
            "format": "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "retries": 3,
            "socket_timeout": 12,
            "progress_hooks": [self._progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.extract_info(url, download=True)

            if self.isInterruptionRequested():
                return

            downloaded_file = self._find_downloaded_file()
            if downloaded_file is None:
                self.failed.emit(self.video_id, "İndirilen dosya bulunamadı.")
                return

            self.completed.emit(self.video_id, str(downloaded_file.resolve()))
        except Exception as exc:  # yt-dlp can raise many extractor/network errors.
            self.failed.emit(self.video_id, str(exc))

    def _progress_hook(self, info: dict[str, Any]) -> None:
        if self.isInterruptionRequested():
            raise RuntimeError("İndirme iptal edildi.")

        status = info.get("status")
        if status == "downloading":
            total = info.get("total_bytes") or info.get("total_bytes_estimate") or 0
            downloaded = info.get("downloaded_bytes") or 0
            percent = int((downloaded / total) * 100) if total else 0
            self.progress.emit(self.video_id, max(0, min(99, percent)), "İndiriliyor")
        elif status == "finished":
            self.progress.emit(self.video_id, 100, "Tamamlanıyor")

    def _find_downloaded_file(self) -> Path | None:
        candidates = [
            path
            for path in self.download_dir.glob(f"{self.video_id}.*")
            if path.is_file() and path.suffix not in {".part", ".ytdl"}
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda path: path.stat().st_mtime)


class DownloadManager(QObject):
    download_started = Signal(dict)
    download_progress = Signal(str, int, str)
    download_completed = Signal(dict, str)
    download_failed = Signal(dict, str)

    def __init__(self, download_dir: str | Path, parent=None) -> None:
        super().__init__(parent)
        self.download_dir = Path(download_dir)
        self._threads: dict[str, DownloadThread] = {}
        self._tracks: dict[str, dict[str, Any]] = {}

    def is_downloading(self, video_id: str) -> bool:
        return video_id in self._threads

    def active_video_ids(self) -> set[str]:
        return set(self._threads)

    def start_download(self, track: dict[str, Any]) -> bool:
        video_id = track.get("video_id")
        if not video_id or video_id in self._threads:
            return False

        thread = DownloadThread(track, self.download_dir)
        self._threads[video_id] = thread
        self._tracks[video_id] = dict(track)

        thread.progress.connect(self.download_progress.emit)
        thread.completed.connect(self._on_completed)
        thread.failed.connect(self._on_failed)
        thread.finished.connect(thread.deleteLater)

        self.download_started.emit(dict(track))
        thread.start()
        return True

    def cancel_all(self) -> None:
        threads = list(self._threads.items())
        for _video_id, thread in threads:
            if thread.isRunning():
                thread.requestInterruption()
        for video_id, thread in threads:
            if thread.isRunning():
                thread.wait()
            if not thread.isRunning():
                self._threads.pop(video_id, None)
                self._tracks.pop(video_id, None)

    def _on_completed(self, video_id: str, file_path: str) -> None:
        thread = self._threads.pop(video_id, None)
        track = self._tracks.pop(video_id, {"video_id": video_id})
        if thread is not None:
            thread.requestInterruption()
        self.download_completed.emit(track, file_path)

    def _on_failed(self, video_id: str, message: str) -> None:
        thread = self._threads.pop(video_id, None)
        track = self._tracks.pop(video_id, {"video_id": video_id})
        if thread is not None:
            thread.requestInterruption()
        self.download_failed.emit(track, message)
