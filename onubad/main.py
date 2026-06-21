"""Entry point. Routes CLI actions to a single running instance, else starts."""

import sys

from . import ipc
from .history import History


def _parse_action(argv):
    if "--clipboard" in argv:
        return "clipboard"
    if "--open" in argv:
        return "open"
    return None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    action = _parse_action(argv)

    # Hand off to an already-running instance if present.
    if action and ipc.try_connect_and_send(action):
        return 0

    # Heavy GUI imports happen only when we are the primary instance.
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, GLib
    except Exception as exc:  # noqa: BLE001
        print(f"GTK unavailable: {exc}", file=sys.stderr)
        return 1

    try:
        from .tray import Tray
    except (ValueError, ImportError) as exc:
        print(f"AppIndicator typelib missing ({exc}).\n"
              "Install it: sudo apt install gir1.2-ayatanaappindicator3-0.1",
              file=sys.stderr)
        return 1

    from .popup import Popup

    popup = Popup(History())

    def do_action(name):
        if name == "clipboard":
            popup.show_and_translate_clipboard()
        else:
            popup.show()
        return False  # one-shot idle callback

    server = ipc.serve(lambda a: GLib.idle_add(do_action, a))

    def quit_app():
        try:
            server.close()
        finally:
            tray.stop()
            Gtk.main_quit()
        return False

    tray = Tray(
        on_open=lambda: GLib.idle_add(do_action, "open"),
        on_clipboard=lambda: GLib.idle_add(do_action, "clipboard"),
        on_quit=lambda: GLib.idle_add(quit_app),
    )
    _ = tray  # keep the indicator referenced for the app's lifetime

    if action:  # launched with an action and no prior instance
        GLib.idle_add(do_action, action)

    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
