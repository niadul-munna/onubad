"""StatusNotifierItem tray via AyatanaAppIndicator3 (native, no pip deps).

Registers an SNI item that COSMIC's status-area applet renders in the panel.
"""

import os
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except (ValueError, ImportError):  # older distros
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3 as AppIndicator

from gi.repository import Gtk  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

ICON_NAME = "translate-tool"


def _icon_dir():
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    d = Path(base) / "translate-tool" / "icons"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _bengali_font(size):
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", ":lang=bn"],
                             capture_output=True, timeout=3)
        path = out.stdout.decode().strip()
        if path:
            return ImageFont.truetype(path, size)
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _generate_icon(path):
    img = Image.new("RGBA", (64, 64), (37, 99, 175, 255))
    d = ImageDraw.Draw(img)
    font = _bengali_font(44)
    if font:
        d.text((14, 4), "অ", fill="white", font=font)
    else:
        d.text((16, 20), "Bn", fill="white")
    img.save(path)


def _ensure_icon():
    d = _icon_dir()
    icon = d / f"{ICON_NAME}.png"
    if not icon.exists():
        _generate_icon(icon)
    return str(d)


class Tray:
    def __init__(self, on_open, on_clipboard, on_quit):
        icon_dir = _ensure_icon()
        self.ind = AppIndicator.Indicator.new_with_path(
            "translate-tool", ICON_NAME,
            AppIndicator.IndicatorCategory.APPLICATION_STATUS, icon_dir)
        self.ind.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self.ind.set_title("Translate EN↔BN")

        menu = Gtk.Menu()
        for label, cb in (("Open", on_open),
                          ("Translate clipboard", on_clipboard),
                          ("Quit", on_quit)):
            item = Gtk.MenuItem(label=label)
            item.connect("activate", lambda _w, c=cb: c())
            menu.append(item)
        menu.show_all()
        self.ind.set_menu(menu)
        self.menu = menu  # keep reference alive

    def stop(self):
        self.ind.set_status(AppIndicator.IndicatorStatus.PASSIVE)
