# Deliberate deviations from the original

Each entry needs a reason and the developer's approval.

## Visuals are the lowest priority

The port shows the original's own images, but the visuals are built last and kept simple: screens are drawn from the original's layouts and images, without its animations, transitions or exact fonts, and some details may be missing or placed differently. The screen may not look the same as the original. Two things are added for anyone watching: a caption strip at the bottom showing the focused menu item, or during play the command being called, and a frame round the BopJect being called. The picture is redrawn at most 30 times a second so drawing never delays input. Everything that matters for play is delivered through speech and sound, which always come first. Reason: the game is made to be played without sight; the visuals are for sighted people watching or helping. Approved 2026-09-30.

## Menu order is top to bottom

The original menus are touch screens with round buttons scattered around, so they have no list order. Menu items are listed by their on-screen position, top to bottom, using the button centers from the decoded nibs. Back is not a list item; it is on the back key. Reason: menus must be linear to be navigated by keyboard and speech. Approved 2026-09-29.

## Online features are left out

More Games (an EA store link), the Friends and Global score tabs, Weekly scores, Submit Score, Facebook sharing, and the Origin network are not included. Only local scores remain. Reason: the services behind them no longer exist. Approved 2026-09-29.

## Menus wrap around

Moving past the last item goes to the first, and the other way round. Reason: keyboard navigation convenience. Approved 2026-09-29.

## Theme is a menu item

The original changed skins (Original, Halloween, Christmas) by swiping the main menu sideways. Here it is a Theme choice at the bottom of the main menu, where the original's "swipe for themes" hint sat, changed with Left, Right or Enter. It cycles in the original's order and restarts the menu music like a swipe did. Reason: keyboard operation. Approved 2026-09-29.

## Escape on the main menu quits

The iPhone game had no way to quit. Here the back key on the main menu exits the game immediately, with no confirmation. Reason: a desktop program needs a keyboard way to exit. Approved 2026-09-29.

## Silent commands are not offered for now

The original's Commands setting had VOX, SFX and Silent. Silent showed each command as a picture with no sound, which cannot be played without sight. The Commands choice offers only VOX and SFX. The original's Silent behavior stays documented in ORIGINAL_BEHAVIOR.md and in code comments, in case it is added later. Reason: accessibility. Approved 2026-09-29.

## Help popup speaks the command's key

When a command called 2 times or fewer is failed, the original paused on a help popup showing the command's tutorial text, with Continue and Try It. Here the popup is a menu with the same two buttons, and the text names the command and its key, for example "Twist It: press Left.". The timing of the pause is unchanged. Reason: the touch instructions do not apply to a keyboard. Approved 2026-09-29; Try It added 2026-09-30.

## A key speaks the score during play

The original showed moves and points on screen during a game. Here a key (currently S) speaks them on demand instead of after every move, which would talk over the callouts. It never counts as a move. Points are moves plus bonus score, as the original showed them during play. Reason: accessibility. Approved 2026-09-29.

## Rhythm grades are spoken on request

In Basic and Extreme the original showed PERFECT, GOOD or OK after every move. Here the score key also says the last move's grade, for example "Last move Perfect." Speaking each grade automatically would land on top of the next callout. A later option could speak grades automatically, interrupting other speech. Reason: accessibility. Approved 2026-09-29.

## Streak banners are spoken

The original showed a "25 PERFECT streak" or "25 GOOD streak" banner. Here it is spoken, for example "25 Perfect streak." Reason: accessibility. Approved 2026-09-29.

## New commands are announced

In Basic and Extreme a new BopJect appeared on screen when a command entered play. Here its entrance is spoken, for example "Spin added." The first time a command is ever unlocked, the original's unlock message is spoken instead, for example "Spin to Win! Spin Unlocked", and remembered in progress.json so it is only heard once, as in the original. Reason: accessibility. Approved 2026-09-29.

## Tutorials for the keyboard

The tutorials are built as the original's: Help's Tutorials list, one practice screen per command, Try It on the help popup, and the one-time question before the first game. The differences:

