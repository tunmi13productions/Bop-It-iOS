import random
import unittest
from unittest import mock

from bopit import i18n
from bopit import platform
from bopit.audio import Audio
from bopit.config import LANGUAGE_SOUNDS_DIR
from bopit.engine.banter import Banter


class TranslationTests(unittest.TestCase):
    def tearDown(self) -> None:
        i18n.set_language("en")

    def test_english_is_unchanged(self) -> None:
        i18n.set_language("en")
        self.assertEqual(i18n.tr("Quick Play"), "Quick Play")

    def test_original_translations(self) -> None:
        i18n.set_language("de")
        self.assertEqual(i18n.tr("Quick Play"), "Schnelles Spiel")
        self.assertEqual(i18n.tr("Settings"), "Einstellungen")
        self.assertEqual(i18n.trf("Player %i Time", 3), "Zeit Spieler 3")
        i18n.set_language("es")
        self.assertEqual(i18n.tr("Play again"), "volver a jugar")
        i18n.set_language("fr")
        self.assertEqual(i18n.tr("Classic"), "Classique")
        i18n.set_language("it")
        self.assertEqual(i18n.tr("Back"), "Indietro")

    def test_case_insensitive_fallback(self) -> None:
        i18n.set_language("it")
        # The original's label was "options"; the port says "Options".
        self.assertEqual(i18n.tr("Options").casefold(), "opzioni")

    def test_port_only_text_stays_english(self) -> None:
        i18n.set_language("de")
        self.assertEqual(i18n.tr("Theme"), "Theme")
        self.assertEqual(i18n.tr("Bop it to start."), "Bop it to start.")

    def test_system_language_is_known(self) -> None:
        self.assertIn(i18n.system_language(), i18n.LANGUAGES)

    def test_mac_language_list_is_read_in_order(self) -> None:
        # The Mac's AppleLanguages is a list of BCP 47 tags, in the user's own order.
        def read(*languages: str) -> str:
            listing = "(\n" + "".join(f'    "{tag}",\n' for tag in languages) + ")"
            done = mock.Mock(returncode=0, stdout=listing)
            with mock.patch.object(platform, "MAC", True), \
                 mock.patch.object(platform, "WINDOWS", False), \
                 mock.patch("subprocess.run", return_value=done):
                return i18n.system_language()

        self.assertEqual(read("de-DE", "en-US"), "de")
        self.assertEqual(read("fr-CA"), "fr")
        # A language the port does not have is passed over rather than taken as English.
        self.assertEqual(read("hu-HU", "it-IT"), "it")

    def test_every_catalog_loads(self) -> None:
        for code in ("de", "es", "fr", "it"):
            i18n.set_language(code)
            self.assertNotEqual(i18n.tr("Games"), "Games", code)


class BanterLanguageTests(unittest.TestCase):
    def test_english_only_lines(self) -> None:
        lines = {Banter(random.Random(s), english=False).pick(10) for s in range(300)}
        self.assertTrue(all(int(line[-2:]) < 50 for line in lines))
        english = {Banter(random.Random(s)).pick(10) for s in range(300)}
        self.assertTrue(any(int(line[-2:]) >= 50 for line in english))


class VoiceLanguageTests(unittest.TestCase):
    def test_language_recordings_replace_english(self) -> None:
        audio = Audio(lambda m: None)
        audio._sounds = {"VO_Bop": object(), "de/VO_Bop": object(),
                         "VO_Die_01_HLWN": object()}
        audio.set_language("de")
        self.assertEqual(audio._localized("VO_Bop"), "de/VO_Bop")
        # Anything the language does not have is the shared sound, as in the original.
        self.assertEqual(audio._localized("VO_Die_01_HLWN"), "VO_Die_01_HLWN")
        audio.set_language("en")
        self.assertEqual(audio._localized("VO_Bop"), "VO_Bop")

    def test_every_language_has_its_voices(self) -> None:
        needed = ["VO_Bop", "VO_Twist", "VO_Pull", "VO_Pass", "VO_Die_01",
                  "VO_Miscellaneous_Bop It [Intro]"]
        needed += [f"VO_Banter_{n:02d}" for n in (1, 2, 7, 8, 41)]
        for code in ("de", "es", "fr", "it"):
            names = {p.stem for p in (LANGUAGE_SOUNDS_DIR / code).glob("*.wav")}
            for name in needed:
                self.assertIn(name, names, f"{code} {name}")


if __name__ == "__main__":
    unittest.main()
