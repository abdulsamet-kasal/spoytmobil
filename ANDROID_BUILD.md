# Android Build Notes

This project now has two entry points:

- `main.py`: Kivy mobile app used by Buildozer.
- `desktop_main.py`: original PySide6 desktop app.

## What Changed For Android

- The mobile UI is implemented with Kivy widgets in `main.py`.
- Qt-dependent downloader and stream resolver classes were left in place for the desktop app.
- Android/mobile code uses pure Python services:
  - `core/download_service.py`
  - `core/stream_service.py`
  - `core/platform_paths.py`
- App data is written to Kivy's app-private `user_data_dir` on Android. This maps to app-private storage under Android/data and avoids relying on broad shared storage access for normal downloads.
- `buildozer.spec` includes `ffmpeg` as requested. The first package attempt may still expose recipe or transitive dependency issues around `yt-dlp`; if that happens, use a custom python-for-android recipe or move stream/download resolution to a small REST backend.

## Build

Buildozer works best from Linux or WSL:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip buildozer cython
buildozer -v android debug
```

## Build Without Local WSL

Native Windows cannot build the Android target with Buildozer. If you want to
avoid downloading WSL files locally, use the included GitHub Actions workflow:

```text
.github/workflows/android-debug.yml
```

Push the project to GitHub, open the repository's Actions tab, run
`Android Debug APK`, then download the `spoyt-debug-apk` artifact from the
completed workflow run. The downloads happen on GitHub's Linux runner instead
of this computer.

Other no-WSL options:

- Docker Desktop with the Buildozer image, but Docker on Windows usually still
  uses WSL2 internally and downloads a large Linux image.
- A Linux VPS/cloud machine, then run `buildozer -v android debug` there.
- Rewriting the app as a native Android/Kotlin project, which avoids Buildozer
  but is a much larger rewrite and does not preserve the Python backend as-is.

This machine also has a local Buildozer source checkout at:

```text
C:\Users\abdul\Desktop\kivy-buildozer-b4ae422
```

It can be installed from source into a Python environment:

```powershell
python -m venv .buildozer-venv
.\.buildozer-venv\Scripts\python.exe -m pip install -e C:\Users\abdul\Desktop\kivy-buildozer-b4ae422
.\.buildozer-venv\Scripts\buildozer.exe --version
```

However, Android builds still need Linux, WSL, or Docker. The local Buildozer
source raises `Windows platform not yet working for Android` when importing the
Android target on native Windows. On this machine, WSL and Docker were not found,
so the APK build cannot be completed here until one of those environments is
installed.

With Docker installed, the local Buildozer checkout can be used like this:

```powershell
cd C:\Users\abdul\Desktop\kivy-buildozer-b4ae422
docker build --tag=kivy/buildozer .
cd C:\Users\abdul\Desktop\spoytmobil
docker run --interactive --tty --rm `
  --volume "$env:USERPROFILE\.buildozer:/home/user/.buildozer" `
  --volume "${PWD}:/home/user/hostcwd" `
  kivy/buildozer android debug
```

The same commands are also available as project scripts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\check_android_build_env.ps1
powershell -ExecutionPolicy Bypass -File scripts\build_android_docker.ps1
```

Inside WSL/Ubuntu:

```bash
bash scripts/build_android_wsl.sh
```

The debug APK is usually created under:

```text
bin/spoyt-0.1.0-arm64-v8a_armeabi-v7a-debug.apk
```

## Install And Test

Connect a device with USB debugging enabled, then run:

```bash
buildozer android deploy run logcat
```

Manual smoke test:

1. Launch Spoyt.
2. Search for a track.
3. Play a result.
4. Like the result.
5. Download the result.
6. Open Library, check Liked and Downloads.
7. Relaunch the app and confirm the library data persists.

## Known Android Risks

- `yt-dlp` is pure Python, but python-for-android does not guarantee a first-party recipe for every release. Keep `yt-dlp` current and expect to troubleshoot extractor dependencies.
- Remote stream playback through Kivy's `SoundLoader` can vary by Android device and audio provider. Offline downloaded m4a playback is the more reliable path.
- NewPipeExtractor is not currently used by this codebase. If a Java NewPipeExtractor integration is added later, package it through Gradle/JAR and call it through `pyjnius`; this is more brittle than the current `yt-dlp` path.
