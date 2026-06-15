"""Pure Python stream URL resolution shared by mobile UI code."""

from __future__ import annotations

import yt_dlp


DEFAULT_AUDIO_FORMAT = "bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio/best"


def resolve_stream_url(video_id: str) -> str:
    """Resolve a YouTube video id to a playable audio URL."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    options = {
        "format": DEFAULT_AUDIO_FORMAT,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
        "socket_timeout": 12,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

    stream_url = info.get("url")
    if stream_url:
        return stream_url

    formats = info.get("formats") or []
    audio_formats = [item for item in formats if item.get("acodec") != "none"]
    if audio_formats:
        candidate = audio_formats[-1].get("url")
        if candidate:
            return candidate

    raise RuntimeError("Audio stream could not be resolved.")
