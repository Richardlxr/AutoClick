from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from clicker.models import Macro, MacroStep, TargetPoint
from clicker.runner import DryRunClickBackend, MacroRunner
from clicker.windows_input import (
    CLICK_MODE_MOUSE_EVENT,
    CLICK_MODE_SEPARATE,
    CLICK_MODE_SENDINPUT,
    IS_WINDOWS,
    KEYBOARD_MODE_SCAN_CODE,
    KEYBOARD_MODE_VIRTUAL_KEY,
    MOUSE_MODE_ABSOLUTE,
    MOUSE_MODE_CURSOR,
    WindowsClickBackend,
    is_f7_pressed,
    make_process_dpi_aware,
    parse_key_combination,
)


ACTION_CLICK_LABEL = "点击坐标"
ACTION_KEY_LABEL = "键盘按键"
ACTION_LABEL_TO_VALUE = {ACTION_CLICK_LABEL: "click", ACTION_KEY_LABEL: "key"}
ACTION_VALUE_TO_LABEL = {"click": ACTION_CLICK_LABEL, "key": ACTION_KEY_LABEL}
MOUSE_MODE_LABELS = {
    "光标移动（旧版，优先尝试）": MOUSE_MODE_CURSOR,
    "绝对移动（新版）": MOUSE_MODE_ABSOLUTE,
}
KEYBOARD_MODE_LABELS = {
    "虚拟键（旧版，优先尝试）": KEYBOARD_MODE_VIRTUAL_KEY,
    "扫描码（游戏可试）": KEYBOARD_MODE_SCAN_CODE,
}
CLICK_MODE_LABELS = {
    "分离点击（推荐）": CLICK_MODE_SEPARATE,
    "快速点击": CLICK_MODE_SENDINPUT,
    "旧版 mouse_event": CLICK_MODE_MOUSE_EVENT,
}

COMMON_KEYS = [
    "Enter",
    "Esc",
    "Tab",
    "Space",
    "Backspace",
    "Delete",
    "Up",
    "Down",
    "Left",
    "Right",
    "Ctrl+C",
    "Ctrl+V",
    "Ctrl+A",
    "Ctrl+S",
    "Alt+Tab",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
]


class ClickMacroApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        make_process_dpi_aware()

        self.title("自动点击器")
        self.geometry("1080x700")
        self.minsize(960, 640)
        self.configure(bg="#eef3f8")

        self.macro = Macro()
        self.selected_point_id: str | None = None
        self.capture_after_id: str | None = None

        backend = WindowsClickBackend() if IS_WINDOWS else DryRunClickBackend()
        self.runner = MacroRunner(
            backend=backend,
            on_event=self._handle_runner_event,
            stop_predicate=is_f7_pressed,
        )

        self._build_variables()
        self._configure_style()
        self._build_ui()
        self._refresh_all()
        self._sync_action_fields()
        self._set_status("就绪，可以开始配置宏。" if IS_WINDOWS else "预览模式：真实点击和按键需要在 Windows 上运行。")

    def _build_variables(self) -> None:
        self.point_name_var = tk.StringVar(value="点位 1")
        self.point_x_var = tk.StringVar(value="0")
        self.point_y_var = tk.StringVar(value="0")
        self.step_action_var = tk.StringVar(value=ACTION_CLICK_LABEL)
        self.step_point_var = tk.StringVar(value="")
        self.step_key_var = tk.StringVar(value="Enter")
        self.step_delay_var = tk.StringVar(value="500")
        self.step_repeats_var = tk.StringVar(value="1")
        self.step_interval_var = tk.StringVar(value="80")
        self.loop_count_var = tk.StringVar(value="1")
        self.mouse_mode_var = tk.StringVar(value="光标移动（旧版，优先尝试）")
        self.click_mode_var = tk.StringVar(value="分离点击（推荐）")
        self.click_hold_var = tk.StringVar(value="60")
        self.keyboard_mode_var = tk.StringVar(value="虚拟键（旧版，优先尝试）")
        self.status_var = tk.StringVar(value="")

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        font = ("Microsoft YaHei UI", 10)
        title_font = ("Microsoft YaHei UI", 20, "bold")
        subtitle_font = ("Microsoft YaHei UI", 10)
        heading_font = ("Microsoft YaHei UI", 10, "bold")

        style.configure(".", font=font)
        style.configure("App.TFrame", background="#eef3f8")
        style.configure("Header.TFrame", background="#eef3f8")
        style.configure("Title.TLabel", background="#eef3f8", foreground="#172033", font=title_font)
        style.configure("Subtitle.TLabel", background="#eef3f8", foreground="#5d6b82", font=subtitle_font)
        style.configure("Card.TLabelframe", background="#ffffff", bordercolor="#d9e2ef", relief="solid")
        style.configure(
            "Card.TLabelframe.Label",
            background="#eef3f8",
            foreground="#243044",
            font=heading_font,
        )
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("TLabel", background="#ffffff", foreground="#243044")
        style.configure("Muted.TLabel", background="#ffffff", foreground="#68778d")
        style.configure("Status.TLabel", background="#ffffff", foreground="#335074")
        style.configure("TEntry", fieldbackground="#ffffff", bordercolor="#cbd7e6", lightcolor="#cbd7e6")
        style.configure("TCombobox", fieldbackground="#ffffff", bordercolor="#cbd7e6", lightcolor="#cbd7e6")
        style.configure("TButton", padding=(12, 7), background="#edf3fa", foreground="#1f2a3d")
        style.map("TButton", background=[("active", "#e0e9f5")])
        style.configure("Accent.TButton", background="#2563eb", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#1d4ed8")], foreground=[("active", "#ffffff")])
        style.configure("Danger.TButton", background="#fee2e2", foreground="#991b1b")
        style.map("Danger.TButton", background=[("active", "#fecaca")])
        style.configure("Treeview", rowheight=30, background="#ffffff", fieldbackground="#ffffff", foreground="#172033")
        style.configure("Treeview.Heading", font=heading_font, background="#e8eef6", foreground="#253246")
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#172033")])

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main = ttk.Frame(self, padding=16, style="App.TFrame")
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(1, weight=1)

        self._build_header(main)
        self._build_points_panel(main)
        self._build_steps_panel(main)
        self._build_run_panel(main)
        self._build_menu()

        self.bind_all("<F5>", lambda _event: self.start_macro())
        self.bind_all("<F6>", lambda _event: self.toggle_pause())
        self.bind_all("<F7>", lambda _event: self.stop_macro())

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Header.TFrame")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="自动点击器", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="坐标点击和键盘按键可以混排执行", style="Subtitle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(3, 0)
        )

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="新建宏", command=self.new_macro)
        file_menu.add_command(label="打开宏...", command=self.open_macro)
        file_menu.add_command(label="保存宏...", command=self.save_macro)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.destroy)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        self.config(menu=menu_bar)

    def _build_points_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="目标点", padding=12, style="Card.TLabelframe")
        frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.points_tree = ttk.Treeview(
            frame,
            columns=("name", "x", "y"),
            show="headings",
            selectmode="browse",
            height=12,
        )
        self.points_tree.heading("name", text="名称")
        self.points_tree.heading("x", text="X 坐标")
        self.points_tree.heading("y", text="Y 坐标")
        self.points_tree.column("name", width=180, anchor="w")
        self.points_tree.column("x", width=90, anchor="e")
        self.points_tree.column("y", width=90, anchor="e")
        self.points_tree.grid(row=0, column=0, sticky="nsew")
        self.points_tree.bind("<<TreeviewSelect>>", self._on_point_select)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.points_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.points_tree.configure(yscrollcommand=scrollbar.set)

        form = ttk.Frame(frame, style="Card.TFrame")
        form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        for column in range(5):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="名称").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.point_name_var, width=12).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Label(form, text="X").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.point_x_var, width=8).grid(row=1, column=1, sticky="ew", padx=(0, 8))
        ttk.Label(form, text="Y").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.point_y_var, width=8).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Button(form, text="新增点位", command=self.add_point, style="Accent.TButton").grid(
            row=1, column=3, sticky="ew", padx=(0, 8)
        )
        ttk.Button(form, text="更新选中", command=self.update_selected_point).grid(row=1, column=4, sticky="ew")

        actions = ttk.Frame(frame, style="Card.TFrame")
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for column in range(3):
            actions.columnconfigure(column, weight=1)

        ttk.Button(actions, text="3 秒捕获新增", command=self.capture_point_later).grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(actions, text="取消选择", command=self.clear_point_selection).grid(
            row=0, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Button(actions, text="删除选中", command=self.delete_point, style="Danger.TButton").grid(
            row=0, column=2, sticky="ew"
        )

    def _build_steps_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="宏步骤", padding=12, style="Card.TLabelframe")
        frame.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.steps_tree = ttk.Treeview(
            frame,
            columns=("order", "action", "detail", "delay", "repeats", "interval"),
            show="headings",
            selectmode="browse",
            height=12,
        )
        headings = {
            "order": "#",
            "action": "类型",
            "detail": "目标 / 按键",
            "delay": "等待(ms)",
            "repeats": "次数",
            "interval": "间隔(ms)",
        }
        widths = {"order": 42, "action": 78, "detail": 170, "delay": 82, "repeats": 60, "interval": 82}
        for column, text in headings.items():
            self.steps_tree.heading(column, text=text)
            anchor = "w" if column in {"action", "detail"} else "e"
            self.steps_tree.column(column, width=widths[column], anchor=anchor)
        self.steps_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.steps_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.steps_tree.configure(yscrollcommand=scrollbar.set)

        form = ttk.Frame(frame, style="Card.TFrame")
        form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        for column in range(6):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="操作").grid(row=0, column=0, sticky="w")
        self.action_combo = ttk.Combobox(
            form,
            textvariable=self.step_action_var,
            state="readonly",
            values=[ACTION_CLICK_LABEL, ACTION_KEY_LABEL],
            width=10,
        )
        self.action_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.action_combo.bind("<<ComboboxSelected>>", lambda _event: self._sync_action_fields())

        ttk.Label(form, text="目标点").grid(row=0, column=1, sticky="w")
        self.point_combo = ttk.Combobox(form, textvariable=self.step_point_var, state="readonly", width=16)
        self.point_combo.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="按键").grid(row=0, column=2, sticky="w")
        self.key_combo = ttk.Combobox(form, textvariable=self.step_key_var, values=COMMON_KEYS, width=14)
        self.key_combo.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        self.key_combo.bind("<FocusIn>", lambda _event: self._set_status("按键可输入 A、B、C、D、Enter、F5、Ctrl+C 等。"))

        ttk.Label(form, text="等待").grid(row=0, column=3, sticky="w")
        ttk.Entry(form, textvariable=self.step_delay_var, width=8).grid(row=1, column=3, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="次数").grid(row=0, column=4, sticky="w")
        ttk.Entry(form, textvariable=self.step_repeats_var, width=8).grid(row=1, column=4, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="间隔").grid(row=0, column=5, sticky="w")
        ttk.Entry(form, textvariable=self.step_interval_var, width=8).grid(row=1, column=5, sticky="ew")

        buttons = ttk.Frame(frame, style="Card.TFrame")
        buttons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for column in range(4):
            buttons.columnconfigure(column, weight=1)

        ttk.Button(buttons, text="添加步骤", command=self.add_step, style="Accent.TButton").grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        ttk.Button(buttons, text="上移", command=lambda: self.move_step(-1)).grid(
            row=0, column=1, sticky="ew", padx=(0, 8)
        )
        ttk.Button(buttons, text="下移", command=lambda: self.move_step(1)).grid(
            row=0, column=2, sticky="ew", padx=(0, 8)
        )
        ttk.Button(buttons, text="删除步骤", command=self.delete_step, style="Danger.TButton").grid(
            row=0, column=3, sticky="ew"
        )

    def _build_run_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="运行控制", padding=12, style="Card.TLabelframe")
        frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(16, 0))
        for column in range(6):
            frame.columnconfigure(column, weight=1)

        ttk.Label(frame, text="循环次数（0 为无限）").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, text="鼠标模式").grid(row=0, column=1, sticky="w")
        ttk.Label(frame, text="点击模式").grid(row=0, column=2, sticky="w")
        ttk.Label(frame, text="按住(ms)").grid(row=0, column=3, sticky="w")
        ttk.Label(frame, text="键盘模式").grid(row=0, column=4, sticky="w")
        ttk.Entry(frame, textvariable=self.loop_count_var, width=10).grid(row=1, column=0, sticky="ew", padx=(0, 10))
        ttk.Combobox(
            frame,
            textvariable=self.mouse_mode_var,
            state="readonly",
            values=list(MOUSE_MODE_LABELS),
            width=18,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 10))
        ttk.Combobox(
            frame,
            textvariable=self.click_mode_var,
            state="readonly",
            values=list(CLICK_MODE_LABELS),
            width=16,
        ).grid(row=1, column=2, sticky="ew", padx=(0, 10))
        ttk.Entry(frame, textvariable=self.click_hold_var, width=8).grid(row=1, column=3, sticky="ew", padx=(0, 10))
        ttk.Combobox(
            frame,
            textvariable=self.keyboard_mode_var,
            state="readonly",
            values=list(KEYBOARD_MODE_LABELS),
            width=18,
        ).grid(row=1, column=4, sticky="ew", padx=(0, 10))

        buttons = ttk.Frame(frame, style="Card.TFrame")
        buttons.grid(row=2, column=0, columnspan=6, sticky="ew", pady=(10, 0))
        for column in range(5):
            buttons.columnconfigure(column, weight=1)

        ttk.Button(buttons, text="开始 F5", command=self.start_macro, style="Accent.TButton").grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        ttk.Button(buttons, text="暂停 / 继续 F6", command=self.toggle_pause).grid(
            row=0, column=1, sticky="ew", padx=(0, 10)
        )
        ttk.Button(buttons, text="停止 F7", command=self.stop_macro, style="Danger.TButton").grid(
            row=0, column=2, sticky="ew", padx=(0, 10)
        )
        ttk.Button(buttons, text="保存宏", command=self.save_macro).grid(row=0, column=3, sticky="ew", padx=(0, 10))
        ttk.Button(buttons, text="打开宏", command=self.open_macro).grid(row=0, column=4, sticky="ew")

        status = ttk.Label(frame, textvariable=self.status_var, anchor="w", style="Status.TLabel")
        status.grid(row=3, column=0, columnspan=6, sticky="ew", pady=(12, 0))

    def add_point(self) -> None:
        payload = self._point_form_payload()
        if payload is None:
            return

        name, x, y = payload
        self.macro.points.append(TargetPoint(name=name, x=x, y=y))
        self.selected_point_id = None
        self.point_name_var.set(f"点位 {len(self.macro.points) + 1}")
        self._set_status(f"已新增：{name}。当前共有 {len(self.macro.points)} 个目标点。")
        self._refresh_all()

    def update_selected_point(self) -> None:
        if not self.selected_point_id:
            messagebox.showinfo("未选择目标点", "请先在目标点列表中选择要更新的点位。")
            return

        payload = self._point_form_payload()
        if payload is None:
            return

        point = self._find_point(self.selected_point_id)
        if point is None:
            self.selected_point_id = None
            self._refresh_all()
            messagebox.showerror("目标点不存在", "选中的目标点已经不存在。")
            return

        name, x, y = payload
        point.name = name
        point.x = x
        point.y = y
        self._set_status(f"已更新：{name}")
        self._refresh_all()

    def clear_point_selection(self) -> None:
        self.selected_point_id = None
        selected = self.points_tree.selection()
        if selected:
            self.points_tree.selection_remove(*selected)
        self.points_tree.focus("")
        self.point_name_var.set(f"点位 {len(self.macro.points) + 1}")
        self.point_x_var.set("0")
        self.point_y_var.set("0")
        self._set_status("已取消选择。填写坐标后可继续新增点位。")

    def _point_form_payload(self) -> tuple[str, int, int] | None:
        try:
            name = self.point_name_var.get().strip() or f"点位 {len(self.macro.points) + 1}"
            x = int(self.point_x_var.get())
            y = int(self.point_y_var.get())
        except ValueError:
            messagebox.showerror("点位无效", "X 和 Y 坐标必须是整数。")
            return None
        return name, x, y

    def capture_point_later(self) -> None:
        if self.capture_after_id is not None:
            self.after_cancel(self.capture_after_id)
            self.capture_after_id = None

        self._countdown_capture(3)

    def _countdown_capture(self, seconds_left: int) -> None:
        if seconds_left > 0:
            self._set_status(f"请把鼠标移动到目标位置，{seconds_left} 秒后捕获。")
            self.capture_after_id = self.after(1000, lambda: self._countdown_capture(seconds_left - 1))
            return

        x, y = self.winfo_pointerxy()
        self.point_x_var.set(str(x))
        self.point_y_var.set(str(y))
        if not self.point_name_var.get().strip():
            self.point_name_var.set(f"点位 {len(self.macro.points) + 1}")
        self.capture_after_id = None
        self.add_point()

    def delete_point(self) -> None:
        if not self.selected_point_id:
            return
        point = self._find_point(self.selected_point_id)
        self.macro.points = [item for item in self.macro.points if item.id != self.selected_point_id]
        self.macro.steps = [step for step in self.macro.steps if step.target_id != self.selected_point_id]
        self.selected_point_id = None
        self._set_status(f"已删除：{point.name if point else '目标点'}")
        self._refresh_all()

    def add_step(self) -> None:
        action = ACTION_LABEL_TO_VALUE.get(self.step_action_var.get(), "click")
        try:
            delay_ms = int(self.step_delay_var.get())
            repeats = int(self.step_repeats_var.get())
            interval_ms = int(self.step_interval_var.get())
        except ValueError:
            messagebox.showerror("步骤无效", "等待、次数、间隔必须是整数。")
            return

        if action == "click":
            point = self._point_from_combo_label(self.step_point_var.get())
            if point is None:
                messagebox.showerror("缺少目标点", "请先选择一个目标点。")
                return
            step = MacroStep(
                action="click",
                target_id=point.id,
                delay_ms=delay_ms,
                clicks=repeats,
                interval_ms=interval_ms,
            )
            summary = point.name
        else:
            keys = self.step_key_var.get().strip()
            try:
                parse_key_combination(keys)
            except ValueError as error:
                messagebox.showerror("按键无效", str(error))
                return
            step = MacroStep(action="key", keys=keys, delay_ms=delay_ms, clicks=repeats, interval_ms=interval_ms)
            summary = keys

        errors = Macro(points=self.macro.points, steps=[step]).validate()
        if errors:
            messagebox.showerror("步骤无效", "\n".join(errors))
            return

        self.macro.steps.append(step)
        self._set_status(f"已添加步骤：{summary}")
        self._refresh_steps(select_index=len(self.macro.steps) - 1)

    def delete_step(self) -> None:
        index = self._selected_step_index()
        if index is None:
            return
        del self.macro.steps[index]
        self._set_status("已删除所选步骤。")
        self._refresh_steps()

    def move_step(self, direction: int) -> None:
        index = self._selected_step_index()
        if index is None:
            return
        new_index = index + direction
        if new_index < 0 or new_index >= len(self.macro.steps):
            return
        self.macro.steps[index], self.macro.steps[new_index] = self.macro.steps[new_index], self.macro.steps[index]
        self._refresh_steps(select_index=new_index)

    def start_macro(self) -> None:
        if self.runner.is_running:
            return
        try:
            loop_count = int(self.loop_count_var.get())
            click_hold_ms = int(self.click_hold_var.get())
            if click_hold_ms < 0:
                raise ValueError("按住时间必须大于等于 0。")
            self._configure_input_modes()
            self.runner.start(self.macro, loop_count=loop_count)
        except Exception as error:
            messagebox.showerror("无法开始", str(error))

    def _configure_input_modes(self) -> None:
        backend = self.runner.backend
        if not hasattr(backend, "configure_modes"):
            return
        mouse_mode = MOUSE_MODE_LABELS.get(self.mouse_mode_var.get(), MOUSE_MODE_CURSOR)
        click_mode = CLICK_MODE_LABELS.get(self.click_mode_var.get(), CLICK_MODE_SEPARATE)
        keyboard_mode = KEYBOARD_MODE_LABELS.get(self.keyboard_mode_var.get(), KEYBOARD_MODE_VIRTUAL_KEY)
        backend.configure_modes(
            mouse_mode=mouse_mode,
            click_mode=click_mode,
            click_hold_ms=int(self.click_hold_var.get()),
            keyboard_mode=keyboard_mode,
        )

    def toggle_pause(self) -> None:
        if not self.runner.is_running:
            return
        if self.runner.is_paused:
            self.runner.resume()
        else:
            self.runner.pause()

    def stop_macro(self) -> None:
        self.runner.stop()
        self._set_status("正在停止...")

    def new_macro(self) -> None:
        if self.runner.is_running:
            messagebox.showwarning("宏正在运行", "请先停止当前宏。")
            return
        self.macro = Macro()
        self.selected_point_id = None
        self.point_name_var.set("点位 1")
        self.point_x_var.set("0")
        self.point_y_var.set("0")
        self.step_action_var.set(ACTION_CLICK_LABEL)
        self.step_key_var.set("Enter")
        self._refresh_all()
        self._sync_action_fields()
        self._set_status("已新建宏。")

    def save_macro(self) -> None:
        path = filedialog.asksaveasfilename(
            title="保存宏",
            defaultextension=".json",
            filetypes=[("自动点击器宏", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        Path(path).write_text(json.dumps(self.macro.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        self._set_status(f"已保存：{path}")

    def open_macro(self) -> None:
        if self.runner.is_running:
            messagebox.showwarning("宏正在运行", "请先停止当前宏。")
            return
        path = filedialog.askopenfilename(
            title="打开宏",
            filetypes=[("自动点击器宏", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.macro = Macro.from_dict(data)
        except Exception as error:
            messagebox.showerror("无法打开宏", str(error))
            return
        self.selected_point_id = None
        self._refresh_all()
        self._set_status(f"已打开：{path}")

    def _handle_runner_event(self, event: dict[str, Any]) -> None:
        self.after(0, lambda: self._apply_runner_event(event))

    def _apply_runner_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "started":
            loops = event.get("loop_count")
            loop_text = "无限循环" if loops == 0 else f"{loops} 次"
            self._set_status(f"正在运行：{loop_text}。按 F7 可停止。")
        elif event_type == "step_started":
            if event.get("action") == "click":
                self._set_status(
                    f"第 {event['loop']} 轮，第 {event['step_index']} 步：点击 {event['target']} "
                    f"({event['x']}, {event['y']})。"
                )
            else:
                self._set_status(f"第 {event['loop']} 轮，第 {event['step_index']} 步：按键 {event['keys']}。")
        elif event_type == "clicked":
            self._set_status(f"已点击 {event['target']}，第 {event['repeat_index']} 次。")
        elif event_type == "key_pressed":
            self._set_status(f"已按键 {event['keys']}，第 {event['repeat_index']} 次。")
        elif event_type == "paused":
            self._set_status("已暂停。")
        elif event_type == "resumed":
            self._set_status("已继续。")
        elif event_type == "stopped":
            self._set_status("已停止。")
        elif event_type == "finished":
            self._set_status(f"已完成 {event.get('completed_loops', 0)} 轮。")
        elif event_type == "error":
            self._set_status(f"错误：{event.get('message')}")
            messagebox.showerror("宏运行错误", str(event.get("message")))

    def _on_point_select(self, _event: object) -> None:
        selected = self.points_tree.selection()
        if not selected:
            self.selected_point_id = None
            return
        self.selected_point_id = selected[0]
        point = self._find_point(self.selected_point_id)
        if point is not None:
            self.point_name_var.set(point.name)
            self.point_x_var.set(str(point.x))
            self.point_y_var.set(str(point.y))

    def _sync_action_fields(self) -> None:
        action = ACTION_LABEL_TO_VALUE.get(self.step_action_var.get(), "click")
        if action == "click":
            self.point_combo.configure(state="readonly")
            self.key_combo.configure(state="disabled")
        else:
            self.point_combo.configure(state="disabled")
            self.key_combo.configure(state="normal")

    def _refresh_all(self) -> None:
        self._refresh_points()
        self._refresh_steps()
        self._refresh_point_combo()

    def _refresh_points(self) -> None:
        self.points_tree.delete(*self.points_tree.get_children())
        for point in self.macro.points:
            self.points_tree.insert("", "end", iid=point.id, values=(point.name, point.x, point.y))
        if self.selected_point_id and self._find_point(self.selected_point_id):
            self.points_tree.selection_set(self.selected_point_id)
            self.points_tree.focus(self.selected_point_id)
        else:
            self.selected_point_id = None

    def _refresh_steps(self, select_index: int | None = None) -> None:
        self.steps_tree.delete(*self.steps_tree.get_children())
        point_map = self.macro.point_map()
        for index, step in enumerate(self.macro.steps):
            action_label = ACTION_VALUE_TO_LABEL.get(step.action, step.action)
            if step.action == "click":
                point = point_map.get(step.target_id)
                detail = f"{point.name} ({point.x}, {point.y})" if point else "目标点不存在"
            else:
                detail = step.keys
            self.steps_tree.insert(
                "",
                "end",
                iid=step.id,
                values=(index + 1, action_label, detail, step.delay_ms, step.clicks, step.interval_ms),
            )
        if select_index is not None and 0 <= select_index < len(self.macro.steps):
            step_id = self.macro.steps[select_index].id
            self.steps_tree.selection_set(step_id)
            self.steps_tree.focus(step_id)

    def _refresh_point_combo(self) -> None:
        labels = [self._combo_label(point) for point in self.macro.points]
        self.point_combo["values"] = labels
        if labels and self.step_point_var.get() not in labels:
            self.step_point_var.set(labels[0])
        elif not labels:
            self.step_point_var.set("")

    def _find_point(self, point_id: str) -> TargetPoint | None:
        return next((point for point in self.macro.points if point.id == point_id), None)

    def _combo_label(self, point: TargetPoint) -> str:
        return f"{point.name} ({point.x}, {point.y})"

    def _point_from_combo_label(self, label: str) -> TargetPoint | None:
        for point in self.macro.points:
            if self._combo_label(point) == label:
                return point
        return None

    def _selected_step_index(self) -> int | None:
        selected = self.steps_tree.selection()
        if not selected:
            return None
        step_id = selected[0]
        for index, step in enumerate(self.macro.steps):
            if step.id == step_id:
                return index
        return None

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)


if __name__ == "__main__":
    ClickMacroApp().mainloop()
