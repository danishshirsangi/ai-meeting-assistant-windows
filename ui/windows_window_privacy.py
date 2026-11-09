import ctypes
import sys
from ctypes import wintypes


WDA_NONE = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011


def set_window_capture_exclusion(window, excluded):
    """Best-effort Windows display-affinity capture exclusion.

    WDA_EXCLUDEFROMCAPTURE is supported on Windows 10 version 2004 and later.
    It is not a universal privacy boundary; individual capture apps and APIs
    may behave differently.
    """
    if sys.platform != "win32":
        return False, "Window capture exclusion is available only on Windows."

    try:
        hwnd = wintypes.HWND(int(window.winId()))
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        set_affinity = user32.SetWindowDisplayAffinity
        set_affinity.argtypes = [wintypes.HWND, wintypes.DWORD]
        set_affinity.restype = wintypes.BOOL

        affinity = WDA_EXCLUDEFROMCAPTURE if excluded else WDA_NONE
        if not set_affinity(hwnd, affinity):
            error_code = ctypes.get_last_error()
            return False, (
                "Windows rejected the display-affinity request "
                f"(error {error_code})."
            )
        return True, "Windows display affinity updated."
    except Exception as exc:
        return False, str(exc)
