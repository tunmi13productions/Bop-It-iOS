# Speech interruption policy

All speech goes through `bopit/speech.py`. No other module imports Prism.

## Backend

Prism picks the best available backend. On the developer's Windows machine that is NVDA, and on the Mac VoiceOver when it is running, otherwise the system's own voice through Prism's AVSpeech backend. NVDA's backend cannot report whether it is currently speaking, so nothing in this policy depends on knowing that. `Speech.is_speaking()` returns None when the backend cannot tell.

Text is sent with Prism's `output`, which speaks and also sends to a braille display, when the backend supports it.

If Prism fails to initialize, the error is logged and printed, and speech falls back to printing each message to the console as a line starting with `SPEECH:`.

## Three kinds of speech

1. Queued: `speak(text)`. Waits behind whatever is already being said. For informational messages that should not cut anything off.
2. Interrupting: `speak(text, interrupt=True)`. Cuts off current speech. Used for menu navigation, so fast arrowing never builds a backlog, and for game commands, which must replace anything stale immediately.
3. Protected: `speak(text, interrupt=True, protect=True)`. Used for score announcements and game over. The utterance is shielded until its estimated end.

## What protection does

While protected speech is active:

- An interrupting request is downgraded to queued, so it is heard after the protected message instead of cutting it off.
- `stop()` is ignored. `stop(force=True)` still works and clears protection.
- Another protected request may interrupt, and queued protected requests extend the protected window.

Since NVDA cannot report when it finishes, the protected window is estimated as the text length divided by `speech_chars_per_second` in settings (default 18), plus 0.3 seconds. If your NVDA rate is faster or slower, adjust that setting.

## Timing

Speech never blocks the game loop. Game timing windows are measured from the audio prompt, never from speech.
