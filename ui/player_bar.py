"""Alt taraftaki Spotify benzeri çalma çubuğu.

QMediaPlayer ile gerçek ses çalar; çalınacak şarkının akış (stream) URL'si
yt-dlp aracılığıyla (StreamResolverThread) arka planda çözülür.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSlider,
    QSizePolicy,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from ui.icon_button import IconButton, VolumeIcon
from core.library_store import LibraryStore
from core.stream_resolver import StreamResolverThread
from core.thumbnail_loader import ThumbnailLoader


def format_ms(milliseconds: int) -> str:
    total_seconds = int(milliseconds / 1000)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


class SeekSlider(QSlider):
    seek_requested = Signal(int)

    def _value_from_event(self, event) -> int:
        position = event.position().x() if hasattr(event, "position") else event.x()
        return QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            int(position),
            max(1, self.width()),
        )

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            value = self._value_from_event(event)
            self.setSliderDown(True)
            self.setValue(value)
            self.seek_requested.emit(value)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.isSliderDown():
            value = self._value_from_event(event)
            self.setValue(value)
            self.sliderMoved.emit(value)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.isSliderDown():
            value = self._value_from_event(event)
            self.setValue(value)
            self.setSliderDown(False)
            self.seek_requested.emit(value)
            self.sliderReleased.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)


class PlayerBar(QWidget):
    track_finished = Signal()

    def __init__(self, library_store: LibraryStore | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("PlayerBar")
        self.setFixedHeight(88)

        self.library_store = library_store
        self.current_track: dict | None = None
        self._resolver_thread: StreamResolverThread | None = None
        self._resolver_threads: list[StreamResolverThread] = []
        self._stream_retry_count = 0
        self._pending_seek_position: int | None = None

        # --- Ses altyapısı ---
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 8, 18, 8)
        layout.setSpacing(14)

        # ----------------------------------------------------------------
        # Sol: şu an çalan şarkı bilgisi
        # ----------------------------------------------------------------
        info_layout = QHBoxLayout()
        info_layout.setSpacing(10)

        self.thumb_label = QLabel()
        self.thumb_label.setObjectName("Thumbnail")
        self.thumb_label.setFixedSize(52, 52)
        self.thumb_label.setScaledContents(True)
        info_layout.addWidget(self.thumb_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.title_label = QLabel("Çalan şarkı yok")
        self.title_label.setObjectName("NowPlayingTitle")

        self.artist_label = QLabel("")
        self.artist_label.setObjectName("NowPlayingArtist")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.artist_label)
        info_layout.addLayout(text_layout)

        info_container = QWidget()
        info_container.setObjectName("NowPlayingPanel")
        info_container.setLayout(info_layout)
        info_container.setMinimumWidth(230)
        info_container.setMaximumWidth(340)
        info_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(info_container, 1)

        # ----------------------------------------------------------------
        # Orta: kontroller + ilerleme çubuğu
        # ----------------------------------------------------------------
        center_container = QWidget()
        center_container.setObjectName("PlayerCenterPanel")
        center_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(12, 0, 12, 0)
        center_layout.setSpacing(3)

        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(16)

        self.prev_btn = IconButton("previous")
        self.prev_btn.setObjectName("ControlButton")

        self.play_btn = IconButton("play", icon_color="#050505")
        self.play_btn.setObjectName("PlayButtonMain")

        self.next_btn = IconButton("next")
        self.next_btn.setObjectName("ControlButton")

        buttons_layout.addWidget(self.prev_btn)
        buttons_layout.addWidget(self.play_btn)
        buttons_layout.addWidget(self.next_btn)
        center_layout.addLayout(buttons_layout)

        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)

        self.elapsed_label = QLabel("0:00")
        self.elapsed_label.setObjectName("TimeLabel")
        self.elapsed_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("TimeLabel")

        self.seek_slider = SeekSlider(Qt.Horizontal)
        self.seek_slider.setObjectName("SeekSlider")
        self.seek_slider.setRange(0, 0)

        progress_layout.addWidget(self.elapsed_label)
        progress_layout.addWidget(self.seek_slider)
        progress_layout.addWidget(self.duration_label)
        center_layout.addLayout(progress_layout)

        layout.addWidget(center_container, 2)

        # ----------------------------------------------------------------
        # Sağ: ses seviyesi
        # ----------------------------------------------------------------
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)

        volume_icon = VolumeIcon()

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setObjectName("VolumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMinimumWidth(86)
        self.volume_slider.setMaximumWidth(132)
        self.volume_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)

        volume_container = QWidget()
        volume_container.setObjectName("VolumePanel")
        volume_container.setLayout(volume_layout)
        volume_container.setMinimumWidth(144)
        volume_container.setMaximumWidth(178)
        volume_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout.addWidget(volume_container)

        # ----------------------------------------------------------------
        # Bağlantılar
        # ----------------------------------------------------------------
        self.play_btn.clicked.connect(self.toggle_play)
        self.volume_slider.valueChanged.connect(self._set_volume)
        self.seek_slider.sliderMoved.connect(self._preview_seek)
        self.seek_slider.sliderReleased.connect(self._seek_to_slider_value)
        self.seek_slider.seek_requested.connect(self._seek)

        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_player_error)

        self._set_volume(self.volume_slider.value())

    # ----------------------------------------------------------------
    # Genel API
    # ----------------------------------------------------------------
    def play_track(self, track: dict) -> None:
        """Verilen şarkıyı çalmaya başlar.

        Önce arayüzü güncelleyip "yükleniyor" durumunu gösterir, ardından
        gerçek akış URL'sini arka planda çözer.
        """
        self.current_track = track
        self._stream_retry_count = 0

        title = track.get("title", "Bilinmiyor")
        self.title_label.setText(f"{title} (yükleniyor...)")
        self.artist_label.setText(track.get("artist", ""))
        self.thumb_label.setPixmap(QPixmap())

        thumb_url = track.get("thumbnail")
        if thumb_url:
            ThumbnailLoader.instance().load(thumb_url, self.thumb_label.setPixmap)

        local_path = track.get("local_path")
        if not local_path and self.library_store is not None:
            local_path = self.library_store.get_download_path(track["video_id"])

        if local_path and Path(local_path).exists():
            self._cancel_resolvers()
            self.title_label.setText(title)
            self.player.setSource(QUrl.fromLocalFile(str(local_path)))
            self.player.play()
            return

        self._start_stream_resolver(track["video_id"])

    # ----------------------------------------------------------------
    # İç yardımcılar
    # ----------------------------------------------------------------
    def _start_stream_resolver(self, video_id: str) -> None:
        self._cancel_resolvers()

        thread = StreamResolverThread(video_id)
        self._resolver_thread = thread
        self._resolver_threads.append(thread)
        thread.resolved.connect(self._on_stream_resolved)
        thread.error.connect(self._on_resolve_error)
        thread.finished.connect(lambda t=thread: self._on_resolver_finished(t))
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _cancel_resolvers(self, wait: bool = False) -> None:
        for thread in list(self._resolver_threads):
            if thread.isRunning():
                thread.requestInterruption()
                if wait:
                    thread.wait()
            if not thread.isRunning():
                self._on_resolver_finished(thread)

    def _on_resolver_finished(self, thread: StreamResolverThread) -> None:
        if thread in self._resolver_threads:
            self._resolver_threads.remove(thread)
        if self._resolver_thread is thread:
            self._resolver_thread = None

    def _on_stream_resolved(self, video_id: str, stream_url: str) -> None:
        if not self.current_track or self.current_track.get("video_id") != video_id:
            return  # Kullanıcı başka bir şarkıya geçmiş olabilir

        self.title_label.setText(self.current_track.get("title", "Bilinmiyor"))
        self.player.setSource(QUrl(stream_url))
        self.player.play()

    def _on_resolve_error(self, message: str) -> None:
        self.title_label.setText("Akış alınamadı")
        self.artist_label.setText(message[:80])

    def _on_player_error(self, error, message: str) -> None:
        if error == QMediaPlayer.Error.NoError or not self.current_track:
            return

        video_id = self.current_track.get("video_id")
        local_path = self.current_track.get("local_path")
        if not local_path and self.library_store is not None and video_id:
            local_path = self.library_store.get_download_path(video_id)

        if not local_path and video_id and self._stream_retry_count < 1:
            self._stream_retry_count += 1
            self.title_label.setText(
                f"{self.current_track.get('title', 'Bilinmiyor')} (yeniden deneniyor...)"
            )
            self._start_stream_resolver(video_id)
            return

        self.title_label.setText("Çalma hatası")
        self.artist_label.setText((message or "Ses kaynağı oynatılamadı.")[:80])

    def toggle_play(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def shutdown(self) -> None:
        self.player.stop()
        self.player.setSource(QUrl())
        self._cancel_resolvers(wait=True)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.set_icon("pause")
        else:
            self.play_btn.set_icon("play")

    def _on_duration_changed(self, duration: int) -> None:
        self.seek_slider.setRange(0, duration)
        self.duration_label.setText(format_ms(duration))

    def _on_position_changed(self, position: int) -> None:
        if (
            self._pending_seek_position is not None
            and abs(position - self._pending_seek_position) > 1500
        ):
            return
        if (
            self._pending_seek_position is not None
            and abs(position - self._pending_seek_position) <= 1500
        ):
            self._pending_seek_position = None
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self.elapsed_label.setText(format_ms(position))

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.track_finished.emit()

    def _preview_seek(self, position: int) -> None:
        self.elapsed_label.setText(format_ms(position))

    def _seek_to_slider_value(self) -> None:
        self._seek(self.seek_slider.value())

    def _seek(self, position: int) -> None:
        maximum = self.seek_slider.maximum()
        if maximum <= 0:
            return
        position = max(self.seek_slider.minimum(), min(position, maximum))
        self._pending_seek_position = position
        self.seek_slider.setValue(position)
        self.elapsed_label.setText(format_ms(position))
        self.player.setPosition(position)
        QTimer.singleShot(180, lambda p=position: self._ensure_seek_applied(p))

    def _ensure_seek_applied(self, position: int) -> None:
        if self._pending_seek_position != position:
            return
        if abs(self.player.position() - position) > 1500:
            self.player.setPosition(position)
            QTimer.singleShot(300, lambda p=position: self._clear_pending_seek(p))
            return
        self._pending_seek_position = None

    def _clear_pending_seek(self, position: int) -> None:
        if self._pending_seek_position == position:
            self._pending_seek_position = None

    def _set_volume(self, value: int) -> None:
        self.audio_output.setVolume(value / 100)
