# Bop It (accessible port)

An accessible port of Bop It for iPhone (version 1.1.9, for iOS 3.0), made so that blind and low-vision players can play it with a keyboard and a screen reader. It is a faithful port, not a remake: the game rules, timing, speed-ups, scoring, menus, sounds and music follow the original, recovered from the original app itself. Everything the original showed on screen is spoken, and the game can be played with no screen at all.

It runs on Windows and macOS, speaks through your screen reader (NVDA on Windows, VoiceOver on the Mac, others through Prism), and plays its sound through OpenAL Soft.

The game has its own help and tutorials: see Options, then Help, in the game. This readme is for the repository.

## AI notice

This port was written with Claude Opus 5.5, an AI model made by Anthropic, working with and directed by the developer, who tested every part of it. The design decisions, and every change from the original, were approved by the developer and are listed in docs/DEVIATIONS.md.

## The original game and its assets

Bop It, and every asset in this repository that comes from the original app, belong to their respective holders. That includes the voices, sound effects, music, images, text, screen layouts and the original app bundle in BopIt.app. They are used here only to preserve a game that has been unavailable for about a decade, and to make it playable for people who could never play it. No ownership of them is claimed.

The holders have every right to ask for this repository, or any part of it, to be taken down, and such a request will be honoured.

BOP IT is a trademark of Hasbro. The iPhone game was published by EA.

## Credits

The original Bop It for iPhone, as its credits screen gives them:

- Concept and production by KID Group: Dan Klitsner, Brian Clemens, Gary Levenberg, Roberto Antonio and Claire Sanders.
- Software development by Riptide Games: Ohm Unmongkolthavong, Seth Howard, Jayson Flick, Bryan Mashinter, Mike Montgomery, Brian Robbins and Jonathan Hartstein.
- Audio by Hasbro and Adam Rossi Audio.
- 3D assets by Perez Design.
- Special thanks to the Hasbro and EA teams.

This port:

- Port, accessibility design and testing by tunmi13productions.
- The Head 2 Head side cues (the green and blue sounds in sounds/accessibility) are from Game Master Audio's Retro Classic pack, in its Collectables set.
- Code written with Claude Opus 5.5 (see the AI notice above).

Built with:

- pygame, for the window, keyboard and timing.
- Prism (the prismatoid package), for speech.
- OpenAL Soft, through cyal, for audio.
- soundfile, for decoding the sounds.
- uv, for the packages.
- The NVDA controller client, on Windows.
- PyInstaller, for building the game.

## License

The port's own code is under the MIT License, in LICENSE. That license covers only the code written for this port. It does not cover the original game's assets described above, which remain their holders' property. The vendored libraries in vendor carry their own licenses beside them.

## Playing from source

1. Install 64-bit Python 3.12, and uv.
2. Install the game's packages into .venv:

```
uv sync
```

3. From the repository folder, start the game:

```
uv run python -m bopit
```

uv reads pyproject.toml and uv.lock, which between them pin every package the game needs on either platform. requirements.txt is the same set exported for pip, if you would rather not use uv; `uv sync` is the way the port is developed and built.

The first time it runs, the game writes settings.json, keys.json and its other files beside itself. The game keys can be changed in keys.json, and Help, Keys in the game lists them. Start it with the --help flag to see the debug options, including a bot that plays the game by itself; docs/DEBUG_MODE.md explains them.

Escape leaves the game from the main menu. From anywhere, it is Alt+F4 on Windows and Command Q on the Mac.

## Building the game

compiler.py builds the game for whichever platform you are on: into dist\BopIt around BopIt.exe on Windows, and into dist\BopIt.app on the Mac, with everything it needs inside.

1. Install PyInstaller as well as the game's packages:

```
uv sync --group dev
```

which is `pip install pyinstaller` if you are not using uv.

2. Double-click compiler.py, or run it, and choose a build from the menu:

```
uv run python compiler.py
```

3. The game is dist\BopIt\BopIt.exe, or dist\BopIt.app. That folder or bundle is all a player needs.

You can also give the compiler a flag and skip the menu. To build the game:

```
uv run python compiler.py
```

To build it with a console window, to see why it will not start:

```
uv run python compiler.py --console
```

To empty PyInstaller's cache first:

```
uv run python compiler.py --clean
```

To see what a build would do, without building anything:

```
uv run python compiler.py --dry-run
```

A built game keeps the player's settings, scores, keys and logs beside the executable on Windows and beside BopIt.app on the Mac, so a new build does not lose them. If it ever fails to start, it writes crash.txt there.

The Mac build is signed ad hoc, which is what PyInstaller does there already and is enough for the game to run. The first time it opens the microphone, macOS asks for permission; the answer is in the bundle's Info.plist.

## Releasing

releaser.py builds, zips and publishes a release on GitHub. Releases are numbered by build: 1, 2, 3 and so on. VERSION holds the last build number.

1. Install the GitHub CLI and sign in:

```
gh auth login
```

2. Commit and push all your changes. The releaser will not start otherwise.
3. Optionally, write what changed in changelog.txt, one line each, under a line that says unrelease: like this:

```
unrelease:
Added the Text size setting.
Fixed the Blitz Challenge break screen.
```

4. Double-click releaser.py, or run it. It says which build it will make and asks once. Type Y and press Enter.

```
uv run python releaser.py
```

It then does the rest:

- It sets VERSION to the new build number, and files any changelog lines under "Build" and the number.
- It builds the game with compiler.py.
- It zips the build to dist\BopIt-<number>.zip. On the Mac the zip is made with ditto, so the bundle's symlinks survive it.
- It commits VERSION as "Build" and the number, and pushes.
- It tags the commit with the build number, and pushes the tag.
- It uploads the zip as the GitHub release "Bop It build" and the number, with the changelog lines as its notes.

If the build fails, VERSION and the changelog are put back as they were.

## Rebuilding the game's files from the original

The sounds, images, layouts and translations in this repository were extracted from the original app in BopIt.app by the scripts in tools. You only need them to extract again.

To sort the original's sounds into sounds, with each language's voices in sounds/languages:

```
python tools/extract_sounds.py
```

To convert the original's iPhone images into ordinary PNG files in images (this one needs Pillow and numpy):

```
python tools/extract_images.py
```

To turn the original's screen layouts into the drawing lists in layouts:

```
python tools/extract_layouts.py
```

To build the translations in bopit/lang from the original's own translations:

```
python tools/extract_texts.py
```

## Documents

- docs/ORIGINAL_BEHAVIOR.md records how the original works, and how each fact was found.
- docs/DEVIATIONS.md lists every way this port differs from the original, and why.
- docs/DEBUG_MODE.md explains debug mode.

## Running the tests

From the repository folder:

```
uv run python -m unittest discover -s tests
```
