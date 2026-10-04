"""Start Bop It. The same as python -m bopit, and the script compiler.py builds from.

A built game has no console window, so if it fails before speech is working, the error is
written to crash.txt beside the executable, or on the Mac beside the app bundle, with the
rest of the player's files.
"""

import sys
import traceback

from bopit.__main__ import main
from bopit.config import USER_DIR

if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        if getattr(sys, "frozen", False):
            (USER_DIR / "crash.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
