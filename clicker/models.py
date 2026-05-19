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
    target_id: str
    delay_ms: int = 0
    clicks: int = 1
    interval_ms: int = 80
    button: str = "left"
    id: str = field(default_factory=new_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "target_id": self.target_id,
            "delay_ms": self.delay_ms,
            "clicks": self.clicks,
            "interval_ms": self.interval_ms,
            "button": self.button,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MacroStep":
        return cls(
            id=str(data.get("id") or new_id()),
            target_id=str(data.get("target_id") or ""),
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

        if not self.points:
            errors.append("Add at least one target point.")
        if not self.steps:
            errors.append("Add at least one macro step.")

        seen_point_ids: set[str] = set()
        for point in self.points:
            if point.id in seen_point_ids:
                errors.append(f"Duplicate point id: {point.id}")
            seen_point_ids.add(point.id)

        for index, step in enumerate(self.steps, start=1):
            prefix = f"Step {index}"
            if step.target_id not in point_ids:
                errors.append(f"{prefix} references a missing target point.")
            if step.delay_ms < 0:
                errors.append(f"{prefix} delay must be 0 or greater.")
            if step.clicks < 1:
                errors.append(f"{prefix} click count must be at least 1.")
            if step.interval_ms < 0:
                errors.append(f"{prefix} interval must be 0 or greater.")
            if step.button not in {"left", "right", "middle"}:
                errors.append(f"{prefix} has an unsupported mouse button.")

        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
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
