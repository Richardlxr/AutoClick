from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from clicker.models import Macro, MacroStep, TargetPoint
from clicker.runner import DryRunClickBackend, MacroRunner
from clicker.windows_input import IS_WINDOWS, WindowsClickBackend, is_f7_pressed, make_process_dpi_aware


class ClickMacroApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        make_process_dpi_aware()

        self.title("Click Macro")
        self.geometry("980x640")
        self.minsize(900, 580)

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
        self._build_ui()
        self._refresh_all()
        self._set_status(
            "Ready. Real clicks use Windows SendInput."
            if IS_WINDOWS
            else "Dry-run mode: real clicking is available on Windows."
        )

    def _build_variables(self) -> None:
        self.point_name_var = tk.StringVar(value="P1")
        self.point_x_var = tk.StringVar(value="0")
        self.point_y_var = tk.StringVar(value="0")
        self.step_point_var = tk.StringVar(value="")
        self.step_delay_var = tk.StringVar(value="500")
        self.step_clicks_var = tk.StringVar(value="1")
        self.step_interval_var = tk.StringVar(value="80")
        self.loop_count_var = tk.StringVar(value="1")
        self.status_var = tk.StringVar(value="")

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main = ttk.Frame(self, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        self._build_points_panel(main)
        self._build_steps_panel(main)
        self._build_run_panel(main)
        self._build_menu()

        self.bind_all("<F5>", lambda _event: self.start_macro())
        self.bind_all("<F6>", lambda _event: self.toggle_pause())
        self.bind_all("<F7>", lambda _event: self.stop_macro())

    def _build_menu(self) -> None:
        menu_bar = tk.Menu(self)
        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="New", command=self.new_macro)
        file_menu.add_command(label="Open...", command=self.open_macro)
        file_menu.add_command(label="Save As...", command=self.save_macro)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menu_bar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menu_bar)

    def _build_points_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Target Points", padding=10)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.points_tree = ttk.Treeview(
            frame,
            columns=("name", "x", "y"),
            show="headings",
            selectmode="browse",
            height=12,
        )
        self.points_tree.heading("name", text="Name")
        self.points_tree.heading("x", text="X")
        self.points_tree.heading("y", text="Y")
        self.points_tree.column("name", width=160, anchor="w")
        self.points_tree.column("x", width=90, anchor="e")
        self.points_tree.column("y", width=90, anchor="e")
        self.points_tree.grid(row=0, column=0, sticky="nsew")
        self.points_tree.bind("<<TreeviewSelect>>", self._on_point_select)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.points_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.points_tree.configure(yscrollcommand=scrollbar.set)

        form = ttk.Frame(frame)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for column in range(6):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.point_name_var, width=12).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        ttk.Label(form, text="X").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.point_x_var, width=8).grid(row=1, column=1, sticky="ew", padx=(0, 6))
        ttk.Label(form, text="Y").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.point_y_var, width=8).grid(row=1, column=2, sticky="ew", padx=(0, 6))

        ttk.Button(form, text="Add / Update", command=self.add_or_update_point).grid(
            row=1, column=3, sticky="ew", padx=(0, 6)
        )
        ttk.Button(form, text="Capture in 3s", command=self.capture_point_later).grid(
            row=1, column=4, sticky="ew", padx=(0, 6)
        )
        ttk.Button(form, text="Delete", command=self.delete_point).grid(row=1, column=5, sticky="ew")

    def _build_steps_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Macro Steps", padding=10)
        frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.steps_tree = ttk.Treeview(
            frame,
            columns=("order", "point", "delay", "clicks", "interval"),
            show="headings",
            selectmode="browse",
            height=12,
        )
        headings = {
            "order": "#",
            "point": "Point",
            "delay": "Delay ms",
            "clicks": "Clicks",
            "interval": "Interval ms",
        }
        widths = {"order": 40, "point": 150, "delay": 90, "clicks": 70, "interval": 90}
        for column, text in headings.items():
            self.steps_tree.heading(column, text=text)
            self.steps_tree.column(column, width=widths[column], anchor="e" if column != "point" else "w")
        self.steps_tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.steps_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.steps_tree.configure(yscrollcommand=scrollbar.set)

        form = ttk.Frame(frame)
        form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for column in range(7):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Point").grid(row=0, column=0, sticky="w")
        self.point_combo = ttk.Combobox(form, textvariable=self.step_point_var, state="readonly", width=16)
        self.point_combo.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        ttk.Label(form, text="Delay").grid(row=0, column=1, sticky="w")
        ttk.Entry(form, textvariable=self.step_delay_var, width=8).grid(row=1, column=1, sticky="ew", padx=(0, 6))

        ttk.Label(form, text="Clicks").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.step_clicks_var, width=8).grid(row=1, column=2, sticky="ew", padx=(0, 6))

        ttk.Label(form, text="Interval").grid(row=0, column=3, sticky="w")
        ttk.Entry(form, textvariable=self.step_interval_var, width=8).grid(row=1, column=3, sticky="ew", padx=(0, 6))

        ttk.Button(form, text="Add Step", command=self.add_step).grid(row=1, column=4, sticky="ew", padx=(0, 6))
        ttk.Button(form, text="Up", command=lambda: self.move_step(-1)).grid(row=1, column=5, sticky="ew", padx=(0, 6))
        ttk.Button(form, text="Down", command=lambda: self.move_step(1)).grid(row=1, column=6, sticky="ew")

        ttk.Button(frame, text="Delete Selected Step", command=self.delete_step).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_run_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Run", padding=10)
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        for column in range(8):
            frame.columnconfigure(column, weight=1)

        ttk.Label(frame, text="Loops (0 = forever)").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.loop_count_var, width=10).grid(row=1, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Start (F5)", command=self.start_macro).grid(row=1, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Pause / Resume (F6)", command=self.toggle_pause).grid(
            row=1, column=2, sticky="ew", padx=(0, 8)
        )
        ttk.Button(frame, text="Stop (F7)", command=self.stop_macro).grid(row=1, column=3, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Save", command=self.save_macro).grid(row=1, column=4, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Open", command=self.open_macro).grid(row=1, column=5, sticky="ew")

        status = ttk.Label(frame, textvariable=self.status_var, anchor="w")
        status.grid(row=2, column=0, columnspan=8, sticky="ew", pady=(10, 0))

    def add_or_update_point(self) -> None:
        try:
            name = self.point_name_var.get().strip() or f"P{len(self.macro.points) + 1}"
            x = int(self.point_x_var.get())
            y = int(self.point_y_var.get())
        except ValueError:
            messagebox.showerror("Invalid point", "X and Y must be integers.")
            return

        if self.selected_point_id:
            point = self._find_point(self.selected_point_id)
            if point is not None:
                point.name = name
                point.x = x
                point.y = y
                self._set_status(f"Updated {name}.")
        else:
            self.macro.points.append(TargetPoint(name=name, x=x, y=y))
            self.point_name_var.set(f"P{len(self.macro.points) + 1}")
            self._set_status(f"Added {name}.")
        self._refresh_all()

    def capture_point_later(self) -> None:
        if self.capture_after_id is not None:
            self.after_cancel(self.capture_after_id)
            self.capture_after_id = None

        self._countdown_capture(3)

    def _countdown_capture(self, seconds_left: int) -> None:
        if seconds_left > 0:
            self._set_status(f"Move your cursor to the target point. Capturing in {seconds_left}s...")
            self.capture_after_id = self.after(1000, lambda: self._countdown_capture(seconds_left - 1))
            return

        x, y = self.winfo_pointerxy()
        self.point_x_var.set(str(x))
        self.point_y_var.set(str(y))
        if not self.point_name_var.get().strip():
            self.point_name_var.set(f"P{len(self.macro.points) + 1}")
        self.capture_after_id = None
        self.add_or_update_point()

    def delete_point(self) -> None:
        if not self.selected_point_id:
            return
        point = self._find_point(self.selected_point_id)
        self.macro.points = [item for item in self.macro.points if item.id != self.selected_point_id]
        self.macro.steps = [step for step in self.macro.steps if step.target_id != self.selected_point_id]
        self.selected_point_id = None
        self._set_status(f"Deleted {point.name if point else 'point'} and related steps.")
        self._refresh_all()

    def add_step(self) -> None:
        selected = self.step_point_var.get()
        point = self._point_from_combo_label(selected)
        if point is None:
            messagebox.showerror("Missing point", "Choose a target point first.")
            return
        try:
            delay_ms = int(self.step_delay_var.get())
            clicks = int(self.step_clicks_var.get())
            interval_ms = int(self.step_interval_var.get())
        except ValueError:
            messagebox.showerror("Invalid step", "Delay, clicks, and interval must be integers.")
            return

        step = MacroStep(target_id=point.id, delay_ms=delay_ms, clicks=clicks, interval_ms=interval_ms)
        errors = Macro(points=self.macro.points, steps=[step]).validate()
        if errors:
            messagebox.showerror("Invalid step", "\n".join(errors))
            return

        self.macro.steps.append(step)
        self._set_status(f"Added step for {point.name}.")
        self._refresh_steps()

    def delete_step(self) -> None:
        index = self._selected_step_index()
        if index is None:
            return
        del self.macro.steps[index]
        self._set_status("Deleted selected step.")
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
            self.runner.start(self.macro, loop_count=loop_count)
        except Exception as error:
            messagebox.showerror("Cannot start macro", str(error))

    def toggle_pause(self) -> None:
        if not self.runner.is_running:
            return
        if self.runner.is_paused:
            self.runner.resume()
        else:
            self.runner.pause()

    def stop_macro(self) -> None:
        self.runner.stop()
        self._set_status("Stopping...")

    def new_macro(self) -> None:
        if self.runner.is_running:
            messagebox.showwarning("Macro running", "Stop the macro before creating a new one.")
            return
        self.macro = Macro()
        self.selected_point_id = None
        self.point_name_var.set("P1")
        self.point_x_var.set("0")
        self.point_y_var.set("0")
        self._refresh_all()
        self._set_status("New macro.")

    def save_macro(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Macro",
            defaultextension=".json",
            filetypes=[("Click macro", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        Path(path).write_text(json.dumps(self.macro.to_dict(), indent=2), encoding="utf-8")
        self._set_status(f"Saved {path}.")

    def open_macro(self) -> None:
        if self.runner.is_running:
            messagebox.showwarning("Macro running", "Stop the macro before opening another one.")
            return
        path = filedialog.askopenfilename(
            title="Open Macro",
            filetypes=[("Click macro", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self.macro = Macro.from_dict(data)
        except Exception as error:
            messagebox.showerror("Cannot open macro", str(error))
            return
        self.selected_point_id = None
        self._refresh_all()
        self._set_status(f"Opened {path}.")

    def _handle_runner_event(self, event: dict[str, Any]) -> None:
        self.after(0, lambda: self._apply_runner_event(event))

    def _apply_runner_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type == "started":
            loops = event.get("loop_count")
            loop_text = "forever" if loops == 0 else str(loops)
            self._set_status(f"Running for {loop_text} loop(s). Press F7 to stop.")
        elif event_type == "step_started":
            self._set_status(
                f"Loop {event['loop']} step {event['step_index']}: {event['target']} at ({event['x']}, {event['y']})."
            )
        elif event_type == "clicked":
            self._set_status(
                f"Clicked {event['target']} ({event['click_index']}) at ({event['x']}, {event['y']})."
            )
        elif event_type == "paused":
            self._set_status("Paused.")
        elif event_type == "resumed":
            self._set_status("Resumed.")
        elif event_type == "stopped":
            self._set_status("Stopped.")
        elif event_type == "finished":
            self._set_status(f"Finished {event.get('completed_loops', 0)} loop(s).")
        elif event_type == "error":
            self._set_status(f"Error: {event.get('message')}")
            messagebox.showerror("Macro error", str(event.get("message")))

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
            point = point_map.get(step.target_id)
            point_name = point.name if point else "(missing)"
            self.steps_tree.insert(
                "",
                "end",
                iid=step.id,
                values=(index + 1, point_name, step.delay_ms, step.clicks, step.interval_ms),
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
