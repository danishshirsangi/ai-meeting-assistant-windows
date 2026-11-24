"""Visual dimming only; never calls Windows display-affinity APIs."""
from PySide6.QtCore import QObject, QEvent
from PySide6.QtWidgets import QGraphicsOpacityEffect

from core.user_settings import normalize_appearance


def target_opacity(enabled, transparency, interactive=True, reveal=False):
    if not enabled or reveal:
        return 1.0
    amount = normalize_appearance({"transparency": transparency})["transparency"]
    return max(0.12 if interactive else 0.0, 1.0 - amount / 100.0)


class FocusAppearance(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.targets = {}
        self.preferences = normalize_appearance({})
        self.enabled = False

    def add(self, widget, interactive=True, keep_visible=None):
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(1.0)
        widget.setGraphicsEffect(effect)
        self.targets[widget] = (effect, interactive, keep_visible)
        widget.installEventFilter(self)
        self.refresh(widget)

    def configure(self, enabled, preferences):
        self.enabled = bool(enabled)
        self.preferences = normalize_appearance(preferences)
        for widget in self.targets:
            self.refresh(widget)

    def refresh(self, widget, hover=None, focused=None):
        effect, interactive, keep_visible = self.targets[widget]
        if hover is None:
            hover = widget.underMouse()
        if focused is None:
            focused = widget.hasFocus()
        reveal = bool(keep_visible and keep_visible()) or (
            interactive and (focused or (hover and self.preferences["restore_on_hover"])))
        effect.setOpacity(target_opacity(self.enabled, self.preferences["transparency"],
                                         interactive, reveal))

    def eventFilter(self, watched, event):
        if watched in self.targets:
            kind = event.type()
            if kind == QEvent.Type.Enter:
                self.refresh(watched, hover=True)
            elif kind == QEvent.Type.Leave:
                self.refresh(watched, hover=False)
            elif kind == QEvent.Type.FocusIn:
                self.refresh(watched, focused=True)
            elif kind == QEvent.Type.FocusOut:
                self.refresh(watched, focused=False)
        return super().eventFilter(watched, event)
