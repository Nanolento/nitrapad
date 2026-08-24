import curses
import sys
import os
import time

from screen import Screen
from file import File
from input import get_keybind, resolve_keybind
import command

TAB_WIDTH = 4


class State:
    def __init__(self):
        self.file_path = "*NEW*"
        self.filename = "*NEW*"  # only basename, displayed in status line etc.
        self.mode = "normal"  # mode for interpreting input
        self.ending = False  # whether to quit the application yet.


# This class contains everything the editor needs to function.
class Editor:
    screen: Screen
    width: int
    height: int
    command_registry: command.CommandRegistry

    def __init__(self, width, height, screen):
        self.screen = screen
        self.width = width
        self.height = height
        self.command_registry = command.CommandRegistry()


def create_prompt(stdscr, x, y, width, message):
    """
    Creates a prompt screen, lets the user do something and then returns the value.
    """
    prompt_screen = Screen(len(message) + 1, curses.LINES-2, curses.COLS, stdscr, stype="prompt")


def handle_input(state, editor: Editor):
    cur_x_diff = 0
    cur_y_diff = 0

    key_ch = editor.screen.curses_screen.get_wch()
    key_str = get_keybind(key_ch, editor.screen.curses_screen)

    if key_str == "RESIZE":
        editor.screen.handle_resize()
        return
    
    command_str = resolve_keybind(key_str)
    if not command_str:
        editor.screen.draw_status_message(f"Unbound key '{key_str}'.")

    # Bit by bit, replace the below match-case with the new command system, check if the
    # command is registered already, otherwise simply use the match-case to figure it out.
    if editor.command_registry.resolve(command_str):
        editor.command_registry.execute(command_str, editor)
    else:
        match command_str:
            case "insert-char":
                editor.screen.buff.insert_char(editor.screen.buff.cur_x, editor.screen.buff.cur_y,
                                               key_ch)
                cur_x_diff += 1
                editor.screen.dirty_lines.add(editor.screen.cur_y)
            case "insert-tab":
                width_needed = TAB_WIDTH - ((editor.screen.buff.cur_x) % TAB_WIDTH)
                for i in range(width_needed):
                    editor.screen.buff.insert_char(editor.screen.buff.cur_x, editor.screen.buff.cur_y,
                                                   " ")
                    editor.screen.dirty_lines.add(editor.screen.cur_y)
                    cur_x_diff += width_needed
            case "insert-newline":
                editor.screen.buff.add_newline(editor.screen.buff.cur_x, editor.screen.buff.cur_y)
                cur_y_diff += 1
                cur_x_diff = -editor.screen.cur_x - editor.screen.scroll_x
                editor.screen.dirty_lines.update(range(editor.screen.cur_y, editor.screen.edit_height))
            case "delete-line":
                if len(editor.screen.buff) > 1:
                    del editor.screen.buff.lines[editor.screen.buff.cur_y]
                    editor.screen.dirty_lines.update(range(editor.screen.cur_y, editor.screen.edit_height))
                    if editor.screen.buff.cur_y >= len(editor.screen.buff) - 1 and editor.screen.buff.cur_y > 0:
                        cur_y_diff -= 1
                    else:
                        cur_x_diff = -editor.screen.buff.cur_x
                        editor.screen.buff.lines[0] = ""
                        editor.screen.dirty_lines.add(0)
            case "delete-forward":
                y_pos = editor.screen.buff.cur_y
                current_line = editor.screen.buff.lines[y_pos]
                if editor.screen.buff.cur_x == len(current_line) and y_pos < len(editor.screen.buff) - 1:
                    next_line = editor.screen.buff.lines[y_pos+1]
                    del editor.screen.buff.lines[y_pos+1]
                    editor.screen.buff.lines[y_pos] += next_line
                    editor.screen.dirty_lines.update(range(editor.screen.cur_y, editor.screen.edit_height))
                elif len(editor.screen.buff.lines[y_pos]) > 0:
                    editor.screen.buff.delete_char(editor.screen.buff.cur_x, y_pos)
                    editor.screen.dirty_lines.add(editor.screen.cur_y)
            case "delete-backward":
                if editor.screen.buff.cur_x > 0:
                    cur_x_diff -= 1
                    editor.screen.buff.delete_char(editor.screen.buff.cur_x-1, editor.screen.buff.cur_y)
                    editor.screen.dirty_lines.add(editor.screen.cur_y)
                elif editor.screen.buff.cur_x == 0 and editor.screen.buff.cur_y > 0:
                    # delete newline
                    y_pos = editor.screen.buff.cur_y
                    current_line = editor.screen.buff.lines[y_pos]
                    editor.screen.buff.lines[y_pos-1] += current_line
                    del editor.screen.buff.lines[y_pos]
                    cur_y_diff -= 1
                    cur_x_diff = len(editor.screen.buff.lines[y_pos-1]) - \
                        len(current_line) - editor.screen.buff.cur_x
                    if editor.screen.scroll_y + editor.screen.edit_height >= len(editor.screen.buff):
                        editor.screen.dirty_lines.update(range(editor.screen.edit_height))
                        editor.screen.dirty_lines.update(range(max(0, editor.screen.cur_y-1),
                                                               editor.screen.edit_height))
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
                result, result_msg = editor.screen.buff.save()
                if result:
                    editor.screen.draw_status_message(result_msg, tone="message")
                else:
                    editor.screen.draw_status_message(result_msg, tone="auto")
            case "open-file":
                # open a new file
                editor.screen.draw_status_message("Opening files not implemented until prompt is done!", tone="warning")
            case "prompt":
                value = editor.screen.prompt("Enter a value:")
                editor.screen.draw_status_message(f"You said this {value}", tone="message")
            case "quit":
                state.ending = True
            case _:
                pass  # do nothing
        if cur_x_diff != 0 or cur_y_diff != 0:
            # Move logical cursor and visual cursor together
            editor.screen.move_cursor(cur_x_diff, cur_y_diff, relative=True)

    if len(editor.screen.dirty_lines) > 0:
        editor.screen.draw_screen()


def register_basic_commands(cmd_reg: command.CommandRegistry):
    """
    Registers the most basic commands into the command registry.
    Includes things like basic movement and typing.
    """
    # Movement commands
    cmd_reg.register(command.move_left_cmd)
    cmd_reg.register(command.move_right_cmd)
    cmd_reg.register(command.move_up_cmd)
    cmd_reg.register(command.move_down_cmd)

        
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
    editor = Editor(editor_width, editor_height, screen)
    # This is there so the initial "Loaded in file" message can appear
    if not screen.message_shown:
        screen.draw_status()
    else:
        screen.message_shown = False
    screen.put_terminal_cursor()

    # Register commands
    register_basic_commands(editor.command_registry)
    
    while True:
        curses.raw()
        if state.ending:
            return
        handle_input(state, editor)
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
