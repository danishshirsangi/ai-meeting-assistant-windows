"""Translucent workspace chrome and application-wide tooltip suppression."""
from PySide6.QtCore import QObject, QEvent, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QToolTip


def background_alpha(active, amount):
    # A nonzero alpha preserves hit testing on Windows layered windows.
    return max(1, round(255 * (1 - max(0, min(100, amount)) / 100))) if active else 255


class NoTooltips(QObject):
    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.ToolTip:
            QToolTip.hideText()
            event.accept()
            return True
        return super().eventFilter(watched, event)


class TitleBar(QWidget):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setObjectName("windowTitleBar")
        self.setStyleSheet("QWidget#windowTitleBar { background: #102219; border-bottom: 1px solid #28573b; }")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 3, 5, 3)
        label = QLabel("AI Meeting Assistant")
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        row.addWidget(label)
        row.addStretch()
        maximize = QPushButton("□")
        maximize.setAccessibleName("Maximize or restore window")
        maximize.clicked.connect(self.toggle_maximize)
        close = QPushButton("×")
        close.setAccessibleName("Close application")
        close.setStyleSheet("QPushButton { background: #a62d38; color: white; padding: 3px 12px; }")
        close.clicked.connect(window.close)
        row.addWidget(maximize)
        row.addWidget(close)

    def toggle_maximize(self):
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window.windowHandle()
            if handle is not None:
                handle.startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
