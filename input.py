import curses

keybinds = {
    "Alt-x": "prompt",
    "Alt-s": "save-file",
    "Alt-f": "open-file",
    "Alt-q": "quit",
    "Enter": "insert-newline",
    "char-type": "insert-char",
    "Backspace": "delete-backward",
    "Ctrl-d": "delete-line",
    "Delete": "delete-forward",
    "Tab": "insert-tab",
    "ArrowUp": "move-up",
    "ArrowDown": "move-down",
    "ArrowLeft": "move-left",
    "ArrowRight": "move-right",
}


def resolve_keybind(key_str):
    if key_str in keybinds:
        return keybinds[key_str]
    else:
        return False


def get_keybind(key_ch, stdscr):
    if isinstance(key_ch, str):  # most typing and keybinds
        ord_ch = ord(key_ch)
        if ord_ch == 27:
            key_str = "Esc"
            # Enable halfdelay mode, for detecting if Esc or Alt+X key combo.
            curses.halfdelay(1)
            # no worries about setting this. The main loop will reset
            # raw mode automatically.
            just_esc = False
            try:
                # get second key but only wait a bit, thanks to halfdelay.
                key_ch2 = stdscr.get_wch()
            except curses.error:
                # we got no input, just Esc.
                just_esc = True

            if not just_esc:
                ord_ch2 = ord(key_ch2)
                if 65 <= ord_ch2 <= 126:
                    key_str = f"Alt-{key_ch2}"
                elif 48 <= ord_ch2 <= 57:
                    key_str = f"Alt-{str(ord_ch2-48)}"
        elif (key_ch == "\n" or
              ord_ch == 10 or
              ord_ch == 13):
            key_str = "Enter"
        elif ord_ch == 0:
            key_str = "Ctrl-Space"
        elif ord_ch == 9:
            key_str = "Tab"
        elif 1 <= ord_ch <= 26:
            key_str = f"Ctrl-{chr(ord_ch+96)}"
        elif key_ch.isprintable():
            key_str = "char-type"
        else:
            key_str = f"UNK STR {repr(key_ch)}"
    elif isinstance(key_ch, int):  # special chars
        match key_ch:
            case curses.KEY_DOWN:
                key_str = "ArrowDown"
            case curses.KEY_UP:
                key_str = "ArrowUp"
            case curses.KEY_LEFT:
                key_str = "ArrowLeft"
            case curses.KEY_RIGHT:
                key_str = "ArrowRight"
            case curses.KEY_BACKSPACE:
                key_str = "Backspace"
            case curses.KEY_DC:
                key_str = "Delete"
            case _:
                key_str = f"UNK INT {key_ch}"
    return key_str
