from __future__ import annotations

import ctypes
import platform
import time
from ctypes import wintypes


IS_WINDOWS = platform.system() == "Windows"

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
KEYEVENTF_KEYUP = 0x0002
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


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


BUTTON_FLAGS = {
    "left": (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
    "right": (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}

KEY_ALIASES = {
    "CTRL": 0x11,
    "CONTROL": 0x11,
    "SHIFT": 0x10,
    "ALT": 0x12,
    "WIN": 0x5B,
    "WINDOWS": 0x5B,
    "CMD": 0x5B,
    "COMMAND": 0x5B,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "TAB": 0x09,
    "SPACE": 0x20,
    "SPACEBAR": 0x20,
    "BACKSPACE": 0x08,
    "BKSP": 0x08,
    "DELETE": 0x2E,
    "DEL": 0x2E,
    "INSERT": 0x2D,
    "INS": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PAGE UP": 0x21,
    "PGUP": 0x21,
    "PAGEDOWN": 0x22,
    "PAGE DOWN": 0x22,
    "PGDN": 0x22,
    "UP": 0x26,
    "ARROWUP": 0x26,
    "DOWN": 0x28,
    "ARROWDOWN": 0x28,
    "LEFT": 0x25,
    "ARROWLEFT": 0x25,
    "RIGHT": 0x27,
    "ARROWRIGHT": 0x27,
    "CAPSLOCK": 0x14,
    "NUMLOCK": 0x90,
    "SCROLLLOCK": 0x91,
    "PRINTSCREEN": 0x2C,
    "PRTSC": 0x2C,
    "PAUSE": 0x13,
    "PLUS": 0xBB,
    "MINUS": 0xBD,
    "COMMA": 0xBC,
    "PERIOD": 0xBE,
    "DOT": 0xBE,
    "SLASH": 0xBF,
    "BACKSLASH": 0xDC,
    "SEMICOLON": 0xBA,
    "QUOTE": 0xDE,
    "APOSTROPHE": 0xDE,
    "LEFTBRACKET": 0xDB,
    "RIGHTBRACKET": 0xDD,
    "GRAVE": 0xC0,
    "BACKTICK": 0xC0,
}

MODIFIER_VKS = {0x10, 0x11, 0x12, 0x5B}

for index in range(1, 25):
    KEY_ALIASES[f"F{index}"] = 0x70 + index - 1

for index in range(10):
    KEY_ALIASES[f"NUM{index}"] = 0x60 + index


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


def parse_key_combination(keys: str) -> list[int]:
    parts = [part.strip() for part in keys.split("+") if part.strip()]
    if not parts:
        raise ValueError("请输入键盘按键。")
    return [virtual_key_for_name(part) for part in parts]


def virtual_key_for_name(name: str) -> int:
    normalized = " ".join(name.strip().upper().split())
    compact = normalized.replace(" ", "")

    if normalized in KEY_ALIASES:
        return KEY_ALIASES[normalized]
    if compact in KEY_ALIASES:
        return KEY_ALIASES[compact]
    if len(normalized) == 1 and "A" <= normalized <= "Z":
        return ord(normalized)
    if len(normalized) == 1 and "0" <= normalized <= "9":
        return ord(normalized)

    if IS_WINDOWS and len(name) == 1:
        result = _user32().VkKeyScanW(ord(name))
        if result != -1:
            return result & 0xFF

    raise ValueError(f"不支持的键盘按键：{name}")


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

    def press_keys(self, keys: str) -> None:
        key_codes = parse_key_combination(keys)
        modifiers = [key_code for key_code in key_codes if key_code in MODIFIER_VKS]
        regular_keys = [key_code for key_code in key_codes if key_code not in MODIFIER_VKS]
        if not regular_keys and modifiers:
            regular_keys = modifiers[-1:]
            modifiers = modifiers[:-1]

        for key_code in modifiers:
            self._send_key(key_code, key_up=False)
        for key_code in regular_keys:
            self._send_key(key_code, key_up=False)
            self._send_key(key_code, key_up=True)
        for key_code in reversed(modifiers):
            self._send_key(key_code, key_up=True)

    def _send_mouse_flag(self, flag: int) -> None:
        user32 = _user32()
        event = INPUT(
            type=INPUT_MOUSE,
            union=INPUT_UNION(mi=MOUSEINPUT(0, 0, 0, flag, 0, ULONG_PTR(0))),
        )
        sent = user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if sent != 1:
            raise OSError("SendInput failed.")

    def _send_key(self, key_code: int, key_up: bool) -> None:
        user32 = _user32()
        flags = KEYEVENTF_KEYUP if key_up else 0
        event = INPUT(
            type=INPUT_KEYBOARD,
            union=INPUT_UNION(ki=KEYBDINPUT(key_code, 0, flags, 0, ULONG_PTR(0))),
        )
        sent = user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
        if sent != 1:
            raise OSError("SendInput failed.")
