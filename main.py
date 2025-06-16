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


def resolve_keybind(key_str):
    """
    This function will take the key_str passed in, and return the corresponding command name.
    For now, these commands will be hardcoded locked to the keybind, but in the future
    this will be configurable, maybe.
    """
    match key_str:
        case ["C-x", "s"]:
            return "save-file"
        case ["C-x", "q"]:
            return "quit"
        case _:
            # Nothing bound.
            return False

    

def handle_input(stdscr, state, screen):
    cur_x_diff = 0
    cur_y_diff = 0
    key_sequence = []

    while True:
        # Resolve key sequences. They are started with any C- keybind (ctrl).
        command = resolve_keybind(key_sequence)
        if command:
            break
        # if not yet reached a dest: ask for input!
        key_ch = stdscr.get_wch()
        if isinstance(key_ch, str):
            if ord(key_ch) <= 31:
                if key_ch == "\x18":
                    key_sequence.append("C-x")
                elif key_ch == "\x04":
                    key_sequence.append("C-d")
                elif key_ch == "\x07":
                    break # stop the key sequence.
                # Other ctrl+X situations can be added later.
            elif key_ch == "\n":
                command = "insert-newline"
                break
            elif len(key_sequence) == 0:
                # handle regular typing
                command = "insert-char"
                break
            else:
                key_sequence.append(key_ch)
        else:
            if key_ch in [curses.KEY_DOWN, curses.KEY_UP, curses.KEY_LEFT, curses.KEY_RIGHT]:
                command = "move-cursor"
                break

    # TEMP: command handling here, later will add command handling library.
    match command:
        case "quit":
            state.ending = True
        case "insert-char":
            screen.buff.insert_char(screen.buff.cur_x, screen.buff.cur_y, key_ch)
            screen.dirty_lines.add(screen.cur_y)
            cur_x_diff += 1
        case "move-cursor":
            match key_ch:
                case curses.KEY_DOWN:
                    cur_y_diff += 1
                case curses.KEY_UP:
                    cur_y_diff -= 1
                case curses.KEY_LEFT:
                    cur_x_diff -= 1
                case curses.KEY_RIGHT:
                    cur_x_diff += 1
        case _:
            # Invalid command, just do nothing
            screen.draw_status_message(f"'{" ".join(key_sequence)}' is unbound!", tone="message")
    
        # if not state.filename == "!DEBUG_KEY!":
    #         match state.mode:
    #             case "normal":
    #                 match key_ch:
    #                     case c if isinstance(c, str):
    #                         # Character typed.
    #                         if c == chr(24):
    #                             key_str = "ctrl+x"
    #                             state.mode = "command"
    #                         elif c == chr(10):
    #                             key_str = "enter"
    #                             # Enter. Add a newline.
    #                             screen.buff.add_newline(screen.buff.cur_x, screen.buff.cur_y)
    #                             cur_y_diff += 1 # TODO: Make this scroll nicer. Probs scroll function? Or cursor move function
    #                             cur_x_diff = -screen.cur_x - screen.scroll_x
    #                             screen.dirty_lines.update(range(screen.cur_y, screen.height))
    #                         elif c == chr(9):
    #                             key_str = "TAB"
    #                             # tab key
    #                             # TODO: make this toggleable.
    #                             # Currently just forced expandtab
    #                             width_needed = TAB_WIDTH - ((screen.buff.cur_x) % TAB_WIDTH)
    #                             for i in range(width_needed):
    #                                 screen.buff.insert_char(screen.buff.cur_x, screen.buff.cur_y, " ")
    #                             screen.dirty_lines.add(screen.cur_y)
    #                             cur_x_diff += width_needed
    #                         else:
    #                             key_str = c  # a letter was input.
    #                             screen.buff.insert_char(screen.buff.cur_x, screen.buff.cur_y, c)
    #                             screen.dirty_lines.add(screen.cur_y)
    #                             cur_x_diff += 1
    #                     case 258:
    #                         key_str = "arrow_down"
    #                         cur_y_diff += 1 # all that other code is now the responsibility of screen.move_cursor
    #                     case 259:
    #                         key_str = "arrow_up"
    #                         # The below code was kept for reference.
    #                         # if state.cur_y > 0:
    #                         #     state.cur_y -= 1
    #                         #     cursor_wrap_text(state)
    #                         # elif state.scroll_y > 0:
    #                         #     state.scroll_y -= 1
    #                         #     state.screen_dirty = True
    #                         # stdscr.move(state.cur_y, state.cur_x)
    #                         cur_y_diff -= 1
    #                     case 260:
    #                         key_str = "arrow_left"
    #                         cur_x_diff -= 1
    #                         # if state.cur_x > 0:
    #                         #     state.cur_x -= 1
    #                         #     state.preferred_cur_x = state.cur_x
    #                         #     cursor_wrap_text(state)
    #                         # stdscr.move(state.cur_y, state.cur_x)
    #                     case 261:
    #                         key_str = "arrow_right"
    #                         cur_x_diff += 1
    #                     case 263:
    #                         key_str = "backspace"
    #                         if screen.buff.cur_x > 0:
    #                             cur_x_diff -= 1
    #                             screen.buff.delete_char(screen.buff.cur_x-1, screen.buff.cur_y)
    #                             screen.dirty_lines.add(screen.cur_y)
    #                     case 330:
    #                         key_str = "del"
    #                         y_pos = screen.buff.cur_y
    #                         if len(screen.buff.lines[y_pos]) > 0:
    #                             screen.buff.delete_char(screen.buff.cur_x, y_pos)
    #                             screen.dirty_lines.add(screen.cur_y)
    #                     case _:
    #                         key_str = f"UNK {repr(key_ch)}"
    #             case "command":
    #                 match key_ch:
    #                     case 'q':
    #                         key_str = "q"
    #                         # exit application.
    #                         state.ending = True
    #                     case 's':
    #                         key_str = "s"
    #                         # save file
    #                         result, result_msg = screen.buff.save()
    #                         if result:
    #                             screen.draw_status_message(result_msg, tone="message")
    #                         else:
    #                             screen.draw_status_message(result_msg, tone="auto")
    #                         state.mode = "normal"
    #                     case _:
    #                         state.mode = "normal"
    #                         key_str = f"UNK {repr(key_ch)}"
    #     else:
    #         # KEY DEBUG MODE
    #         key_str = repr(key_ch)
    #         screen.buff.lines[0] = key_str
    #         screen.draw_screen(redraw=True)
    # except curses.error:
    #     key_str = "none"

    if len(screen.dirty_lines) > 0:
        screen.draw_screen()
    if cur_x_diff != 0 or cur_y_diff != 0:
        # Move logical cursor and visual cursor together
        screen.move_cursor(cur_x_diff, cur_y_diff, relative=True)


def main_loop(stdscr, file_path, state):
    curses.use_default_colors()
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
        if state.ending:
            return
        key_pressed = handle_input(stdscr, state, screen)
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
