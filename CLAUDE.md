# Project: Accessible Port of Bop It (iOS 3.0)

## What this is

This is a faithful port of the iOS 3.0 version of Bop It, a game that has been dead for roughly a decade. The goal is an accessible version for blind and low-vision players. The developer is totally blind. Everything you build must work perfectly without sight.

## Prime directive: fidelity

This is a port, not a remake, not a reimagining, not "Bop It but better."

- Match the original's behavior exactly: game rules, command pool, timing windows, speed progression, scoring, menu structure, menu order, sound triggers, and edge cases.
- Do not invent features, rebalance timing, or "improve" anything unless the developer explicitly asks. If the original did something odd, we do the odd thing.
- If you do not know how the original behaved, stop and ask. Do not guess and do not fill gaps with plausible-sounding behavior.
- Any deliberate deviation must be listed in `docs/DEVIATIONS.md` with a reason, and only after the developer approves it. The only expected deviations are accessibility additions (speech, keyboard controls, debug mode).

## Second prime directive: accessibility

Accessibility and speech operation come before everything else, including graphics, polish, and performance. When there is a conflict, accessibility wins.

- Every piece of information a sighted player would get from the screen must also be delivered through speech and/or audio.
- Every screen, menu, dialog, state change, error, and score update must be announced.
- Never rely on color, position, animation, or any visual-only cue.
- The game must be fully playable with no screen at all.
- Test every feature as if the monitor is unplugged.

## Tech stack

- Python 3.12. Exactly 3.12: cyal, the OpenAL binding, has no wheels past it on any platform, so a newer Python means building cyal from source.
- Dependencies: uv. pyproject.toml says what the game needs, uv.lock pins it, and requirements.txt is exported from those for pip. Do not pip install into the system Python; use `uv sync` and `uv run`.
- Platforms: Windows and macOS, the same game on both. Anything platform-specific belongs in bopit/platform.py, so gameplay code never branches on sys.platform. If a new platform is added, that file and whatever it names are the only places to touch.
- Windowing, input, and event loop: pygame. Note that pygame is used for the window, keyboard events, and timing. Do NOT use pygame.mixer for game audio.
- Speech: Prism. All spoken output goes through Prism. Verify the actual Prism Python API and its available backends before writing code. Do not assume method names. If the bindings are missing or awkward, tell the developer and propose a thin wrapper. On the Mac the backend is VoiceOver, or the system's own voice through Prism's AVSpeech backend.
- Audio: OpenAL Soft, through a Python OpenAL binding. Verify which binding is installed and maintained before choosing one. Spatialization, pitch, and precise timing all matter here. The Mac has no vendored OpenAL Soft and uses cyal's, because cyal links its own through @loader_path; see docs/DEVIATIONS.md.
- Images: the included images may be used, but visuals are low priority. Do not spend effort on graphics until everything else works.

## Speech rules

Build one speech module that everything else calls. No other module talks to Prism directly.

- Provide at least `speak(text, interrupt=False)`, `stop()`, and a way to check whether speech is currently active.
- Define an interruption policy and document it. Menu navigation should interrupt the previous item so fast arrowing does not queue up a backlog. Game commands must interrupt anything stale immediately. Score announcements and game over must not be cut off by stray sounds.
- Speech must never block the game loop, and it must never make timing windows unfair. Timing is measured against the audio prompt, not the end of speech.
- Every menu item announces its name, its position (for example "3 of 5"), and its state if it has one (on, off, selected).
- On entering a screen, announce the screen title and the focused item.
- Keep messages short. Blind players hear everything linearly, so every extra word costs time.
- Fail loudly during development: if Prism fails to initialize, log it clearly and print to the console rather than silently running mute.

## Audio rules

- OpenAL Soft is the only game audio path.
- Load all sounds up front into buffers so nothing hitches mid-game.
- Command prompts must be perfectly timed and reproducible.
- Provide a master volume, and separate speech and effects volume if it is cheap to do.
- Handle device changes and missing devices gracefully, with a spoken message.

## GUI rules

There is essentially no visual GUI. If any GUI toolkit ever comes into play (wx, Qt, or otherwise), it must be fully screen-reader compatible: proper labels, logical focus order, keyboard-only operation. Prefer no widget toolkit at all. Menus are speech-and-keyboard driven inside the pygame loop.

## Build order

1. Project skeleton, config, logging, and the speech module. Prove Prism works with a spoken hello.
2. The audio module. Prove OpenAL Soft plays a sound with a spoken confirmation.
3. Menus: main menu and everything reachable from it, matching the original's structure and order. Full speech feedback.
4. The Bop It game itself: the engine, the command loop, timing, speed progression, scoring, game over, high scores.
5. Debug mode and test tooling (see below).
6. Keyboard binding polish (see below).
7. Visuals, last and only if time allows.

Finish and get approval on each stage before starting the next. Do not skip ahead.

## Keyboard bindings

Bindings should be easy to memorize. Do not finalize them yet. For now, put all bindings in a single config/mapping module so they can be changed in one place. Propose a scheme when we reach step 6, and get approval before hardcoding anything. Arrow keys, Enter, and Escape for menus are safe defaults in the meantime.

## Debug mode

Add a debug mode that lets the game play itself so the developer can listen to it and confirm the engine behaves correctly.

- An autoplay bot issues the correct response to every command, with configurable reaction time, so timing windows can be tested at the edges.
- Options to make the bot fail on purpose (wrong action, late, no action) to test game over and life-loss handling.
- A fixed random seed option so runs are reproducible.
- All speech and audio work exactly as in normal play. The developer is listening, not watching.
- Log every event with timestamps to a text file: command issued, response received, timing delta, score change. A blind developer can read logs with a screen reader, so keep them clean and line-based, one event per line, no fancy formatting.
- Debug mode must be off by default and toggled by a command-line flag.

## Code quality

- Type hints throughout, small modules, and clear separation between engine, speech, audio, input, and menus.
- The game engine must not depend on pygame, Prism, or OpenAL directly, so it can be tested headless.
- Write unit tests for engine logic, especially timing and scoring.
- Keep a `docs/ORIGINAL_BEHAVIOR.md` file where you record everything we know about how the original worked, with a note on how each fact was confirmed.

## Communication style

- The developer uses a screen reader. Do not describe things visually. Do not use ASCII art, box drawing, tables made of pipes, or spinner animations in terminal output.
- When explaining code or structure, describe it in plain linear prose or simple lists.
- Keep terminal output clean and line-based.
- When you are unsure, ask. A short question is cheaper than a wrong assumption.
- The developer enjoys humor, and sarcasm is welcome. Just never at the expense of clarity.
