"""GTK3 popup window: input, output, direction swap, auto-detect, history."""

import threading

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk, Pango  # noqa: E402

from . import translator, clipboard  # noqa: E402
from .history import History  # noqa: E402


class Popup:
    def __init__(self, history=None):
        self.history = history or History()
        self.src, self.dst = "en", "bn"
        self.auto = False
        self._build()
        self._refresh_history()

    # ---- UI construction -------------------------------------------------
    def _build(self):
        self.win = Gtk.Window(title="Translate EN↔BN")
        self.win.set_default_size(480, 460)
        self.win.set_keep_above(True)
        self.win.set_border_width(8)
        self.win.connect("delete-event", self._on_close)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.win.add(root)

        # direction row
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.dir_label = Gtk.Label()
        self.dir_label.set_xalign(0)
        bar.pack_start(self.dir_label, True, True, 0)
        swap = Gtk.Button(label="⇄ Swap")
        swap.connect("clicked", self._swap)
        bar.pack_start(swap, False, False, 0)
        auto = Gtk.ToggleButton(label="Auto")
        auto.set_tooltip_text("Detect source language from input")
        auto.connect("toggled", self._on_auto)
        bar.pack_start(auto, False, False, 0)
        root.pack_start(bar, False, False, 0)

        # input
        self.input = Gtk.TextView()
        self.input.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.input.connect("key-press-event", self._on_input_key)
        root.pack_start(self._scrolled(self.input, 100), True, True, 0)

        # action buttons
        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, cb in (
            ("Translate", lambda *_: self.translate()),
            ("From clipboard", self._from_clipboard),
            ("Copy result", self._copy_result),
        ):
            b = Gtk.Button(label=label)
            b.connect("clicked", cb)
            btns.pack_start(b, True, True, 0)
        root.pack_start(btns, False, False, 0)

        # output
        self.output = Gtk.TextView()
        self.output.set_editable(False)
        self.output.set_cursor_visible(False)
        self.output.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        root.pack_start(self._scrolled(self.output, 100), True, True, 0)

        # history
        exp = Gtk.Expander(label="History")
        hbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.hist_list = Gtk.ListBox()
        self.hist_list.connect("row-activated", self._on_hist_activated)
        hbox.pack_start(self._scrolled(self.hist_list, 120), True, True, 0)
        clear = Gtk.Button(label="Clear history")
        clear.connect("clicked", self._clear_history)
        hbox.pack_start(clear, False, False, 0)
        exp.add(hbox)
        root.pack_start(exp, False, False, 0)

        self._update_dir_label()

    @staticmethod
    def _scrolled(child, min_height):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        sw.set_min_content_height(min_height)
        sw.add(child)
        return sw

    # ---- text helpers ----------------------------------------------------
    def _get_input(self):
        buf = self.input.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

    def _set_input(self, text):
        self.input.get_buffer().set_text(text or "")

    def _set_output(self, text):
        self.output.get_buffer().set_text(text or "")

    def _get_output(self):
        buf = self.output.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

    def _update_dir_label(self):
        mode = " (auto)" if self.auto else ""
        self.dir_label.set_markup(
            f"<b>{self.src.upper()} → {self.dst.upper()}</b>{mode}")

    # ---- actions ---------------------------------------------------------
    def translate(self):
        text = self._get_input()
        if not text.strip():
            return
        if self.auto:
            self.src = translator.detect_lang(text)
            self.dst = "en" if self.src == "bn" else "bn"
            self._update_dir_label()
        self._set_output("…")
        src, dst = self.src, self.dst

        def work():
            try:
                out = translator.translate(text, src, dst)
            except translator.TranslationError as exc:
                GLib.idle_add(self._set_output,
                              f"⚠ Translation failed: {exc}\nCheck internet.")
                return
            GLib.idle_add(self._on_result, src, dst, text, out)

        threading.Thread(target=work, daemon=True).start()

    def _on_result(self, src, dst, text, out):
        self._set_output(out)
        clipboard.copy(out)
        self.history.add(src, dst, text, out)
        self._refresh_history()

    def _swap(self, *_):
        self.src, self.dst = self.dst, self.src
        self._update_dir_label()

    def _on_auto(self, btn):
        self.auto = btn.get_active()
        self._update_dir_label()

    def _from_clipboard(self, *_):
        text = clipboard.paste()
        if text:
            self._set_input(text)
            self.translate()

    def _copy_result(self, *_):
        clipboard.copy(self._get_output())

    def _on_input_key(self, _widget, event):
        ctrl = event.state & Gdk.ModifierType.CONTROL_MASK
        if ctrl and event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.translate()
            return True
        return False

    # ---- history ---------------------------------------------------------
    def _refresh_history(self):
        for child in self.hist_list.get_children():
            self.hist_list.remove(child)
        for item in self.history.recent(30):
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(xalign=0)
            lbl.set_text(f"{item['input'][:34]} → {item['output'][:34]}")
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            row.add(lbl)
            row._item = item
            self.hist_list.add(row)
        self.hist_list.show_all()

    def _on_hist_activated(self, _listbox, row):
        item = row._item
        self.src, self.dst = item["src"], item["dst"]
        self._update_dir_label()
        self._set_input(item["input"])
        self._set_output(item["output"])

    def _clear_history(self, *_):
        self.history.clear()
        self._refresh_history()

    # ---- window lifecycle ------------------------------------------------
    def _on_close(self, *_):
        self.win.hide()
        return True  # keep instance alive; hide instead of destroy

    def show(self):
        self.win.show_all()
        self.win.present()

    def show_and_translate_clipboard(self):
        text = clipboard.paste()
        if text:
            self._set_input(text)
        self.show()
        if text and text.strip():
            self.translate()
