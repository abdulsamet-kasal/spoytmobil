from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, DictProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput

from core.download_service import DownloadService
from core.library_store import LibraryStore
from core.music_api import MusicAPI
from core.platform_paths import get_data_dir
from core.stream_service import resolve_stream_url


GridLayout
Screen
ScreenManager


KV = """
<SpoytButton>:
    background_normal: ""
    background_down: ""
    background_color: self.down_color if self.state == "down" else self.normal_color
    color: 1, 1, 1, 1
    font_size: "14sp"
    size_hint_y: None
    height: dp(44)
    normal_color: 0.12, 0.12, 0.14, 1
    down_color: 0.18, 0.18, 0.21, 1

<PrimaryButton>:
    normal_color: 0.10, 0.70, 0.34, 1
    down_color: 0.08, 0.58, 0.28, 1
    bold: True

<TabButton>:
    background_normal: ""
    background_down: ""
    background_color: (0.10, 0.70, 0.34, 1) if self.state == "down" else (0.08, 0.08, 0.09, 1)
    color: 1, 1, 1, 1
    font_size: "13sp"
    size_hint_y: None
    height: dp(48)

<TrackRow>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(92)
    spacing: dp(10)
    padding: dp(10), dp(8)
    canvas.before:
        Color:
            rgba: 0.10, 0.10, 0.12, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
    AsyncImage:
        source: root.track.get("thumbnail") or ""
        size_hint: None, None
        size: dp(58), dp(58)
        allow_stretch: True
        keep_ratio: True
    BoxLayout:
        orientation: "vertical"
        spacing: dp(2)
        Label:
            text: root.track.get("title", "Unknown")
            color: 1, 1, 1, 1
            bold: True
            halign: "left"
            valign: "middle"
            text_size: self.size
            shorten: True
            shorten_from: "right"
            font_size: "14sp"
        Label:
            text: root.track.get("artist", "")
            color: 0.72, 0.72, 0.74, 1
            halign: "left"
            valign: "middle"
            text_size: self.size
            shorten: True
            shorten_from: "right"
            font_size: "12sp"
        Label:
            text: root.status_text
            color: 0.10, 0.70, 0.34, 1
            halign: "left"
            valign: "middle"
            text_size: self.size
            shorten: True
            font_size: "11sp"
    BoxLayout:
        orientation: "vertical"
        size_hint_x: None
        width: dp(96)
        spacing: dp(6)
        SpoytButton:
            text: "Play"
            height: dp(36)
            on_release: root.play()
        SpoytButton:
            text: "More"
            height: dp(36)
            on_release: root.open_actions()

<SpoytRoot>:
    orientation: "vertical"
    canvas.before:
        Color:
            rgba: 0.05, 0.05, 0.06, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: "vertical"
        padding: dp(14), dp(12), dp(14), dp(8)
        spacing: dp(10)
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(42)
            spacing: dp(8)
            Label:
                text: "Spoyt"
                bold: True
                font_size: "24sp"
                color: 1, 1, 1, 1
                halign: "left"
                valign: "middle"
                text_size: self.size
            Label:
                text: root.status
                font_size: "12sp"
                color: 0.72, 0.72, 0.74, 1
                halign: "right"
                valign: "middle"
                text_size: self.size
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(50)
            spacing: dp(8)
            TextInput:
                id: query_input
                text: root.query
                hint_text: "Search YouTube Music or paste a URL"
                multiline: False
                foreground_color: 1, 1, 1, 1
                hint_text_color: 0.58, 0.58, 0.60, 1
                background_color: 0.11, 0.11, 0.13, 1
                cursor_color: 1, 1, 1, 1
                padding: dp(12), dp(14)
                on_text: root.query = self.text
                on_text_validate: root.search()
            PrimaryButton:
                text: "Search"
                size_hint_x: None
                width: dp(92)
                on_release: root.search()
        ProgressBar:
            max: 100
            value: root.busy_progress
            size_hint_y: None
            height: dp(4)
            opacity: 1 if root.busy else 0
        ScreenManager:
            id: screen_manager
            Screen:
                name: "home"
                BoxLayout:
                    orientation: "vertical"
                    spacing: dp(10)
                    Label:
                        text: "Recently played"
                        size_hint_y: None
                        height: dp(28)
                        bold: True
                        color: 1, 1, 1, 1
                        halign: "left"
                        text_size: self.size
                    ScrollView:
                        do_scroll_x: False
                        GridLayout:
                            id: recent_list
                            cols: 1
                            spacing: dp(8)
                            padding: 0, 0, 0, dp(8)
                            size_hint_y: None
                            height: self.minimum_height
            Screen:
                name: "search"
                ScrollView:
                    do_scroll_x: False
                    GridLayout:
                        id: results_list
                        cols: 1
                        spacing: dp(8)
                        padding: 0, 0, 0, dp(8)
                        size_hint_y: None
                        height: self.minimum_height
            Screen:
                name: "library"
                BoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    BoxLayout:
                        size_hint_y: None
                        height: dp(42)
                        spacing: dp(8)
                        SpoytButton:
                            text: "Liked"
                            on_release: root.show_liked()
                        SpoytButton:
                            text: "Downloads"
                            on_release: root.show_downloads()
                    ScrollView:
                        do_scroll_x: False
                        GridLayout:
                            id: library_list
                            cols: 1
                            spacing: dp(8)
                            padding: 0, 0, 0, dp(8)
                            size_hint_y: None
                            height: self.minimum_height
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(120)
            padding: dp(10), dp(8)
            spacing: dp(6)
            canvas.before:
                Color:
                    rgba: 0.08, 0.08, 0.09, 1
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(8)]
            Label:
                text: root.now_title
                color: 1, 1, 1, 1
                bold: True
                halign: "left"
                valign: "middle"
                text_size: self.size
                shorten: True
                size_hint_y: None
                height: dp(24)
            Label:
                text: root.now_artist
                color: 0.72, 0.72, 0.74, 1
                halign: "left"
                valign: "middle"
                text_size: self.size
                shorten: True
                size_hint_y: None
                height: dp(20)
            Slider:
                min: 0
                max: max(root.duration, 1)
                value: root.position
                disabled: root.duration <= 0
                on_touch_up: root.seek(self.value) if self.collide_point(*args[1].pos) else None
            BoxLayout:
                orientation: "horizontal"
                spacing: dp(8)
                SpoytButton:
                    text: "Prev"
                    on_release: root.play_prev()
                PrimaryButton:
                    text: "Pause" if root.playing else "Play"
                    on_release: root.toggle_play()
                SpoytButton:
                    text: "Next"
                    on_release: root.play_next()
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(50)
            spacing: dp(8)
            TabButton:
                text: "Home"
                state: "down" if root.current_tab == "home" else "normal"
                on_release: root.change_tab("home")
            TabButton:
                text: "Search"
                state: "down" if root.current_tab == "search" else "normal"
                on_release: root.change_tab("search")
            TabButton:
                text: "Library"
                state: "down" if root.current_tab == "library" else "normal"
                on_release: root.change_tab("library")
"""


