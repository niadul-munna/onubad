#!/usr/bin/env bash
# Installer for the COSMIC English↔Bangla tray translator.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
AUTOSTART="$HOME/.config/autostart"
WRAPPER="$BIN/onubad"

echo "==> Checking AppIndicator typelib (needed for the COSMIC panel icon)…"
if ! python3 -c 'import gi; gi.require_version("AyatanaAppIndicator3","0.1")' 2>/dev/null \
   && ! python3 -c 'import gi; gi.require_version("AppIndicator3","0.1")' 2>/dev/null; then
  echo "    Installing gir1.2-ayatanaappindicator3-0.1 (needs sudo)…"
  sudo apt-get update
  sudo apt-get install -y gir1.2-ayatanaappindicator3-0.1
fi

echo "==> Verifying Python dependencies (all from system packages)…"
python3 - <<'PY'
import importlib.util, sys
missing = [m for m in ("gi", "requests", "PIL") if importlib.util.find_spec(m) is None]
if missing:
    print("    Missing python modules:", missing)
    print("    Install with: sudo apt install python3-gi python3-requests python3-pil")
    sys.exit(1)
print("    python deps OK")
PY

echo "==> Installing launcher wrapper -> $WRAPPER"
mkdir -p "$BIN" "$APPS" "$AUTOSTART"
cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
export PYTHONPATH="$HERE\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m onubad.main "\$@"
EOF
chmod +x "$WRAPPER"

echo "==> Installing app launcher + autostart entry"
cat > "$APPS/onubad.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Onubad — EN↔BN
Comment=English↔Bangla translator (tray)
Exec=$WRAPPER
Icon=accessories-dictionary
Terminal=false
Categories=Utility;
EOF
cp "$APPS/onubad.desktop" "$AUTOSTART/onubad.desktop"

cat <<EOF

==> Done.

Start now:        $WRAPPER &
(or log out/in — it autostarts and the icon appears in the COSMIC panel.)

Global hotkey (one-time):
  COSMIC Settings → Keyboard → Shortcuts → Custom → Add
    Command:  $WRAPPER --clipboard      (translate current selection/clipboard)
    Command:  $WRAPPER --open           (just open the window)
  Bind e.g. Super+T. Then: select English text, copy, press the key.

Tip: add ~/.local/bin to PATH to run 'onubad' from any terminal.
EOF
