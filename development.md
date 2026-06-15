# Spoyt Development Notes

Bu dosya, bu noktaya kadar yapilan gelistirmeleri ve karar notlarini kaydeder.

## Hedef

Mevcut PySide6 tabanli Spotify klonunu daha kullanilabilir, modern ve Spotify'a daha yakin bir masaustu muzik uygulamasina donusturmek.

Ana hedefler:

- Muzik arama ve oynatma deneyimini iyilestirmek.
- Calma listesi olusturma, oynatma ve toplu indirme destegi eklemek.
- Indirilenler ve begenilen sarkilar bolumlerini kalici hale getirmek.
- Arama ve liste satirlarina kebap menu ile sarki aksiyonlari eklemek.
- UI'i daha modern, yuvarlak, oranli ve responsive hale getirmek.
- Player bar, modal/dialog, kart, buton ve liste satiri tasarimini sade ama kaliteli bir gorunume cekmek.
- Space tusu ile oynat/duraklat davranisini calistirmak.
- Online stream ve indirilen dosyalarda oynatma/seek davranisini duzeltmek.

## Yapilan Gelistirmeler

### 1. Kalici kutuphane sistemi

- SQLite tabanli `LibraryStore` kullanildi.
- `data/spoyt.db` icinde track, liked, playlist, playlist track, downloads ve recent tablolarinin yonetimi yapildi.
- Sarkilar `video_id` uzerinden tekil tutuluyor.
- Playlist icinde ayni sarkinin tekrar eklenmesi engellendi.
- Indirilen dosya yolu `downloads` tablosunda saklaniyor.
- Son calinanlar `recent_tracks` tablosuna kaydediliyor.

### 2. Playlist ozellikleri

- Playlist olusturma eklendi.
- Arama/listedeki sarkilar playlist'e eklenebilir hale getirildi.
- Playlist icinden sarki kaldirma eklendi.
- Playlist silme icin modern confirm dialog kullanildi.
- Playlist'i bastan oynatma eklendi.
- Playlist'teki tum eksik sarkilari toplu indirme destegi eklendi.

### 3. Begenilen sarkilar

- Sarkilar kebap menuden begenilenlere eklenip cikarilabilir.
- Begenilenler bolumu kalici SQLite verisiyle calisiyor.
- Track row durum etiketi begenildi/offline/indiriliyor bilgisini gosteriyor.

### 4. Indirilenler ve offline calis

- `yt-dlp` ile arka planda ses indirme destegi eklendi.
- Indirilen dosyalar `data/downloads/` altinda saklaniyor.
- Indirilmis sarki calinirken stream yerine lokal dosya kullaniliyor.
- Indirme durumlari search, home ve library ekranlarinda senkron guncelleniyor.
- Uygulama kapanirken aktif indirme thread'leri kontrollu kapatiliyor.

### 5. Player ve oynatma kuyrugu

- `QMediaPlayer` ve `QAudioOutput` ile gercek ses oynatma kullaniliyor.
- Arama sonuclari, playlist, begenilenler ve indirilenler icin kuyruk mantigi eklendi.
- Ileri/geri butonlari kuyruk indeksine gore calisiyor.
- Sarkinin bitmesi durumunda siradaki sarkiya geciliyor.
- Space tusu uygulama genelinde oynat/duraklat olarak calisiyor; text input odaktaysa yazmayi bozmaz.
- Online stream sorunlarinda bir kez tekrar stream cozme deneniyor.

### 6. Seek duzeltmesi

- Progress bara tiklayinca veya surukleyip birakinca gercek `setPosition` uygulanacak sekilde `SeekSlider` eklendi.
- Slider sadece gorsel olarak hareket etmiyor; hedef sureye seek istegi uretiyor.
- Pending seek korumasi ile eski pozisyon sinyali slider'i hemen geri cekmiyor.
- Kisa gecikmeyle seek uygulanmadiysa tekrar `setPosition` deneniyor.

### 7. Arama ve kebap menu

- Arama `ytmusicapi` ile anonim YouTube Music aramasi uzerinden calisiyor.
- Search row uzerinde play, like, add to playlist, download ve remove download aksiyonlari var.
- Kebap menu `QMenu` ve `QAction` ile uygulanmis durumda.

### 8. Thumbnail ve network iyilestirmeleri

- Thumbnail yukleme `QNetworkAccessManager` ile asenkron yapiliyor.
- Silinmis widget'a callback gelmesi durumunda `RuntimeError` yakalaniyor.
- Thumbnail cache eklendi.
- Ayni URL icin pending callback listesi kullanildi; ayni kapak gorseli tekrar tekrar indirilmez.
- Qt HTTP/2 thumbnail protokol hatalarini azaltmak icin request uzerinde HTTP/2 kapatildi.

### 9. Terminal log gurultusu azaltma

- `desktop_main.py` icinde `QT_LOGGING_RULES` ile `qt.network.http2` ve `qt.multimedia.ffmpeg` loglari kapatildi.
- Bu ayar `QApplication` baslamadan once set ediliyor.

