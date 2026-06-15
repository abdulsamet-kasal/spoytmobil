"""Platform-aware storage paths for desktop and Android builds."""

from __future__ import annotations

from pathlib import Path


def get_data_dir(app_name: str = "spoyt") -> Path:
    """Return a writable app data directory.

    On Android/Kivy this is the app-private storage directory under
    Android/data, which avoids broad shared-storage permissions. On desktop it
    falls back to the existing project-level data directory.
    """
    try:
        from kivy.app import App

        app = App.get_running_app()
        if app is not None and getattr(app, "user_data_dir", None):
            path = Path(app.user_data_dir)
            path.mkdir(parents=True, exist_ok=True)
            return path
    except Exception:
        pass

    try:
        from android.storage import app_storage_path

        path = Path(app_storage_path()) / app_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        pass

    path = Path(__file__).resolve().parents[1] / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path
