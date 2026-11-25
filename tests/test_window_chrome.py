from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QRect, QSize, Qt
from PySide6.QtWidgets import QWidget
from ui.window_chrome import NoTooltips, background_alpha, resized_geometry, ResizableFrame


def test_background_alpha():
    assert background_alpha(False, 100) == 255
    assert background_alpha(True, 0) == 255
    assert background_alpha(True, 60) == 102
    assert background_alpha(True, 100) == 1


def test_tooltip_suppression(qt_app):
    widget = QWidget()
    blocker = NoTooltips(widget)
    event = QEvent(QEvent.Type.ToolTip)
    assert blocker.eventFilter(widget, event)
    assert event.isAccepted()
    assert not blocker.eventFilter(widget, QEvent(QEvent.Type.Enter))
    widget.close()


def test_resize_geometry_all_edges():
    original = QRect(100, 100, 1000, 700)
    minimum = QSize(900, 650)
    maximum = QSize(2000, 2000)
    delta = QPoint(50, 25)
    for edges, expected in (
        (Qt.Edge.LeftEdge, QRect(150, 100, 950, 700)),
        (Qt.Edge.RightEdge, QRect(100, 100, 1050, 700)),
        (Qt.Edge.TopEdge, QRect(100, 125, 1000, 675)),
        (Qt.Edge.BottomEdge, QRect(100, 100, 1000, 725)),
        (Qt.Edge.TopEdge | Qt.Edge.LeftEdge, QRect(150, 125, 950, 675)),
        (Qt.Edge.TopEdge | Qt.Edge.RightEdge, QRect(100, 125, 1050, 675)),
        (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge, QRect(150, 100, 950, 725)),
        (Qt.Edge.BottomEdge | Qt.Edge.RightEdge, QRect(100, 100, 1050, 725)),
    ):
        assert resized_geometry(original, delta, edges, minimum, maximum) == expected
    assert resized_geometry(original, QPoint(500, 500), Qt.Edge.LeftEdge | Qt.Edge.TopEdge,
                            minimum, maximum) == QRect(200, 150, 900, 650)


def test_resize_frame_handles(qt_app):
    window = QWidget()
    frame = ResizableFrame(window, QWidget())
    assert len(frame.handles) == 8
    assert all(handle.cursor().shape() != Qt.CursorShape.ArrowCursor for handle in frame.handles)
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()
