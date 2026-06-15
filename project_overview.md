# Spoyt Project Overview

Bu dosya projenin genel yapisini, kullandigi kutuphaneleri, servisleri, API'leri,
dosya organizasyonunu ve temel metodlarini aciklar.

## Genel Bakis

Spoyt, PySide6 ile yazilmis Spotify benzeri bir masaustu muzik uygulamasidir.

Uygulama temel olarak:

- YouTube Music uzerinden sarki arar.
- yt-dlp ile stream URL cozer veya sarkiyi indirir.
- QMediaPlayer ile lokal veya online sesi oynatir.
- SQLite ile kullanici kutuphanesini kalici tutar.
- PySide6 UI bilesenleriyle koyu temali desktop arayuz sunar.

## Ana Teknolojiler

| Teknoloji | Kullanim |
| --- | --- |
| Python | Ana programlama dili |
| PySide6 | Masaustu UI, Qt signal/slot, QMediaPlayer, QNetworkAccessManager |
| ytmusicapi | YouTube Music anonim arama |
| yt-dlp | Stream URL cozme ve audio indirme |
| SQLite | Liked tracks, playlists, downloads, recent tracks |
| QMediaPlayer | Ses oynatma |
| QAudioOutput | Ses cikis ve volume kontrolu |
| QThread | Stream resolver ve download threadleri |
| QNetworkAccessManager | Thumbnail indirme |
| QSS | Qt stylesheet ile tema ve tasarim |

## Android / Kivy Katmani

APK hedefi icin `main.py` Kivy tabanli mobil giris noktasi olarak kullanilir.
Orijinal PySide6 masaustu uygulamasi `desktop_main.py` ile calistirilir.

Mobil katman su servisleri kullanir:

- `core/music_api.py`: YouTube Music arama mantigi korunur.
- `core/library_store.py`: SQLite kutuphane mantigi korunur, veri dizini Android'de app-private storage'a yonlenir.
- `core/stream_service.py`: Qt bagimsiz `yt-dlp` stream URL cozme.
- `core/download_service.py`: Qt bagimsiz threaded `yt-dlp` indirme.
- `core/platform_paths.py`: Desktop ve Android icin yazilabilir veri dizini secimi.

`buildozer.spec` icinde `kivy`, `ytmusicapi`, `yt-dlp`, `certifi` ve `ffmpeg`
requirements olarak tanimlidir.

## Calistirma Noktasi

### `main.py` (Android/Kivy)

Gorevleri:

- Kivy mobil uygulamasini baslatir.
- Arama, oynatma, indirme, begenilenler ve indirilenler icin dikey mobil UI sunar.
- `LibraryStore`, `MusicAPI`, `DownloadService` ve `resolve_stream_url` servislerini kullanir.
- Android'de app-private veri dizinini `core/platform_paths.py` uzerinden secer.

### `desktop_main.py` (PySide6 desktop)

Gorevleri:

- `QT_LOGGING_RULES` ayarlarini yapar.
- `QApplication` olusturur.
- `style.qss` ve `style_overrides.qss` dosyalarini yukler.
- Uygulama ikonunu `assets/spoyt_logo.svg` ile ayarlar.
- `MainWindow` olusturur ve gosterir.

Ana metodlar:

- `load_stylesheet(app)`
- `load_style_overrides(app)`
- `main()`

## Dosya Yapisi

```text
spoyt/
  main.py
  desktop_main.py
  buildozer.spec
  ANDROID_BUILD.md
  requirements.txt
  README.md
  style.qss
  style_overrides.qss
  development.md
  project_overview.md

  assets/
    spoyt_logo.svg

  core/
    __init__.py
    music_api.py
    stream_service.py
    stream_resolver.py
    download_service.py
    download_manager.py
    platform_paths.py
    library_store.py
    thumbnail_loader.py

  ui/
    __init__.py
    main_window.py
    sidebar.py
    home_view.py
    search_view.py
    library_view.py
    track_row.py
    player_bar.py
    icon_button.py
    dialogs.py

  tests/
    test_library_store.py

  data/
    spoyt.db
    downloads/
```

`__pycache__` klasorleri runtime tarafindan uretilir ve uygulama mimarisinin
parcasi degildir.

## Core Katmani

### `core/music_api.py`

YouTube Music aramasini saran ince servis katmanidir.

Kullandigi kutuphane:

- `ytmusicapi.YTMusic`

Ana sinif:

- `MusicAPI`

Ana metod:

