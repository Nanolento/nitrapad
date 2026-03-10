import curses
import sys
import os
import time

from screen import Screen
from file import File
from input import get_keybind, resolve_keybind

TAB_WIDTH = 4


class State:
    def __init__(self):
        self.file_path = "*NEW*"
        self.filename = "*NEW*"  # only basename, displayed in status line etc.
        self.mode = "normal"  # mode for interpreting input
        self.ending = False  # whether to quit the application yet.


def handle_input(stdscr, state, screen):
    cur_x_diff = 0
    cur_y_diff = 0

    key_ch = stdscr.get_wch()
    key_str = get_keybind(key_ch, stdscr)

    if key_str == "RESIZE":
        screen.handle_resize()
        return
    
    command = resolve_keybind(key_str)
    if not command:
        screen.draw_status_message(f"Unbound key '{key_str}'.")

    match command:
        case "insert-char":
            screen.buff.insert_char(screen.buff.cur_x, screen.buff.cur_y,
                                    key_ch)
            cur_x_diff += 1
            screen.dirty_lines.add(screen.cur_y)
        case "insert-tab":
            width_needed = TAB_WIDTH - ((screen.buff.cur_x) % TAB_WIDTH)
            for i in range(width_needed):
                screen.buff.insert_char(screen.buff.cur_x, screen.buff.cur_y,
                                        " ")
            screen.dirty_lines.add(screen.cur_y)
            cur_x_diff += width_needed
        case "insert-newline":
            screen.buff.add_newline(screen.buff.cur_x, screen.buff.cur_y)
            cur_y_diff += 1
            cur_x_diff = -screen.cur_x - screen.scroll_x
            screen.dirty_lines.update(range(screen.cur_y, screen.edit_height))
        case "delete-line":
            if len(screen.buff) > 1:
                del screen.buff.lines[screen.buff.cur_y]
                screen.dirty_lines.update(range(screen.cur_y, screen.edit_height))
                if screen.buff.cur_y >= len(screen.buff) - 1 and screen.buff.cur_y > 0:
                    cur_y_diff -= 1
            else:
                cur_x_diff = -screen.buff.cur_x
                screen.buff.lines[0] = ""
                screen.dirty_lines.add(0)
        case "delete-forward":
            y_pos = screen.buff.cur_y
            current_line = screen.buff.lines[y_pos]
            if screen.buff.cur_x == len(current_line) and y_pos < len(screen.buff) - 1:
                next_line = screen.buff.lines[y_pos+1]
                del screen.buff.lines[y_pos+1]
                screen.buff.lines[y_pos] += next_line
                screen.dirty_lines.update(range(screen.cur_y, screen.edit_height))
            elif len(screen.buff.lines[y_pos]) > 0:
                screen.buff.delete_char(screen.buff.cur_x, y_pos)
                screen.dirty_lines.add(screen.cur_y)
        case "delete-backward":
            if screen.buff.cur_x > 0:
                cur_x_diff -= 1
                screen.buff.delete_char(screen.buff.cur_x-1, screen.buff.cur_y)
                screen.dirty_lines.add(screen.cur_y)
            elif screen.buff.cur_x == 0 and screen.buff.cur_y > 0:
                # delete newline
                y_pos = screen.buff.cur_y
                current_line = screen.buff.lines[y_pos]
                screen.buff.lines[y_pos-1] += current_line
                del screen.buff.lines[y_pos]
                cur_y_diff -= 1
                cur_x_diff = len(screen.buff.lines[y_pos-1]) - \
                    len(current_line) - screen.buff.cur_x
                if screen.scroll_y + screen.edit_height >= len(screen.buff):
                    screen.dirty_lines.update(range(screen.edit_height))
                screen.dirty_lines.update(range(max(0, screen.cur_y-1),
                                                screen.edit_height))
        case "move-up":
            cur_y_diff -= 1
        case "move-down":
            cur_y_diff += 1
        case "move-left":
            cur_x_diff -= 1
        case "move-right":
            cur_x_diff += 1
        case "save-file":
            # save file
            result, result_msg = screen.buff.save()
            if result:
                screen.draw_status_message(result_msg, tone="message")
            else:
                screen.draw_status_message(result_msg, tone="auto")
        case "open-file":
            # open a new file
            screen.draw_status_message("Opening files not implemented until prompt is done!", tone="warning")
        case "prompt":
            value = screen.prompt("Enter a value:")
            screen.draw_status_message(f"You said this {value}", tone="message")
        case "quit":
            state.ending = True
        case _:
            pass  # do nothing

    if len(screen.dirty_lines) > 0:
        screen.draw_screen()
    if cur_x_diff != 0 or cur_y_diff != 0:
        # Move logical cursor and visual cursor together
        screen.move_cursor(cur_x_diff, cur_y_diff, relative=True)


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
        handle_input(stdscr, state, screen)
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
