"""Spotify-like left navigation backed by local library state."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    page_changed = Signal(str)
    playlist_selected = Signal(int)
    create_playlist_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(260)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(6)

        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(10, 0, 10, 0)
        logo_row.setSpacing(10)

        logo_mark = QLabel()
        logo_mark.setObjectName("LogoMark")
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "spoyt_logo.svg"
        logo_mark.setPixmap(QIcon(str(logo_path)).pixmap(38, 38))
        logo_mark.setFixedSize(40, 40)
        logo_mark.setAlignment(Qt.AlignCenter)
        logo_row.addWidget(logo_mark)

        logo = QLabel("Spoyt")
        logo.setObjectName("Logo")
        logo_row.addWidget(logo)
        logo_row.addStretch()

        layout.addLayout(logo_row)
        layout.addSpacing(24)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        self.home_btn = self._create_nav_button("Ana Sayfa", "home")
        self.search_btn = self._create_nav_button("Ara", "search")
        self.library_btn = self._create_nav_button("Kitaplığın", "library")
        self.liked_btn = self._create_nav_button("Beğenilen Şarkılar", "liked")
        self.downloads_btn = self._create_nav_button("İndirilenler", "downloads")

        for btn in (
            self.home_btn,
            self.search_btn,
            self.library_btn,
            self.liked_btn,
            self.downloads_btn,
        ):
            layout.addWidget(btn)
            self.button_group.addButton(btn)

        self.home_btn.setChecked(True)

        layout.addSpacing(20)

        self.create_playlist_btn = QPushButton("+   Yeni Çalma Listesi")
        self.create_playlist_btn.setObjectName("SecondaryButton")
        layout.addWidget(self.create_playlist_btn)

        playlist_label = QLabel("ÇALMA LİSTELERİ")
        playlist_label.setObjectName("SectionLabel")
        layout.addWidget(playlist_label)

        self.playlist_list = QListWidget()
        self.playlist_list.setObjectName("PlaylistList")
        layout.addWidget(self.playlist_list)

        for btn, page_id in (
            (self.home_btn, "home"),
            (self.search_btn, "search"),
            (self.library_btn, "library"),
            (self.liked_btn, "liked"),
            (self.downloads_btn, "downloads"),
        ):
            btn.clicked.connect(lambda _checked, p=page_id: self.page_changed.emit(p))

        self.playlist_list.itemClicked.connect(self._on_playlist_clicked)
        self.create_playlist_btn.clicked.connect(
            lambda _checked=False: self.create_playlist_requested.emit()
        )

    def set_playlists(self, playlists: list[dict]) -> None:
        current_id = self.current_playlist_id()
        self.playlist_list.clear()
        for playlist in playlists:
            name = playlist["name"]
            count = playlist.get("track_count", 0)
            item = QListWidgetItem(f"{name}  ({count})")
            item.setData(Qt.UserRole, int(playlist["id"]))
            self.playlist_list.addItem(item)
            if current_id == int(playlist["id"]):
                self.playlist_list.setCurrentItem(item)

    def select_page(self, page_id: str) -> None:
        pages = {
            "home": self.home_btn,
            "search": self.search_btn,
            "library": self.library_btn,
            "liked": self.liked_btn,
            "downloads": self.downloads_btn,
        }
        self._clear_button_checks()
        if page_id in pages:
            pages[page_id].setChecked(True)
        self.playlist_list.clearSelection()

    def select_playlist(self, playlist_id: int) -> None:
        self._clear_button_checks()
        for row in range(self.playlist_list.count()):
            item = self.playlist_list.item(row)
            if int(item.data(Qt.UserRole)) == playlist_id:
                self.playlist_list.setCurrentItem(item)
                return
        self.playlist_list.clearSelection()

    def current_playlist_id(self) -> int | None:
        item = self.playlist_list.currentItem()
        if item is None:
            return None
        return int(item.data(Qt.UserRole))

    def _create_nav_button(self, text: str, page_id: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("NavButton")
        btn.setCheckable(True)
        btn.setProperty("page", page_id)
        return btn

    def _on_playlist_clicked(self, item: QListWidgetItem) -> None:
        self._clear_button_checks()
        self.playlist_selected.emit(int(item.data(Qt.UserRole)))

    def _clear_button_checks(self) -> None:
        self.button_group.setExclusive(False)
        for button in self.button_group.buttons():
            button.setChecked(False)
        self.button_group.setExclusive(True)
