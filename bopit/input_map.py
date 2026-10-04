"""Every key binding lives here. Nothing else refers to pygame key codes.

Menu keys are fixed, so a broken key file can never lock anyone out of the menus. The game
keys come from keys.json in the game folder, written with the defaults on first run. Key
names are pygame's, for example "space", "left", "q" or "tab". A missing or broken entry
falls back to its default, and each problem is reported.
"""

import json
import logging
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import pygame

from bopit import platform
from bopit.config import KEYS_PATH
from bopit.menu import Nav

log = logging.getLogger(__name__)

MENU_KEYS: dict[int, Nav] = {
    pygame.K_UP: Nav.UP,
    pygame.K_DOWN: Nav.DOWN,
    pygame.K_LEFT: Nav.LEFT,
    pygame.K_RIGHT: Nav.RIGHT,
    pygame.K_HOME: Nav.FIRST,
    pygame.K_END: Nav.LAST,
    pygame.K_RETURN: Nav.SELECT,
    pygame.K_KP_ENTER: Nav.SELECT,
    pygame.K_SPACE: Nav.SELECT,
    pygame.K_ESCAPE: Nav.BACK,
    pygame.K_BACKSPACE: Nav.BACK,
}
MENU_KEYS_TEXT = ("Menus: Up and Down arrows to move, Home and End for the first and last item, "
                  "Left and Right to change a setting, Enter or Space to select, Escape or "
                  "Backspace to go back.")

COMMANDS = ("Bop", "Twist", "Pull", "Spin", "Flick", "Shout", "Squeeze", "Crank", "Shake",
            "Nail", "Brush", "Poke")
H2H_PLAYERS = ("Green", "Blue")
# Head 2 Head keys are by position: each player's Bop, then their commands in picked order.
H2H_SLOTS = ("Bop", "first command", "second command")
ABOUT = ("Bop It keys. Each action takes a list of keys, named as pygame names them, for "
         "example space, left, q, tab. Delete this file to get the defaults back.")

DEFAULTS: dict = {
    "about": ABOUT,
    "game": {
        "Bop": ["space"], "Twist": ["left"], "Pull": ["down"], "Spin": ["right"],
        "Flick": ["up"], "Shout": ["y"], "Squeeze": ["q"], "Crank": ["c"], "Shake": ["k"],
        "Nail": ["n"], "Brush": ["b"], "Poke": ["p"],
    },
    # Speaks the score during a game. Never counts as a move.
    "score": ["s"],
    "pause": ["escape"],
    "head_to_head": {
        "Green": {"Bop": ["f"], "first command": ["d"], "second command": ["s"]},
        "Blue": {"Bop": ["j"], "first command": ["k"], "second command": ["l"]},
        "score": ["tab"],
    },
}


@dataclass
class Bindings:
    game: dict[int, str] = field(default_factory=dict)
    score: set[int] = field(default_factory=set)
    pause: set[int] = field(default_factory=set)
    # key -> (player, slot); slot None is that player's Bop.
    h2h: dict[int, tuple[int, int | None]] = field(default_factory=dict)
    h2h_score: set[int] = field(default_factory=set)


def key_code(name: str) -> int:
    """pygame's key for a name; ValueError for an unknown name."""
    with warnings.catch_warnings():
        # key_code warns before pygame.init(), but the names it knows do not change.
        warnings.simplefilter("ignore")
        return pygame.key.key_code(name)


def spoken_name(key: int) -> str:
    name = pygame.key.name(key)
    return name.upper() if len(name) == 1 else name.title()


class _Builder:
    """Reads one layer of the key file over the defaults, collecting problems."""

    def __init__(self, data: dict, problems: list[str]) -> None:
        self._data = data
        self._problems = problems

    def keys(self, where: str, value: object, default: list[str]) -> list[int]:
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or not value:
            self._problems.append(f"{where}: expected a list of key names; using the default.")
            value = default
        codes = []
        for name in value:
            try:
                codes.append(key_code(str(name)))
            except ValueError:
                self._problems.append(f"{where}: unknown key \"{name}\"; using the default.")
                return [key_code(n) for n in default]
        return codes

    def section(self, where: str, value: object, known: tuple[str, ...]) -> dict:
        if value is None:
            return {}
        if not isinstance(value, dict):
            self._problems.append(f"{where}: expected a set of actions; using the defaults.")
            return {}
        for name in value:
            if name not in known:
                self._problems.append(f"{where}: unknown action \"{name}\"; ignored.")
        return value


