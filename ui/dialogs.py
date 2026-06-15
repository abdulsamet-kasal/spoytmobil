"""Custom dark dialogs that match the Spoyt UI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ModernDialog(QDialog):
    def __init__(self, title: str, subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ModernDialog")
        self.setMinimumWidth(440)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)

        self.surface = QWidget()
        self.surface.setObjectName("DialogSurface")
        shadow = QGraphicsDropShadowEffect(self.surface)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 12)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.surface.setGraphicsEffect(shadow)
        outer.addWidget(self.surface)

        self.layout = QVBoxLayout(self.surface)
        self.layout.setContentsMargins(22, 20, 22, 20)
        self.layout.setSpacing(14)

        header = QHBoxLayout()
        header.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title_label = QLabel(title)
        title_label.setObjectName("DialogTitle")
        title_box.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("DialogSubtitle")
            subtitle_label.setWordWrap(True)
            title_box.addWidget(subtitle_label)

        header.addLayout(title_box, 1)

        close_btn = QPushButton("×")
        close_btn.setObjectName("DialogCloseButton")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.reject)
        header.addWidget(close_btn)

        self.layout.addLayout(header)


class TextInputDialog(ModernDialog):
    def __init__(self, title: str, label: str, parent=None) -> None:
        super().__init__(title, "Yeni bir liste adı gir.", parent)

        self.label = QLabel(label)
        self.label.setObjectName("DialogLabel")
        self.layout.addWidget(self.label)

        self.input = QLineEdit()
        self.input.setObjectName("DialogInput")
        self.input.returnPressed.connect(self.accept)
        self.layout.addWidget(self.input)

        self._add_buttons("Oluştur", "Vazgeç")
        self.input.setFocus()

    def _add_buttons(self, accept_text: str, cancel_text: str) -> None:
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch()

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setObjectName("DialogGhostButton")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        accept_btn = QPushButton(accept_text)
        accept_btn.setObjectName("DialogPrimaryButton")
        accept_btn.clicked.connect(self.accept)
        buttons.addWidget(accept_btn)

        self.layout.addLayout(buttons)

    @classmethod
    def get_text(cls, parent, title: str, label: str) -> tuple[str, bool]:
        dialog = cls(title, label, parent)
        ok = dialog.exec() == QDialog.Accepted
        return dialog.input.text().strip(), ok


class SelectDialog(ModernDialog):
    def __init__(self, title: str, label: str, options: list[str], parent=None) -> None:
        super().__init__(title, "Şarkıyı eklemek istediğin listeyi seç.", parent)

        self.label = QLabel(label)
        self.label.setObjectName("DialogLabel")
        self.layout.addWidget(self.label)

        self.combo = QComboBox()
        self.combo.setObjectName("DialogCombo")
        self.combo.addItems(options)
        self.layout.addWidget(self.combo)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch()

        cancel_btn = QPushButton("Vazgeç")
        cancel_btn.setObjectName("DialogGhostButton")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        accept_btn = QPushButton("Ekle")
        accept_btn.setObjectName("DialogPrimaryButton")
        accept_btn.clicked.connect(self.accept)
        buttons.addWidget(accept_btn)

        self.layout.addLayout(buttons)

    @classmethod
    def get_item(
        cls,
        parent,
        title: str,
        label: str,
        options: list[str],
    ) -> tuple[str, bool]:
        dialog = cls(title, label, options, parent)
        ok = dialog.exec() == QDialog.Accepted
        return dialog.combo.currentText(), ok


class ConfirmDialog(ModernDialog):
    def __init__(self, title: str, message: str, parent=None) -> None:
        super().__init__(title, message, parent)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch()

        cancel_btn = QPushButton("Vazgeç")
        cancel_btn.setObjectName("DialogGhostButton")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        delete_btn = QPushButton("Sil")
        delete_btn.setObjectName("DialogDangerButton")
        delete_btn.clicked.connect(self.accept)
        buttons.addWidget(delete_btn)

        self.layout.addLayout(buttons)

    @classmethod
    def ask(cls, parent, title: str, message: str) -> bool:
        return cls(title, message, parent).exec() == QDialog.Accepted


class AlertDialog(ModernDialog):
    def __init__(self, title: str, message: str, parent=None) -> None:
        super().__init__(title, message, parent)

        buttons = QHBoxLayout()
        buttons.addStretch()
        ok_btn = QPushButton("Tamam")
        ok_btn.setObjectName("DialogPrimaryButton")
        ok_btn.clicked.connect(self.accept)
        buttons.addWidget(ok_btn)
        self.layout.addLayout(buttons)

    @classmethod
    def show(cls, parent, title: str, message: str) -> None:
        cls(title, message, parent).exec()
