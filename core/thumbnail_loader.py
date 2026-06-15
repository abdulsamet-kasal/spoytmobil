"""Albüm kapağı (thumbnail) görsellerini ağ üzerinden asenkron indirir.

Qt'nin kendi QNetworkAccessManager'ını kullanır, böylece ek bir bağımlılığa
(requests vb.) gerek kalmaz ve indirme işlemi arayüzü bloklamaz.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest


class ThumbnailLoader(QObject):
    _instance: "ThumbnailLoader | None" = None

    def __init__(self) -> None:
        super().__init__()
        self.manager = QNetworkAccessManager()
        self._cache: dict[str, QPixmap] = {}
        self._pending: dict[str, list[Callable[[QPixmap], None]]] = {}

    @classmethod
    def instance(cls) -> "ThumbnailLoader":
        if cls._instance is None:
            cls._instance = ThumbnailLoader()
        return cls._instance

    def load(self, url: str, callback: Callable[[QPixmap], None]) -> None:
        if not url:
            return

        if url in self._cache:
            self._safe_callback(callback, self._cache[url])
            return

        if url in self._pending:
            self._pending[url].append(callback)
            return

        self._pending[url] = [callback]
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.Attribute.Http2AllowedAttribute, False)
        request.setRawHeader(
            b"User-Agent",
            b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Spoyt/1.0",
        )
        reply = self.manager.get(request)
        reply.finished.connect(lambda: self._on_finished(url, reply))

    def _on_finished(self, url: str, reply) -> None:
        callbacks = self._pending.pop(url, [])
        try:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                self._cache[url] = pixmap
                for callback in callbacks:
                    self._safe_callback(callback, pixmap)
        finally:
            reply.deleteLater()

    @staticmethod
    def _safe_callback(callback: Callable[[QPixmap], None], pixmap: QPixmap) -> None:
        try:
            callback(pixmap)
        except RuntimeError:
            # The row/player widget may have been deleted before the async
            # network reply arrived.
            pass
