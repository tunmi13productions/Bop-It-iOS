"""The pygame window, event loop and screen stack."""

import logging
import time
from typing import Protocol

import pygame

from bopit import screens
from bopit import platform
from bopit.audio import Audio, Voice
from bopit import i18n
from bopit.config import Settings, save_settings
from bopit.debug.event_log import EventLog
from bopit.debug.options import DebugOptions
from bopit.engine.game import (BASIC, BLITZ, BLITZ_CHALLENGE, CLASSIC, EXTREME, HEAD_TO_HEAD,
                               PASS_IT_BASIC, PASS_IT_EXTREME, ModeRules)
from bopit.game_screen import GameScreen
from bopit.tutorial_screen import TutorialScreen
from bopit.visuals import Renderer
from bopit.input_map import load_bindings, menu_nav_for
from bopit.menu import Menu
from bopit.microphone import Microphone
from bopit.progress import Progress
from bopit.savegame import SavedGame
from bopit.tips import PORT_TIPS, Tips
from bopit.scores import Scores
from bopit.speech import Speech
from bopit.themes import themed

log = logging.getLogger(__name__)

# Keys are timestamped when the loop sees them, so a faster loop means fairer timing.
FRAMES_PER_SECOND = 120
# The picture is redrawn at most this often, so drawing never takes time from input.
DRAW_INTERVAL = 1 / 30
MODES: dict[str, ModeRules] = {"Classic": CLASSIC, "Basic": BASIC, "Extreme": EXTREME,
                               "Blitz": BLITZ, "Pass It Basic": PASS_IT_BASIC,
                               "Pass It Extreme": PASS_IT_EXTREME,
                               "Blitz Challenge": BLITZ_CHALLENGE,
                               "Head 2 Head": HEAD_TO_HEAD}
# The launch voice (LandingPage::setInitialPositions).
LAUNCH_VOICE_POSITION = 0.35
LAUNCH_VOICE = "VO_Miscellaneous_Bop It [Intro]"
# Multiplayer modes that go through the command picker first.
PICKER_MODES = {"Pass It Basic", "Pass It Extreme", "Head 2 Head"}


class Screen(Protocol):
    title: str

    def enter(self, now: float) -> None: ...

    def key(self, key: int, now: float) -> None: ...

    def update(self, now: float) -> None: ...


