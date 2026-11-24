import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget, QPushButton
from core.user_settings import DEFAULT_SHORTCUTS
from ui.settings_dialog import SettingsPage


def test_embedded_settings_navigation():
    app = QApplication.instance() or QApplication([])
    stack = QStackedWidget()
    workspace = QWidget()
    stack.addWidget(workspace)
    saved = []
    page = SettingsPage(DEFAULT_SHORTCUTS, None, saved.append, lambda key: None,
                        lambda: stack.setCurrentWidget(workspace), stack)
    stack.addWidget(page)
    stack.setCurrentWidget(page)
    assert not page.isWindow()
    page.refresh(DEFAULT_SHORTCUTS, "example_value_123456", "Ready", api_tab=True)
    assert page.tabs.currentIndex() == 1
    page.record.setText("Ctrl+F8")
    page.save_shortcuts()
    assert saved[0]["record"] == "Ctrl+F8"
    page.findChild(QPushButton, "settingsBackButton").click()
    assert stack.currentWidget() is workspace
    stack.close()
