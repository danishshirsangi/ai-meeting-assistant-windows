from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QSlider,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from core.user_settings import DEFAULT_SHORTCUTS, validate_shortcuts, DEFAULT_APPEARANCE, normalize_appearance


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
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #25432d; background: #101a13; } QTabBar::tab { background: #17271b; padding: 12px 20px; color: #cfe9d4; } QTabBar::tab:selected { background: #285737; color: #ffffff; }")
        tabs = self.tabs
        layout.addWidget(tabs, 1)

        keys = QWidget()
        form = QFormLayout(keys)
        form.setContentsMargins(24, 24, 24, 24)
        form.setVerticalSpacing(16)
        hint = QLabel("Enter a combination such as Ctrl+Alt+R. Use Ctrl or Alt with a letter, digit or F1–F12.")
        hint.setWordWrap(True)
        form.addRow(hint)
        self.record = QLineEdit(shortcuts["record"])
        self.visibility = QLineEdit(shortcuts["visibility"])
        form.addRow("Start / stop recording", self.record)
        form.addRow("Hide / restore window", self.visibility)
        reset = QPushButton("Restore defaults")
        reset.clicked.connect(self.reset_shortcuts)
        form.addRow(reset)
        save = QPushButton("Save shortcuts")
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
        save_api = QPushButton("Save and check connection")
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
        explanation = QLabel("Adjust workspace dimming when capture protection is on. This is visual only and never changes Windows capture protection. Questions, answers and Settings stay fully visible.")
        explanation.setWordWrap(True)
        appearance_form.addRow(explanation)
        self.transparency = QSlider(Qt.Orientation.Horizontal)
        self.transparency.setRange(0, 100)
        self.transparency.setValue(60)
        self.transparency_value = QLabel("60%")
        slider_row = QHBoxLayout()
        slider_row.addWidget(self.transparency, 1)
        slider_row.addWidget(self.transparency_value)
        appearance_form.addRow("Interface transparency", slider_row)
        minimum = QLabel("0% = solid · 100% = maximum dimming; controls retain 12% visibility.")
        minimum.setWordWrap(True)
        appearance_form.addRow(minimum)
        self.restore_hover = QCheckBox("Restore full opacity on hover")
        self.restore_hover.setChecked(True)
        appearance_form.addRow(self.restore_hover)
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

    def appearance_changed(self, _value=None):
        self.transparency_value.setText(f"{self.transparency.value()}%")
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
        self.record.setText(DEFAULT_SHORTCUTS["record"])
        self.visibility.setText(DEFAULT_SHORTCUTS["visibility"])

    def save_shortcuts(self):
        try:
            values = validate_shortcuts(self.record.text(), self.visibility.text())
            self.apply_shortcuts(values)
        except (ValueError, OSError, RuntimeError) as exc:
            self.key_status.setText(str(exc))
            return
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
