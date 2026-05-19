from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import Macro


class ClickBackend(Protocol):
    def click(self, x: int, y: int, button: str = "left") -> None:
        ...


EventCallback = Callable[[dict[str, Any]], None]
StopPredicate = Callable[[], bool]


@dataclass
class DryRunClickBackend:
    clicks: list[tuple[int, int, str]] = field(default_factory=list)

    def click(self, x: int, y: int, button: str = "left") -> None:
        self.clicks.append((x, y, button))


class MacroRunner:
    def __init__(
        self,
        backend: ClickBackend,
        on_event: EventCallback | None = None,
        stop_predicate: StopPredicate | None = None,
    ) -> None:
        self.backend = backend
        self.on_event = on_event
        self.stop_predicate = stop_predicate
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def start(self, macro: Macro, loop_count: int = 1) -> None:
        with self._lock:
            if self.is_running:
                raise RuntimeError("Macro is already running.")
            errors = macro.validate()
            if errors:
                raise ValueError("\n".join(errors))
            if loop_count < 0:
                raise ValueError("Loop count must be 0 or greater.")

            self._stop_event.clear()
            self._pause_event.clear()
            snapshot = macro.clone()
            self._thread = threading.Thread(
                target=self._run,
                args=(snapshot, loop_count),
                name="MacroRunner",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._pause_event.clear()

    def pause(self) -> None:
        if self.is_running:
            self._pause_event.set()
            self._emit({"type": "paused"})

    def resume(self) -> None:
        if self.is_running:
            self._pause_event.clear()
            self._emit({"type": "resumed"})

    def wait(self, timeout: float | None = None) -> None:
        thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)

    def _run(self, macro: Macro, loop_count: int) -> None:
        point_map = macro.point_map()
        completed_loops = 0
        self._emit({"type": "started", "loop_count": loop_count})

        try:
            while not self._should_stop():
                if loop_count and completed_loops >= loop_count:
                    break

                completed_loops += 1
                self._emit({"type": "loop_started", "loop": completed_loops})

                for step_index, step in enumerate(macro.steps, start=1):
                    if self._should_stop():
                        break

                    target = point_map[step.target_id]
                    self._emit(
                        {
                            "type": "step_started",
                            "loop": completed_loops,
                            "step_index": step_index,
                            "target": target.name,
                            "x": target.x,
                            "y": target.y,
                        }
                    )

                    if not self._wait_ms(step.delay_ms):
                        break

                    for click_index in range(1, step.clicks + 1):
                        if self._should_stop():
                            break
                        self.backend.click(target.x, target.y, step.button)
                        self._emit(
                            {
                                "type": "clicked",
                                "loop": completed_loops,
                                "step_index": step_index,
                                "click_index": click_index,
                                "target": target.name,
                                "x": target.x,
                                "y": target.y,
                            }
                        )
                        if click_index < step.clicks and not self._wait_ms(step.interval_ms):
                            break

            final_type = "stopped" if self._stop_event.is_set() else "finished"
            self._emit({"type": final_type, "completed_loops": completed_loops})
        except Exception as error:
            self._emit({"type": "error", "message": str(error)})
        finally:
            self._stop_event.set()
            self._pause_event.clear()

    def _wait_ms(self, delay_ms: int) -> bool:
        remaining = max(0, delay_ms) / 1000
        last_tick = time.monotonic()
        while remaining > 0:
            if self._should_stop():
                return False
            if self._pause_event.is_set():
                self._wait_if_paused()
                last_tick = time.monotonic()
                continue

            sleep_for = min(0.03, remaining)
            time.sleep(sleep_for)
            now = time.monotonic()
            remaining -= now - last_tick
            last_tick = now
        return not self._should_stop()

    def _wait_if_paused(self) -> None:
        while self._pause_event.is_set() and not self._should_stop():
            time.sleep(0.05)

    def _should_stop(self) -> bool:
        if self._stop_event.is_set():
            return True
        if self.stop_predicate is not None and self.stop_predicate():
            self._stop_event.set()
            return True
        return False

    def _emit(self, event: dict[str, Any]) -> None:
        if self.on_event is not None:
            self.on_event(event)
