import ctypes
import logging
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    if sys.platform != "win32":
        raise RuntimeError(
            "This repository contains the Windows build of AI Meeting Assistant."
        )

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
    icon_path = Path(__file__).resolve().parent / "assets" / "interview-copilot.svg"
    app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
