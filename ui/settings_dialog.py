from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from ui.shortcut_capture import ShortcutCapture
from PySide6.QtWidgets import (
    QCheckBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QSlider, QFrame,
    QPushButton, QTabWidget, QVBoxLayout, QWidget, QStyle, QApplication,
)

from core.user_settings import DEFAULT_SHORTCUTS, validate_shortcuts, DEFAULT_APPEARANCE, normalize_appearance


class AppearancePreview(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.amount = 60
        self.setMinimumHeight(165)
        self.setAccessibleName("Workspace appearance preview")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(self.width() / 320, self.height() / 165)
        painter.setPen(QPen(QColor("#36664a"), 1))
        painter.setBrush(QColor("#071710"))
        painter.drawRoundedRect(1, 1, 318, 163, 9, 9)
        painter.setOpacity(max(.12, 1 - self.amount / 100))
        painter.setBrush(QColor("#31523e"))
        painter.setPen(Qt.PenStyle.NoPen)
        for x in (10, 85, 160, 235):
            painter.drawRoundedRect(x, 12, 67, 16, 4, 4)
        painter.drawRoundedRect(10, 140, 300, 15, 4, 4)
        painter.setOpacity(1)
        painter.setBrush(QColor("#102b1b"))
        painter.setPen(QPen(QColor("#42ce70"), 1))
        painter.drawRoundedRect(10, 36, 90, 95, 7, 7)
        painter.drawRoundedRect(106, 36, 204, 95, 7, 7)
        painter.setPen(QColor("#effff2"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(20, 53, "Questions")
        painter.drawText(116, 53, "Answer")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#496b57"))
        for y in (65, 80, 95):
            painter.drawRoundedRect(116, y, 170 if y != 95 else 105, 5, 2, 2)
        painter.end()


class SettingsPage(QWidget):
    def __init__(self, shortcuts, api_key, apply_shortcuts, apply_key, go_back, parent=None, apply_appearance=None):
        super().__init__(parent)
        self.apply_shortcuts = apply_shortcuts
        self.apply_key = apply_key
        self.apply_appearance = apply_appearance
        self.appearance = DEFAULT_APPEARANCE.copy()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(16)
        header = QHBoxLayout()
        back = QPushButton("Back to workspace")
        back.setObjectName("settingsBackButton")
        back.clicked.connect(go_back)
        header.addWidget(back)
        title = QLabel("Settings")
        title.setObjectName("appTitle")
        header.addWidget(title)
        header.addStretch()
        self.connection_status = QLabel("")
        self.connection_status.setObjectName("status")
        header.addWidget(self.connection_status)
        layout.addLayout(header)
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.tabs.tabBar().hide()
        self.setStyleSheet("""
            QFrame#settingsNav, QFrame#settingsCard { background: #0b2418; border: 1px solid #28573b; border-radius: 12px; }
            QPushButton#settingsNavButton { text-align: left; padding: 13px 10px; font-size: 13px; border: 1px solid transparent; background: transparent; }
            QPushButton#settingsNavButton:checked { background: #1b492d; border: 1px solid #78ed8d; color: #f4fff6; }
            QLabel#settingsHeading { font-size: 22px; font-weight: 800; }
            QLineEdit:focus { border: 2px solid #70f28b; }
            QSlider::groove:horizontal { height: 8px; background: #25432d; border-radius: 4px; }
            QSlider::sub-page:horizontal { background: #48d764; border-radius: 4px; }
            QSlider::handle:horizontal { background: #ecfff0; width: 18px; margin: -5px 0; border-radius: 9px; }
            QTabWidget::pane { background: #0b1911; border: 1px solid #28573b; border-radius: 12px; }
        """)
        tabs = self.tabs
        body = QHBoxLayout()
        body.setSpacing(14)
        nav = QFrame()
        nav.setObjectName("settingsNav")
        nav.setFixedWidth(210)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(10, 12, 10, 12)
        self.nav_buttons = []
        for index, (label, icon) in enumerate((
            ("Keyboard Shortcuts", QStyle.StandardPixmap.SP_ComputerIcon),
            ("Gemini API Key", QStyle.StandardPixmap.SP_DialogApplyButton),
            ("Appearance", QStyle.StandardPixmap.SP_DesktopIcon),
        )):
            button = QPushButton(label)
            button.setObjectName("settingsNavButton")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setIcon(self.style().standardIcon(icon))
            button.clicked.connect(lambda checked=False, i=index: self.tabs.setCurrentIndex(i))
            nav_layout.addWidget(button)
            self.nav_buttons.append(button)
        nav_layout.addStretch()
        body.addWidget(nav)
        body.addWidget(tabs, 1)
        layout.addLayout(body, 1)
        tabs.currentChanged.connect(self._sync_navigation)

        keys = QWidget()
        form = QFormLayout(keys)
        form.setContentsMargins(24, 24, 24, 24)
        form.setVerticalSpacing(16)
        heading = QLabel("Keyboard Shortcuts")
        heading.setObjectName("settingsHeading")
        form.addRow(heading)
        hint = QLabel("Click a shortcut field, then hold Ctrl or Alt and press a letter, digit or F1–F12. Plus signs are added automatically. Esc cancels.")
        hint.setWordWrap(True)
        form.addRow(hint)
        self.record = ShortcutCapture(shortcuts["record"])
        self.visibility = ShortcutCapture(shortcuts["visibility"])
        for name, field in (("Start / Stop Recording", self.record), ("Hide / Restore Window", self.visibility)):
            card = QFrame()
            card.setObjectName("settingsCard")
            row = QHBoxLayout(card)
            row.addWidget(QLabel(name), 1)
            row.addWidget(field, 2)
            edit = QPushButton("Edit")
            edit.clicked.connect(field.begin_capture)
            row.addWidget(edit)
            form.addRow(card)
        reset = QPushButton("Restore defaults")
        reset.clicked.connect(self.reset_shortcuts)
        form.addRow(reset)
        save = QPushButton("Save changes")
        save.setObjectName("primaryButton")
        save.clicked.connect(self.save_shortcuts)
        form.addRow(save)
        self.key_status = QLabel("")
        self.key_status.setWordWrap(True)
        form.addRow(self.key_status)
        tabs.addTab(keys, "Keyboard shortcuts")

        api = QWidget()
        api_form = QFormLayout(api)
        api_form.setContentsMargins(24, 24, 24, 24)
        api_form.setVerticalSpacing(16)
        api_heading = QLabel("Gemini API Key")
        api_heading.setObjectName("settingsHeading")
        api_form.addRow(api_heading)
        note = QLabel("Your key is stored in the local .env file, not encrypted. Do not share your configured portable folder.")
        note.setWordWrap(True)
        api_form.addRow(note)
        self.api = QLineEdit(api_key or "")
        self.api.setEchoMode(QLineEdit.EchoMode.Password)
        self.api.setPlaceholderText("Enter Gemini API key")
        api_form.addRow("Gemini API key", self.api)
        show = self.show_key = QPushButton("Show key")
        show.setCheckable(True)
        show.toggled.connect(lambda checked: (
            self.api.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password),
            show.setText("Hide key" if checked else "Show key")
        ))
        api_form.addRow(show)
        paste = QPushButton("Paste key")
        paste.clicked.connect(lambda: self.api.setText(QApplication.clipboard().text().strip()))
        api_form.addRow(paste)
        save_api = QPushButton("Save and check connection")
        save_api.setObjectName("primaryButton")
        save_api.clicked.connect(self.save_api)
        api_form.addRow(save_api)
        self.api_status = QLabel("")
        self.api_status.setWordWrap(True)
        api_form.addRow(self.api_status)
        tabs.addTab(api, "Gemini API key")

        appearance = QWidget()
        appearance_form = QFormLayout(appearance)
        appearance_form.setContentsMargins(24, 24, 24, 24)
        appearance_form.setVerticalSpacing(16)
        explanation = QLabel("Adjust real workspace background transparency and control dimming when capture protection is on. This is visual only and never changes Windows capture protection. Questions, answers and Settings stay fully visible.")
        explanation.setWordWrap(True)
        appearance_heading = QLabel("Appearance")
        appearance_heading.setObjectName("settingsHeading")
        appearance_form.addRow(appearance_heading)
        appearance_form.addRow(explanation)
        self.transparency = QSlider(Qt.Orientation.Horizontal)
        self.transparency.setRange(0, 100)
        self.transparency.setValue(60)
        self.transparency_value = QLabel("60%")
        slider_row = QHBoxLayout()
        slider_row.addWidget(self.transparency, 1)
        slider_row.addWidget(self.transparency_value)
        slider_card = QFrame()
        slider_card.setObjectName("settingsCard")
        slider_layout = QVBoxLayout(slider_card)
        slider_layout.addWidget(QLabel("Interface transparency"))
        slider_layout.addLayout(slider_row)
        appearance_form.addRow(slider_card)
        minimum = QLabel("0% = solid · 100% = nearly clear background; controls retain 12% visibility.")
        minimum.setWordWrap(True)
        appearance_form.addRow(minimum)
        self.restore_hover = QCheckBox("Restore full opacity on hover")
        self.restore_hover.setChecked(True)
        hover_card = QFrame()
        hover_card.setObjectName("settingsCard")
        QVBoxLayout(hover_card).addWidget(self.restore_hover)
        appearance_form.addRow(hover_card)
        preview_card = QFrame()
        preview_card.setObjectName("settingsCard")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.addWidget(QLabel("Live Preview · visual dimming only"))
        self.preview = AppearancePreview()
        preview_layout.addWidget(self.preview)
        appearance_form.addRow(preview_card)
        reset_appearance = QPushButton("Reset to default")
        reset_appearance.clicked.connect(self.reset_appearance)
        appearance_form.addRow(reset_appearance)
        self.appearance_status = QLabel("")
        appearance_form.addRow(self.appearance_status)
        self.appearance_timer = QTimer(self)
        self.appearance_timer.setSingleShot(True)
        self.appearance_timer.setInterval(200)
        self.appearance_timer.timeout.connect(self.flush_appearance)
        self.transparency.valueChanged.connect(self.appearance_changed)
        self.restore_hover.toggled.connect(self.appearance_changed)
        tabs.addTab(appearance, "Appearance")
        self._sync_navigation(0)


    def _sync_navigation(self, index):
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].setChecked(True)

    def set_appearance(self, values):
        self.appearance_timer.stop()
        self.appearance = normalize_appearance(values)
        self.transparency.blockSignals(True)
        self.restore_hover.blockSignals(True)
        self.transparency.setValue(self.appearance["transparency"])
        self.restore_hover.setChecked(self.appearance["restore_on_hover"])
        self.transparency.blockSignals(False)
        self.restore_hover.blockSignals(False)
        self.transparency_value.setText(f'{self.appearance["transparency"]}%')
        self.appearance_status.clear()
        self.preview.amount = self.appearance['transparency']
        self.preview.update()

    def appearance_changed(self, _value=None):
        self.transparency_value.setText(f"{self.transparency.value()}%")
        self.preview.amount = self.transparency.value()
        self.preview.update()
        self.appearance_timer.start()

    def flush_appearance(self):
        self.appearance_timer.stop()
        values = {"transparency": self.transparency.value(),
                  "restore_on_hover": self.restore_hover.isChecked()}
        if values == self.appearance:
            return True
        try:
            if self.apply_appearance:
                self.apply_appearance(values)
        except OSError:
            self.appearance_status.setText("Unable to save appearance. Check folder permissions.")
            return False
        self.appearance = values
        self.appearance_status.setText("Saved")
        return True

    def reset_appearance(self):
        self.transparency.setValue(DEFAULT_APPEARANCE["transparency"])
        self.restore_hover.setChecked(DEFAULT_APPEARANCE["restore_on_hover"])
        self.flush_appearance()

    def refresh(self, shortcuts, api_key, status, api_tab=False):
        self.record.cancel_capture()
        self.visibility.cancel_capture()
        self.record.setText(shortcuts["record"])
        self.visibility.setText(shortcuts["visibility"])
        self.show_key.setChecked(False)
        self.api.setEchoMode(QLineEdit.EchoMode.Password)
        self.api.setText(api_key or "")
        self.key_status.clear()
        self.api_status.clear()
        self.connection_status.setText(status)
        self.tabs.setCurrentIndex(1 if api_tab else 0)

    def clear_sensitive_fields(self):
        self.show_key.setChecked(False)
        self.api.clear()

    def reset_shortcuts(self):
        self.record.cancel_capture()
        self.visibility.cancel_capture()
        self.record.setText(DEFAULT_SHORTCUTS["record"])
        self.visibility.setText(DEFAULT_SHORTCUTS["visibility"])

    def save_shortcuts(self):
        try:
            values = validate_shortcuts(self.record.text(), self.visibility.text())
            self.apply_shortcuts(values)
        except (ValueError, OSError, RuntimeError) as exc:
            self.key_status.setText(str(exc))
            return
        self.record.cancel_capture()
        self.visibility.cancel_capture()
        self.record.setText(values["record"])
        self.visibility.setText(values["visibility"])
        self.key_status.setText("Saved. Shortcuts activate when you return to the workspace.")

    def save_api(self):
        try:
            self.apply_key(self.api.text())
        except ValueError as exc:
            self.api_status.setText(str(exc))
        except Exception:
            self.api_status.setText("Could not save key. Check folder permissions and try again.")
        else:
            self.api_status.setText("Saved. Checking Gemini connection…")
