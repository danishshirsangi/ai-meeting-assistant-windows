import ctypes
import logging
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.window_chrome import NoTooltips


def main():
    log_options = {}
    if getattr(sys, "frozen", False):
        log_dir = Path(sys.executable).resolve().parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_options = {"filename": str(log_dir / "application.log"), "encoding": "utf-8"}
    logging.basicConfig(
        **log_options,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if sys.platform != "win32":
        raise RuntimeError(
            "This repository contains the Windows build of AI Meeting Assistant."
        )

    if "--packaging-smoke-test" in sys.argv:
        try:
            import soundcard
            import sounddevice
            import soundfile
            import faster_whisper
            import ctranslate2
            import av
            import onnxruntime
            import pymupdf
            from docx import Document
            from pynput import keyboard
            from google import genai
            from PySide6 import QtSvg
            from pygments.lexers import get_lexer_by_name
            get_lexer_by_name("python")
            logging.info("Frozen dependency smoke test passed")
        except Exception:
            logging.exception("Frozen dependency smoke test failed")
            sys.exit(1)
        sys.exit(0)

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "DanishShirsangi.AIMeetingAssistant.Windows"
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("AI Meeting Assistant")
    app.setOrganizationName("AI Meeting Assistant")
    app.setStyle("Fusion")
    no_tooltips = NoTooltips(app)
    app.installEventFilter(no_tooltips)
    icon_path = Path(__file__).resolve().parent / "assets" / "interview-copilot.svg"
    app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
