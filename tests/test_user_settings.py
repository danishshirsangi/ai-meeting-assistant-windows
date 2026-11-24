import pytest
from core import user_settings as settings


def test_shortcut_normalization():
    assert settings.normalize_shortcut("alt+CTRL+r") == "Ctrl+Alt+R"
    assert settings.pynput_shortcut("Ctrl+F8") == "<ctrl>+<f8>"


@pytest.mark.parametrize("value", ["R", "Shift+A", "Ctrl+Ctrl+R", "Ctrl+R+H", "Ctrl+F99"])
def test_invalid_shortcuts(value):
    with pytest.raises(ValueError):
        settings.normalize_shortcut(value)


def test_duplicates():
    with pytest.raises(ValueError):
        settings.validate_shortcuts("Ctrl+Alt+R", "alt+ctrl+r")


def test_preferences_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "config_dir", lambda: tmp_path)
    assert settings.load_shortcuts() == settings.DEFAULT_SHORTCUTS
    values = settings.validate_shortcuts("Ctrl+F8", "Alt+F9")
    settings.save_shortcuts(values)
    assert settings.load_shortcuts() == values
    (tmp_path / "shortcuts.json").write_text("invalid")
    assert settings.load_shortcuts() == settings.DEFAULT_SHORTCUTS


def test_key_replacement_preserves_other_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "config_dir", lambda: tmp_path)
    path = tmp_path / ".env"
    path.write_text("GEMINI_MODEL=example-model\n")
    settings.save_api_key("example_value_123456")
    settings.save_api_key("replacement_value_123456")
    assert settings.saved_api_key() == "replacement_value_123456"
    assert "GEMINI_MODEL=example-model" in path.read_text()
