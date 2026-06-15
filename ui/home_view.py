"""Home page with quick library shortcuts, recents, and recommendations."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.library_store import LibraryStore
from core.music_api import MusicAPI
from ui.track_row import TrackRow


CATEGORIES: list[tuple[str, str]] = [
    ("Popüler Şarkılar", "top hits"),
    ("Pop", "pop music hits"),
    ("Hip Hop", "hip hop hits"),
    ("Türkçe Pop", "türkçe pop şarkılar"),
]


class HomeView(QWidget):
    QUICK_CARD_HEIGHT = 78
    QUICK_CARD_GAP = 10
    QUICK_SIDE_PADDING = 48

    track_selected = Signal(dict, list)
    track_action_requested = Signal(str, dict)
    collection_requested = Signal(str, object)
    create_playlist_requested = Signal()

    def __init__(
        self,
        music_api: MusicAPI,
        library_store: LibraryStore,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.music_api = music_api
        self.library_store = library_store
        self.setObjectName("HomeView")
        self._loaded_recommendations = False
        self._rows_by_video: dict[str, list[TrackRow]] = {}
        self._downloading_video_ids: set[str] = set()
        self._quick_button_count = 0
        self._quick_columns = 0
        self._quick_available_width = 0
        self._quick_card_width = 0
        self._quick_rows: list[QHBoxLayout] = []

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ResultsScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(24, 24, 24, 24)
        self.container_layout.setSpacing(16)

        title = QLabel("Günaydın")
        title.setObjectName("PageTitle")
        self.container_layout.addWidget(title)

        self.quick_layout = QVBoxLayout()
        self.quick_layout.setSpacing(10)
        self.container_layout.addLayout(self.quick_layout)

        self.recent_title = QLabel("Yakınlarda Çalınanlar")
        self.recent_title.setObjectName("SectionTitle")
        self.container_layout.addWidget(self.recent_title)

        self.recent_layout = QVBoxLayout()
        self.recent_layout.setSpacing(2)
        self.container_layout.addLayout(self.recent_layout)

        self.recommendations_layout = QVBoxLayout()
        self.recommendations_layout.setSpacing(8)
        self.container_layout.addLayout(self.recommendations_layout)

        self.container_layout.addStretch()

        self.scroll_area.setWidget(container)
        outer_layout.addWidget(self.scroll_area)

    def load_recommendations(self) -> None:
        if self._loaded_recommendations:
            return
        self._loaded_recommendations = True

        for category_name, query in CATEGORIES:
            section_label = QLabel(category_name)
            section_label.setObjectName("SectionTitle")
            self.recommendations_layout.addWidget(section_label)

            results = self.music_api.search(query, filter_type="songs", limit=5)
            if not results:
                empty_label = QLabel("Yüklenemedi.")
                empty_label.setObjectName("InfoLabel")
                self.recommendations_layout.addWidget(empty_label)
                continue

            for track in results:
                row = self._create_row(track, queue=results)
                self.recommendations_layout.addWidget(row)

    def refresh_dynamic_sections(self) -> None:
        self._clear_layout(self.quick_layout)
        self._clear_layout(self.recent_layout)
        self._quick_button_count = 0
        self._quick_rows = []
        self._quick_available_width = self._quick_layout_width()
        self._quick_columns = self._quick_column_count()
        self._quick_card_width = self._quick_card_width_for_columns(self._quick_columns)

        summary = self.library_store.get_summary()
        self._add_quick_button(
            "Beğenilen Şarkılar",
            f"{summary['liked']} şarkı",
            "liked",
            None,
        )
        self._add_quick_button(
            "İndirilenler",
            f"{summary['downloads']} şarkı",
            "downloads",
            None,
        )

        playlists = self.library_store.list_playlists()
        for playlist in playlists[:2]:
            self._add_quick_button(
                playlist["name"],
                f"{playlist.get('track_count', 0)} şarkı",
                "playlist",
                int(playlist["id"]),
            )

        if len(playlists) < 2:
            create_btn = QPushButton("+\nYeni Çalma Listesi")
            create_btn.setObjectName("QuickCardButton")
            self._configure_quick_button(create_btn)
            create_btn.clicked.connect(
                lambda _checked=False: self.create_playlist_requested.emit()
            )
            self._add_quick_widget(create_btn)

        self._finish_quick_rows()

        recent_tracks = self.library_store.list_recent_tracks(limit=6)
        if not recent_tracks:
            empty = QLabel("Bir şarkı çaldığında burada hızlıca geri dönebilirsin.")
            empty.setObjectName("InfoLabel")
            empty.setWordWrap(True)
            self.recent_layout.addWidget(empty)
            return

        for track in recent_tracks:
            row = self._create_row(track, queue=recent_tracks)
            self.recent_layout.addWidget(row)

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

    def _add_quick_button(
        self,
        title: str,
        subtitle: str,
        kind: str,
        identifier: object,
    ) -> None:
        button = QPushButton(f"{title}\n{subtitle}")
        button.setObjectName("QuickCardButton")
        self._configure_quick_button(button)
        button.clicked.connect(
            lambda _checked=False, k=kind, i=identifier: self.collection_requested.emit(k, i)
        )
        self._add_quick_widget(button)

    def _configure_quick_button(self, button: QPushButton) -> None:
        button.setFixedSize(self._quick_card_width, self.QUICK_CARD_HEIGHT)
        button.setMinimumWidth(0)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def _add_quick_widget(self, widget: QWidget) -> None:
        columns = max(1, self._quick_columns)
        if self._quick_button_count % columns == 0:
            row_widget = QWidget()
            row_widget.setObjectName("QuickCardRow")
            row_widget.setFixedWidth(self._quick_available_width)
            row_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(10)
            self.quick_layout.addWidget(row_widget)
            self._quick_rows.append(row_layout)

        self._quick_rows[-1].addWidget(widget, 1)
        self._quick_button_count += 1

    def _finish_quick_rows(self) -> None:
        if not self._quick_rows:
            return
        columns = max(1, self._quick_columns)
        used_in_last_row = self._quick_button_count % columns
        if used_in_last_row == 0:
            return
        for _ in range(columns - used_in_last_row):
            self._quick_rows[-1].addStretch(1)

    def _quick_column_count(self) -> int:
        width = self._quick_available_width or self._quick_layout_width()
        return self._quick_column_count_for_width(width)

    @staticmethod
    def _quick_column_count_for_width(width: int) -> int:
        if width < 560:
            return 1
        if width < 1100:
            return 2
        if width < 1450:
            return 3
        return 4

    def _quick_layout_width(self) -> int:
        return max(240, self.scroll_area.viewport().width() - self.QUICK_SIDE_PADDING)

    def _quick_card_width_for_columns(self, columns: int) -> int:
        gaps = self.QUICK_CARD_GAP * max(0, columns - 1)
        return max(180, int((self._quick_available_width - gaps) / max(1, columns)))

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if not hasattr(self, "scroll_area"):
            return
        width = self._quick_layout_width()
        columns = self._quick_column_count_for_width(width)
        if self._quick_columns and (
            columns != self._quick_columns
            or abs(width - self._quick_available_width) > 4
        ):
            self.refresh_dynamic_sections()

    def _create_row(self, track: dict, queue: list[dict]) -> TrackRow:
        row = TrackRow(track)
        row.play_requested.connect(lambda selected, q=queue: self.track_selected.emit(selected, q))
        row.action_requested.connect(self.track_action_requested.emit)

        video_id = track.get("video_id")
        if video_id:
            self._rows_by_video.setdefault(video_id, []).append(row)
        self._sync_row_state(row)
        return row

    def _sync_row_state(self, row: TrackRow) -> None:
        video_id = row.track.get("video_id")
        if not video_id:
            return
        row.set_state(
            liked=self.library_store.is_liked(video_id),
            downloaded=self.library_store.is_downloaded(video_id),
            downloading=video_id in self._downloading_video_ids,
        )

    def _clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh_dynamic_sections()
        self.load_recommendations()
