"""Which platform the port is running on, decided once.

The port began on Windows. Every platform-specific choice now sits in this one
module, so nothing else in the game branches on sys.platform: the OpenAL Soft
library the loader opens, the chord that quits, the name of the game's files,
and where a frozen build keeps the player's own files. A new platform means
touching this file and whatever it names, not the game.

The Mac equivalents, one for one:

    Windows                            macOS
    ---------------------------------  -----------------------------------
    vendor/openal/OpenAL32.dll         the OpenAL Soft cyal carries
    NVDA (through Prism)               VoiceOver, through Prism
    Alt+F4                             Command Q
    dist\\BopIt\\BopIt.exe             dist/BopIt.app/Contents/MacOS/BopIt
    files beside the executable        files beside BopIt.app
    GetUserDefaultUILanguage           the user's preferred languages
"""

import sys
from pathlib import Path

WINDOWS = sys.platform == "win32"
MAC = sys.platform == "darwin"
LINUX = sys.platform.startswith("linux")

#: The one name the rest of the port tests against.
PLATFORM = "mac" if MAC else "windows" if WINDOWS else "linux" if LINUX else sys.platform

IS_FROZEN = bool(getattr(sys, "frozen", False))

#: The game, as the player launches it on each platform.
PROGRAM_NAME = "BopIt"
BUNDLE_NAME = "BopIt.app"
EXECUTABLE = "BopIt.exe" if WINDOWS else PROGRAM_NAME

#: The vendored OpenAL Soft, as (folder in vendor, file name), where there is one.
#: cyal links against OpenAL32.dll, or libopenal.so.1 on Linux, and once a library
#: is loaded under that name the system reuses it, so opening ours first makes cyal
#: use ours too. There is no macOS entry: cyal's Mac wheel links OpenAL Soft
#: through @loader_path, so only the copy beside cyal is ever used, and vendoring
#: a second one would only pretend to change it. See openal_loader.
OPENAL_LIBRARIES = {"win32": ("openal", "OpenAL32.dll"),
                    "linux": ("openal", "libopenal.so.1")}


def openal_library(vendor_dir: Path) -> Path | None:
    """The vendored OpenAL Soft for this platform, or None when there is none."""
    found = OPENAL_LIBRARIES.get(sys.platform)
    return vendor_dir.joinpath(*found) if found else None


def quit_hint() -> str:
    """The chord that leaves the game from anywhere, which no key inside it does."""
    return "Alt+F4" if WINDOWS else "Command Q" if MAC else "Alt+F4"


def is_quit(key: int, mod: int) -> bool:
    """Whether a key event is the platform's quit chord.

    The modifiers are read off the event, because there is nothing else to read
    them from: a built Mac game has no menu bar of its own, so there is no
    Application menu to quit it from.
    """
    import pygame

    if WINDOWS:
        return key == pygame.K_F4 and bool(mod & pygame.KMOD_ALT)
    if MAC:
        # SDL puts the Command key in KMOD_META on macOS. There is no KMOD_SUPER to
        # add to it, and pygame only grows new names with new versions.
        return key == pygame.K_q and bool(mod & pygame.KMOD_META)
    return False


def user_dir(project_root: Path) -> Path:
    """Where the player's own files live: settings, scores, keys and logs.

    From source that is the project folder. A built game keeps them beside
    itself, so a new build does not lose them: beside BopIt.exe on Windows, and
    beside BopIt.app on the Mac, whose own files are inside the bundle and would
    be thrown away by the next build.
    """
    if not IS_FROZEN:
        return project_root
    executable = Path(sys.executable).resolve()
    if not MAC:
        return executable.parent
    # .../dist/BopIt.app/Contents/MacOS/BopIt -> .../dist
    macos = executable.parent
    if macos.name != "MacOS" or macos.parent.name != "Contents":
        return macos
    return macos.parent.parent.parent


def built_game(dist: Path) -> Path:
    """The finished game inside a build folder: the program on Windows, the .app
    on the Mac, which is what a player launches there."""
    return dist / (BUNDLE_NAME if MAC else PROGRAM_NAME)