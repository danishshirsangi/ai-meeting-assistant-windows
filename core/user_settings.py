"""Local preferences for the desktop application."""
import json
import re
import sys
from pathlib import Path

from dotenv import dotenv_values, set_key

DEFAULT_SHORTCUTS = {"record": "Ctrl+Alt+R", "visibility": "Ctrl+Alt+H"}
MODIFIERS = ("Ctrl", "Alt", "Shift")


def config_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parents[1]


def normalize_shortcut(value):
    parts = [part.strip().lower() for part in value.split("+")]
    if len(parts) < 2 or len(set(parts)) != len(parts):
        raise ValueError("Use at least one modifier and one key, e.g. Ctrl+Alt+R.")
    mods = parts[:-1]
    key = parts[-1]
    if any(mod not in {"ctrl", "alt", "shift"} for mod in mods):
        raise ValueError("Use Ctrl, Alt or Shift as modifiers.")
    if not any(mod in {"ctrl", "alt"} for mod in mods):
        raise ValueError("Include Ctrl or Alt to avoid triggering while typing.")
    if not re.fullmatch(r"[a-z0-9]|f(?:[1-9]|1[0-2])", key):
        raise ValueError("Use a letter, digit or F1–F12 as the final key.")
    return "+".join([mod for mod in MODIFIERS if mod.lower() in mods] + [key.upper()])


def validate_shortcuts(record, visibility):
    result = {"record": normalize_shortcut(record), "visibility": normalize_shortcut(visibility)}
    if result["record"] == result["visibility"]:
        raise ValueError("Choose different shortcuts for each action.")
    return result


def pynput_shortcut(value):
    parts = normalize_shortcut(value).lower().split("+")
    return "+".join([f"<{part}>" for part in parts[:-1]] + [
        f"<{parts[-1]}>" if len(parts[-1]) > 1 else parts[-1]
    ])


def load_shortcuts():
    try:
        data = json.loads((config_dir() / "shortcuts.json").read_text(encoding="utf-8"))
        return validate_shortcuts(data["record"], data["visibility"])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return DEFAULT_SHORTCUTS.copy()


def save_shortcuts(shortcuts):
    values = validate_shortcuts(shortcuts["record"], shortcuts["visibility"])
    folder = config_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "shortcuts.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(values, indent=2), encoding="utf-8")
    temporary.replace(path)


def saved_api_key():
    return dotenv_values(config_dir() / ".env").get("GEMINI_API_KEY") or None


def save_api_key(key):
    key = key.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{15,256}", key):
        raise ValueError("Enter a valid Gemini API key without spaces.")
    folder = config_dir()
    folder.mkdir(parents=True, exist_ok=True)
    success, _, _ = set_key(str(folder / ".env"), "GEMINI_API_KEY", key)
    if not success:
        raise OSError("Could not save the API key.")
