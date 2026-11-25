import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from ui.shortcut_capture import ShortcutCapture


def test_capture_chord_and_cancel():
    app = QApplication.instance() or QApplication([])
    field = ShortcutCapture("Ctrl+Alt+R")
    field.begin_capture()
    QTest.keyPress(field, Qt.Key.Key_Control, Qt.KeyboardModifier.ControlModifier)
    assert field.text() == "Ctrl+"
    QTest.keyPress(field, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
    assert field.text() == "Ctrl+Alt+"
    QTest.keyClick(field, Qt.Key.Key_G, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier)
    assert field.text() == "Ctrl+Alt+G"
    field.cancel_capture()
    field.begin_capture()
    QTest.keyClick(field, Qt.Key.Key_Escape)
    assert field.text() == "Ctrl+Alt+G"
    field.close()


def test_function_key():
    app = QApplication.instance() or QApplication([])
    field = ShortcutCapture("Ctrl+Alt+H")
    field.begin_capture()
    QTest.keyClick(field, Qt.Key.Key_F8, Qt.KeyboardModifier.ControlModifier)
    assert field.text() == "Ctrl+F8"
    field.close()
