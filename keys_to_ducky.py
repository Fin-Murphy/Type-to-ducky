#!/usr/bin/env python3
"""Record your keystrokes and translate them into a Ducky Script.

Recording begins the moment the script runs and stops when you type '~'.
The resulting Ducky Script is printed and saved to a file.

Requires:  pip install pynput
macOS:     grant Accessibility permission to your terminal app
           (System Settings -> Privacy & Security -> Accessibility),
           otherwise no keystrokes are captured.

Usage:     python3 keys_to_ducky.py [output_file]   # default: payload.txt
"""

import sys

try:
    from pynput import keyboard
except ImportError:
    sys.exit("pynput is required.  Install it with:  pip install pynput")

# Non-printable keys -> Ducky Script keywords
SPECIAL = {
    keyboard.Key.enter: "ENTER",
    keyboard.Key.tab: "TAB",
    keyboard.Key.esc: "ESCAPE",
    keyboard.Key.backspace: "BACKSPACE",
    keyboard.Key.delete: "DELETE",
    keyboard.Key.up: "UP",
    keyboard.Key.down: "DOWN",
    keyboard.Key.left: "LEFT",
    keyboard.Key.right: "RIGHT",
    keyboard.Key.home: "HOME",
    keyboard.Key.end: "END",
    keyboard.Key.page_up: "PAGEUP",
    keyboard.Key.page_down: "PAGEDOWN",
    keyboard.Key.insert: "INSERT",
    keyboard.Key.caps_lock: "CAPSLOCK",
    keyboard.Key.menu: "MENU",
    keyboard.Key.print_screen: "PRINTSCREEN",
    keyboard.Key.pause: "BREAK",
    keyboard.Key.f1: "F1", keyboard.Key.f2: "F2", keyboard.Key.f3: "F3",
    keyboard.Key.f4: "F4", keyboard.Key.f5: "F5", keyboard.Key.f6: "F6",
    keyboard.Key.f7: "F7", keyboard.Key.f8: "F8", keyboard.Key.f9: "F9",
    keyboard.Key.f10: "F10", keyboard.Key.f11: "F11", keyboard.Key.f12: "F12",
}

# Modifier keys -> Ducky Script modifier names
MODIFIERS = {
    keyboard.Key.ctrl: "CTRL", keyboard.Key.ctrl_l: "CTRL", keyboard.Key.ctrl_r: "CTRL",
    keyboard.Key.alt: "ALT", keyboard.Key.alt_l: "ALT", keyboard.Key.alt_r: "ALT",
    keyboard.Key.alt_gr: "ALT",
    keyboard.Key.shift: "SHIFT", keyboard.Key.shift_l: "SHIFT", keyboard.Key.shift_r: "SHIFT",
    keyboard.Key.cmd: "GUI", keyboard.Key.cmd_l: "GUI", keyboard.Key.cmd_r: "GUI",
}

# Emit combined modifiers in a stable, conventional order
MOD_ORDER = ["CTRL", "ALT", "SHIFT", "GUI"]

STOP_CHAR = "~"

lines = []      # finished Ducky Script lines
buffer = []     # pending printable characters (become a STRING line)
held = set()    # modifier names currently pressed


def flush():
    """Turn any buffered printable characters into a STRING line."""
    if buffer:
        lines.append("STRING " + "".join(buffer))
        buffer.clear()


def active_mods():
    return [m for m in MOD_ORDER if m in held]


def on_press(key):
    # Track modifier presses; they only matter combined with another key.
    if key in MODIFIERS:
        held.add(MODIFIERS[key])
        return

    char = getattr(key, "char", None)

    # Stop the moment the '~' character is typed (any layout).
    if char == STOP_CHAR:
        flush()
        return False

    mods = active_mods()
    # A combo means a real (non-shift) modifier is down, or shift is
    # held together with a non-printable key such as SHIFT+TAB.
    combo = any(m in held for m in ("CTRL", "ALT", "GUI"))

    if char is not None:
        # Under CTRL, pynput reports a control character (e.g. \x03 for c);
        # map it back to the plain letter for a readable combo.
        if "CTRL" in held and len(char) == 1 and ord(char) < 0x20:
            char = chr(ord(char) + 96)
        if combo:
            flush()
            lines.append(" ".join(mods + [char]))
        else:
            # Plain typing (shift is already reflected in the character).
            buffer.append(char)
    elif key in SPECIAL:
        flush()
        keyword = SPECIAL[key]
        if mods:  # include SHIFT here so SHIFT+TAB etc. are captured
            lines.append(" ".join(mods + [keyword]))
        else:
            lines.append(keyword)
    else:
        flush()
        lines.append("REM unmapped key: {!r}".format(key))


def on_release(key):
    if key in MODIFIERS:
        held.discard(MODIFIERS[key])


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "payload.txt"

    print("Recording keystrokes -- type '~' to stop.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    script = "\n".join(lines) + ("\n" if lines else "")
    with open(out_path, "w") as fh:
        fh.write(script)

    print("\n--- Ducky Script ---")
    print(script if lines else "(nothing recorded)")
    print("Saved to: {}".format(out_path))


if __name__ == "__main__":
    main()
