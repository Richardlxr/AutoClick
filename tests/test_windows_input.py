import unittest

from clicker.windows_input import (
    ScreenBounds,
    absolute_mouse_coordinates,
    parse_key_combination,
    validate_screen_point,
    virtual_key_for_name,
)


class WindowsInputTests(unittest.TestCase):
    def test_parse_key_combination_supports_common_shortcuts(self) -> None:
        self.assertEqual(parse_key_combination("Ctrl+C"), [0x11, ord("C")])
        self.assertEqual(parse_key_combination("Alt + Tab"), [0x12, 0x09])

    def test_parse_key_combination_supports_plain_letter_keys(self) -> None:
        self.assertEqual(parse_key_combination("A"), [ord("A")])
        self.assertEqual(parse_key_combination("B"), [ord("B")])
        self.assertEqual(parse_key_combination("C"), [ord("C")])
        self.assertEqual(parse_key_combination("D"), [ord("D")])

    def test_virtual_key_for_name_supports_aliases(self) -> None:
        self.assertEqual(virtual_key_for_name("Enter"), 0x0D)
        self.assertEqual(virtual_key_for_name("F5"), 0x74)
        self.assertEqual(virtual_key_for_name("Page Up"), 0x21)

    def test_parse_key_combination_rejects_empty_input(self) -> None:
        with self.assertRaises(ValueError):
            parse_key_combination("")

    def test_validate_screen_point_accepts_points_inside_virtual_screen(self) -> None:
        bounds = ScreenBounds(left=-100, top=10, width=300, height=200)

        validate_screen_point(-100, 10, bounds)
        validate_screen_point(199, 209, bounds)

    def test_validate_screen_point_rejects_points_outside_virtual_screen(self) -> None:
        bounds = ScreenBounds(left=0, top=0, width=1920, height=1080)

        with self.assertRaisesRegex(ValueError, "目标坐标"):
            validate_screen_point(1920, 100, bounds)

    def test_absolute_mouse_coordinates_normalize_virtual_screen_points(self) -> None:
        bounds = ScreenBounds(left=0, top=0, width=1920, height=1080)

        self.assertEqual(absolute_mouse_coordinates(0, 0, bounds), (0, 0))
        self.assertEqual(absolute_mouse_coordinates(1919, 1079, bounds), (65535, 65535))

    def test_absolute_mouse_coordinates_support_negative_virtual_screen_origin(self) -> None:
        bounds = ScreenBounds(left=-1920, top=0, width=3840, height=1080)

        self.assertEqual(absolute_mouse_coordinates(-1920, 0, bounds), (0, 0))
        self.assertEqual(absolute_mouse_coordinates(1919, 1079, bounds), (65535, 65535))


if __name__ == "__main__":
    unittest.main()
