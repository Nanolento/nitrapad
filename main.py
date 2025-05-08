import curses
import sys
import os

TAB_WIDTH = 4

class State:
    def __init__(self):
        self.cur_x = 0
        self.cur_y = 0
        self.preferred_cur_x = 0 # Remember x value for convenient cursor movement
        self.scroll_x = 0 # Horizontal scrolling unimplemented for now.
        self.scroll_y = 0
        self.win_height = 40
        self.win_width = 80
        self.editor_height = 39
        self.editor_width = 80
        self.buffer_lines = []
        self.screen_dirty = True # will make it redraw on next cycle.
        self.file_path = "*NEW*"
        self.filename = "*NEW*" # only basename, displayed in status line etc.
        self.mode = "normal" # mode for interpreting input
        self.ending = False # whether to quit the application yet.


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
    except:
        debug_str = "Could not make debug info. Something's wrong!"
    return debug_str
    

def draw_screen(screen, state):
    if len(state.buffer_lines) > state.editor_height:
        buffer_scr = state.buffer_lines[state.scroll_y:state.scroll_y+state.editor_height]
    else:
        buffer_scr = state.buffer_lines
    screen.clear()
    cur_y = 0
    cur_x = 0
    assert len(buffer_scr) <= state.editor_height, "Too many lines were given to draw"
        
    for line in buffer_scr:
        cur_x = 0
        for char in line.rstrip():
            if ord(char) == 9:
                cur_x += 1
                continue
            if cur_x < state.editor_width and cur_y < state.editor_height:
                try:
                    screen.addch(cur_y, cur_x, char)
                except curses.error as e:
                    if cur_x != state.editor_width - 1 or cur_y != state.editor_height - 1:
                        # raise an exception only if the cur pos is irregular
                        # ncurses raises exception if drawing to bottom right corner for some reason.
                        raise Exception(f"could not draw char {repr(char)}: {e}\nDEBUG INFO:\n{_debug_info(state)}")
                cur_x += 1
            else:
                break
        cur_y += 1
    screen.refresh()


def cursor_wrap_text(state):
    """
    This function moves the cursor so that it is always in valid text. (horizontally)
    """
    # Vertical cursor movement
    # Basically make it not go below where text ends in small files, or
    # when scrolling too far.
    if state.scroll_y + state.cur_y >= len(state.buffer_lines):
        state.cur_y = max(0, len(state.buffer_lines) - 1)
    # Get current line for horizontal movement check.
    if len(state.buffer_lines) > 0:
        current_line = state.buffer_lines[state.scroll_y+state.cur_y]
    else:
        return # nothing to do if no text.
    # Horizontal cursor movement
    if state.cur_x > len(current_line) - 1 or \
       state.preferred_cur_x > len(current_line) - 1:
        state.cur_x = len(current_line) - 1 # Move to end of line
    else:
        state.cur_x = state.preferred_cur_x


def draw_line(state, text_y, screen_y, screen):
    cur_x = 0
    line = state.buffer_lines[text_y]
    for char in line.rstrip():
        if ord(char) == 9:
            cur_x += 1
            continue
        if cur_x < state.editor_width and screen_y < state.editor_height:
            try:
                screen.addch(screen_y, cur_x, char)
            except curses.error as e:
                if cur_x != state.editor_width - 1 or screen_y != state.editor_height - 1:
                    # raise an exception only if the cur pos is irregular
                    # ncurses raises exception if drawing to bottom right corner for some reason.
                    raise Exception(f"could not draw char {repr(char)}: {e}\nDEBUG INFO:\n{_debug_info(state)}")
            cur_x += 1
        else:
            break


def insert_char(state, x, y, char, textw):
    """
    Inserts the given character into the buffer at the given position.
    Will also update the screen if needed.
    """
    state.buffer_lines[y] = state.buffer_lines[y][:x] + char + state.buffer_lines[y][x:]
    draw_line(state, y, y-state.scroll_y, textw)
    textw.refresh()


def handle_input(statusw, stdscr, state, textw):
    try:
        key_ch = stdscr.get_wch()
        match state.mode:
            case "normal":
                match key_ch:
                    case 258:
                        key_str = "arrow_down"
                        if state.cur_y < state.editor_height - 1:
                            state.cur_y += 1
                            cursor_wrap_text(state)
                        elif state.scroll_y < len(state.buffer_lines) - state.editor_height:
                            state.scroll_y += 1
                            state.screen_dirty = True
                        stdscr.move(state.cur_y, state.cur_x)
                    case 259:
                        key_str = "arrow_up"
                        if state.cur_y > 0:
                            state.cur_y -= 1
                            cursor_wrap_text(state)
                        elif state.scroll_y > 0:
                            state.scroll_y -= 1
                            state.screen_dirty = True
                        stdscr.move(state.cur_y, state.cur_x)
                    case 260:
                        key_str = "arrow_left"
                        if state.cur_x > 0:
                            state.cur_x -= 1
                            state.preferred_cur_x = state.cur_x
                            cursor_wrap_text(state)
                        stdscr.move(state.cur_y, state.cur_x)
                    case 261:
                        key_str = "arrow_right"
                        if state.cur_x < state.editor_width - 1:
                            state.cur_x += 1
                            state.preferred_cur_x = state.cur_x
                            cursor_wrap_text(state)
                        stdscr.move(state.cur_y, state.cur_x)
                    case c if c == chr(24):
                        key_str = "ctrl+x"
                        state.mode = "command"
                    case c if (c >= chr(65) and c <= chr(90)) or \
                         (c >= chr(97) and c <= chr(122)):
                        key_str = c  # a letter was input.
                        insert_char(state, state.cur_x, state.scroll_y+state.cur_y, c, textw)
                        state.cur_x += 1
                        state.preferred_cur_x = state.cur_x
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
    except (KeyboardInterrupt, curses.error):
        key_str = "ctrl+c"
    
    statusw.clear()
    if key_str != "ctrl+c":
        status_str = f"{state.filename if state.mode == 'normal' else state.mode.upper()}, " + \
            f"X: {state.cur_x+state.scroll_x} ({state.cur_x}/{state.preferred_cur_x}), " + \
            f"Y: {state.cur_y+state.scroll_y+1} ({state.cur_y}), INPUT: {key_str}"
    else:
        status_str = "To quit Nitra, press Ctrl+x, then q"
    statusw.addstr(0, 0, status_str)
    statusw.refresh()
    # move cursor back to avoid confusing user
    stdscr.move(state.cur_y, state.cur_x)

    
def main_loop(stdscr, state):
    curses.use_default_colors()
    stdscr.clear()
    state.win_width = curses.COLS
    state.win_height = curses.LINES
    state.editor_width = state.win_width
    state.editor_height = state.win_height - 1
    statusw = stdscr.subwin(1, state.win_width, state.win_height - 1, 0)
    textw = stdscr.subwin(state.editor_height, state.editor_width, 0, 0)
    while True:
        if state.ending:
            return
        if state.screen_dirty:
            state.screen_dirty = False
            draw_screen(textw, state)
        handle_input(statusw, stdscr, state, textw)


def main():
    state = State()
    if len(sys.argv) == 2:
        state.buffer_lines = load_file(sys.argv[1])
        state.file_path = sys.argv[1]
        state.filename = os.path.basename(state.file_path)
        if not state.buffer_lines:
            print("Could not load file!")
            return

    curses.wrapper(main_loop, state)
    
    
if __name__ == "__main__":
    main()

