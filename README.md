# Spoyt - Spotify Clone (PySide6)

PySide6 ile geliştirilmiş, Spotify benzeri masaüstü müzik uygulaması. Arama
için `ytmusicapi`, stream ve app içi offline indirme için `yt-dlp` kullanır.

## Özellikler

- Spotify benzeri koyu tema, sol navigasyon, içerik alanı ve alt player bar
- YouTube Music üzerinden şarkı arama
- Arama ve liste satırlarında kebap menü: beğen, çalma listesine ekle, indir
- Yerel çalma listesi oluşturma, listeye şarkı ekleme/kaldırma
- Çalma listesini tek tuşla oynatma ve tüm eksik şarkılarını indirme
- Beğenilen Şarkılar ve İndirilenler bölümleri
- App içi offline indirme ve indirilen dosyadan çalma
- Space tuşu ile oynat/duraklat
- Ana sayfada hızlı kütüphane kartları, son çalınanlar ve öneri rafları
- Kalıcı veri: `data/spoyt.db` ve `data/downloads/`

## Kurulum

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Çalıştırma

Desktop PySide6 app:

```bash
python desktop_main.py
```

Kivy mobile UI local preview:

```bash
python main.py
```

## Android APK

Buildozer uses `main.py` as the Android/Kivy entry point. Build from Linux or
WSL:

```bash
pip install buildozer cython
buildozer -v android debug
```

See `ANDROID_BUILD.md` for deploy, logcat, and smoke-test steps.

## Test

```bash
python -m compileall .
python -m unittest discover -s tests -v
```

## Proje Yapısı

```text
core/
  music_api.py          # ytmusicapi arama sarmalayıcısı
  stream_resolver.py    # yt-dlp ile stream URL çözme
  download_manager.py   # arka planda app içi indirme
  library_store.py      # SQLite kütüphane/playlist/download store
  thumbnail_loader.py   # asenkron kapak görseli yükleme
ui/
  main_window.py        # tüm servis ve ekran bağlantıları
  home_view.py          # ana sayfa
  search_view.py        # arama sayfası
  library_view.py       # kütüphane, beğenilenler, indirilenler, playlistler
  track_row.py          # şarkı satırı ve kebap menü
  sidebar.py            # navigasyon ve gerçek playlist listesi
  player_bar.py         # player bar ve offline/stream oynatma
```

## Not

Bu proje kişisel/eğitim amaçlıdır. YouTube/YouTube Music içeriğine resmi
olmayan araçlarla erişir; herkese açık dağıtım veya ticari kullanım öncesinde
ilgili platformların kullanım şartlarını ve telif kurallarını inceleyin.