- Each tutorial text names the command and its key, for example "Twist It: press Left.", instead of the original's touch and phone-movement instructions. Shout keeps its microphone X-Move line when the microphone setting is on. The same text is used on the help popup.
- The original's Help button replayed an animation of the move, and one also played while the tutorial was open. Here Help reads the tutorial text again.
- While practicing, every key goes to the game, and the pause key (Escape) stops, like the original's Try button turning into Stop. Starting practice says "Practice. Escape to stop."; stopping says "Stopped.".

Reason: the original's tutorials were visual and touch based. Approved 2026-09-30.

## Microphone setting for the Shout It X-Move

The original always used the microphone for the Shout It X-Move. It is kept here with the original's timing (listening starts 0.46 seconds per pitch into a Shout turn), threshold (0.6 linear average level) and bonus (25), but only the level is measured and nothing is played back. A Microphone setting, added as the last Settings item, turns it on or off; it defaults to on. If no microphone can be opened, "No microphone found. Use the Shout key." is spoken once and the key still works. Reason: desktop speakers can leak game sound into a microphone, which the phone's hardware did not. Approved 2026-09-29.

## Pause key and the back key in the pause menu

The original paused with an on-screen pause button. Here the back key (Escape) pauses during a game. In the pause menu the back key resumes, as pressing the original's pause button again closed the menu. On the "Bop It to start" screen, where there is nothing to pause yet, the back key returns to the main menu. Reason: keyboard operation. Approved 2026-09-29.

## Quick Play is chosen by holding Enter

The original chose the Quick Play mode by holding a mode button. Here Enter (or Space) is held on a mode, with the original's timings: 1.2 seconds sets it, a release within 1.1 seconds starts the mode. The original's "default selected" marker is spoken as the item's state ("Classic, Quick Play, 1 of 4") and the change is announced ("Classic is now your Quick Play game."). The first-visit popup reads "Press and hold Enter on any game mode to make it your Quick Play game" instead of "press and hold any game mode button". Reason: keyboard operation and accessibility. Approved 2026-09-29.

## Scores page adaptations

Only the local list is kept (the Friends, Global, Weekly and All Time tabs were online). The mode tabs are a Mode choice at the top. An empty list reads "No scores" rather than being silent. Reason: online services are gone; an empty table must be spoken. Approved 2026-09-29 as part of dropping online features.

## Trophy notices are spoken

The original's "new trophy" image during play, and the trophy shown on the end screen, are spoken as "New trophy." The end screen's trophy button becomes a "Trophies" item at the top of its menu. On the Trophies page, earned trophies read their medal ("bronze trophy") and the rest read "locked". Reason: accessibility. Approved 2026-09-29.

## Tips adapted for this port

Of the original's 12 end-screen tips: the two about Submit Score (Facebook and the leaderboard) are removed; three touch-screen and phone tips are rewritten: "Try holding the device flat, like it's on a table" became "Trouble with X-Moves? Shout it loud and close to your microphone", "Try Silent Mode" became "Turn the Microphone off in Options>Settings", and "Try doing the finger gesture directly on top of it" became "Wait for the command to finish, then press its key". The Tutorials tip is left out until tutorials exist. The rest, including the two Bop It XT and Bop It HD tips, are verbatim. The original's 26 percent chance and no-repeat order are kept. Reason: the originals referred to things this port does not have. Approved 2026-09-29.

## Help overview adapted for this port

The Help overview keeps the original's sections, order and wording except where it described the phone, the touch screen or online features (the port's text is in bopit/port_texts.py, the original in bopit/texts.py): the Zoom set-up note became a headphones note; "using the touch screen" became "using the keyboard"; the X-Move section describes the microphone shout; Basic's hint about the dancing BopJects became "listen to the music: time your move with the second beat after the command"; the Scoring section points to Games>Scores instead of the leaderboard and Facebook; the Facebook section is removed; the pause button became Escape; Silent is removed from the Commands line, "Tap Off" became "Set it to Off" and a Microphone line is added; Quick Play says "Press and hold Enter on any game mode for about a second" (the original said 2 seconds; its code used 1.2). Head2Head's description (in Help and on its intro screen) says "Complete the moves on your side of the keyboard. Press your Bop key first" instead of "your half of the screen. Tap your half of the Bop first"; the other multiplayer descriptions are unchanged (approved 2026-09-30). Reason: the original text described things this port does not have. Approved 2026-09-30.

