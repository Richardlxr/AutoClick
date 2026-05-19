import unittest

from clicker.windows_input import parse_key_combination, virtual_key_for_name


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


if __name__ == "__main__":
    unittest.main()