def is_probable_url(value: str) -> bool:
    return value.startswith(("http://", "https://")) or "youtube.com/watch" in value or "youtu.be/" in value


def video_id_from_url(value: str) -> str | None:
    if "youtu.be/" in value:
        return value.rsplit("/", 1)[-1].split("?", 1)[0]
    if "v=" in value:
        return value.split("v=", 1)[-1].split("&", 1)[0]
    return None


def format_seconds(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes}:{secs:02d}"


class SpoytButton(Button):
    normal_color = ListProperty([0.12, 0.12, 0.14, 1])
    down_color = ListProperty([0.18, 0.18, 0.21, 1])


class PrimaryButton(SpoytButton):
    normal_color = ListProperty([0.10, 0.70, 0.34, 1])
    down_color = ListProperty([0.08, 0.58, 0.28, 1])


class TabButton(Button):
    pass


class TrackRow(BoxLayout):
    track = DictProperty({})
    status_text = StringProperty("")

    def __init__(self, root: "SpoytRoot", track: dict[str, Any], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.root = root
        self.track = track
        self.status_text = root.status_for_track(track)

    def play(self) -> None:
        self.root.play_track(self.track)

    def open_actions(self) -> None:
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(12))
        popup = Popup(title=self.track.get("title", "Track"), content=content, size_hint=(0.86, None), height=dp(280))
        actions = [
            ("Play", lambda: self.root.play_track(self.track)),
            ("Like / Unlike", lambda: self.root.toggle_like(self.track)),
            ("Download", lambda: self.root.start_download(self.track)),
            ("Remove Download", lambda: self.root.remove_download(self.track)),
        ]
        for label, callback in actions:
            button = Button(text=label, size_hint_y=None, height=dp(44))
            button.bind(on_release=lambda _btn, cb=callback: (popup.dismiss(), cb()))
            content.add_widget(button)
        popup.open()


