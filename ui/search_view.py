"""Search page: query input, result list, and row action forwarding."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.library_store import LibraryStore
from core.music_api import MusicAPI
from ui.track_row import TrackRow


class SearchView(QWidget):
    track_selected = Signal(dict, list)
    track_action_requested = Signal(str, dict)

    def __init__(
        self,
        music_api: MusicAPI,
        library_store: LibraryStore,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.music_api = music_api
        self.library_store = library_store
        self.setObjectName("SearchView")

        self.current_results: list[dict] = []
        self._rows_by_video: dict[str, list[TrackRow]] = {}
        self._downloading_video_ids: set[str] = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 0)
        layout.setSpacing(16)

        search_frame = QWidget()
        search_frame.setObjectName("SearchBarFrame")
        search_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        search_bar_layout = QHBoxLayout(search_frame)
        search_bar_layout.setContentsMargins(8, 6, 6, 6)
        search_bar_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Şarkı, sanatçı veya albüm ara...")
        self.search_input.setFrame(False)
        self.search_input.setMinimumHeight(44)
        self.search_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.search_button = QPushButton("Ara")
        self.search_button.setObjectName("SearchButton")
        self.search_button.setFixedSize(112, 44)
        self.search_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        search_bar_layout.addWidget(self.search_input, 1)
        search_bar_layout.addWidget(self.search_button)
        layout.addWidget(search_frame)

        self.status_label = QLabel("")
        self.status_label.setObjectName("StatusLabel")
        layout.addWidget(self.status_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("ResultsScroll")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 16)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch()

        self.scroll_area.setWidget(self.results_container)
        layout.addWidget(self.scroll_area)

        self.search_button.clicked.connect(self.perform_search)
        self.search_input.returnPressed.connect(self.perform_search)

    def perform_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return

        self.status_label.setText(f'"{query}" için aranıyor...')
        self._clear_results()

        results = self.music_api.search(query, filter_type="songs", limit=25)
        self.current_results = results

        if not results:
            self.status_label.setText("Sonuç bulunamadı. Bağlantınızı kontrol edin.")
            return

        self.status_label.setText(f'"{query}" için {len(results)} sonuç')

        for index, track in enumerate(results, start=1):
            row = self._create_row(track, index=index)
            self.results_layout.insertWidget(self.results_layout.count() - 1, row)

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

    def _create_row(self, track: dict, index: int | None = None) -> TrackRow:
        row = TrackRow(track, index=index)
        row.play_requested.connect(self._on_play_requested)
        row.action_requested.connect(self._on_action_requested)

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

    def _on_play_requested(self, track: dict) -> None:
        self.track_selected.emit(track, self.current_results)

    def _on_action_requested(self, action: str, track: dict) -> None:
        self.track_action_requested.emit(action, track)

    def _clear_results(self) -> None:
        self._rows_by_video.clear()
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
