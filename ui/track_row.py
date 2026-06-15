"""Reusable song row with playback and library actions."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtWidgets import QPushButton

from core.thumbnail_loader import ThumbnailLoader
from ui.icon_button import IconButton


class TrackRow(QWidget):
    """Shows one track and exposes Spotify-like row actions."""

    play_requested = Signal(dict)
    action_requested = Signal(str, dict)

    def __init__(
        self,
        track: dict,
        index: int | None = None,
        parent=None,
        extra_actions: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__(parent)
        self.track = track
        self.extra_actions = extra_actions or []
        self._liked = False
        self._downloaded = False
        self._downloading = False
        self.setObjectName("TrackRow")
        self.setCursor(Qt.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        if index is not None:
            index_label = QLabel(str(index))
            index_label.setObjectName("TrackIndex")
            index_label.setFixedWidth(30)
            index_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(index_label)

        self.thumb_label = QLabel()
        self.thumb_label.setObjectName("Thumbnail")
        self.thumb_label.setFixedSize(58, 58)
        self.thumb_label.setScaledContents(True)
        layout.addWidget(self.thumb_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel(track.get("title", "Bilinmiyor"))
        self.title_label.setObjectName("TrackTitle")

        self.artist_label = QLabel(track.get("artist", "Bilinmeyen Sanatçı"))
        self.artist_label.setObjectName("TrackArtist")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        layout.addLayout(text_layout, 1)

        self.state_label = QLabel("")
        self.state_label.setObjectName("TrackState")
        self.state_label.setMinimumWidth(96)
        self.state_label.setMaximumWidth(160)
        self.state_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.state_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.state_label)

        self.duration_label = QLabel(track.get("duration", ""))
        self.duration_label.setObjectName("TrackDuration")
        self.duration_label.setFixedWidth(48)
        self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self.duration_label)

        self.play_btn = IconButton("play")
        self.play_btn.setObjectName("PlayRowButton")
        self.play_btn.setFixedSize(42, 42)
        self.play_btn.setToolTip("Çal")
        layout.addWidget(self.play_btn)

        self.more_btn = QPushButton("⋯")
        self.more_btn.setObjectName("MoreRowButton")
        self.more_btn.setFixedSize(42, 42)
        self.more_btn.setToolTip("Seçenekler")
        layout.addWidget(self.more_btn)

        self.play_btn.clicked.connect(self._emit_play)
        self.more_btn.clicked.connect(self._show_menu)

        thumb_url = track.get("thumbnail")
        if thumb_url:
            ThumbnailLoader.instance().load(thumb_url, self._set_thumbnail)

    def set_state(
        self,
        *,
        liked: bool | None = None,
        downloaded: bool | None = None,
        downloading: bool | None = None,
    ) -> None:
        if liked is not None:
            self._liked = liked
        if downloaded is not None:
            self._downloaded = downloaded
        if downloading is not None:
            self._downloading = downloading

        markers: list[str] = []
        if self._liked:
            markers.append("♥ Beğenildi")
        if self._downloaded:
            markers.append("↓ Offline")
        elif self._downloading:
            markers.append("… İniyor")
        self.state_label.setText("  ".join(markers))

    def _emit_play(self) -> None:
        self.play_requested.emit(self.track)

    def _show_menu(self) -> None:
        menu = QMenu(self)
        self._add_action(menu, "Çal", "play")
        menu.addSeparator()

        like_label = "Beğenilerden çıkar" if self._liked else "Beğenilenlere ekle"
        self._add_action(menu, like_label, "toggle_like")
        self._add_action(menu, "Çalma listesine ekle...", "add_to_playlist")

        if self._downloading:
            action = QAction("İndiriliyor...", menu)
            action.setEnabled(False)
            menu.addAction(action)
        elif self._downloaded:
            self._add_action(menu, "İndirmeyi kaldır", "remove_download")
        else:
            self._add_action(menu, "İndir", "download")

        if self.extra_actions:
            menu.addSeparator()
            for action_id, label in self.extra_actions:
                self._add_action(menu, label, action_id)

        menu.exec(self.more_btn.mapToGlobal(self.more_btn.rect().bottomLeft()))

    def _add_action(self, menu: QMenu, label: str, action_id: str) -> None:
        action = QAction(label, menu)
        action.triggered.connect(
            lambda _checked=False, a=action_id: self.action_requested.emit(a, self.track)
        )
        menu.addAction(action)

    def _set_thumbnail(self, pixmap: QPixmap) -> None:
        try:
            self.thumb_label.setPixmap(pixmap)
        except RuntimeError:
            pass

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self._emit_play()
        super().mouseDoubleClickEvent(event)
