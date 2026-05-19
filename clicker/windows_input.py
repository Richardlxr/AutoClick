from __future__ import annotations

import ctypes
import platform
import time
from dataclasses import dataclass
from ctypes import wintypes


IS_WINDOWS = platform.system() == "Windows"

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008
MAPVK_VK_TO_VSC = 0
SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79
VK_F7 = 0x76

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong
_USER32 = None


@dataclass(frozen=True, slots=True)
class ScreenBounds:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def contains(self, x: int, y: int) -> bool:
        return self.left <= x < self.right and self.top <= y < self.bottom

    def describe(self) -> str:
        return f"X {self.left} 到 {self.right - 1}，Y {self.top} 到 {self.bottom - 1}"


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

EXTENDED_KEY_VKS = {
    0x21,
    0x22,
    0x23,
    0x24,
    0x25,
    0x26,
    0x27,
    0x28,
    0x2D,
    0x2E,
    0x5B,
    0x5C,
    0x6F,
    0x90,
    0x91,
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
    global _USER32
    if not IS_WINDOWS:
        raise RuntimeError("Windows input is only available on Windows.")
    if _USER32 is None:
        _USER32 = ctypes.WinDLL("user32", use_last_error=True)
        _USER32.GetAsyncKeyState.argtypes = [wintypes.INT]
        _USER32.GetAsyncKeyState.restype = wintypes.SHORT
        _USER32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
        _USER32.GetCursorPos.restype = wintypes.BOOL
        _USER32.GetSystemMetrics.argtypes = [wintypes.INT]
        _USER32.GetSystemMetrics.restype = wintypes.INT
        _USER32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
        _USER32.MapVirtualKeyW.restype = wintypes.UINT
        _USER32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
        _USER32.SendInput.restype = wintypes.UINT
    return _USER32


def _last_windows_error(action: str) -> str:
    code = ctypes.get_last_error()
    if code:
        return f"{action}失败。Windows 错误码 {code}：{ctypes.FormatError(code).strip()}"
    return f"{action}失败。Windows 没有返回更具体的错误码。"


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
        raise OSError(_last_windows_error("读取鼠标位置"))
    return int(point.x), int(point.y)


def virtual_screen_bounds() -> ScreenBounds:
    user32 = _user32()
    return ScreenBounds(
        left=int(user32.GetSystemMetrics(SM_XVIRTUALSCREEN)),
        top=int(user32.GetSystemMetrics(SM_YVIRTUALSCREEN)),
        width=int(user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)),
        height=int(user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)),
    )


def validate_screen_point(x: int, y: int, bounds: ScreenBounds) -> None:
    if bounds.contains(x, y):
        return
    raise ValueError(
        f"目标坐标 ({x}, {y}) 不在当前屏幕范围内。当前屏幕范围：{bounds.describe()}。"
        "请重新捕获目标点，或检查显示器连接、分辨率和缩放设置。"
    )


def absolute_mouse_coordinates(x: int, y: int, bounds: ScreenBounds) -> tuple[int, int]:
    validate_screen_point(x, y, bounds)
    width = max(1, bounds.width - 1)
    height = max(1, bounds.height - 1)
    absolute_x = round((x - bounds.left) * 65535 / width)
    absolute_y = round((y - bounds.top) * 65535 / height)
    return absolute_x, absolute_y


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

        x = int(x)
        y = int(y)
        absolute_x, absolute_y = absolute_mouse_coordinates(x, y, virtual_screen_bounds())

        move_flags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK
        self._send_mouse_input(MOUSEINPUT(absolute_x, absolute_y, 0, move_flags, 0, ULONG_PTR(0)), "移动鼠标")
        if self.settle_seconds:
            time.sleep(self.settle_seconds)

        down_flag, up_flag = BUTTON_FLAGS[button]
        self._send_input_events(
            [
                INPUT(type=INPUT_MOUSE, union=INPUT_UNION(mi=MOUSEINPUT(0, 0, 0, down_flag, 0, ULONG_PTR(0)))),
                INPUT(type=INPUT_MOUSE, union=INPUT_UNION(mi=MOUSEINPUT(0, 0, 0, up_flag, 0, ULONG_PTR(0)))),
            ],
            "发送鼠标点击",
        )

    def press_keys(self, keys: str) -> None:
        key_codes = parse_key_combination(keys)
        modifiers = [key_code for key_code in key_codes if key_code in MODIFIER_VKS]
        regular_keys = [key_code for key_code in key_codes if key_code not in MODIFIER_VKS]
        if not regular_keys and modifiers:
            regular_keys = modifiers[-1:]
            modifiers = modifiers[:-1]

        for key_code in modifiers:
            self._send_key_scan_code(key_code, key_up=False)
        for key_code in regular_keys:
            self._send_key_scan_code(key_code, key_up=False)
            self._send_key_scan_code(key_code, key_up=True)
        for key_code in reversed(modifiers):
            self._send_key_scan_code(key_code, key_up=True)

    def _send_mouse_input(self, mouse_input: MOUSEINPUT, action: str) -> None:
        self._send_input_events([INPUT(type=INPUT_MOUSE, union=INPUT_UNION(mi=mouse_input))], action)

    def _send_key_scan_code(self, key_code: int, key_up: bool) -> None:
        user32 = _user32()
        scan_code = user32.MapVirtualKeyW(key_code, MAPVK_VK_TO_VSC)
        flags = KEYEVENTF_SCANCODE
        if key_code in EXTENDED_KEY_VKS:
            flags |= KEYEVENTF_EXTENDEDKEY
        if key_up:
            flags |= KEYEVENTF_KEYUP
        event = INPUT(
            type=INPUT_KEYBOARD,
            union=INPUT_UNION(ki=KEYBDINPUT(0, scan_code, flags, 0, ULONG_PTR(0))),
        )
        self._send_input_events([event], "发送键盘按键")

    def _send_input_events(self, events: list[INPUT], action: str) -> None:
        user32 = _user32()
        input_array = (INPUT * len(events))(*events)
        ctypes.set_last_error(0)
        sent = user32.SendInput(len(events), input_array, ctypes.sizeof(INPUT))
        if sent != len(events):
            raise OSError(_last_windows_error(action))
