"""Release Bop It: build it, zip it, tag it with the build number and upload it to GitHub.

Double-click this file, or run python releaser.py. It says what it will do and asks once,
then waits for Enter at the end so you can hear how it went.

Releases are numbered 1, 2, 3 and so on. VERSION holds the last build number; a release
takes the next one. The steps:

    1. check     everything is committed and pushed, and the GitHub CLI (gh) is signed in
    2. version   VERSION becomes the new build number; if changelog.txt has lines under
                 "unrelease:", they are filed under "Build <n>:" (there is no minimum or maximum)
    3. build     compiler.py builds dist\\BopIt, or dist\\BopIt.app on the Mac; if it fails,
                 VERSION and the changelog go back
    4. zip       the build becomes dist\\BopIt-<n>.zip, which extracts to a BopIt folder on
                 Windows and to BopIt.app on the Mac
    5. commit    VERSION and the changelog are committed as "Build <n>" and pushed
    6. tag       the commit is tagged <n>, and the tag is pushed
    7. upload    the zip goes up as the GitHub release "Bop It build <n>", with that build's
                 changelog lines as its notes (or just "Bop It build <n>")
"""

import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import compiler  # noqa: E402
from bopit import platform  # noqa: E402

VERSION_FILE = HERE / "VERSION"
CHANGELOG = HERE / "changelog.txt"
UNRELEASE = "unrelease:"


def say(text: str = "") -> None:
    print(text, flush=True)


def run(*cmd: str) -> tuple[bool, str]:
    proc = subprocess.run(list(cmd), cwd=HERE, capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout + proc.stderr).strip()


def current_build() -> int:
    text = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else ""
    return int(text) if text.isdigit() else 0


def file_changelog(text: str, build: int) -> tuple[str, list[str]]:
    """The changelog with the lines under "unrelease:" moved under "Build <n>:", and those
    lines. A fresh, empty "unrelease:" heading stays at the top for the next build."""
    lines = text.replace("\r\n", "\n").split("\n")
    if UNRELEASE not in [line.strip() for line in lines]:
        return text, []
    start = [line.strip() for line in lines].index(UNRELEASE)
    end = start + 1
    while end < len(lines) and not re.match(r"^[^\s:]+( \d+)?:$", lines[end].strip()):
        end += 1
    entries = [line for line in lines[start + 1:end] if line.strip()]
    if not entries:
        return text, []
    filed = lines[:start] + [UNRELEASE, "", f"Build {build}:"] + entries + [""] + lines[end:]
    return "\n".join(filed).rstrip("\n") + "\n", entries


def check() -> list[str]:
    found = []
    ok, status = run("git", "status", "--porcelain")
    if not ok or status:
        found.append("there are uncommitted changes; commit them first")
    run("git", "fetch", "--quiet")
    ok, ahead = run("git", "rev-list", "--count", "@{u}..HEAD")
    if not ok or ahead != "0":
        found.append("there are commits not pushed yet; push them first")
    if shutil.which("gh") is None:
        found.append("the GitHub CLI, gh, is not installed")
    elif not run("gh", "auth", "status")[0]:
        found.append("the GitHub CLI is not signed in; run gh auth login")
    return found + [f"  {p}" for p in compiler.problems()]


def make_zip(build: int) -> Path:
    archive = compiler.DIST / f"{compiler.NAME}-{build}.zip"
    if platform.MAC:
        # ditto, because an app bundle is not a folder of files: it has symlinks and
        # resource forks, and a plain zip writes the links as copies of what they point
        # at, which the Finder then refuses to open. ditto -c -k is how macOS itself
        # makes a zip of a bundle, and it is on every Mac.
        done = subprocess.run(["/usr/bin/ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                               str(compiler.OUTPUT), str(archive)],
                              capture_output=True, text=True)
        if done.returncode != 0:
            raise SystemExit(f"Could not zip the app: {done.stderr.strip()}")
        return archive
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(compiler.OUTPUT.rglob("*")):
            if path.is_file():
                zf.write(path, Path(compiler.NAME) / path.relative_to(compiler.OUTPUT))
    return archive


def release() -> int:
    build = current_build() + 1
    tag = str(build)
    say(f"Bop It releaser. This makes build {build}: it builds the game, zips it, commits "
        f"VERSION, tags it {tag} and uploads it to GitHub as \"Bop It build {build}\".")
    found = check()
    if found:
        say("It cannot go ahead:")
        for problem in found:
            say(f"  {problem}")
        return 2
    if run("git", "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}")[0]:
        say(f"The tag {tag} already exists, so build {build} has been released. Check VERSION.")
        return 2
    if input("Release it? Type Y and press Enter: ").strip().lower() != "y":
        say("Nothing was done.")
        return 0

    old_version = VERSION_FILE.read_text(encoding="utf-8") if VERSION_FILE.exists() else None
    old_changelog = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else None
    VERSION_FILE.write_text(f"{build}\n", encoding="utf-8")
    notes: list[str] = []
    if old_changelog is not None:
        new_changelog, notes = file_changelog(old_changelog, build)
        CHANGELOG.write_text(new_changelog, encoding="utf-8")
    say(f"VERSION is now {build}.{' ' + str(len(notes)) + ' changelog lines filed.' if notes else ''}")

    if compiler.main([]) != 0:
        say("The build failed, so VERSION and the changelog are back as they were.")
        if old_version is None:
            VERSION_FILE.unlink()
        else:
            VERSION_FILE.write_text(old_version, encoding="utf-8")
        if old_changelog is not None:
            CHANGELOG.write_text(old_changelog, encoding="utf-8")
        return 1
    archive = make_zip(build)
    say(f"Zipped: {archive.name}, {archive.stat().st_size // (1024 * 1024)} MB.")

    files = ["VERSION"] + (["changelog.txt"] if CHANGELOG.exists() else [])
    for step, cmd in (("commit", ("git", "add", *files)),
                      ("commit", ("git", "commit", "-m", f"Build {build}")),
                      ("push", ("git", "push")),
                      ("tag", ("git", "tag", tag)),
                      ("push the tag", ("git", "push", "origin", tag))):
        ok, out = run(*cmd)
        if not ok:
            say(f"Could not {step}: {out}")
            return 1
    say(f"Committed as \"Build {build}\" and tagged {tag}.")

    title = f"Bop It build {build}"
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
        fh.write("\n".join(notes) if notes else title)
        notes_file = fh.name
    ok, out = run("gh", "release", "create", tag, str(archive), "--title", title,
                  "--notes-file", notes_file)
    Path(notes_file).unlink(missing_ok=True)
    if not ok:
        say(f"The upload failed: {out}")
        return 1
    say(f"Released: {out}")
    return 0


if __name__ == "__main__":
    code = 1
    try:
        code = release()
    finally:
        if sys.stdin.isatty():
            input("Finished. Press Enter to close this window.")
    sys.exit(code)
