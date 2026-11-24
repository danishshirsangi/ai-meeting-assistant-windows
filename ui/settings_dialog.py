from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QVBoxLayout, QWidget,
)

from core.user_settings import DEFAULT_SHORTCUTS, validate_shortcuts


class SettingsDialog(QDialog):
    def __init__(self, shortcuts, api_key, apply_shortcuts, apply_key, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(490)
        self.apply_shortcuts = apply_shortcuts
        self.apply_key = apply_key
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        keys = QWidget()
        form = QFormLayout(keys)
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
        note = QLabel("Your key is stored in the local .env file, not encrypted. Do not share your configured portable folder.")
        note.setWordWrap(True)
        api_form.addRow(note)
        self.api = QLineEdit(api_key or "")
        self.api.setEchoMode(QLineEdit.EchoMode.Password)
        self.api.setPlaceholderText("Enter Gemini API key")
        api_form.addRow("Gemini API key", self.api)
        show = QPushButton("Show key")
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
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)

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
        self.key_status.setText("Saved. Shortcuts activate when Settings closes.")

    def save_api(self):
        try:
            self.apply_key(self.api.text())
        except ValueError as exc:
            self.api_status.setText(str(exc))
        except Exception:
            self.api_status.setText("Could not save key. Check folder permissions and try again.")
        else:
            self.api_status.setText("Saved. Connection check started; see the main window status.")
