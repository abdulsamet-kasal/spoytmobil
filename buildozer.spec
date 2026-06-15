[app]

title = Spoyt
package.name = spoyt
package.domain = org.spoyt

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,svg,txt,md
source.exclude_dirs = tests,bin,venv,.venv,__pycache__,data,data/downloads

version = 0.1.0
orientation = portrait
fullscreen = 0

requirements = python3,kivy,ytmusicapi,yt-dlp,certifi,ffmpeg

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_AUDIO
android.api = 35
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a
android.allow_backup = False

log_level = 2
warn_on_root = 1

[buildozer]

log_level = 2
warn_on_root = 1
