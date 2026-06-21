"""Wayland clipboard wrappers (wl-copy / wl-paste), X11 xclip fallback."""

import shutil
import subprocess

_PASTE = (
    ["wl-paste", "--no-newline"],
    ["xclip", "-selection", "clipboard", "-o"],
)
_COPY = (
    ["wl-copy"],
    ["xclip", "-selection", "clipboard"],
)


def _first_available(cmds):
    for cmd in cmds:
        if shutil.which(cmd[0]):
            return cmd
    return None


def paste():
    """Return clipboard text, or '' if unavailable."""
    cmd = _first_available(_PASTE)
    if not cmd:
        return ""
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=3)
        return out.stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        return ""


def copy(text):
    """Put `text` on the clipboard. Silent on failure."""
    cmd = _first_available(_COPY)
    if not cmd:
        return
    try:
        subprocess.run(cmd, input=(text or "").encode("utf-8"), timeout=3)
    except (OSError, subprocess.SubprocessError):
        pass
