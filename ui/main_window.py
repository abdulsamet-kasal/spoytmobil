"""Main window wiring: sidebar, content views, library state, and player."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.download_manager import DownloadManager
from core.library_store import LibraryStore
from core.music_api import MusicAPI
from ui.dialogs import AlertDialog, ConfirmDialog, SelectDialog, TextInputDialog
from ui.home_view import HomeView
from ui.library_view import LibraryView
from ui.player_bar import PlayerBar
from ui.search_view import SearchView
from ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Spoyt")
        self.setWindowIcon(
            QIcon(str(Path(__file__).resolve().parents[1] / "assets" / "spoyt_logo.svg"))
        )

        self.music_api = MusicAPI()
        self.library_store = LibraryStore()
        self.download_manager = DownloadManager(self.library_store.downloads_dir)
        self._closing = False

        self.playback_queue: list[dict] = []
        self.queue_index: int = -1

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        self.sidebar = Sidebar()
        top_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("ContentStack")

        self.home_view = HomeView(self.music_api, self.library_store)
        self.search_view = SearchView(self.music_api, self.library_store)
        self.library_view = LibraryView(self.library_store)

        self.stack.addWidget(self.home_view)
        self.stack.addWidget(self.search_view)
        self.stack.addWidget(self.library_view)

        top_layout.addWidget(self.stack, 1)

        top_container = QWidget()
        top_container.setLayout(top_layout)
        main_layout.addWidget(top_container, 1)

        self.player_bar = PlayerBar(self.library_store)
        main_layout.addWidget(self.player_bar)

        self._connect_signals()
        self._refresh_sidebar()
        QApplication.instance().installEventFilter(self)

    def _connect_signals(self) -> None:
        self.sidebar.page_changed.connect(self._change_page)
        self.sidebar.playlist_selected.connect(
            lambda playlist_id: self._open_collection("playlist", playlist_id)
        )
        self.sidebar.create_playlist_requested.connect(self._create_playlist)

        for view in (self.search_view, self.home_view, self.library_view):
            view.track_selected.connect(self._play_track)
            view.track_action_requested.connect(self._handle_track_action)

        self.home_view.collection_requested.connect(self._open_collection)
        self.home_view.create_playlist_requested.connect(self._create_playlist)
        self.library_view.collection_requested.connect(self._open_collection)
        self.library_view.create_playlist_requested.connect(self._create_playlist)
        self.library_view.delete_playlist_requested.connect(self._delete_playlist)
        self.library_view.play_collection_requested.connect(self._play_collection)
        self.library_view.download_collection_requested.connect(self._download_tracks)

        self.download_manager.download_started.connect(self._on_download_started)
        self.download_manager.download_progress.connect(self._on_download_progress)
        self.download_manager.download_completed.connect(self._on_download_completed)
        self.download_manager.download_failed.connect(self._on_download_failed)

        self.player_bar.track_finished.connect(self._play_next)
        self.player_bar.next_btn.clicked.connect(self._play_next)
        self.player_bar.prev_btn.clicked.connect(self._play_prev)

    def _change_page(self, page_id: str) -> None:
        if page_id == "home":
            self.stack.setCurrentIndex(0)
            self.sidebar.select_page("home")
            self.home_view.refresh_dynamic_sections()
        elif page_id == "search":
            self.stack.setCurrentIndex(1)
            self.sidebar.select_page("search")
            self.search_view.search_input.setFocus()
        elif page_id == "liked":
            self._open_collection("liked", None)
        elif page_id == "downloads":
            self._open_collection("downloads", None)
        else:
            self.stack.setCurrentIndex(2)
            self.sidebar.select_page("library")
            self.library_view.show_overview()

    def _open_collection(self, kind: str, identifier: object) -> None:
        self.stack.setCurrentIndex(2)
        if kind == "liked":
            self.sidebar.select_page("liked")
            self.library_view.show_liked()
        elif kind == "downloads":
            self.sidebar.select_page("downloads")
            self.library_view.show_downloads()
        elif kind == "playlist" and identifier is not None:
            playlist_id = int(identifier)
            self.sidebar.select_playlist(playlist_id)
            self.library_view.show_playlist(playlist_id)
        else:
            self.sidebar.select_page("library")
            self.library_view.show_overview()

    def _play_track(self, track: dict, results_list: list[dict]) -> None:
        self.playback_queue = results_list or [track]
        self.queue_index = self._find_queue_index(track)
        self._play_track_now(track)

    def _play_collection(self, tracks: list[dict]) -> None:
        if tracks:
            self._play_track(tracks[0], tracks)

    def _play_track_now(self, track: dict) -> None:
        self.library_store.record_played(track)
        playable_track = self.library_store.hydrate_track(track)
        self.player_bar.play_track(playable_track)
        self.home_view.refresh_dynamic_sections()

    def _play_next(self) -> None:
        if not self.playback_queue:
            return
        next_index = self.queue_index + 1
        if next_index < len(self.playback_queue):
            self.queue_index = next_index
            self._play_track_now(self.playback_queue[next_index])

    def _play_prev(self) -> None:
        if not self.playback_queue:
            return
        prev_index = self.queue_index - 1
        if prev_index >= 0:
            self.queue_index = prev_index
            self._play_track_now(self.playback_queue[prev_index])

    def _handle_track_action(self, action: str, track: dict) -> None:
        if action == "play":
            self._play_track(track, [track])
        elif action == "toggle_like":
            liked = self.library_store.toggle_liked(track)
            message = "Beğenilenlere eklendi." if liked else "Beğenilerden çıkarıldı."
            self.statusBar().showMessage(message, 3500)
            self._refresh_library_surfaces(track.get("video_id"))
        elif action == "add_to_playlist":
            self._add_track_to_playlist(track)
        elif action == "download":
            self._start_download(track)
        elif action == "remove_download":
            self.library_store.remove_download(track["video_id"], delete_file=True)
            self.statusBar().showMessage("İndirme kaldırıldı.", 3500)
            self._refresh_library_surfaces(track.get("video_id"))
        elif action == "remove_from_playlist":
            playlist_id = self.library_view.current_playlist_id
            if playlist_id is not None:
                self.library_store.remove_from_playlist(playlist_id, track["video_id"])
                self.statusBar().showMessage("Şarkı listeden kaldırıldı.", 3500)
                self._refresh_library_surfaces(track.get("video_id"))

    def _download_tracks(self, tracks: list[dict]) -> None:
        queued = 0
        skipped = 0
        for track in tracks:
            video_id = track.get("video_id")
            if not video_id or self.library_store.is_downloaded(video_id):
                skipped += 1
                continue
            if self._start_download(track, quiet=True):
                queued += 1
            else:
                skipped += 1

        if queued:
            self.statusBar().showMessage(
                f"{queued} şarkı indirme kuyruğuna alındı.", 5000
            )
        elif skipped:
            self.statusBar().showMessage("Listedeki şarkılar zaten indirilmiş.", 5000)

    def _add_track_to_playlist(self, track: dict) -> None:
        playlists = self.library_store.list_playlists()
        if not playlists:
            playlist_id = self._create_playlist(show_playlist=False)
            if playlist_id is None:
                return
        else:
            options = [playlist["name"] for playlist in playlists]
            options.append("Yeni çalma listesi...")
            selected, ok = SelectDialog.get_item(
                self,
                "Çalma listesine ekle",
                "Çalma listesi:",
                options,
            )
            if not ok:
                return
            if selected == "Yeni çalma listesi...":
                playlist_id = self._create_playlist(show_playlist=False)
                if playlist_id is None:
                    return
            else:
                playlist_id = next(
                    int(playlist["id"])
                    for playlist in playlists
                    if playlist["name"] == selected
                )

        added = self.library_store.add_to_playlist(playlist_id, track)
        if added:
            self.statusBar().showMessage("Çalma listesine eklendi.", 3500)
        else:
            self.statusBar().showMessage("Bu şarkı zaten listede.", 3500)
        self._refresh_library_surfaces(track.get("video_id"))

    def _create_playlist(self, show_playlist: bool = True) -> int | None:
        name, ok = TextInputDialog.get_text(
            self,
            "Yeni çalma listesi",
            "Çalma listesi adı:",
        )
        if not ok:
            return None

        try:
            playlist_id = self.library_store.create_playlist(name)
        except ValueError as exc:
            AlertDialog.show(self, "Spoyt", str(exc))
            return None

        self._refresh_library_surfaces()
        if show_playlist:
            self._open_collection("playlist", playlist_id)
        self.statusBar().showMessage("Çalma listesi oluşturuldu.", 3500)
        return playlist_id

    def _delete_playlist(self, playlist_id: int) -> None:
        playlist = self.library_store.get_playlist(playlist_id)
        if playlist is None:
            return

        if not ConfirmDialog.ask(
            self,
            "Çalma listesini sil",
            f'"{playlist["name"]}" silinsin mi?',
        ):
            return

        self.library_store.delete_playlist(playlist_id)
        self._refresh_library_surfaces()
        self._open_collection("library", None)
        self.statusBar().showMessage("Çalma listesi silindi.", 3500)

    def _start_download(self, track: dict, quiet: bool = False) -> bool:
        video_id = track.get("video_id")
        if not video_id:
            return False
        if self.library_store.is_downloaded(video_id):
            if not quiet:
                self.statusBar().showMessage("Bu şarkı zaten indirilmiş.", 3500)
            return False
        if not self.download_manager.start_download(track):
            if not quiet:
                self.statusBar().showMessage("İndirme zaten devam ediyor.", 3500)
            return False
        return True

    def _on_download_started(self, track: dict) -> None:
        if self._closing:
            return
        video_id = track["video_id"]
        self._set_download_in_progress(video_id, True)
        self.statusBar().showMessage(f'İndiriliyor: {track.get("title", "Şarkı")}', 3500)

    def _on_download_progress(self, video_id: str, percent: int, label: str) -> None:
        if self._closing:
            return
        self.statusBar().showMessage(f"{label}: %{percent}", 1200)

    def _on_download_completed(self, track: dict, file_path: str) -> None:
        if self._closing:
            self.library_store.mark_downloaded(track, file_path)
            return
        self.library_store.mark_downloaded(track, file_path)
        self._set_download_in_progress(track["video_id"], False)
        self.statusBar().showMessage("İndirme tamamlandı.", 5000)
        self._refresh_library_surfaces(track.get("video_id"))

    def _on_download_failed(self, track: dict, message: str) -> None:
        if self._closing:
            return
        video_id = track.get("video_id")
        if video_id:
            self._set_download_in_progress(video_id, False)
            self._refresh_library_surfaces(video_id)
        AlertDialog.show(self, "İndirme başarısız", message[:500])

    def _set_download_in_progress(self, video_id: str, in_progress: bool) -> None:
        self.search_view.set_download_in_progress(video_id, in_progress)
        self.home_view.set_download_in_progress(video_id, in_progress)
        self.library_view.set_download_in_progress(video_id, in_progress)

    def _refresh_sidebar(self) -> None:
        self.sidebar.set_playlists(self.library_store.list_playlists())

    def _refresh_library_surfaces(self, video_id: str | None = None) -> None:
        self._refresh_sidebar()
        self.search_view.refresh_track_state(video_id)
        self.home_view.refresh_track_state(video_id)
        self.home_view.refresh_dynamic_sections()
        self.library_view.refresh_current()

    def _find_queue_index(self, track: dict) -> int:
        video_id = track.get("video_id")
        for index, queued_track in enumerate(self.playback_queue):
            if queued_track.get("video_id") == video_id:
                return index
        return 0 if self.playback_queue else -1

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if (
            event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Space
            and not event.isAutoRepeat()
        ):
            app = QApplication.instance()
            focus_widget = app.focusWidget() if app is not None else None
            text_widgets = (QLineEdit, QTextEdit, QPlainTextEdit)
            if isinstance(obj, text_widgets) or isinstance(focus_widget, text_widgets):
                return False
            self.player_bar.toggle_play()
            return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._closing = True
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        self.player_bar.shutdown()
        self.download_manager.cancel_all()
        self.library_store.close()
        super().closeEvent(event)
