import unittest

from clicker.models import Macro, MacroStep, TargetPoint
from clicker.runner import DryRunClickBackend, MacroRunner


class MacroRunnerTests(unittest.TestCase):
    def test_runner_clicks_steps_in_order_for_each_loop(self) -> None:
        backend = DryRunClickBackend()
        events: list[str] = []
        macro = Macro(
            points=[
                TargetPoint(name="A", x=10, y=20, id="a"),
                TargetPoint(name="B", x=30, y=40, id="b"),
            ],
            steps=[
                MacroStep(target_id="a", clicks=1, interval_ms=0),
                MacroStep(target_id="b", clicks=2, interval_ms=0),
            ],
        )
        runner = MacroRunner(backend=backend, on_event=lambda event: events.append(event["type"]))

        runner.start(macro, loop_count=2)
        runner.wait(timeout=2)

        self.assertEqual(
            backend.clicks,
            [
                (10, 20, "left"),
                (30, 40, "left"),
                (30, 40, "left"),
                (10, 20, "left"),
                (30, 40, "left"),
                (30, 40, "left"),
            ],
        )
        self.assertIn("finished", events)

    def test_runner_rejects_invalid_macro(self) -> None:
        runner = MacroRunner(backend=DryRunClickBackend())
        macro = Macro(points=[], steps=[])

        with self.assertRaises(ValueError):
            runner.start(macro)


if __name__ == "__main__":
    unittest.main()