class SpoytRoot(BoxLayout):
    query = StringProperty("")
    status = StringProperty("Ready")
    current_tab = StringProperty("home")
    now_title = StringProperty("No track playing")
    now_artist = StringProperty("")
    busy = BooleanProperty(False)
    busy_progress = NumericProperty(0)
    position = NumericProperty(0)
    duration = NumericProperty(0)
    playing = BooleanProperty(False)
    queue = ListProperty([])

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        data_dir = get_data_dir("spoyt")
        self.library = LibraryStore(data_dir)
        self.music_api = MusicAPI()
        self.downloader = DownloadService(self.library.downloads_dir)
        self.current_track: dict[str, Any] | None = None
        self.queue_index = -1
        self.sound = None
        self._paused_position = 0.0
        self._suppress_stop = False
        self._position_event = Clock.schedule_interval(self._tick_position, 0.5)
        Clock.schedule_once(lambda _dt: self.refresh_home(), 0)

    def change_tab(self, name: str) -> None:
        self.current_tab = name
        self.ids.screen_manager.current = name
        if name == "home":
            self.refresh_home()
        elif name == "library":
            self.show_liked()

    def set_status(self, text: str, busy: bool = False, progress: int = 0) -> None:
        self.status = text
        self.busy = busy
        self.busy_progress = progress

    def search(self) -> None:
        query = self.query.strip()
        if not query:
            return
        self.change_tab("search")
        self.set_status("Searching...", True, 25)
        threading.Thread(target=self._search_worker, args=(query,), daemon=True).start()

    def _search_worker(self, query: str) -> None:
        if is_probable_url(query):
            video_id = video_id_from_url(query)
            tracks = [{
                "video_id": video_id,
                "title": query,
                "artist": "YouTube",
                "duration": "",
                "thumbnail": "",
            }] if video_id else []
        else:
            tracks = self.music_api.search(query)
        Clock.schedule_once(lambda _dt: self._show_results(tracks), 0)

    @mainthread
    def _show_results(self, tracks: list[dict[str, Any]]) -> None:
        self.queue = tracks
        self.queue_index = -1
        self._fill_list(self.ids.results_list, tracks)
        self.set_status(f"{len(tracks)} result(s)", False, 0)

    def _fill_list(self, target, tracks: list[dict[str, Any]]) -> None:
        target.clear_widgets()
        if not tracks:
            target.add_widget(self._empty_label("Nothing here yet."))
            return
        for track in tracks:
            target.add_widget(TrackRow(self, self.library.hydrate_track(track)))

    def _empty_label(self, text: str) -> Label:
        return Label(
            text=text,
            color=(0.72, 0.72, 0.74, 1),
            size_hint_y=None,
            height=dp(72),
            halign="center",
            valign="middle",
        )

    def status_for_track(self, track: dict[str, Any]) -> str:
        video_id = track.get("video_id", "")
        labels = []
        if video_id and self.library.is_liked(video_id):
            labels.append("Liked")
        if video_id and self.library.is_downloaded(video_id):
            labels.append("Offline")
        if video_id and self.downloader.is_downloading(video_id):
            labels.append("Downloading")
        return "  ".join(labels)

    def refresh_home(self) -> None:
        self._fill_list(self.ids.recent_list, self.library.list_recent_tracks(limit=20))

    def show_liked(self) -> None:
        self._fill_list(self.ids.library_list, self.library.list_liked_tracks())

    def show_downloads(self) -> None:
        self._fill_list(self.ids.library_list, self.library.list_downloads())

    def toggle_like(self, track: dict[str, Any]) -> None:
        liked = self.library.toggle_liked(track)
        self.set_status("Liked" if liked else "Removed from liked")
        self.refresh_visible_lists()

    def remove_download(self, track: dict[str, Any]) -> None:
        video_id = track.get("video_id")
        if video_id:
            self.library.remove_download(video_id)
            self.set_status("Download removed")
            self.refresh_visible_lists()

    def start_download(self, track: dict[str, Any]) -> None:
        started = self.downloader.start_download(
            track,
            on_progress=lambda video_id, percent, label: Clock.schedule_once(
                lambda _dt: self._on_download_progress(video_id, percent, label), 0
            ),
            on_completed=lambda video_id, file_path: Clock.schedule_once(
                lambda _dt: self._on_download_completed(track, file_path), 0
            ),
            on_failed=lambda video_id, message: Clock.schedule_once(
                lambda _dt: self._on_download_failed(track, message), 0
            ),
        )
        if started:
            self.set_status("Download started", True, 5)
            self.refresh_visible_lists()

    def _on_download_progress(self, _video_id: str, percent: int, label: str) -> None:
        self.set_status(label, True, percent)

    def _on_download_completed(self, track: dict[str, Any], file_path: str) -> None:
        self.library.mark_downloaded(track, file_path)
        self.set_status("Download complete")
        self.refresh_visible_lists()

    def _on_download_failed(self, _track: dict[str, Any], message: str) -> None:
        self.set_status(message[:48] or "Download failed")
        self.refresh_visible_lists()

    def refresh_visible_lists(self) -> None:
        self.refresh_home()
        if self.current_tab == "search":
            self._fill_list(self.ids.results_list, list(self.queue))
        elif self.current_tab == "library":
            self.show_liked()

    def play_track(self, track: dict[str, Any]) -> None:
        if track in self.queue:
            self.queue_index = list(self.queue).index(track)
        else:
            self.queue = [track]
            self.queue_index = 0
        hydrated = self.library.hydrate_track(track)
        self.current_track = hydrated
        self.now_title = hydrated.get("title", "Unknown")
        self.now_artist = hydrated.get("artist", "")
        self.library.record_played(hydrated)
        self.set_status("Loading audio...", True, 30)
        threading.Thread(target=self._prepare_audio_worker, args=(hydrated,), daemon=True).start()

    def _prepare_audio_worker(self, track: dict[str, Any]) -> None:
        local_path = track.get("local_path")
        if local_path and Path(local_path).exists():
            source = local_path
        else:
            try:
                source = resolve_stream_url(track["video_id"])
            except Exception as exc:
                Clock.schedule_once(lambda _dt: self.set_status(str(exc)[:48] or "Stream failed"), 0)
                return
        Clock.schedule_once(lambda _dt: self._play_source(source), 0)

    @mainthread
    def _play_source(self, source: str) -> None:
        if self.sound is not None:
            self._suppress_stop = True
            self.sound.stop()
            self.sound.unload()
            self._suppress_stop = False
        self.sound = SoundLoader.load(source)
        if self.sound is None:
            self.set_status("Audio backend could not load source")
            return
        self.duration = max(0, self.sound.length or 0)
        self.position = 0
        self._paused_position = 0
        self.sound.bind(on_stop=lambda *_args: self._on_sound_stop())
        self.sound.play()
        self.playing = True
        self.set_status("Playing")

    def toggle_play(self) -> None:
        if self.sound is None:
            if self.current_track:
                self.play_track(self.current_track)
            return
        if self.playing:
            self._paused_position = self.sound.get_pos() or self.position
            self._suppress_stop = True
            self.sound.stop()
            self._suppress_stop = False
            self.playing = False
        else:
            self.sound.play()
            if self._paused_position > 0:
                self.seek(self._paused_position)
            self.playing = True

    def play_next(self) -> None:
        if not self.queue:
            return
        next_index = self.queue_index + 1
        if next_index >= len(self.queue):
            self.set_status("Queue ended")
            return
        self.queue_index = next_index
        self.play_track(self.queue[self.queue_index])

    def play_prev(self) -> None:
        if not self.queue:
            return
        self.queue_index = max(0, self.queue_index - 1)
        self.play_track(self.queue[self.queue_index])

    def seek(self, position: float) -> None:
        if self.sound is not None and self.duration > 0:
            try:
                self.sound.seek(position)
            except Exception:
                pass

    def _tick_position(self, _dt: float) -> None:
        if self.sound is None:
            self.position = 0
            self.duration = 0
            return
        self.position = self.sound.get_pos() or 0
        if self.sound.length:
            self.duration = self.sound.length

    def _on_sound_stop(self) -> None:
        self.playing = False
        if self._suppress_stop:
            return
        if self.duration > 0 and self.position >= max(0, self.duration - 1):
            self.play_next()

    def shutdown(self) -> None:
        self.downloader.cancel_all()
        if self._position_event is not None:
            self._position_event.cancel()
        if self.sound is not None:
            self._suppress_stop = True
            self.sound.stop()
            self.sound.unload()
            self._suppress_stop = False
        self.library.close()


class SpoytApp(App):
    def build(self):
        Builder.load_string(KV)
        self.title = "Spoyt"
        return SpoytRoot()

    def on_stop(self) -> None:
        root = self.root
        if root is not None and hasattr(root, "shutdown"):
            root.shutdown()


if __name__ == "__main__":
    SpoytApp().run()