class MenuScreen:
    """Runs a speech menu as a screen."""

    def __init__(self, app: "App", menu: Menu) -> None:
        self.title = menu.title
        self._app = app
        self._menu = menu

    def enter(self, now: float) -> None:
        self._menu.enter(self._app.speech)

    def key(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.handle(nav, self._app.speech, self._app.play_themed, now)

    def caption(self) -> str:
        return self._menu.describe()

    def key_up(self, key: int, now: float) -> None:
        nav = menu_nav_for(key)
        if nav is not None:
            self._menu.release(nav, self._app.play_themed, now)

    def update(self, now: float) -> None:
        self._menu.update(now)


class App:
    def __init__(self, speech: Speech, audio: Audio, settings: Settings,
                 debug: DebugOptions | None = None, event_log: EventLog | None = None) -> None:
        self.speech = speech
        if not settings.language:
            # The first run takes the system's language, as the original took the phone's.
            settings.language = i18n.system_language()
        i18n.set_language(settings.language)
        if hasattr(audio, "set_language"):
            audio.set_language(settings.language)
        self.debug = debug
        self.event_log = event_log
        self.audio = audio
        self.settings = settings
        self.scores = Scores()
        self.progress = Progress()
        self.microphone = Microphone()
        self.saved_game = SavedGame()
        self.tips = Tips(PORT_TIPS)
        self.announced_no_microphone = False
        # Bop_ItViewController::viewDidLoad: 2 players until changed, for the session.
        self.blitz_players = 2
        self._stack: list[Screen] = []
        self._running = False
        self._menu_music: Voice | None = None
        # How often each command has been called. The original kept this on its Command
        # objects, which lived across games until the command list was rebuilt.
        self.times_called: dict[str, int] = {}
        self._commands_key = (settings.theme, settings.shout_it)
        # GameSettings modeToReturnFromTutorial: set whenever a game mode is entered, and
        # forgotten only by an end screen's Menu, the intro's Back or the end screen's
        # Trophies button. While set, Back from any tutorial starts that mode again.
        self.tutorial_return: tuple[ModeRules, tuple[str, ...]] | None = None

    # Navigation

    def push(self, screen: Menu | Screen) -> None:
        self._stack.append(self._as_screen(screen))
        self._enter_top()

    def replace(self, screen: Menu | Screen) -> None:
        self._stack[-1] = self._as_screen(screen)
        self._enter_top()

    def pop(self) -> None:
        if len(self._stack) <= 1:
            return
        self._stack.pop()
        self._enter_top()

    def return_to_menu(self) -> None:
        """GameController::returnToMenu: back to the main menu with the menu music."""
        del self._stack[1:]
        # Rebuilt so the Play item shows Quick Play or Resume Game correctly.
        self._stack[0] = self._as_screen(screens.main_menu(self))
        self.start_menu_music()
        self._enter_top()

    def leave_game(self) -> None:
        """An end screen's Menu, or the intro's Back (releaseModeString, returnToMenu)."""
        self.clear_tutorial_return()
        self.return_to_menu()

    def clear_tutorial_return(self) -> None:
        self.tutorial_return = None

    def open_tutorial(self, command: str) -> None:
        self.push(TutorialScreen(self, command))

    def try_tutorial(self, command: str) -> None:
        """Try It on the help popup (GameViewController::errorHelpPressed): out of the game
        to Help's tutorials and into this command's tutorial."""
        self._to_tutorials()
        self.push(TutorialScreen(self, command))

    def tutorial_back(self) -> None:
        """Back from a tutorial: into the mode it came from, or back to the tutorials."""
        if self.tutorial_return is not None:
            rules, picked = self.tutorial_return
            del self._stack[1:]
            self._stack[0] = self._as_screen(screens.main_menu(self))
            self._begin(rules, picked)
            return
        self.pop()
        self.start_menu_music()

    def _to_tutorials(self) -> None:
        """Main menu, Options, Help and its Tutorials tab, as the original rebuilt its
        screens, with the menu music back on (GameController::returnBack)."""
        del self._stack[1:]
        self._stack[0] = self._as_screen(screens.main_menu(self))
        self._stack.append(self._as_screen(screens.options_menu(self)))
        self._stack.append(self._as_screen(screens.help_menu(self)))
        self.start_menu_music()
        self.push(screens.tutorials_menu(self))

    def first_time(self, flag: str) -> bool:
        return self.progress.first_time(flag)

    def open_trophies(self) -> None:
        self.push(screens.trophies_menu(self))

    def has_saved_game(self) -> bool:
        return self.saved_game.exists()

    def play_pressed(self) -> None:
        """LandingPage::executePlayButtonPressed: resume a saved game, else Quick Play."""
        saved = self.saved_game.take()
        if saved is not None and saved.get("mode") in MODES:
            self.stop_menu_music()
            rules = MODES[saved["mode"]]
            self.tutorial_return = (rules, tuple(saved.get("picked", ())))
            self.push(GameScreen(self, rules, saved=saved))
            return
        self.start_mode(self.settings.quick_play)

    def quit(self) -> None:
        log.info("Quit from main menu")
        self._running = False

    def not_built(self, what: str) -> None:
        self.speech.speak(f"{what} is not built yet.", interrupt=True)

    def start_mode(self, name: str) -> None:
        rules = MODES.get(name)
        if rules is None:
            self.not_built(name)
            return
        if name in PICKER_MODES:
            self.push(screens.picker_menu(self, name, lambda picked: self._begin(rules, picked)))
            return
        if rules.challenge_target is not None:
            self.push(screens.player_select_menu(self, lambda: self._begin(rules, ())))
            return
        self._begin(rules, ())

    def _begin(self, rules: ModeRules, picked: tuple[str, ...]) -> None:
        # Choosing a mode stops the menu music (GameController::init).
        self.stop_menu_music()
        self.tutorial_return = (rules, picked)
        if self.first_time("tutorial_popup"):
            # The first game ever asks about the tutorials instead of showing its intro.
            self.push(screens.tutorial_popup(
                self, lambda: self.replace(GameScreen(self, rules, start_now=True, picked=picked,
                                                      announce_start=False)),
                self._to_tutorials))
            return
        best = self.scores.best(rules.name) if rules.tracks_trophies else None
        self.push(screens.intro_menu(self, rules.name, best,
                                     lambda: self.replace(GameScreen(self, rules, picked=picked))))

    # Settings and sound

    def settings_changed(self) -> None:
        self.audio.set_mix(self.settings.sfx_volume / 100, self.settings.music_volume / 100)
        # The original rebuilt its commands (GameSettings::createCommands) on a theme or
        # Shout It change, which reset their call counts.
        key = (self.settings.theme, self.settings.shout_it)
        if key != self._commands_key:
            self._commands_key = key
            self.times_called.clear()
        save_settings(self.settings)

    def language_changed(self) -> None:
        i18n.set_language(self.settings.language)
        self.audio.set_language(self.settings.language)
        self.settings_changed()

    def play(self, name: str) -> None:
        self.audio.play(name)

    def speak(self, text: str) -> None:
        self.speech.speak(text, interrupt=True)

    def play_themed(self, name: str) -> None:
        """For sounds the original passed through GetSkinFilename, like menu buttons."""
        self.audio.play(themed(name, self.settings.theme))

    def play_launch_voice(self) -> None:
        """LandingPage::setInitialPositions, the first time the main menu appears (not when a
        saved game resumes): in English, VO_Bop from 0.35 seconds in; in the other languages,
        their "Bop It" intro recording. At the effects volume, whatever the Commands setting."""
        if self.settings.language == "en":
            voice = self.audio.play("VO_Bop")
            if voice is not None:
                voice.seek(LAUNCH_VOICE_POSITION)
        else:
            self.audio.play(LAUNCH_VOICE)

    def start_menu_music(self) -> None:
        if self._menu_music is not None and self._menu_music.playing:
            return
        self._menu_music = self.audio.play(
            themed("MUSIC_MenuMusic", self.settings.theme), loop=True, music=True)

    def stop_menu_music(self) -> None:
        if self._menu_music is not None:
            self._menu_music.stop()
            self._menu_music = None

    # Loop

    def run(self) -> None:
        pygame.init()
        # The original's 320 by 480 point screen, scaled up to fit the desktop.
        surface = pygame.display.set_mode((320, 480), pygame.SCALED)
        pygame.display.set_caption("Bop It")
        renderer = Renderer(surface)
        last_draw = 0.0
        clock = pygame.time.Clock()
        self.settings_changed()
        self._load_keys()
        # The original starts the menu music at launch whatever the Commands setting.
        self.start_menu_music()
        self.push(screens.main_menu(self))
        if self.saved_game.exists():
            # Bop_ItAppDelegate::doFinishLaunching: a saved game resumes at launch, paused.
            self.play_pressed()
        else:
            self.play_launch_voice()
        self._running = True
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    self._key_down(event, time.perf_counter())
                elif event.type == pygame.KEYUP:
                    key_up = getattr(self._stack[-1], "key_up", None)
                    if key_up is not None:
                        key_up(event.key, time.perf_counter())
            self._stack[-1].update(time.perf_counter())
            self.audio.update()
            now = time.perf_counter()
            if now - last_draw >= DRAW_INTERVAL:
                last_draw = now
                self._draw(renderer)
            clock.tick(FRAMES_PER_SECOND)
        self.microphone.close()
        pygame.quit()

    def _load_keys(self) -> None:
        """keys.json, written with the defaults on first run. Problems are logged, printed
        and summed up in speech; the keys in use are always complete."""
        problems = load_bindings()
        for problem in problems:
            log.error("keys.json: %s", problem)
            print(f"keys.json: {problem}")
        if problems:
            count = len(problems)
            self.speech.speak(f"keys.json has {count} problem{'s' if count > 1 else ''}. "
                              "Default keys used there. Details in the console and the log.",
                              protect=True)

    def _draw(self, renderer: Renderer) -> None:
        """The picture, lowest priority: a drawing problem is logged once and never stops
        the game."""
        screen = self._stack[-1]
        try:
            caption = getattr(screen, "caption", lambda: None)()
            texts: dict[str, str] = {}
            if screen.title == "Bop It":
                # LandingPage::setPlayButtonLabel: "quick" over "play", or "resume" over
                # "game" when there is a saved game.
                top, bottom = ("resume", "game") if self.has_saved_game() else ("quick", "play")
                texts = {"playLabel": i18n.tr(top), "playLabel2": i18n.tr(bottom)}
            elif screen.title in MODES:
                texts = self._intro_texts(screen.title)
            renderer.draw(screen, self.settings.theme, caption, texts, self.settings.text_size)
            pygame.display.flip()
        except Exception:
            if not getattr(self, "_draw_failed", False):
                self._draw_failed = True
                log.exception("Drawing failed; the game carries on without updating the picture")

    def _intro_texts(self, mode: str) -> dict[str, str]:
        """GameModeIntro::viewDidLoad filled in the mode, its description and the high
        score; multiplayer modes had none."""
        texts = {"gameModeLabel": i18n.tr(mode),
                 "gameModeDescriptionLabel": i18n.tr(screens.MODE_DESCRIPTIONS.get(mode, ""))}
        rules = MODES[mode]
        best = self.scores.best(mode) if rules.tracks_trophies else None
        if best is None or (best.score == 0 and best.moves == 0):
            texts.update(highScoresStaticLabel="", highMovesLabel="", highScoreLabel="")
        elif rules.blitz_target is not None:
            texts.update(highMovesLabel=f"{best.score:.4f}s", highScoreLabel="")
        else:
            texts.update(highMovesLabel=f"{best.moves} {i18n.tr('Moves')}",
                         highScoreLabel=f"{int(best.score):,} {i18n.tr('Points')}")
        return texts

    def _key_down(self, event: pygame.event.Event, now: float) -> None:
        if platform.is_quit(event.key, event.mod):
            self._running = False
            return
        self._stack[-1].key(event.key, now)

    def _as_screen(self, screen: Menu | Screen) -> Screen:
        return MenuScreen(self, screen) if isinstance(screen, Menu) else screen

    def _enter_top(self) -> None:
        screen = self._stack[-1]
        log.info("Screen: %s", screen.title)
        if self.event_log is not None:
            self.event_log.line(time.perf_counter(), f"screen: {screen.title}")
        screen.enter(time.perf_counter())
