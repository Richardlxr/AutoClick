from __future__ import annotations

import ctypes
import platform
import time
from ctypes import wintypes


IS_WINDOWS = platform.system() == "Windows"

INPUT_MOUSE = 0
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
VK_F7 = 0x76

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


BUTTON_FLAGS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}


def _user32() -> ctypes.WinDLL:
    if not IS_WINDOWS:
        raise RuntimeError("Windows input is only available on Windows.")
    return ctypes.windll.user32


def make_process_dpi_aware() -> None:
    if not IS_WINDOWS:
        return
    try:
        _user32().SetProcessDPIAware()
    except Exception:
        pass


def cursor_position() -> tuple[int, int]:
    user32 = _user32()
    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        raise OSError("GetCursorPos failed.")
    return int(point.x), int(point.y)


def is_f7_pressed() -> bool:
    if not IS_WINDOWS:
        return False
    return bool(_user32().GetAsyncKeyState(VK_F7) & 0x8000)


class WindowsClickBackend:
    def __init__(self, settle_seconds: float = 0.02) -> None:
        if not IS_WINDOWS:
            raise RuntimeError("WindowsClickBackend can only run on Windows.")
        make_process_dpi_aware()
        self.settle_seconds = settle_seconds

    def click(self, x: int, y: int, button: str = "left") -> None:
        if button not in BUTTON_FLAGS:
            raise ValueError(f"Unsupported mouse button: {button}")

        user32 = _user32()
        if not user32.SetCursorPos(int(x), int(y)):
            raise OSError("SetCursorPos failed.")
        if self.settle_seconds:
            time.sleep(self.settle_seconds)

        down_flag, up_flag = BUTTON_FLAGS[button]
        self._send_mouse_flag(down_flag)
        self._send_mouse_flag(up_flag)

    def _send_mouse_flag(self, flag: int) -> None:
        user32 = _user32()
        event = INPUT(
            type=INPUT_MOUSE,
            union=INPUT_UNION(mi=MOUSEINPUT(0, 0, 0, flag, 0, ULONG_PTR(0))),
        )
        sent = user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if sent != 1:
            raise OSError("SendInput failed.")
