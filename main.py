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
        self.win_height = 40
        self.win_width = 80
        self.buffer_lines = []
        self.screen_dirty = True # will make it redraw on next cycle.


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


def draw_screen(stdscr, state):
    if len(state.buffer_lines) > state.win_height:
        buffer_scr = state.buffer_lines[state.scroll_y:state.scroll_y+state.win_height-1]
    else:
        buffer_scr = state.buffer_lines
    stdscr.clear()
    cur_y = 0
    cur_x = 0
    assert len(buffer_scr) <= state.win_height - 1, "Too many lines were given to draw"
        
    for line in buffer_scr:
        cur_x = 0
        for char in line.rstrip():
            if ord(char) == 9:
                cur_x += TAB_WIDTH
                continue
            if cur_x < state.win_width:
                stdscr.addch(cur_y, cur_x, char)
                cur_x += 1
            else:
                break
        cur_y += 1


def handle_input(statusw, stdscr, state):
    key_ch = stdscr.get_wch()
    match key_ch:
        case 258:
            key_str = "arrow_down"
            if state.cur_y < state.win_height - 2:
                state.cur_y += 1
            elif state.scroll_y < len(state.buffer_lines) - state.win_height:
                state.scroll_y += 1
                state.screen_dirty = True
            stdscr.move(state.cur_y, state.cur_x)
        case 259:
            key_str = "arrow_up"
            if state.cur_y > 0:
                state.cur_y -= 1
            elif state.scroll_y > 0:
                state.scroll_y -= 1
                state.screen_dirty = True
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

    
def main_loop(stdscr, state):
    curses.use_default_colors()
    ypos = 0
    statusw = stdscr.subwin(1, state.win_width, state.win_height-1, 0)
    while True:
        if state.screen_dirty:
            state.screen_dirty = False
            draw_screen(stdscr, state)
            stdscr.refresh()
        handle_input(statusw, stdscr, state)


def main():
    state = State()
    if len(sys.argv) == 2:
        state.buffer_lines = load_file(sys.argv[1])
        if not state.buffer_lines:
            print("Could not load file!")
            return

    curses.wrapper(main_loop, state)
    
    
if __name__ == "__main__":
    main()

