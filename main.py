import curses
import sys
import os
import time

from screen import Screen

TAB_WIDTH = 4

class State:
    def __init__(self):
        self.cur_x = 0
        self.cur_y = 0
        self.preferred_cur_x = 0  # Remember x value for convenient cursor movement
        self.scroll_x = 0  # Horizontal scrolling unimplemented for now.
        self.scroll_y = 0
        self.win_height = 40
        self.win_width = 80
        self.editor_height = 39
        self.editor_width = 80
        self.buffer_lines = []
        self.screen_dirty = True  # will make it redraw on next cycle.
        self.file_path = "*NEW*"
        self.filename = "*NEW*"  # only basename, displayed in status line etc.
        self.mode = "normal"  # mode for interpreting input
        self.ending = False  # whether to quit the application yet.


def load_file(file_path):
    if os.path.isfile(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                buff = [line.rstrip("\r\n") for line in f.readlines()]
        except UnicodeDecodeError:
            print("This is most likely not a text file, since Unicode decoding failed!\n"
                  "Nitra works with UTF-8 encoded text files only (for now).")
            return None
        return buff
    else:
        print("That file does not exist!")
        return None


def _debug_info(state):
    try:
        debug_str = f"""
        Current line: {state.buffer_lines[state.scroll_y+state.cur_y].rstrip()}
        Current line length: {len(state.buffer_lines[state.scroll_y+state.cur_y])}
        Cursor X/Y: {state.cur_x}/{state.cur_y}
        Scroll X/Y: {state.scroll_x}/{state.scroll_y}
        Absolute X/Y: {state.scroll_x + state.cur_x}/{state.scroll_y + state.cur_y}
        File line count: {len(state.buffer_lines)}
        """
    except Exception:
        debug_str = "Could not make debug info. Something's wrong!"
    return debug_str


def handle_input(stdscr, state, screen):
    cur_x_diff = 0
    cur_y_diff = 0
    try:
        key_ch = stdscr.get_wch()
        if not state.filename == "!DEBUG_KEY!":
            match state.mode:
                case "normal":
                    match key_ch:
                        case c if isinstance(c, str):
                            # Character typed.
                            if c == chr(24):
                                key_str = "ctrl+x"
                                state.mode = "command"
                            elif c == chr(10):
                                key_str = "enter"
                                # Enter. Add a newline.
                                screen.buff.add_newline(screen.scroll_x+screen.cur_x, screen.scroll_y+screen.cur_y)
                                cur_y_diff += 1 # TODO: Make this scroll nicer. Probs scroll function? Or cursor move function
                                cur_x_diff = -screen.cur_x - screen.scroll_x
                                screen.dirty_lines.update(range(screen.cur_y, screen.height))
                            elif c == chr(9):
                                key_str = "TAB"
                                # tab key
                                # TODO: make this toggleable.
                                # Currently just forced expandtab
                                width_needed = TAB_WIDTH - ((screen.scroll_x + screen.cur_x) % TAB_WIDTH)
                                for i in range(width_needed):
                                    screen.buff.insert_char(screen.scroll_x+screen.cur_x, screen.scroll_y+screen.cur_y, " ")
                                screen.dirty_lines.add(screen.cur_y)
                                cur_x_diff += width_needed
                            else:
                                key_str = c  # a letter was input.
                                screen.buff.insert_char(screen.scroll_x+screen.cur_x, screen.scroll_y+screen.cur_y, c)
                                screen.dirty_lines.add(screen.cur_y)
                                cur_x_diff += 1
                        case 258:
                            key_str = "arrow_down"
                            cur_y_diff += 1 # all that other code is now the responsibility of screen.move_cursor
                        case 259:
                            key_str = "arrow_up"
                            # The below code was kept for reference.
                            # if state.cur_y > 0:
                            #     state.cur_y -= 1
                            #     cursor_wrap_text(state)
                            # elif state.scroll_y > 0:
                            #     state.scroll_y -= 1
                            #     state.screen_dirty = True
                            # stdscr.move(state.cur_y, state.cur_x)
                            cur_y_diff -= 1
                        case 260:
                            key_str = "arrow_left"
                            cur_x_diff -= 1
                            # if state.cur_x > 0:
                            #     state.cur_x -= 1
                            #     state.preferred_cur_x = state.cur_x
                            #     cursor_wrap_text(state)
                            # stdscr.move(state.cur_y, state.cur_x)
                        case 261:
                            key_str = "arrow_right"
                            cur_x_diff += 1
                        case 263:
                            key_str = "backspace"
                            if screen.cur_x > 0:
                                cur_x_diff -= 1
                                screen.buff.delete_char(screen.scroll_x+screen.cur_x-1, screen.scroll_y+screen.cur_y)
                                screen.dirty_lines.add(screen.cur_y)
                        case 330:
                            key_str = "del"
                            y_pos = screen.scroll_y + screen.cur_y
                            if len(screen.buff.lines[y_pos]) > 0:
                                delete_char(screen, screen.scroll_x+screen.cur_x, y_pos)
                                screen.dirty_lines.add(screen.cur_y)
                        case _:
                            key_str = f"UNK {repr(key_ch)}"
                case "command":
                    match key_ch:
                        case 'q':
                            key_str = "q"
                            # exit application.
                            state.ending = True
                        case _:
                            state.mode = "normal"
                            key_str = f"UNK {repr(key_ch)}"
        else:
            # KEY DEBUG MODE
            key_str = repr(key_ch)
            for c in key_str:
                insert_char(screen, screen.scroll_x+screen.cur_x, screen.scroll_y+screen.cur_y, c)
                screen.cur_x += 1
            add_newline(screen, screen.scroll_x+screen.cur_x, screen.scroll_y+screen.cur_y)
            screen.cur_x = 0
            screen.cur_y += 1
            if screen.cur_y > screen.edit_height - 1:
                screen.scroll_y += 1
                screen.cur_y = screen.edit_height - 1
                screen.draw_screen(redraw=True)
    except curses.error:
        key_str = "none"

    if len(screen.dirty_lines) > 0:
        screen.draw_screen()
    if cur_x_diff != 0 or cur_y_diff != 0:
        screen.move_cursor(cur_x_diff, cur_y_diff, relative=True)

    return key_str != "none"


def main_loop(stdscr, state):
    curses.use_default_colors()
    stdscr.clear()
    state.win_width = curses.COLS
    state.win_height = curses.LINES
    state.editor_width = state.win_width
    state.editor_height = state.win_height
    screen = Screen(0, 0, state.editor_width, state.editor_height, stdscr)
    screen.draw_screen(redraw=True)
    while True:
        if state.ending:
            return
        key_pressed = handle_input(stdscr, state, screen)
        screen.draw_status()
        screen.put_cursor()


def main():
    state = State()
    if len(sys.argv) == 2:
        if sys.argv[1] == "!debug_key!":
            print("Enabled key_debug mode")
            state.filename = "!DEBUG_KEY!"
        else:
            state.buffer_lines = load_file(sys.argv[1])
            state.file_path = sys.argv[1]
            state.filename = os.path.basename(state.file_path)
            if not state.buffer_lines:
                print("Could not load file!")
                return

    curses.wrapper(main_loop, state)


if __name__ == "__main__":
    main()
