"""Library screens for playlists, liked songs, and downloads."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.library_store import LibraryStore
from ui.track_row import TrackRow


class LibraryView(QWidget):
    ACTION_BUTTON_HEIGHT = 46
    ACTION_BUTTON_WIDTH = 152

    track_selected = Signal(dict, list)
    track_action_requested = Signal(str, dict)
    collection_requested = Signal(str, object)
    create_playlist_requested = Signal()
    delete_playlist_requested = Signal(int)
    play_collection_requested = Signal(list)
    download_collection_requested = Signal(list)

    def __init__(self, library_store: LibraryStore, parent=None) -> None:
        super().__init__(parent)
        self.library_store = library_store
        self.setObjectName("LibraryView")

        self.current_kind = "overview"
        self.current_playlist_id: int | None = None
        self.current_tracks: list[dict] = []
        self._rows_by_video: dict[str, list[TrackRow]] = {}
        self._downloading_video_ids: set[str] = set()
        self._overview_columns = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 0)
        layout.setSpacing(14)

        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        self.title_label = QLabel("Kitaplığın")
        self.title_label.setObjectName("PageTitle")
        title_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setObjectName("InfoLabel")
        title_layout.addWidget(self.subtitle_label)

        header_layout.addLayout(title_layout)

        self.actions_layout = QGridLayout()
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setHorizontalSpacing(12)
        self.actions_layout.setVerticalSpacing(10)
        self.actions_layout.setAlignment(Qt.AlignRight)

        self.play_collection_btn = QPushButton("▶ Çal")
        self.play_collection_btn.setObjectName("PrimaryPillButton")
        self._configure_header_button(self.play_collection_btn)
        self.play_collection_btn.hide()
        self.actions_layout.addWidget(self.play_collection_btn, 0, 0)

        self.download_collection_btn = QPushButton("↓ Tümünü İndir")
        self.download_collection_btn.setObjectName("SecondaryButton")
        self._configure_header_button(self.download_collection_btn)
        self.download_collection_btn.hide()
        self.actions_layout.addWidget(self.download_collection_btn, 0, 1)

        self.delete_playlist_btn = QPushButton("Sil")
        self.delete_playlist_btn.setObjectName("DangerButton")
        self._configure_header_button(self.delete_playlist_btn)
        self.delete_playlist_btn.hide()
        self.actions_layout.addWidget(self.delete_playlist_btn, 0, 2)

        self.create_playlist_btn = QPushButton("+ Çalma Listesi")
        self.create_playlist_btn.setObjectName("SearchButton")
        self._configure_header_button(self.create_playlist_btn)
        self.actions_layout.addWidget(self.create_playlist_btn, 0, 3)

        self._arrange_header_buttons()
        header_layout.addLayout(self.actions_layout)
        layout.addLayout(header_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ResultsScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 24)
        self.content_layout.setSpacing(8)
        self.content_layout.addStretch()

        self.scroll_area.setWidget(self.content_container)
        layout.addWidget(self.scroll_area, 1)

        self.create_playlist_btn.clicked.connect(
            lambda _checked=False: self.create_playlist_requested.emit()
        )
        self.play_collection_btn.clicked.connect(
            lambda _checked=False: self.play_collection_requested.emit(self.current_tracks)
        )
        self.download_collection_btn.clicked.connect(
            lambda _checked=False: self.download_collection_requested.emit(self.current_tracks)
        )
        self.delete_playlist_btn.clicked.connect(self._request_delete_current_playlist)

        self.show_overview()

    def _configure_header_button(self, button: QPushButton) -> None:
        button.setFixedSize(self.ACTION_BUTTON_WIDTH, self.ACTION_BUTTON_HEIGHT)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _header_buttons(self) -> list[QPushButton]:
        return [
            self.play_collection_btn,
            self.download_collection_btn,
            self.delete_playlist_btn,
            self.create_playlist_btn,
        ]

    def _action_column_count(self) -> int:
        width = self.width()
        if hasattr(self, "scroll_area"):
            width = self.scroll_area.viewport().width()
        available_columns = max(1, width // (self.ACTION_BUTTON_WIDTH + 12))
        return max(1, min(4, available_columns))

    def _arrange_header_buttons(self) -> None:
        for button in self._header_buttons():
            self.actions_layout.removeWidget(button)

        visible_buttons = [button for button in self._header_buttons() if not button.isHidden()]
        if not visible_buttons:
            return

        columns = min(len(visible_buttons), self._action_column_count())
        self._set_grid_stretches(self.actions_layout, columns)
        for index, button in enumerate(visible_buttons):
            self.actions_layout.addWidget(button, index // columns, index % columns)

    def _card_column_count(self) -> int:
        if not hasattr(self, "scroll_area"):
            width = self.width()
        else:
            width = self.scroll_area.viewport().width()
        if width < 620:
            return 1
        if width < 1040:
            return 2
        return 3

    @staticmethod
    def _set_grid_stretches(layout: QGridLayout, columns: int) -> None:
        for column in range(4):
            layout.setColumnStretch(column, 1 if column < columns else 0)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "actions_layout"):
            self._arrange_header_buttons()
        if self.current_kind != "overview" or not hasattr(self, "scroll_area"):
            return
        columns = self._card_column_count()
        if self._overview_columns and columns != self._overview_columns:
            self.show_overview()

    def show_overview(self) -> None:
        self.current_kind = "overview"
        self.current_playlist_id = None
        self.current_tracks = []
        self._rows_by_video.clear()

        summary = self.library_store.get_summary()
        playlists = self.library_store.list_playlists()
        self.title_label.setText("Kitaplığın")
        self.subtitle_label.setText(
            f"{summary['liked']} beğeni · {summary['downloads']} indirme · "
            f"{summary['playlists']} çalma listesi"
        )
        self.delete_playlist_btn.hide()
        self.play_collection_btn.hide()
        self.download_collection_btn.hide()
        self._arrange_header_buttons()
        self._clear_content()

        columns = self._card_column_count()
        self._overview_columns = columns

        grid_container = QWidget()
        grid_container.setObjectName("OverviewGrid")
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setHorizontalSpacing(14)
        grid_layout.setVerticalSpacing(14)

        cards = [
            ("Beğenilen Şarkılar", f"{summary['liked']} şarkı", "liked", None),
            ("İndirilenler", f"{summary['downloads']} çevrimdışı şarkı", "downloads", None),
        ]

        summary_columns = min(2, columns)
        self._set_grid_stretches(grid_layout, summary_columns)

        for index, (title, subtitle, kind, identifier) in enumerate(cards):
            button = self._create_collection_button(title, subtitle, kind, identifier)
            grid_layout.addWidget(button, index // summary_columns, index % summary_columns)

        self.content_layout.insertWidget(self.content_layout.count() - 1, grid_container)

        if playlists:
            section = QLabel("Çalma Listeleri")
            section.setObjectName("SectionTitle")
            self.content_layout.insertWidget(self.content_layout.count() - 1, section)

            playlist_grid_container = QWidget()
            playlist_grid_container.setObjectName("OverviewGrid")
            playlist_grid = QGridLayout(playlist_grid_container)
            playlist_grid.setContentsMargins(0, 0, 0, 0)
            playlist_grid.setHorizontalSpacing(14)
            playlist_grid.setVerticalSpacing(14)
            self._set_grid_stretches(playlist_grid, columns)
            for index, playlist in enumerate(playlists):
                button = self._create_collection_button(
                    playlist["name"],
                    f"{playlist.get('track_count', 0)} şarkı",
                    "playlist",
                    int(playlist["id"]),
                )
                playlist_grid.addWidget(button, index // columns, index % columns)
            self.content_layout.insertWidget(
                self.content_layout.count() - 1,
                playlist_grid_container,
            )
        else:
            empty = QLabel("Henüz çalma listen yok. İlk listeyi oluşturup şarkı ekleyebilirsin.")
            empty.setObjectName("InfoLabel")
            empty.setWordWrap(True)
            self.content_layout.insertWidget(self.content_layout.count() - 1, empty)

    def show_liked(self) -> None:
        tracks = self.library_store.list_liked_tracks()
        self._render_track_collection(
            title="Beğenilen Şarkılar",
            subtitle=f"{len(tracks)} şarkı",
            tracks=tracks,
            empty_text="Beğendiğin şarkılar burada görünecek.",
            kind="liked",
        )

    def show_downloads(self) -> None:
        tracks = self.library_store.list_downloads()
        self._render_track_collection(
            title="İndirilenler",
            subtitle=f"{len(tracks)} çevrimdışı şarkı",
            tracks=tracks,
            empty_text="İndirdiğin şarkılar burada çevrimdışı çalınabilir.",
            kind="downloads",
        )

    def show_playlist(self, playlist_id: int) -> None:
        playlist = self.library_store.get_playlist(playlist_id)
        if playlist is None:
            self.show_overview()
            return

        tracks = self.library_store.get_playlist_tracks(playlist_id)
        self._render_track_collection(
            title=playlist["name"],
            subtitle=f"{len(tracks)} şarkı",
            tracks=tracks,
            empty_text="Bu çalma listesi boş. Arama sonuçlarından şarkı ekleyebilirsin.",
            kind="playlist",
            playlist_id=playlist_id,
            extra_actions=[("remove_from_playlist", "Bu listeden kaldır")],
        )

    def refresh_current(self) -> None:
        if self.current_kind == "liked":
            self.show_liked()
        elif self.current_kind == "downloads":
            self.show_downloads()
        elif self.current_kind == "playlist" and self.current_playlist_id is not None:
            self.show_playlist(self.current_playlist_id)
        else:
            self.show_overview()

    def refresh_track_state(self, video_id: str | None = None) -> None:
        if video_id is None:
            row_pairs = [
                (stored_video_id, row)
                for stored_video_id, row_list in self._rows_by_video.items()
                for row in row_list
            ]
        else:
            row_pairs = [(video_id, row) for row in self._rows_by_video.get(video_id, [])]

        alive_rows: dict[str, list[TrackRow]] = {}
        for stored_video_id, row in row_pairs:
            try:
                self._sync_row_state(row)
            except RuntimeError:
                continue
            alive_rows.setdefault(stored_video_id, []).append(row)

        if video_id is None:
            self._rows_by_video = alive_rows
        else:
            self._rows_by_video[video_id] = alive_rows.get(video_id, [])

    def set_download_in_progress(self, video_id: str, in_progress: bool) -> None:
        if in_progress:
            self._downloading_video_ids.add(video_id)
        else:
            self._downloading_video_ids.discard(video_id)
        self.refresh_track_state(video_id)

    def _render_track_collection(
        self,
        *,
        title: str,
        subtitle: str,
        tracks: list[dict],
        empty_text: str,
        kind: str,
        playlist_id: int | None = None,
        extra_actions: list[tuple[str, str]] | None = None,
    ) -> None:
        self.current_kind = kind
        self.current_playlist_id = playlist_id
        self.current_tracks = tracks
        self._rows_by_video.clear()

        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)
        has_tracks = bool(tracks)
        self.play_collection_btn.setVisible(has_tracks)
        self.download_collection_btn.setVisible(has_tracks)
        self.delete_playlist_btn.setVisible(kind == "playlist")
        self._arrange_header_buttons()
        self._clear_content()

        if not tracks:
            empty = QLabel(empty_text)
            empty.setObjectName("InfoLabel")
            empty.setWordWrap(True)
            self.content_layout.insertWidget(self.content_layout.count() - 1, empty)
            return

        for index, track in enumerate(tracks, start=1):
            row = TrackRow(track, index=index, extra_actions=extra_actions)
            row.play_requested.connect(self._on_play_requested)
            row.action_requested.connect(self._on_action_requested)
            video_id = track.get("video_id")
            if video_id:
                self._rows_by_video.setdefault(video_id, []).append(row)
            self._sync_row_state(row)
            self.content_layout.insertWidget(self.content_layout.count() - 1, row)

    def _add_collection_button(
        self,
        title: str,
        subtitle: str,
        kind: str,
        identifier: object,
    ) -> None:
        button = self._create_collection_button(title, subtitle, kind, identifier)
        self.content_layout.insertWidget(self.content_layout.count() - 1, button)

    def _create_collection_button(
        self,
        title: str,
        subtitle: str,
        kind: str,
        identifier: object,
    ) -> QPushButton:
        button = QPushButton(f"{title}\n{subtitle}")
        button.setObjectName("LibraryCardButton")
        button.setMinimumHeight(112)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.clicked.connect(
            lambda _checked=False, k=kind, i=identifier: self.collection_requested.emit(k, i)
        )
        return button

    def _sync_row_state(self, row: TrackRow) -> None:
        video_id = row.track.get("video_id")
        if not video_id:
            return
        row.set_state(
            liked=self.library_store.is_liked(video_id),
            downloaded=self.library_store.is_downloaded(video_id),
            downloading=video_id in self._downloading_video_ids,
        )

    def _on_play_requested(self, track: dict) -> None:
        self.track_selected.emit(track, self.current_tracks)

    def _on_action_requested(self, action: str, track: dict) -> None:
        self.track_action_requested.emit(action, track)

    def _request_delete_current_playlist(self) -> None:
        if self.current_playlist_id is not None:
            self.delete_playlist_requested.emit(self.current_playlist_id)

    def _clear_content(self) -> None:
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
