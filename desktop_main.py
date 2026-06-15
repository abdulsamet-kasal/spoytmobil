import os
import sys

os.environ.setdefault(
    "QT_LOGGING_RULES",
    ";".join(
        [
            "qt.network.http2=false",
            "qt.multimedia.ffmpeg=false",
            "qt.multimedia.ffmpeg.*=false",
        ]
    ),
)

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_stylesheet(app: QApplication) -> None:
    style_path = os.path.join(BASE_DIR, "style.qss")
    try:
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("style.qss bulunamadi, varsayilan stil kullaniliyor.")


def load_style_overrides(app: QApplication) -> None:
    style_path = os.path.join(BASE_DIR, "style_overrides.qss")
    try:
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(app.styleSheet() + "\n" + f.read())
    except FileNotFoundError:
        pass


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Spoyt")
    app.setWindowIcon(QIcon(os.path.join(BASE_DIR, "assets", "spoyt_logo.svg")))

    load_stylesheet(app)
    load_style_overrides(app)

    window = MainWindow()
    window.resize(1280, 800)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
