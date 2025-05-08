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


def handle_input(statusw, stdscr):
    key_ch = stdscr.getch()
    match key_ch:
        case 258:
            key_str = "arrow_down"
        case 259:
            key_str = "arrow_up"
        case 260:
            key_str = "arrow_left"
        case 261:
            key_str = "arrow_right"
        case _:
            key_str = f"UNK {str(key_ch)}"
    statusw.clear()
    statusw.addstr(0, 0, key_str)
    statusw.refresh()

    
def main_loop(stdscr, buffer_lines):
    curses.use_default_colors()
    state = State()
    ypos = 0
    statusw = stdscr.subwin(1, curses.COLS, curses.LINES-1, 0)
    draw_screen(stdscr, buffer_lines[ypos:ypos+curses.LINES-1], state)
    while True:
        
        stdscr.refresh()
        handle_input(statusw, stdscr)

        


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

