from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QWidget
from ui.window_chrome import NoTooltips, background_alpha


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
