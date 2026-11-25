"""Capture shortcut chords locally, only while the field is focused."""
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QLineEdit
from core.user_settings import normalize_shortcut


class ShortcutCapture(QLineEdit):
    def __init__(self, value, parent=None):
        super().__init__(value, parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Press a key combination…")
        self.setAccessibleName("Keyboard shortcut recorder")
        self._previous = value
        self._capturing = False
        self._finished = False

    def begin_capture(self):
        if not self._capturing:
            self._previous = self.text()
        self._capturing = True
        self._finished = False
        self.clear()
        self.setFocus()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.begin_capture()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if not self._capturing:
            self.begin_capture()

    def focusOutEvent(self, event):
        self.cancel_capture()
        super().focusOutEvent(event)

    def cancel_capture(self):
        if self._capturing and not self._finished:
            self.setText(self._previous)
        self._capturing = False
        self._finished = False

    def event(self, event):
        if event.type() == QEvent.Type.ShortcutOverride and self._capturing:
            event.accept()
            return True
        return super().event(event)

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            event.accept()
            return
        if not self._capturing:
            self.begin_capture()
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.setText(self._previous)
            self._capturing = False
            event.accept()
            return
        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            self.cancel_capture()
            self.focusNextPrevChild(key == Qt.Key.Key_Tab)
            return
        flags = event.modifiers()
        modifiers = [(Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Control, "Ctrl"),
                     (Qt.KeyboardModifier.AltModifier, Qt.Key.Key_Alt, "Alt"),
                     (Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_Shift, "Shift")]
        parts = [name for flag, modifier_key, name in modifiers
                 if flags & flag or key == modifier_key]
        if flags & Qt.KeyboardModifier.MetaModifier or key == Qt.Key.Key_Meta:
            self.setText(self._previous)
            self._capturing = False
            event.accept()
            return
        if key in [item[1] for item in modifiers]:
            if not self._finished:
                self.setText("+".join(parts) + "+")
            event.accept()
            return
        if self._finished:
            self._previous = self.text()
            self._finished = False
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z or Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            parts.append(chr(key))
        elif Qt.Key.Key_F1 <= key <= Qt.Key.Key_F12:
            parts.append(f"F{key - Qt.Key.Key_F1 + 1}")
        else:
            self.setText(self._previous)
            self._capturing = False
            event.accept()
            return
        try:
            self.setText(normalize_shortcut("+".join(parts)))
            self._finished = True
        except ValueError:
            self.setText("+".join(parts))
        event.accept()

    def keyReleaseEvent(self, event):
        event.accept()
