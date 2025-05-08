import curses
from time import sleep
import sys
import os

TAB_WIDTH = 4

class State:
    def __init__(self):
        self.cur_x = 0
        self.cur_y = 0
        self.scroll_x = 0 # Horizontal scrolling unimplemented for now.
        self.scroll_y = 0
        self.win_height = curses.LINES-1
        self.win_width = curses.COLS


def load_file(file_path):
    if os.path.isfile(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                buff = f.readlines()
        except UnicodeDecodeError:
            print("This is most likely not a text file, since Unicode decoding failed!\n"
                  "Nitra works with UTF-8 encoded text files only (for now).")
            return None
        return buff
    else:
        print("That file does not exist!")
        return None


def draw_screen(stdscr, buffer_scr, state):
    stdscr.clear()
    cur_y = 0
    cur_x = 0
    assert len(buffer_scr) <= curses.LINES - 1, "Too many lines were given to draw"
        
    for line in buffer_scr:
        cur_x = 0
        for char in line.rstrip():
            if ord(char) == 9:
                cur_x += TAB_WIDTH
                continue
            stdscr.addch(state.scroll_y+cur_y, cur_x, char)
            cur_x += 1
        cur_y += 1


def handle_input(statusw, stdscr, state):
    key_ch = stdscr.get_wch()
    match key_ch:
        case 258:
            key_str = "arrow_down"
            if state.cur_y < state.win_height - 1:
                state.cur_y += 1
            stdscr.move(state.cur_y, state.cur_x)
        case 259:
            key_str = "arrow_up"
            if state.cur_y > 0:
                state.cur_y -= 1
            stdscr.move(state.cur_y, state.cur_x)
        case 260:
            key_str = "arrow_left"
            if state.cur_x > 0:
                state.cur_x -= 1
            stdscr.move(state.cur_y, state.cur_x)
        case 261:
            key_str = "arrow_right"
            if state.cur_x < state.win_width - 1:
                state.cur_x += 1
            stdscr.move(state.cur_y, state.cur_x)
        case _:
            key_str = f"UNK {repr(key_ch)}"
    statusw.clear()
    status_str = f"X: {state.cur_x+state.scroll_x} ({state.cur_x}), " + \
                 f"Y: {state.cur_y+state.scroll_y} ({state.cur_y}), INPUT: {key_str}"
    statusw.addstr(0, 0, status_str)
    statusw.refresh()

    
def main_loop(stdscr, buffer_lines):
    curses.use_default_colors()
    state = State()
    ypos = 0
    statusw = stdscr.subwin(1, curses.COLS, curses.LINES-1, 0)
    if len(buffer_lines) > state.win_height:
        draw_screen(stdscr, buffer_lines[state.scroll_y:state.scroll_y+curses.LINES-1], state)
    else:
        draw_screen(stdscr, buffer_lines, state)
    while True:
        stdscr.refresh()
        handle_input(statusw, stdscr, state)


def main():
    if len(sys.argv) < 2:
        buffer_lines = []
    else:
        buffer_lines = load_file(sys.argv[1])
        if not buffer_lines:
            print("Could not load file!")
            return

    curses.wrapper(main_loop, buffer_lines)
    
    
if __name__ == "__main__":
    main()