- `search(query, filter_type="songs", limit=20)`

Donen track formati:

```python
{
    "video_id": "...",
    "title": "...",
    "artist": "...",
    "duration": "...",
    "thumbnail": "..."
}
```

### `core/stream_resolver.py`

Online oynatma icin YouTube video ID'sinden gercek audio stream URL'si cozer.

Kullandigi kutuphane:

- `yt_dlp.YoutubeDL`
- `PySide6.QtCore.QThread`

Ana sinif:

- `StreamResolverThread`

Signal'lar:

- `resolved(video_id, stream_url)`
- `error(message)`

Ana metod:

- `run()`

yt-dlp format tercihi:

```text
bestaudio[ext=m4a]/bestaudio[acodec^=mp4a]/bestaudio/best
```

### `core/download_manager.py`

App icinde offline playback icin audio indirir.

Kullandigi kutuphane:

- `yt_dlp.YoutubeDL`
- `QThread`
- `QObject`

Ana siniflar:

- `DownloadThread`
- `DownloadManager`

`DownloadThread` signal'lari:

- `progress(video_id, percent, label)`
- `completed(video_id, file_path)`
- `failed(video_id, message)`

`DownloadManager` signal'lari:

- `download_started(track)`
- `download_progress(video_id, percent, label)`
- `download_completed(track, file_path)`
- `download_failed(track, message)`

Ana metodlar:

- `start_download(track)`
- `cancel_all()`
- `is_downloading(video_id)`
- `active_video_ids()`

### `core/library_store.py`

SQLite tabanli kalici kutuphane servisidir.

Kullandigi kutuphane:

- `sqlite3`
- `pathlib.Path`

Varsayilan veri dizini:

```text
data/
```

Varsayilan veritabani:

```text
data/spoyt.db
```

Indirme dizini:

```text
data/downloads/
```

SQLite tablolari:

- `tracks`
- `liked_tracks`
- `playlists`
- `playlist_tracks`
- `downloads`
- `recent_tracks`

Ana metod gruplari:

- Track:
  - `ensure_track(track)`
  - `get_track(video_id)`
  - `hydrate_track(track)`

- Liked:
  - `toggle_liked(track)`
  - `like_track(track)`
  - `unlike_track(video_id)`
  - `is_liked(video_id)`
  - `list_liked_tracks()`

- Playlist:
  - `create_playlist(name)`
  - `list_playlists()`
  - `get_playlist(playlist_id)`
  - `delete_playlist(playlist_id)`
  - `add_to_playlist(playlist_id, track)`
  - `remove_from_playlist(playlist_id, video_id)`
  - `get_playlist_tracks(playlist_id)`

- Downloads:
  - `mark_downloaded(track, file_path)`
  - `remove_download(video_id, delete_file=True)`
  - `is_downloaded(video_id)`
  - `get_download_path(video_id)`
  - `list_downloads()`

- Recents:
  - `record_played(track)`
  - `list_recent_tracks(limit=8)`

- Summary:
  - `get_summary()`

### `core/thumbnail_loader.py`

Kapak gorsellerini asenkron yukler.

Kullandigi PySide6 siniflari:

- `QNetworkAccessManager`
- `QNetworkRequest`
- `QPixmap`

Ozellikler:

- HTTP/2 request attribute kapatildi.
- User-Agent header eklendi.
- URL bazli cache var.
- Ayni URL icin pending callback listesi var.
- Widget silindiyse callback `RuntimeError` yakalar.

Ana sinif:

- `ThumbnailLoader`

Ana metodlar:

- `instance()`
- `load(url, callback)`
- `_on_finished(url, reply)`
- `_safe_callback(callback, pixmap)`

## UI Katmani

### `ui/main_window.py`

Uygulamanin ana orkestrasyon katmanidir.

Olusturdugu servisler:

- `MusicAPI`
- `LibraryStore`
- `DownloadManager`

Olusturdugu view'lar:

- `Sidebar`
- `HomeView`
- `SearchView`
- `LibraryView`
- `PlayerBar`

Ana sorumluluklar:

- Sayfa gecisleri.
- Signal/slot baglantilari.
- Playback queue ve next/previous.
- Track action yonetimi.
- Playlist olusturma/silme.
- Download baslatma ve download durumlarini UI'a yansitma.
- Space tusu ile play/pause.
- Uygulama kapanisinda thread ve store temizligi.

Ana metodlar:

