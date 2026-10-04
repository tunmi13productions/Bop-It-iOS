"""Build Bop It into a program with PyInstaller, for the platform you are on.

Double-click this file, or run python compiler.py with nothing after it, for a numbered menu;
it waits for Enter at the end so you can hear how it went. Or give a flag:

    python compiler.py              build
    python compiler.py --console    build with a console window, to see why the game will not start
    python compiler.py --clean      empty PyInstaller's cache first
    python compiler.py --dry-run    say what a build would do, build nothing

On Windows the build lands in dist\\BopIt, around BopIt.exe; on the Mac it is dist\\BopIt.app.
The game's own files (sounds, images, layouts, translations, OpenAL Soft and, on Windows, the
NVDA library) go inside it; VERSION, the license and the changelog go beside it. The player's
settings, scores, keys and logs are written beside the executable when the game runs, or on
the Mac beside the app bundle, so a new build does not lose them. releaser.py zips this folder.

The Mac build needs one thing PyInstaller cannot be told: macOS refuses microphone access
without a usage description in the bundle's Info.plist, and the Shout It X-Move needs the
microphone. So the bundle's Info.plist is finished off after the build and the bundle is
re-signed, which is why this is a script and not just a PyInstaller command line.
"""

import argparse
import importlib.machinery
import importlib.util
import os
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bopit import platform  # noqa: E402

NAME = platform.PROGRAM_NAME
ENTRY = "BopIt.py"
DIST = HERE / "dist"
OUTPUT = platform.built_game(DIST)
# What the Mac's bundle says it is. Reverse DNS, so LaunchServices and Spotlight have
# something sane to key on; the Windows build needs no equivalent.
BUNDLE_IDENTIFIER = "com.tunmi13productions.bopit"
# Shown in the privacy prompt macOS puts up the first time the microphone is opened.
MICROPHONE_DESCRIPTION = "Bop It measures how loud you shout, for the Shout It X-Move bonus."
# Bundled with the game, as (source, folder inside the build).
DATA = (("sounds", "sounds"), ("images", "images"), ("layouts", "layouts"),
        ("bopit/lang", "bopit/lang"), ("vendor/openal/license.txt", "licenses/openal-soft"))
if platform.WINDOWS:
    # The NVDA controller client is Prism's, and Prism only asks for it on Windows.
    DATA += (("vendor/nvda/license.txt", "licenses/nvda-controller-client"),)
# Beside the game, for the player to read: (source, name in the build).
SIDE_FILES = (("VERSION", "VERSION"), ("LICENSE", "license.txt"),
              ("changelog.txt", "changelog.txt"))
# What the game needs installed here to be bundled: (module, what pip calls it).
PACKAGES = (("pygame", "pygame"), ("prism", "prismatoid"), ("cyal", "cyal"),
            ("soundfile", "soundfile"), ("numpy", "numpy"), ("PyInstaller", "pyinstaller"))


def say(text: str = "") -> None:
    print(text, flush=True)


def version() -> str:
    path = HERE / "VERSION"
    return path.read_text(encoding="utf-8").strip() if path.exists() else ""


def binaries() -> tuple[tuple[str, str], ...]:
    """The libraries to bundle, as (source, folder inside the build).

    OpenAL Soft is named after what the loader opens, which is OpenAL32.dll on Windows
    (soft_oal.dll in vendor is the same file). There is no Mac entry: cyal's wheel
    carries its own OpenAL Soft and links it through @loader_path, so --collect-all
    brings it along. The NVDA controller client is Prism's, and Windows only.
    """
    library = platform.openal_library(HERE / "vendor")
    found: tuple[tuple[str, str], ...] = ()
    if library is not None:
        found += ((str(library.relative_to(HERE)), str(library.parent.relative_to(HERE))),)
    if platform.WINDOWS:
        found += (("vendor/nvda/nvdaControllerClient64.dll", "vendor/nvda"),)
    return found


def problems() -> list[str]:
    found = []
    if not (platform.WINDOWS or platform.MAC):
        found.append("this builds for Windows and macOS, so run it on one of those, "
                     f"not on {platform.PLATFORM}")
    missing = [pip for module, pip in PACKAGES if importlib.util.find_spec(module) is None]
    if missing:
        found.append("install these first: pip install " + " ".join(missing))
    for source, _ in DATA + binaries():
        if not (HERE / source).exists():
            found.append(f"{source} is missing")
    return found


def prism_native() -> list[Path]:
    """Prism's compiled module in prism/_native, which --collect-all leaves behind."""
    spec = importlib.util.find_spec("prism")
    if spec is None or not spec.submodule_search_locations:
        return []
    folder = Path(list(spec.submodule_search_locations)[0]) / "_native"
    suffixes = tuple(importlib.machinery.EXTENSION_SUFFIXES)
    return sorted(p for p in folder.glob("*") if p.name.endswith(suffixes))