def build(data: dict) -> tuple[Bindings, list[str]]:
    """Bindings from key file data, and the problems found. Anything missing or broken uses
    its default. A key bound twice in the same kind of game keeps its first binding."""
    problems: list[str] = []
    b = _Builder(data, problems)
    for name in data:
        if name not in DEFAULTS:
            problems.append(f"unknown section \"{name}\"; ignored.")
    result = Bindings()

    # Solo and Pass It: pause first, then the score, then the commands.
    taken: dict[int, str] = {}

    def claim(key: int, action: str, context: dict[int, str]) -> bool:
        if key in context:
            problems.append(f"{spoken_name(key)} is bound to both {context[key]} and {action}; "
                            f"kept for {context[key]}.")
            return False
        context[key] = action
        return True

    pause = b.keys("pause", data.get("pause", DEFAULTS["pause"]), DEFAULTS["pause"])
    result.pause = {k for k in pause if claim(k, "pause", taken)}
    if not result.pause:
        result.pause = {key_code(n) for n in DEFAULTS["pause"]}
    score = b.keys("score", data.get("score", DEFAULTS["score"]), DEFAULTS["score"])
    result.score = {k for k in score if claim(k, "score", taken)}
    game = b.section("game", data.get("game"), COMMANDS)
    for command in COMMANDS:
        default = DEFAULTS["game"][command]
        for k in b.keys(f"game {command}", game.get(command, default), default):
            if claim(k, command, taken):
                result.game[k] = command

    # Head 2 Head: pause, then its score, then each player's keys.
    h2h_taken: dict[int, str] = {k: "pause" for k in result.pause}
    h2h_defaults = DEFAULTS["head_to_head"]
    h2h = b.section("head_to_head", data.get("head_to_head"), H2H_PLAYERS + ("score",))
    score = b.keys("head_to_head score", h2h.get("score", h2h_defaults["score"]),
                   h2h_defaults["score"])
    result.h2h_score = {k for k in score if claim(k, "Head 2 Head score", h2h_taken)}
    for player, name in enumerate(H2H_PLAYERS):
        section = b.section(f"head_to_head {name}", h2h.get(name), H2H_SLOTS)
        for slot, slot_name in enumerate(H2H_SLOTS):
            default = h2h_defaults[name][slot_name]
            where = f"head_to_head {name} {slot_name}"
            for k in b.keys(where, section.get(slot_name, default), default):
                if claim(k, f"{name} {slot_name}", h2h_taken):
                    result.h2h[k] = (player, slot - 1 if slot else None)
    return result, problems


_current, _ = build(DEFAULTS)


def load_bindings(path: Path = KEYS_PATH) -> list[str]:
    """Load keys.json, writing it with the defaults if it is missing. Returns the problems
    found; the bindings in use are always complete."""
    global _current
    if not path.exists():
        try:
            path.write_text(json.dumps(DEFAULTS, indent=2) + "\n", encoding="utf-8")
            log.info("Wrote default keys to %s", path)
        except OSError as error:
            log.error("Could not write %s: %s", path, error)
        _current, problems = build(DEFAULTS)
        return problems
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("the file is not a set of sections")
    except (OSError, ValueError) as error:
        _current, _ = build(DEFAULTS)
        return [f"{path.name} could not be read ({error}); using the default keys."]
    _current, problems = build(data)
    return problems


def menu_nav_for(key: int) -> Nav | None:
    return MENU_KEYS.get(key)


def game_command_for(key: int) -> str | None:
    return _current.game.get(key)


def is_score_key(key: int) -> bool:
    return key in _current.score


def is_pause_key(key: int) -> bool:
    return key in _current.pause


def is_h2h_score_key(key: int) -> bool:
    return key in _current.h2h_score


def key_name_for(command: str) -> str | None:
    """The first key bound to a command, as a spoken name."""
    for key, bound in _current.game.items():
        if bound == command:
            return spoken_name(key)
    return None


def h2h_slot_for(key: int) -> tuple[int, int | None] | None:
    """(player, slot) for a Head 2 Head key; slot None is that player's Bop."""
    return _current.h2h.get(key)


def h2h_key_name(player: int, slot: int | None) -> str:
    for key, bound in _current.h2h.items():
        if bound == (player, slot):
            return spoken_name(key)
    return "no key"


def _names(keys: set[int] | list[int]) -> str:
    return " or ".join(spoken_name(k) for k in sorted(keys)) or "no key"


def describe_bindings() -> list[str]:
    """The current keys as short lines for the Help screen."""
    lines = []
    for command in COMMANDS:
        keys = [k for k, c in _current.game.items() if c == command]
        lines.append(f"{command}: {_names(keys)}")
    lines.append(f"Score: {_names(_current.score)}")
    lines.append(f"Pause: {_names(_current.pause)}")
    for player, name in enumerate(H2H_PLAYERS):
        parts = []
        for slot, slot_name in enumerate(H2H_SLOTS):
            want = (player, slot - 1 if slot else None)
            parts.append(f"{slot_name} {_names([k for k, s in _current.h2h.items() if s == want])}")
        lines.append(f"Head 2 Head {name}: " + ", ".join(parts))
    lines.append(f"Head 2 Head score: {_names(_current.h2h_score)}")
    lines.append(MENU_KEYS_TEXT)
    # Escape leaves the game from the main menu, but nothing inside a game does, and a
    # built Mac game has no menu bar to click, so the chord has to be written down.
    lines.append(f"To leave the game from anywhere, press {platform.quit_hint()}.")
    lines.append("To change the game keys, edit keys.json in the game folder.")
    return lines
