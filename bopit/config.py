"""Paths and user settings."""

import json
import logging
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from bopit import platform

log = logging.getLogger(__name__)

if platform.IS_FROZEN:
    # A build made by compiler.py: the game's own files are bundled in PyInstaller's folder.
    PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
# The player's own files (settings, scores, keys, logs): beside the executable, or beside
# the .app bundle on the Mac, where the next build would swallow them.
USER_DIR = platform.user_dir(PROJECT_ROOT)
ORIGINAL_APP_DIR = PROJECT_ROOT / "BopIt.app"
ORIGINAL_LANG_DIR = ORIGINAL_APP_DIR / "English.lproj"
SOUNDS_DIR = PROJECT_ROOT / "sounds"
VENDOR_DIR = PROJECT_ROOT / "vendor"
# Each language's own recordings, in a folder named by its code (de, es, fr, it). English is
# the rest of SOUNDS_DIR.
LANGUAGE_SOUNDS_DIR = SOUNDS_DIR / "languages"
# Folders under SOUNDS_DIR that are not loaded with the English sounds: the languages are
# loaded separately.
UNLOADED_SOUND_DIRS = ("languages",)
LOG_DIR = USER_DIR / "logs"
SETTINGS_PATH = USER_DIR / "settings.json"
KEYS_PATH = USER_DIR / "keys.json"


# The original's three kinds of command. Silent showed commands as pictures only; it is
# kept here for reference but not offered, see docs/DEVIATIONS.md.
COMMAND_MODES = ("VOX", "SFX", "Silent")
SELECTABLE_COMMAND_MODES = ("VOX", "SFX")
# The Text size setting's range and step, in points.
TEXT_SIZE_MIN, TEXT_SIZE_MAX, TEXT_SIZE_STEP = 12, 32, 2


@dataclass
class Settings:
    # The original's settings, with its defaults from GameSettings::loadGameSettings.
    commands: str = "VOX"
    banter: bool = True
    shout_it: bool = True
    music_volume: int = 100
    sfx_volume: int = 60
    # Index into themes.THEMES. The original starts on Original (SkinsManager::init).
    theme: int = 0
    # With no choice saved, Play started Basic (LandingPage::executePlayButtonPressed).
    quick_play: str = "Basic"
    # Commands last picked in the multiplayer command picker. Empty means its defaults.
    picked: list[str] = field(default_factory=list)
    # Our additions.
    # The language, a code from i18n.LANGUAGES. Empty until the first run takes the system's.
    language: str = ""
    # Shout It X-Move through the microphone (the original's "shout Yeah!" move).
    microphone: bool = True
    # The size of the caption text on screen, in points, for anyone watching (TEXT_SIZES).
    text_size: int = 16
    master_volume: float = 1.0
    # Used to estimate how long protected speech lasts, since NVDA cannot report it.
    speech_chars_per_second: float = 18.0


def load_settings(path: Path = SETTINGS_PATH) -> Settings:
    if not path.exists():
        return Settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Could not read settings from %s, using defaults: %s", path, exc)
        return Settings()
    known = {f.name for f in fields(Settings)}
    settings = Settings(**{k: v for k, v in data.items() if k in known})
    if settings.commands not in SELECTABLE_COMMAND_MODES:
        log.warning("Commands setting %r is not available, using VOX", settings.commands)
        settings.commands = "VOX"
    return settings


def save_settings(settings: Settings, path: Path = SETTINGS_PATH) -> None:
    path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")