### 10. UI modernizasyonu

- Sidebar logo ve uygulama iconu `assets/spoyt_logo.svg` ile guncellendi.
- Butonlar, kartlar, liste satirlari, dialoglar ve player bar daha modern koyu tema ile duzenlendi.
- `IconButton` ile play/pause/previous/next ikonlari custom paint edildi.
- Previous/next ikonlari daha temiz chevron + bar formuna cekildi.
- Modal dialoglar frameless, shadow'lu ve app stiline uygun hale getirildi.
- `style_overrides.qss` eklendi; son tasarim duzeltmeleri `style.qss` tarafindan ezilmesin diye `main.py` icinde en son yukleniyor.

### 11. Responsive duzeltmeler

- Search bar input ve Ara butonu tek kapsul icinde hizalandi.
- Library aksiyon butonlari ayni olcu ailesine cekildi.
- Library overview kartlari genislik durumuna gore kolon sayisini degistiriyor.
- Home quick kartlari once grid ile yapildi, sonra screenshot'taki overflow sorunu nedeniyle satir bazli responsive sisteme gecildi.
- Home quick kart genisligi viewport'a gore piksel olarak hesaplanir.
- Dar genislikte 1 kolon, orta genislikte 2 kolon, genis ekranlarda 3/4 kolon kullanilir.
- Quick kartlarin viewport disina tasmasi engellendi.

## Eklenen veya Guncellenen Dosyalar

- `desktop_main.py`
  - Qt logging rules eklendi.
  - `style_overrides.qss` en son yuklenecek sekilde `load_style_overrides()` eklendi.

- `style.qss`
  - Genel koyu tema ve birden cok UI pass icerir.

- `style_overrides.qss`
  - Player bar, quick card ve son UI duzeltmelerini kesin olarak uygular.

- `assets/spoyt_logo.svg`
  - Uygulama ve sidebar logosu.

- `core/library_store.py`
  - SQLite kutuphane, playlist, liked, downloads, recents store.

- `core/download_manager.py`
  - Arka planda yt-dlp indirme thread yonetimi.

- `core/stream_resolver.py`
  - yt-dlp ile stream URL cozumleme.

- `core/thumbnail_loader.py`
  - Asenkron thumbnail yukleme, cache, HTTP/2 kapatma ve guvenli callback.

- `ui/main_window.py`
  - Tum servisler, ekranlar, queue, keyboard shortcut, download ve player baglantilari.

- `ui/home_view.py`
  - Quick kartlar, recent tracks ve oneriler.
  - Satir bazli responsive quick card sistemi.

- `ui/search_view.py`
  - Search bar ve arama sonuclari.

- `ui/library_view.py`
  - Library overview, liked, downloads ve playlist sayfalari.
  - Playlist oynatma ve tumunu indirme butonlari.

- `ui/track_row.py`
  - Track row, play button, kebap menu ve state label.

- `ui/player_bar.py`
  - Player bar, QMediaPlayer, local/stream playback, SeekSlider, seek fix.

- `ui/dialogs.py`
  - Modern text input, select, confirm ve alert dialoglari.

- `ui/icon_button.py`
  - Custom painted player ve row ikonlari.

## Dogrulama Komutlari

Son kontrol komutlari:

```powershell
python -m compileall core ui tests main.py desktop_main.py
python -m unittest discover -s tests -v
```

Ek layout/seek smoke kontrolleri:

- Home quick kartlar 760, 1030, 1280 ve 1700 px genisliklerde overflow yapmiyor.
- `SeekSlider` tiklama testinde orta noktaya tiklama `150000 ms` seek istegi uretti.

## Bilinen Notlar

- YouTube Music ve YouTube stream/indirme islemleri resmi olmayan `ytmusicapi` ve `yt-dlp` araclariyla yapilir.
- Bu uygulama kisisel/egitim amaclidir; yayin veya ticari kullanim oncesi platform kosullari ve telif kurallari incelenmelidir.
- Qt Multimedia bazi codec/stream durumlarinda native FFmpeg loglari uretebilir; ana uygulamada bu loglar logging rules ile susturulmustur.

## Android / Kivy Donusum Notlari

- `main.py` Android/Buildozer icin Kivy mobil giris noktasi olarak ayrildi.
- Eski PySide6 masaustu girisi `desktop_main.py` icinde korunur.
- Qt bagimli desktop servisleri silinmedi; mobil taraf icin saf Python servisler eklendi:
  - `core/download_service.py`
  - `core/stream_service.py`
  - `core/platform_paths.py`
- Android veri dizini Kivy `user_data_dir` uzerinden app-private storage olarak secilir.
- `buildozer.spec` eklendi ve requirements alanina `kivy`, `ytmusicapi`, `yt-dlp`, `certifi`, `ffmpeg` yazildi.
- NewPipeExtractor proje icinde dogrudan kullanilmiyor; Java tabanli NewPipe ihtiyaci dogarsa `pyjnius`/JAR entegrasyonu ayrica degerlendirilmelidir.
