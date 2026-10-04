"""The game's languages. The original shipped English, German, Spanish, French and Italian,
and followed the device's language. Here the language is a setting, first chosen from
the system's language (see docs/DEVIATIONS.md).

Text the original showed is translated with the original's own translations, from the
catalogs in bopit/lang (made by tools/extract_texts.py). Text only this port has stays in
English. tr() takes the English text and returns the translation, or the English text when
there is none.
"""

import json
import locale
import logging
import re
from pathlib import Path

from bopit import platform

log = logging.getLogger(__name__)

# Each language's name, in that language.
LANGUAGES: dict[str, str] = {"en": "English", "de": "Deutsch", "es": "Español",
                             "fr": "Français", "it": "Italiano"}
CATALOG_DIR = Path(__file__).resolve().parent / "lang"
# Windows primary language IDs (the low 10 bits of a LANGID).
_WINDOWS_LANGUAGES = {0x09: "en", 0x07: "de", 0x0A: "es", 0x0C: "fr", 0x10: "it"}

_language = "en"
_exact: dict[str, str] = {}
_catalog: dict[str, str] = {}


def _key(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def language() -> str:
    return _language


def set_language(code: str) -> None:
    global _language, _catalog, _exact
    if code not in LANGUAGES:
        log.error("Unknown language %r; using English", code)
        code = "en"
    _language = code
    _catalog = {}
    _exact = {}
    if code == "en":
        return
    path = CATALOG_DIR / f"{code}.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        log.error("Could not read %s: %s; text stays in English", path, error)
        return
    _exact = dict(raw)
    # The original's labels were often lower case; the port's are capitalized.
    _catalog = {_key(english): translated for english, translated in raw.items()}


def tr(text: str) -> str:
    """The original's translation of text in the current language, or text itself."""
    if not _catalog or not text:
        return text
    exact = _exact.get(text.strip())
    if exact is not None:
        return exact
    return _catalog.get(_key(text), text)


def trf(template: str, *args: object) -> str:
    """A translated printf-style template from the original, such as "Player %i", filled
    in."""
    return tr(template) % args


def system_language() -> str:
    """The system's language if it is one of the five, otherwise English."""
    if platform.WINDOWS:
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return _WINDOWS_LANGUAGES.get(langid & 0x3FF, "en")
        except (AttributeError, OSError):
            pass
    if platform.MAC:
        # The Mac's own language list, the one Settings shows, in the order the user
        # put them. Read with defaults so nothing has to be linked in.
        try:
            import subprocess
            done = subprocess.run(["/usr/bin/defaults", "read", "-g", "AppleLanguages"],
                                   capture_output=True, text=True, timeout=2)
            for tag in re.findall(r'"([^"]+)"', done.stdout or ""):
                code = tag.split("-")[0].split("_")[0].lower()
                if code in LANGUAGES:
                    return code
        except (OSError, ValueError):
            log.debug("Could not read the Mac's language list", exc_info=True)
    name = (locale.getlocale()[0] or "").lower()
    for code in LANGUAGES:
        if name.startswith(code):
            return code
    return "en"
