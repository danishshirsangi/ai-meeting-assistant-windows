import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication, QPushButton, QLabel, QWidget
from PySide6.QtTest import QTest
from core import user_settings as settings
from ui.focus_appearance import FocusAppearance, target_opacity
from ui.settings_dialog import SettingsPage


@pytest.mark.parametrize("amount,expected", [(0, 1), (60, .4), (100, .12), (-5, 1), (200, .12)])
def test_opacity_limits(amount, expected):
    assert target_opacity(True, amount) == pytest.approx(expected)
    assert target_opacity(False, amount) == 1
    assert target_opacity(True, amount, reveal=True) == 1


def test_preferences(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "config_dir", lambda: tmp_path)
    assert settings.load_appearance() == settings.DEFAULT_APPEARANCE
    settings.save_appearance({"transparency": 100, "restore_on_hover": False})
    assert settings.load_appearance() == {"transparency": 100, "restore_on_hover": False}
    (tmp_path / "appearance.json").write_text("broken")
    assert settings.load_appearance() == settings.DEFAULT_APPEARANCE
    assert settings.normalize_appearance({"transparency": True, "restore_on_hover": "no"}) == settings.DEFAULT_APPEARANCE


def test_hover_focus_click_and_restore(qt_app):
    root = QWidget()
    button = QPushButton("Settings", root)
    label = QLabel("Footer", root)
    critical = QPushButton("Recording", root)
    manager = FocusAppearance(root)
    manager.add(button)
    manager.add(label, interactive=False)
    manager.add(critical, keep_visible=lambda: True)
    manager.configure(True, {"transparency": 100, "restore_on_hover": True})
    manager.refresh(button, hover=False, focused=False)
    assert button.graphicsEffect().opacity() == pytest.approx(.12)
    assert label.graphicsEffect().opacity() == 0
    assert critical.graphicsEffect().opacity() == 1
    manager.eventFilter(button, QEvent(QEvent.Type.Enter))
    assert button.graphicsEffect().opacity() == 1
    manager.refresh(button, hover=False, focused=False)
    clicked = []
    button.clicked.connect(lambda: clicked.append(True))
    QTest.mouseClick(button, Qt.MouseButton.LeftButton)
    assert clicked == [True]
    manager.configure(True, {"transparency": 100, "restore_on_hover": False})
    manager.refresh(button, hover=True, focused=False)
    assert button.graphicsEffect().opacity() == pytest.approx(.12)
    manager.refresh(button, hover=False, focused=True)
    assert button.graphicsEffect().opacity() == 1
    manager.configure(False, settings.DEFAULT_APPEARANCE)
    assert all(w.graphicsEffect().opacity() == 1 for w in (button, label, critical))
    root.close()
    root.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()


def test_appearance_page_save_and_reset(qt_app):
    saved = []
    page = SettingsPage(settings.DEFAULT_SHORTCUTS, None, lambda _: None,
                        lambda _: None, lambda: None, apply_appearance=saved.append)
    page.set_appearance(settings.DEFAULT_APPEARANCE)
    page.transparency.setValue(100)
    page.restore_hover.setChecked(False)
    assert page.flush_appearance()
    assert saved[-1] == {"transparency": 100, "restore_on_hover": False}
    page.reset_appearance()
    assert saved[-1] == settings.DEFAULT_APPEARANCE
    page.close()
    page.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()