## Command picker spoken states

In the command picker each command reads "on", "off" or "locked" instead of the original's "(X)" titles and greyed out buttons, Bop It reads "always on", and GO reads "unavailable" until two commands are picked. Trying to pick a fifth says "4 already chosen." where the original silently did nothing. Reason: accessibility. Approved 2026-09-30.

## Head 2 Head callouts are panned

In Head 2 Head each player's commands were on their half of the screen. Here each callout is panned toward its owner (Green, player one, left; Blue, player two, right) and Bop stays in the centre. Reason: the screen halves cannot be seen. Approved 2026-09-30.

When the next command belongs to the other player than the last player's command, a short cue plays first: sounds/accessibility/green.wav or blue.wav, panned to that player's side, as the callout's voice starts (when the turn opens). Bop is shared, gets no cue and does not count as a change. Reason: panning alone is lost on speakers; the developer supplied the sounds, which are from Game Master Audio's Retro Classic pack (Collectables). Approved 2026-09-30.

## Head 2 Head keys, points and a stray Bop

Each player has their own keys, by position: a Bop key and one key for each of their commands, in the order the commands were picked. At "Bop it to start" the game says which command is on which key for each player. The score key is Tab here, as S is one of Green's keys. Reason: two players share one keyboard, and the commands each player owns change with the picks. Approved 2026-09-30.

When someone scores, the port says the scorer's name and new points, for example "Green 3". The original showed a silent animation. Reason: points are the whole game here and the animation cannot be seen. Approved 2026-09-30.

A player who presses their Bop key during the opponent's command gives the opponent the point, like any other press on the opponent's command. In the original the two Bop halves sat outside the screen areas it checked for touches on the wrong side, so such a tap most likely counted as the command's owner failing, handing the tapper a point. Reason: with keys it is always known who pressed, and the original's result looks like an accident of its layout. Approved 2026-09-30.

## Pass It lets the bar finish before passing

The original stopped the music and the success's "b" part at the passing success, waited half a beat and then played the Pass It music and VO_Pass together, so "Pass!" came about 1.3 beats later and off the beat. Here, at the passing success only the queued callout is cut; the loop and the "b" part play to the end of the bar, VO_Pass starts at the success so that its one-beat lead-in ends on the next downbeat, and the Pass It music starts on that downbeat. The next player still starts 3.25 per pitch after the Pass It music begins. Reason: the developer found the original timing broke the rhythm; this keeps "Pass!" on the first beat of the bar. Approved 2026-09-30.

## Keys in a file, and a Keys page in Help

The original was played by touch. Here the game keys (every command, the score key, pause and the Head 2 Head keys) are read from keys.json in the game folder, written with the defaults on first run. A missing or broken entry uses its default, and every problem is logged, printed and summed up in speech. Menu keys are fixed so a broken file cannot lock anyone out. Help has a third item, Keys, after Overview and Tutorials, listing the keys in use. Reason: keyboard play, and the developer asked for keys a player can change. Approved 2026-09-30.

## Text size setting

Options>Settings has a Text size slider, last in the list, from 12 to 32 points in steps of 2, starting at 16. It sets the size of the caption strip at the bottom of the screen; long text wraps and the strip grows to fit, up to half the screen. The labels inside the original's buttons keep their original size. Changing it makes no sound; the new size is spoken. Reason: for low-vision players and anyone watching, who each need a different size. Approved 2026-09-30.

## Language setting

The original followed the device's language and had no setting. Here Options>Settings has a Language item, with each language named in its own language (English, Deutsch, Español, Français, Italiano). The first run picks the system's display language if it is one of the five, otherwise English: Windows's UI language, or the Mac's own list of preferred languages; after that the setting wins, so a player can choose a language different from the system's. Reason: players may want the game in a language other than their computer's. Approved 2026-09-30; the Mac added 2026-10-04.

