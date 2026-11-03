from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NativeDesktopInteractionTests(unittest.TestCase):
    def test_native_shell_has_context_properties_rename_and_double_click(self):
        source = (ROOT / "desktop/native/chimera-desktop-shell.cpp").read_text(encoding="utf-8")
        for token in (
            "show_app_context_menu", "show_app_properties", "rename_app_card",
            "desktop_menu_bar", "gtk_menu_button_new", "desktop_menu_action",
            "card_pointer_pressed", "n_press == 2", "GDK_KEY_F2",
            "GDK_KEY_Return", "GDK_KEY_F10",
        ):
            self.assertIn(token, source)

    def test_native_shell_has_cross_platform_shortcuts_and_depth_controls(self):
        source = (ROOT / "desktop/native/chimera-desktop-shell.cpp").read_text(encoding="utf-8")
        for token in ("GDK_KEY_t", "GDK_KEY_e", "GDK_SUPER_MASK", "box-shadow", "button.accent:active"):
            self.assertIn(token, source)

    def test_voiceconnect_is_registered_as_an_optional_desktop_card(self):
        source = (ROOT / "desktop/native/chimera-desktop-shell.cpp").read_text(encoding="utf-8")
        self.assertIn('"voiceconnect"', source)
        self.assertIn("voiceconnect-launcher.sh", source)
        self.assertIn("https://github.com/amerhwitat/test/tree/feat/voiceconnect-p2p-camera", source)


if __name__ == "__main__":
    unittest.main()
