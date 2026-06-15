"""ytmusicapi etrafında ince bir sarmalayıcı.

Bu modül, oturum açma gerektirmeyen (anonim) arama işlevini kullanarak
şarkı arar ve sonuçları uygulamanın anlayacağı sade bir sözlük formatına
dönüştürür.
"""

from __future__ import annotations

from ytmusicapi import YTMusic


class MusicAPI:
    def __init__(self) -> None:
        # Oturum açmadan (anonim) çalışır; arama için yeterlidir.
        self.yt = YTMusic()

    def search(self, query: str, filter_type: str = "songs", limit: int = 20) -> list[dict]:
        """Verilen sorguyu YouTube Music'te arar.

        Args:
            query: Aranacak metin (şarkı adı, sanatçı, albüm vb.)
            filter_type: "songs", "videos", "albums", "artists" gibi.
            limit: Döndürülecek maksimum sonuç sayısı.

        Returns:
            Her biri title, artist, video_id, duration, thumbnail
            anahtarlarına sahip sözlüklerden oluşan bir liste.
        """
        try:
            raw_results = self.yt.search(query, filter=filter_type, limit=limit)
        except Exception:
            return []

        tracks: list[dict] = []
        for item in raw_results:
            video_id = item.get("videoId")
            if not video_id:
                continue

            artists = item.get("artists") or []
            artist_names = ", ".join(
                a.get("name", "") for a in artists if a.get("name")
            )

            thumbnails = item.get("thumbnails") or []
            thumb_url = thumbnails[-1]["url"] if thumbnails else None

            tracks.append({
                "video_id": video_id,
                "title": item.get("title") or "Bilinmeyen Başlık",
                "artist": artist_names or "Bilinmeyen Sanatçı",
                "duration": item.get("duration") or "",
                "thumbnail": thumb_url,
            })

        return tracks
