"""Translucent workspace chrome and application-wide tooltip suppression."""
from PySide6.QtCore import QObject, QEvent, Qt, QRect
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QToolTip, QGridLayout


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


def resized_geometry(original, delta, edges, minimum, maximum):
    """Resize from selected edges while keeping the opposite edge anchored."""
    x, y, w, h = original.x(), original.y(), original.width(), original.height()
    left = bool(edges & Qt.Edge.LeftEdge)
    right = bool(edges & Qt.Edge.RightEdge)
    top = bool(edges & Qt.Edge.TopEdge)
    bottom = bool(edges & Qt.Edge.BottomEdge)
    if left or right:
        width = max(minimum.width(), min(maximum.width(), w + (-delta.x() if left else delta.x())))
        if left:
            x += w - width
        w = width
    if top or bottom:
        height = max(minimum.height(), min(maximum.height(), h + (-delta.y() if top else delta.y())))
        if top:
            y += h - height
        h = height
    return QRect(x, y, w, h)


class ResizeHandle(QWidget):
    """A dedicated nontransparent resize target for frameless Windows."""
    def __init__(self, window, edges, parent=None):
        super().__init__(parent)
        self.window = window
        self.edges = edges
        self._start = None
        horizontal = bool(edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge))
        vertical = bool(edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge))
        if horizontal and vertical:
            same = bool(edges & Qt.Edge.LeftEdge) == bool(edges & Qt.Edge.TopEdge)
            cursor = Qt.CursorShape.SizeFDiagCursor if same else Qt.CursorShape.SizeBDiagCursor
        elif horizontal:
            cursor = Qt.CursorShape.SizeHorCursor
        else:
            cursor = Qt.CursorShape.SizeVerCursor
        self.setCursor(cursor)
        self.setObjectName("resizeHandle")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#resizeHandle { background-color: rgba(40, 87, 59, 110); }")
        if horizontal:
            self.setFixedWidth(7)
        if vertical:
            self.setFixedHeight(7)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or self.window.isMaximized():
            return super().mousePressEvent(event)
        handle = self.window.windowHandle()
        if handle is not None and handle.startSystemResize(self.edges):
            event.accept()
            return
        self._start = (event.globalPosition().toPoint(), self.window.geometry())
        self.grabMouse()
        event.accept()

    def mouseMoveEvent(self, event):
        if self._start is None:
            return super().mouseMoveEvent(event)
        if not event.buttons() & Qt.MouseButton.LeftButton:
            self._finish()
            return
        point, original = self._start
        minimum = self.window.minimumSize().expandedTo(self.window.minimumSizeHint())
        self.window.setGeometry(resized_geometry(original, event.globalPosition().toPoint() - point,
                                                  self.edges, minimum, self.window.maximumSize()))
        event.accept()

    def _finish(self):
        if self._start is not None:
            self._start = None
            self.releaseMouse()

    def mouseReleaseEvent(self, event):
        self._finish()
        super().mouseReleaseEvent(event)

    def hideEvent(self, event):
        self._finish()
        super().hideEvent(event)


class ResizableFrame(QWidget):
    def __init__(self, window, content):
        super().__init__(window)
        self.window = window
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        grid.addWidget(content, 1, 1)
        grid.setRowStretch(1, 1)
        grid.setColumnStretch(1, 1)
        self.handles = []
        for row, column, edges in (
            (0, 0, Qt.Edge.TopEdge | Qt.Edge.LeftEdge),
            (0, 1, Qt.Edge.TopEdge),
            (0, 2, Qt.Edge.TopEdge | Qt.Edge.RightEdge),
            (1, 0, Qt.Edge.LeftEdge),
            (1, 2, Qt.Edge.RightEdge),
            (2, 0, Qt.Edge.BottomEdge | Qt.Edge.LeftEdge),
            (2, 1, Qt.Edge.BottomEdge),
            (2, 2, Qt.Edge.BottomEdge | Qt.Edge.RightEdge),
        ):
            handle = ResizeHandle(window, edges, self)
            grid.addWidget(handle, row, column)
            self.handles.append(handle)
        window.installEventFilter(self)

    def eventFilter(self, watched, event):
        if watched is self.window and event.type() == QEvent.Type.WindowStateChange:
            visible = not (self.window.isMaximized() or self.window.isFullScreen())
            for handle in self.handles:
                handle.setVisible(visible)
        return super().eventFilter(watched, event)