- `_connect_signals()`
- `_change_page(page_id)`
- `_open_collection(kind, identifier)`
- `_play_track(track, results_list)`
- `_play_collection(tracks)`
- `_play_track_now(track)`
- `_play_next()`
- `_play_prev()`
- `_handle_track_action(action, track)`
- `_download_tracks(tracks)`
- `_add_track_to_playlist(track)`
- `_create_playlist(show_playlist=True)`
- `_delete_playlist(playlist_id)`
- `_start_download(track, quiet=False)`
- `_refresh_library_surfaces(video_id=None)`
- `eventFilter(obj, event)`
- `closeEvent(event)`

### `ui/sidebar.py`

Sol navigasyon panelidir.

Icerik:

- Logo ve app adi.
- Ana Sayfa, Ara, Kitapligin, Begenilen Sarkilar, Indirilenler.
- Yeni Calma Listesi butonu.
- Gercek playlist listesi.

Ana signal'lar:

- `page_changed(page_id)`
- `playlist_selected(playlist_id)`
- `create_playlist_requested()`

### `ui/home_view.py`

Ana sayfa ekranidir.

Icerik:

- Gunaydin basligi.
- Quick card'lar: Begenilenler, Indirilenler, playlistler, Yeni Calma Listesi.
- Yakinlarda Calinanlar.
- Oneri raflari.

Responsive davranis:

- Quick kart genisligi viewport'a gore hesaplanir.
- Dar ekranda 1 kolon, orta ekranda 2 kolon, genis ekranda 3/4 kolon.
- Kartlar satir bazli `QHBoxLayout` ile dizilir.
- Kart overflow'u engellenir.

Ana metodlar:

- `load_recommendations()`
- `refresh_dynamic_sections()`
- `_add_quick_button(...)`
- `_configure_quick_button(button)`
- `_add_quick_widget(widget)`
- `_finish_quick_rows()`
- `_quick_column_count()`
- `_quick_layout_width()`
- `_quick_card_width_for_columns(columns)`
- `resizeEvent(event)`

### `ui/search_view.py`

Arama sayfasidir.

Icerik:

- Tek kapsul icinde search input ve Ara butonu.
- Arama status label.
- Sonuc listesi.

Servis:

- `MusicAPI.search()`

Signal'lar:

- `track_selected(track, queue)`
- `track_action_requested(action, track)`

Ana metodlar:

- `perform_search()`
- `refresh_track_state(video_id=None)`
- `set_download_in_progress(video_id, in_progress)`
- `_create_row(track, index=None)`

### `ui/library_view.py`

Kutuphane, Begenilenler, Indirilenler ve Playlist sayfalarini yonetir.

Icerik:

- Header title/subtitle.
- Play, Tumunu Indir, Sil, Calma Listesi aksiyon butonlari.
- Overview card grid.
- Track collection listeleri.

Signal'lar:

- `track_selected(track, queue)`
- `track_action_requested(action, track)`
- `collection_requested(kind, identifier)`
- `create_playlist_requested()`
- `delete_playlist_requested(playlist_id)`
- `play_collection_requested(tracks)`
- `download_collection_requested(tracks)`

Ana metodlar:

- `show_overview()`
- `show_liked()`
- `show_downloads()`
- `show_playlist(playlist_id)`
- `refresh_current()`
- `_render_track_collection(...)`
- `_create_collection_button(...)`
- `_arrange_header_buttons()`
- `_card_column_count()`

### `ui/track_row.py`

Tek sarki satiri bilesenidir.

Icerik:

- Index.
- Thumbnail.
- Title/artist.
- State label: begenildi, offline, indiriliyor.
- Play button.
- Kebap menu.

Signal'lar:

- `play_requested(track)`
- `action_requested(action, track)`

Kebap menu aksiyonlari:

- `play`
- `toggle_like`
- `add_to_playlist`
- `download`
- `remove_download`
- `remove_from_playlist`

Ana metodlar:

- `set_state(liked=None, downloaded=None, downloading=None)`
- `_show_menu()`
- `_add_action(menu, label, action_id)`
- `_set_thumbnail(pixmap)`

### `ui/player_bar.py`

Alt player bar ve ses oynatma katmanidir.

Kullandigi PySide6 siniflari:

- `QMediaPlayer`
- `QAudioOutput`
- `QSlider`
- `QTimer`
- `QUrl`

Ana siniflar:

- `SeekSlider`
- `PlayerBar`

`SeekSlider`:

- Progress bara tiklayinca hedef degeri hesaplar.
- Surukleme sirasinda slider'i gunceller.
- Birakinca `seek_requested(position)` signal'i uretir.

`PlayerBar`:

- Lokal dosya varsa lokal oynatir.
- Lokal dosya yoksa `StreamResolverThread` ile stream URL cozer.
- Volume kontrolu yapar.
- Duration/position label'larini gunceller.
- Seek icin pending seek korumasi kullanir.

Ana metodlar:

- `play_track(track)`
- `_start_stream_resolver(video_id)`
- `_cancel_resolvers(wait=False)`
- `_on_stream_resolved(video_id, stream_url)`
- `_on_player_error(error, message)`
- `toggle_play()`
- `shutdown()`
- `_on_position_changed(position)`
- `_seek(position)`
- `_ensure_seek_applied(position)`
- `_set_volume(value)`

### `ui/dialogs.py`

Modern dialog bilesenleri.

Siniflar:

- `ModernDialog`
- `TextInputDialog`
- `SelectDialog`
- `ConfirmDialog`
- `AlertDialog`

Kullanim alanlari:

- Playlist olusturma.
- Playlist secme.
- Playlist silme onayi.
- Hata ve bilgi mesaji.

### `ui/icon_button.py`

Custom cizimli buton ve volume ikonu.

Siniflar:

- `IconButton`
- `VolumeIcon`

Desteklenen ikonlar:

- `play`
- `pause`
- `previous`
- `next`

## Stil Sistemi

### `style.qss`

Ana koyu tema dosyasidir. Sidebar, buton, kart, track row, menu, dialog, slider ve player stillerini icerir.

### `style_overrides.qss`

Son duzeltme katmanidir. `desktop_main.py` tarafindan `style.qss` sonrasinda yuklenir.

Kullanim amaci:

- Onceki QSS bloklari son tasarim kararlarini ezmesin.
- Player bar daha sade kalsin.
- Quick card yukseklik/genislik davranisi korunabilsin.

## Veri Akisi

### Arama ve oynatma

1. Kullanici `SearchView` icinde arama yapar.
2. `MusicAPI.search()` YouTube Music sonucunu normalize eder.
3. Her sonuc `TrackRow` olarak gosterilir.
4. Kullanici play yaparsa `MainWindow._play_track()` kuyrugu kurar.
5. `LibraryStore.hydrate_track()` lokal dosya varsa `local_path` ekler.
6. `PlayerBar.play_track()` lokal dosyayi veya stream URL'yi oynatir.

### Playlist'e ekleme

1. `TrackRow` kebap menu `add_to_playlist` aksiyonu uretir.
2. `MainWindow._add_track_to_playlist()` playlist secimi veya yeni playlist dialogu acar.
3. `LibraryStore.add_to_playlist()` track'i kaydeder.
4. Sidebar ve library ekranlari refresh edilir.

### Indirme

1. Kullanici kebap menuden indir der veya collection tumunu indir butonuna basar.
2. `MainWindow._start_download()` `DownloadManager.start_download()` cagirir.
3. `DownloadThread` yt-dlp ile audio indirir.
4. Tamamlaninca `LibraryStore.mark_downloaded()` dosya yolunu kaydeder.
5. UI state offline olarak guncellenir.

### Seek

1. Kullanici seek slider'a tiklar veya surukler.
2. `SeekSlider` hedef pozisyonu hesaplar.
3. `PlayerBar._seek()` `QMediaPlayer.setPosition()` uygular.
4. Pending seek korumasi eski position sinyallerinin slider'i geri cekmesini engeller.
5. Gerekirse kisa gecikmeyle seek tekrar denenir.

## Testler

Test dosyasi:

```text
tests/test_library_store.py
```

Kapsam:

- Liked tracks persist.
- Playlist add/remove/duplicate.
- Download record hydrate/remove file.

Komutlar:

```powershell
python -m compileall core ui tests main.py desktop_main.py
python -m unittest discover -s tests -v
```

## Runtime Dosyalari

Bu dosyalar uygulama calisirken olusur:

- `data/spoyt.db`
- `data/downloads/*.m4a`
- `__pycache__/`

## Dis Servis ve Platform Notlari

- Arama YouTube Music uzerinden `ytmusicapi` ile yapilir.
- Stream URL ve indirme YouTube kaynaklari uzerinden `yt-dlp` ile yapilir.
- Bu servisler resmi Spotify API'si degildir.
- Proje Spotify markasini birebir kullanmaz; Spotify benzeri UI/UX klonudur.
