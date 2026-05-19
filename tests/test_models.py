import unittest

from clicker.models import Macro, MacroStep, TargetPoint


class MacroModelTests(unittest.TestCase):
    def test_macro_round_trips_to_dict(self) -> None:
        point = TargetPoint(name="A", x=10, y=20, id="point-a")
        step = MacroStep(target_id="point-a", delay_ms=100, clicks=2, interval_ms=30, id="step-a")
        macro = Macro(points=[point], steps=[step])

        restored = Macro.from_dict(macro.to_dict())

        self.assertEqual(restored.points[0].name, "A")
        self.assertEqual(restored.points[0].x, 10)
        self.assertEqual(restored.steps[0].action, "click")
        self.assertEqual(restored.steps[0].target_id, "point-a")
        self.assertEqual(restored.steps[0].clicks, 2)

    def test_key_step_round_trips_to_dict_without_points(self) -> None:
        macro = Macro(steps=[MacroStep(action="key", keys="Ctrl+C", clicks=2)])

        restored = Macro.from_dict(macro.to_dict())

        self.assertEqual(restored.steps[0].action, "key")
        self.assertEqual(restored.steps[0].keys, "Ctrl+C")
        self.assertEqual(restored.validate(), [])

    def test_validate_reports_missing_step_target(self) -> None:
        macro = Macro(
            points=[TargetPoint(name="A", x=10, y=20, id="point-a")],
            steps=[MacroStep(target_id="missing")],
        )

        self.assertIn("第 1 步引用了不存在的目标点。", macro.validate())

    def test_validate_reports_missing_key_name(self) -> None:
        macro = Macro(steps=[MacroStep(action="key", keys="")])

        self.assertIn("第 1 步缺少键盘按键。", macro.validate())


if __name__ == "__main__":
    unittest.main()
