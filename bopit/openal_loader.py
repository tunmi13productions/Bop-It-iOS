"""Load the vendored OpenAL Soft before cyal loads its own bundled copy.

cyal links against OpenAL32.dll, or libopenal.so.1 on Linux. Once a library with
that name is loaded, the system reuses it, so preloading ours by full path makes cyal use
it too. Must run before the first import of cyal.

The Mac has no vendored library, and does not need one. cyal's wheel there links
@loader_path/libopenal.1.dylib, which is the OpenAL Soft it carries beside it and which
only it can find; a copy anywhere else is not the one cyal binds to, so pretending
otherwise would be a lie told to the log. loaded_openal_path() says which OpenAL is
really in use on either platform.
"""

import ctypes
import logging
import sys

from bopit import platform
from bopit.config import VENDOR_DIR

log = logging.getLogger(__name__)

_loaded: ctypes.CDLL | None = None


def preload_openal() -> None:
    global _loaded
    if _loaded is not None:
        return
    if "cyal" in sys.modules:
        log.error("cyal was imported before the vendored OpenAL was loaded; using cyal's copy")
        return
    path = platform.openal_library(VENDOR_DIR)
    if path is None:
        log.warning("No vendored OpenAL for platform %s, using the system one", sys.platform)
        return
    try:
        mode = getattr(ctypes, "RTLD_GLOBAL", 0)
        _loaded = ctypes.CDLL(str(path), mode=mode)
    except OSError:
        log.exception("Could not load vendored OpenAL from %s, falling back to cyal's copy", path)
        return
    log.info("Loaded OpenAL from %s", path)


def loaded_openal_path() -> str | None:
    """Full path of the OpenAL library actually in use, or None if it cannot be told.

    Worth having on both platforms, and for the same reason: it is the only way
    to see whether the preload above took, or whether cyal quietly bound to its
    own copy instead.
    """
    if platform.WINDOWS:
        return _windows_openal_path()
    if platform.MAC:
        return _mac_openal_path()
    return str(_loaded or "") or None


def _windows_openal_path() -> str | None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GetModuleHandleW.restype = ctypes.c_void_p
    kernel32.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
    handle = kernel32.GetModuleHandleW("OpenAL32.dll")
    if not handle:
        return None
    buffer = ctypes.create_unicode_buffer(1024)
    kernel32.GetModuleFileNameW(handle, buffer, len(buffer))
    return buffer.value


class _DlInfo(ctypes.Structure):
    """The one field of dl_info the Mac's dladdr fills in that we want."""

    _fields_ = [("dli_fname", ctypes.c_char_p),
                ("dli_fbase", ctypes.c_void_p),
                ("dli_sname", ctypes.c_char_p),
                ("dli_saddr", ctypes.c_void_p)]


def _mac_openal_path() -> str | None:
    """Ask dyld which file supplies alcOpenDevice, which is where OpenAL's
    functions land whether ours or cyal's was loaded."""
    try:
        library = ctypes.CDLL(None)
        library.dladdr.restype = ctypes.c_void_p
        library.dladdr.argtypes = [ctypes.c_void_p, ctypes.POINTER(_DlInfo)]
        address = ctypes.cast(library.alcOpenDevice, ctypes.c_void_p)
        info = _DlInfo()
        if not library.dladdr(address, ctypes.byref(info)):
            return None
        name = info.dli_fname.decode("utf-8", "replace") if info.dli_fname else ""
        return name or None
    except (AttributeError, OSError):
        log.debug("Could not ask dyld which OpenAL is loaded", exc_info=True)
        return None
