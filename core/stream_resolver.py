"""Bir video ID'si için gerçek ses akış (stream) URL'sini arka planda çözer.

yt-dlp çağrısı bir QThread içinde çalışır, böylece arayüz akış URL'si
beklenirken donmaz.
"""

from __future__ import annotations

import yt_dlp
from PySide6.QtCore import QThread, Signal


class StreamResolverThread(QThread):
    # (video_id, stream_url)
    resolved = Signal(str, str)
    # hata mesajı
    error = Signal(str)

    def __init__(self, video_id: str, parent=None) -> None:
        super().__init__(parent)
        self.video_id = video_id

    def run(self) -> None:
        url = f"https://www.youtube.com/watch?v={self.video_id}"

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "socket_timeout": 12,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if self.isInterruptionRequested():
                    return

                stream_url = info.get("url")

                if not stream_url:
                    # Bazı formatlarda direkt url üst seviyede olmayabilir,
                    # formats listesinden en iyi sesli formatı seçelim.
                    formats = info.get("formats") or []
                    audio_formats = [f for f in formats if f.get("acodec") != "none"]
                    if audio_formats:
                        stream_url = audio_formats[-1].get("url")

                if not stream_url:
                    self.error.emit("Ses akışı bulunamadı.")
                    return

                if not self.isInterruptionRequested():
                    self.resolved.emit(self.video_id, stream_url)
        except Exception as exc:  # yt-dlp pek çok farklı hata fırlatabilir
            self.error.emit(str(exc))