def command(console: bool, clean: bool) -> list[str]:
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--noupx", "--name", NAME,
           "--distpath", str(DIST), "--workpath", str(HERE / "build")]
    for source, inside in binaries():
        cmd += ["--add-binary", f"{source}{os.pathsep}{inside}"]
    for source, inside in DATA:
        cmd += ["--add-data", f"{source}{os.pathsep}{inside}"]
    # Imported inside functions, so named outright. Prism loads its compiled half from
    # prism/_native, which is not a package, and needs cffi; soundfile needs its libsndfile.
    cmd += ["--collect-all", "prism", "--collect-all", "cyal", "--collect-all", "soundfile",
            "--collect-all", "_soundfile_data", "--hidden-import", "_cffi_backend"]
    for path in prism_native():
        cmd += ["--add-binary", f"{path}{os.pathsep}prism/_native"]
    if platform.MAC:
        # A windowed build is a .app bundle on the Mac, which is what the player
        # double-clicks. The identifier is fixed here so macOS's privacy prompt names the
        # game rather than the frozen script.
        cmd += ["--osx-bundle-identifier", BUNDLE_IDENTIFIER]
    if not console:
        cmd += ["--windowed"]
    if clean:
        cmd += ["--clean"]
    return cmd + [ENTRY]


def finish_bundle() -> None:
    """Finish the Mac bundle: the microphone's usage description, and a signature.

    Writing Info.plist after PyInstaller has signed the bundle breaks the signature, so
    the bundle is signed again, ad hoc, which is all an unsigned game needs to keep
    working (and what PyInstaller itself does on Apple silicon).
    """
    # PyInstaller builds the onedir folder and then wraps it, so dist/BopIt is a second
    # copy of everything inside the bundle. Only the bundle is the game.
    leftover = DIST / NAME
    if leftover.is_dir():
        shutil.rmtree(leftover)
        say(f"Removed {leftover.name}, which the bundle replaces.")
    path = OUTPUT / "Contents" / "Info.plist"
    info = dict(plistlib.loads(path.read_bytes()))
    info["NSMicrophoneUsageDescription"] = MICROPHONE_DESCRIPTION
    info["NSHighResolutionCapable"] = True
    if version():
        # The build number from VERSION, which is what the game calls its build.
        # PyInstaller only has pyproject.toml's placeholder.
        info["CFBundleShortVersionString"] = version()
        info["CFBundleVersion"] = version()
    path.write_bytes(plistlib.dumps(info))
    say("Added the microphone's usage description to Info.plist.")
    done = subprocess.run(["codesign", "--force", "--sign", "-", "--timestamp=none",
                           str(OUTPUT)], capture_output=True, text=True)
    if done.returncode != 0:
        say("Could not sign the bundle again; the game still runs, but macOS may ask "
            "for the microphone again after every build.")
        say(done.stderr.strip())
    else:
        say("Signed the bundle ad hoc.")


def copy_side_files() -> None:
    beside = OUTPUT.parent if platform.MAC else OUTPUT
    for source, name in SIDE_FILES:
        path = HERE / source
        if path.exists():
            shutil.copy2(path, beside / name)
            say(f"{name} is in the build.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compiler.py", description="build Bop It")
    parser.add_argument("--console", action="store_true", help="keep a console window")
    parser.add_argument("--clean", action="store_true", help="empty PyInstaller's cache first")
    parser.add_argument("--dry-run", action="store_true", help="build nothing, say what would happen")
    args = parser.parse_args(argv)
    os.chdir(HERE)
    found = problems()
    if found:
        say("The build cannot start:")
        for problem in found:
            say(f"  {problem}")
        return 2
    cmd = command(args.console, args.clean)
    if args.dry_run:
        say("Would run: " + " ".join(cmd[1:]))
        say(f"The build would land in {OUTPUT}.")
        return 0
    say(f"Building Bop It{' build ' + version() if version() else ''} into {OUTPUT}. This takes a minute or two.")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    started = time.perf_counter()
    if subprocess.run(cmd).returncode != 0:
        say("PyInstaller failed. Its own output above says why.")
        return 1
    if platform.MAC and not args.console:
        finish_bundle()
    copy_side_files()
    say(f"Built in {time.perf_counter() - started:.0f} seconds.")
    say(f"The game is {OUTPUT if platform.MAC else OUTPUT / platform.EXECUTABLE}")
    if platform.MAC:
        say("Open it from the Finder, or from a terminal with: open " + str(OUTPUT))
    return 0


MENU = (("Build the game", []),
        ("Build with a console window, to see why the game will not start", ["--console"]),
        ("Clean build: empty PyInstaller's cache first", ["--clean"]),
        ("Show what a build would do, without building", ["--dry-run"]))


def run() -> int:
    """Flags build straight away; no flags from a keyboard opens the menu."""
    if sys.argv[1:] or not sys.stdin.isatty():
        return main()
    say(f"Bop It compiler. VERSION is {version() or 'not set yet'}.")
    for number, (text, _) in enumerate(MENU, 1):
        say(f"  {number}. {text}")
    say("  0. Quit")
    while True:
        choice = input("Type a number and press Enter: ").strip()
        if choice == "0":
            return 0
        if choice.isdigit() and 1 <= int(choice) <= len(MENU):
            break
        say(f"There is no choice {choice}.")
    try:
        return main(MENU[int(choice) - 1][1])
    finally:
        input("Finished. Press Enter to close this window.")


if __name__ == "__main__":
    sys.exit(run())
