import sys
import unittest
from unittest import mock

from bopit import platform


class _FakePygame:
    K_F4 = 290
    K_q = 113
    KMOD_ALT = 1024
    KMOD_META = 256


class PlatformTests(unittest.TestCase):
    def test_openal_is_vendored_only_where_it_can_be_used(self) -> None:
        # Windows and Linux name their OpenAL Soft after the file the loader opens,
        # so the vendored copy is the one that gets used. macOS is not in the table:
        # cyal's wheel there links OpenAL Soft through @loader_path, so a vendored
        # copy could never be the one in use.
        self.assertEqual(platform.OPENAL_LIBRARIES["win32"], ("openal", "OpenAL32.dll"))
        self.assertEqual(platform.OPENAL_LIBRARIES["linux"], ("openal", "libopenal.so.1"))
        self.assertNotIn("darwin", platform.OPENAL_LIBRARIES)

    def test_openal_library_is_none_where_there_is_none(self) -> None:
        from pathlib import Path

        with mock.patch.object(sys, "platform", "darwin"):
            self.assertIsNone(platform.openal_library(Path("/vendor")))
        with mock.patch.object(sys, "platform", "win32"):
            self.assertEqual(platform.openal_library(Path("/vendor")),
                             Path("/vendor/openal/OpenAL32.dll"))

    def test_quit_is_alt_f4_on_windows_and_command_q_on_the_mac(self) -> None:
        with mock.patch.dict(sys.modules, {"pygame": _FakePygame}):
            with mock.patch.object(platform, "WINDOWS", True), \
                 mock.patch.object(platform, "MAC", False):
                self.assertTrue(platform.is_quit(_FakePygame.K_F4, _FakePygame.KMOD_ALT))
                self.assertFalse(platform.is_quit(_FakePygame.K_q, 0))
            with mock.patch.object(platform, "WINDOWS", False), \
                 mock.patch.object(platform, "MAC", True):
                self.assertTrue(platform.is_quit(_FakePygame.K_q, _FakePygame.KMOD_META))
                # A plain q is the Brush command, and must never quit.
                self.assertFalse(platform.is_quit(_FakePygame.K_q, 0))
                self.assertFalse(platform.is_quit(_FakePygame.K_F4, _FakePygame.KMOD_ALT))

    def test_quit_hint(self) -> None:
        with mock.patch.object(platform, "WINDOWS", True):
            self.assertEqual(platform.quit_hint(), "Alt+F4")
        with mock.patch.object(platform, "WINDOWS", False), \
             mock.patch.object(platform, "MAC", True):
            self.assertEqual(platform.quit_hint(), "Command Q")

    def test_built_game_is_the_bundle_on_the_mac(self) -> None:
        from pathlib import Path

        dist = Path("/game/dist")
        with mock.patch.object(platform, "MAC", True):
            self.assertEqual(platform.built_game(dist), dist / "BopIt.app")
        with mock.patch.object(platform, "MAC", False):
            self.assertEqual(platform.built_game(dist), dist / "BopIt")

    def test_user_dir_from_source_is_the_project(self) -> None:
        from pathlib import Path

        with mock.patch.object(platform, "IS_FROZEN", False):
            self.assertEqual(platform.user_dir(Path("/game")), Path("/game"))

    def test_user_dir_in_a_built_mac_app_is_beside_the_bundle(self) -> None:
        from pathlib import Path

        executable = Path("/game/dist/BopIt.app/Contents/MacOS/BopIt")
        with mock.patch.object(platform, "IS_FROZEN", True), \
             mock.patch.object(platform, "MAC", True), \
             mock.patch.object(sys, "executable", str(executable)):
            self.assertEqual(platform.user_dir(Path("/game")), Path("/game/dist"))

    def test_user_dir_in_a_built_windows_game_is_beside_the_executable(self) -> None:
        from pathlib import Path

        # Only the folder rule is being checked, so the path is spelled the way the
        # running platform spells it.
        with mock.patch.object(platform, "IS_FROZEN", True), \
             mock.patch.object(platform, "MAC", False), \
             mock.patch.object(sys, "executable", str(Path("/game") / "BopIt" / "BopIt.exe")):
            self.assertEqual(platform.user_dir(Path("/game")), Path("/game/BopIt"))


if __name__ == "__main__":
    unittest.main()