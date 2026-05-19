from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex[:10]


@dataclass(slots=True)
class TargetPoint:
    name: str
    x: int
    y: int
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TargetPoint":
        return cls(
            id=str(data.get("id") or new_id()),
            name=str(data.get("name") or "Point"),
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
        )


@dataclass(slots=True)
class MacroStep:
    target_id: str = ""
    delay_ms: int = 0
    clicks: int = 1
    interval_ms: int = 80
    button: str = "left"
    action: str = "click"
    keys: str = ""
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "target_id": self.target_id,
            "keys": self.keys,
            "delay_ms": self.delay_ms,
            "clicks": self.clicks,
            "interval_ms": self.interval_ms,
            "button": self.button,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroStep":
        return cls(
            id=str(data.get("id") or new_id()),
            action=str(data.get("action") or "click"),
            target_id=str(data.get("target_id") or ""),
            keys=str(data.get("keys") or ""),
            delay_ms=int(data.get("delay_ms", 0)),
            clicks=int(data.get("clicks", 1)),
            interval_ms=int(data.get("interval_ms", 80)),
            button=str(data.get("button") or "left"),
        )


@dataclass(slots=True)
class Macro:
    points: list[TargetPoint] = field(default_factory=list)
    steps: list[MacroStep] = field(default_factory=list)

    def point_map(self) -> dict[str, TargetPoint]:
        return {point.id: point for point in self.points}

    def validate(self) -> list[str]:
        errors: list[str] = []
        point_ids = {point.id for point in self.points}
        has_click_step = any(step.action == "click" for step in self.steps)

        if has_click_step and not self.points:
            errors.append("请至少添加一个目标点。")
        if not self.steps:
            errors.append("请至少添加一个宏步骤。")

        seen_point_ids: set[str] = set()
        for point in self.points:
            if point.id in seen_point_ids:
                errors.append(f"目标点 ID 重复：{point.id}")
            seen_point_ids.add(point.id)

        for index, step in enumerate(self.steps, start=1):
            prefix = f"第 {index} 步"
            if step.action not in {"click", "key"}:
                errors.append(f"{prefix}的操作类型不支持。")
            if step.delay_ms < 0:
                errors.append(f"{prefix}的等待时间必须大于等于 0。")
            if step.clicks < 1:
                errors.append(f"{prefix}的执行次数至少为 1。")
            if step.interval_ms < 0:
                errors.append(f"{prefix}的间隔时间必须大于等于 0。")
            if step.action == "click":
                if step.target_id not in point_ids:
                    errors.append(f"{prefix}引用了不存在的目标点。")
                if step.button not in {"left", "right", "middle"}:
                    errors.append(f"{prefix}的鼠标按键不支持。")
            if step.action == "key" and not step.keys.strip():
                errors.append(f"{prefix}缺少键盘按键。")

        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 2,
            "points": [point.to_dict() for point in self.points],
            "steps": [step.to_dict() for step in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Macro":
        return cls(
            points=[TargetPoint.from_dict(item) for item in data.get("points", [])],
            steps=[MacroStep.from_dict(item) for item in data.get("steps", [])],
        )

    def clone(self) -> "Macro":
        return Macro.from_dict(self.to_dict())
