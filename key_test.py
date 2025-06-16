import curses
import sys
import os
import time

from screen import Screen
from file import File

TAB_WIDTH = 4

class State:
    def __init__(self):
        self.file_path = "*NEW*"
        self.filename = "*NEW*"  # only basename, displayed in status line etc.
        self.mode = "normal"  # mode for interpreting input
        self.ending = False  # whether to quit the application yet.
        self.test_y = 0

keybinds = {
    "Alt-s": "save-file",
    "Alt-q": "quit",
    "Ctrl-d": "delete-line"
}


    
def handle_input(stdscr, state, screen):
    cur_x_diff = 0
    cur_y_diff = 0

    key_ch = stdscr.get_wch()
    if isinstance(key_ch, str): # most typing and keybinds
        ord_ch = ord(key_ch)
        if ord_ch == 27:
            key_str = "Esc"
            curses.halfdelay(5)
            just_esc = False
            try:
                key_ch2 = stdscr.get_wch() # get second key but only wait a bit.
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
        elif ord_ch <= 26:
            key_str = f"Ctrl-{chr(ord_ch+64)}"
        elif 65 <= ord_ch <= 126:
            key_str = key_ch
        else:
            key_str = f"UNK STR {repr(key_ch)}"
    elif isinstance(key_ch, int): # special chars
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
            case _:
                key_str = f"UNK SPC {key_ch}"
    #command = resolve_keybind(key_str)
    
    screen.buff.add_newline(screen.buff.cur_x, screen.buff.cur_y)
    cur_y_diff += 1 # TODO: Make this scroll nicer. Probs scroll function? Or cursor move function
    cur_x_diff = -screen.cur_x - screen.scroll_x
    for c in key_str:
        screen.buff.insert_char(screen.buff.cur_x + cur_x_diff, screen.buff.cur_y, c)
        cur_x_diff += 1
    screen.dirty_lines.update(range(screen.cur_y, screen.height))
    if len(screen.dirty_lines) > 0:
        screen.draw_screen()
    if cur_x_diff != 0 or cur_y_diff != 0:
        # Move logical cursor and visual cursor together
        screen.move_cursor(cur_x_diff, cur_y_diff, relative=True)
    return key_str == "q"
    

def main_loop(stdscr, file_path, state):    
    curses.use_default_colors()
    curses.raw()
    stdscr.clear()
    editor_width = curses.COLS
    editor_height = curses.LINES
    if file_path:
        file = File(file_path)
        screen = Screen(0, 0, editor_width, editor_height, stdscr, file=file)
    else:
        screen = Screen(0, 0, editor_width, editor_height, stdscr)
    screen.draw_screen(redraw=True)
    # This is there so the initial "Loaded in file" message can appear
    if not screen.message_shown:
        screen.draw_status()
    else:
        screen.message_shown = False
    screen.put_terminal_cursor()
    while True:
        curses.raw()
        if state.ending:
            return
        try:
            key_pressed = handle_input(stdscr, state, screen)
            if key_pressed:
                return
        except Exception:
            curses.noraw()
        if screen.message_shown:
            screen.message_shown = False
        else:
            screen.draw_status()
        screen.put_terminal_cursor()


def main():
    state = State()
    file_path = None
    if len(sys.argv) == 2:
        if sys.argv[1] == "!debug_key!":
            print("Enabled key_debug mode")
            state.filename = "!DEBUG_KEY!"
        else:
            file_path = sys.argv[1]
            state.filename = os.path.basename(file_path)

    curses.wrapper(main_loop, file_path, state)


if __name__ == "__main__":
    main()