Text the original showed comes from the original's own translations (bopit/lang, made by tools/extract_texts.py). Text only this port has, such as spoken states, positions like "1 of 5", the Keys page and the reworded Help lines, stays in English. Reason: those texts have no original translation, and machine translations could not be checked. Approved 2026-09-30.

## German banter line 7 from a later version

1.1.9's German banter list includes line 7, but 1.1.9 had no German recording of it, so that slot played nothing. The port uses the German line 7 from a later version of the app, supplied by the developer. Reason: fills an accidental gap. Approved 2026-09-30.

## Sliders move in 10 percent steps

The Music and SFX sliders were continuous touch sliders. With the keyboard, each press moves them 10 percent. Reason: keyboard operation. Approved 2026-09-29.

## The game runs on macOS as well as Windows

The port is the same game on both platforms, not two games: the same engine, the same rules, timing, scoring, menus and sounds, and the same keyboard. Only the four things a platform has to decide live outside the game, in bopit/platform.py: how the game is quit (Alt+F4 on Windows, Command Q on the Mac, since a built Mac game has no menu bar of its own), which OpenAL Soft library is loaded, how the system's language is read, and where a built game keeps the player's own files. Speech is Prism on both, which means NVDA on Windows and VoiceOver or the system's own voice on the Mac; nothing else changed. Reason: the port should reach the players who have a Mac. Added 2026-10-04.

## pygame is started before speech, because the Mac cares about the order

On the Mac, SDL's first call to the video system builds the NSApplication object, gives it a normal activation policy and finishes launching it. If something has already loaded AppKit, SDL finds the application object already in place and leaves it unfinished. Prism's Mac backend loads AppKit on its way to AVFoundation, so starting speech first produced exactly that: the window appeared behind everything else, never took the keyboard, and macOS reported it as not responding, while the game itself ran perfectly well. So `main()` calls `pygame.init()` before `create_speech()`, and the window behaves. The fix is deliberately a change of order rather than a call that patches the policy afterwards, because a policy that is set by hand still leaves the application unfinished, which is the half that makes macOS call the window unresponsive. Symptom to watch for, if it ever comes back: the window is on screen, the game is playable, and no key ever reaches it. Reason: it is otherwise invisible from the code and it makes the game unplayable with sight and speech both. Added 2026-10-05.

## OpenAL Soft is not vendored on macOS

Windows and Linux carry OpenAL Soft in vendor, and bopit/openal_loader.py opens it before cyal is imported so cyal binds to it: cyal's Windows extension links OpenAL32.dll and the loader finds the vendored file already in the system under that name. The Mac cannot work that way. cyal's Mac wheel links OpenAL Soft through @loader_path, which only finds the copy beside cyal itself, so a vendored copy elsewhere would never be the library in use, and shipping one would only make the log lie. So on the Mac the game uses the OpenAL Soft that comes with cyal, which is the same library. bopit/openal_loader.py reports which OpenAL is really loaded on either platform, by asking dyld on the Mac and by asking the loader on Windows. Reason: honesty about what is running, and a 1.7 MB binary in the repository that does nothing. Added 2026-10-04.

## The built Mac game's own files sit beside the bundle

A built Windows game keeps settings.json, keys.json, scores.json, progress.json and logs/ beside BopIt.exe, and a new build leaves them alone. A Mac app keeps everything inside the bundle, where the next build replaces it, so the Mac game keeps its files in the folder holding BopIt.app instead: the same folder the Windows build's files are in, relative to the game. crash.txt goes there too. Reason: the point of keeping them beside the game is not losing them to a rebuild. Added 2026-10-04.

## The Keys page says how to quit from anywhere

Help's Keys page ends with the line "To leave the game from anywhere, press Alt+F4" on Windows and "press Command Q" on the Mac. Escape already leaves the game from the main menu, as it always did, but nothing inside a game does, and the Mac has no menu bar to click. Reason: a blind player has no way to find the chord otherwise. Added 2026-10-04.
