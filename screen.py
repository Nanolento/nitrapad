import curses

class Screen:
    def __init__(self, x, y, width, height, screen, buff=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen
        self.scroll_x = 0  # Scroll positions
        self.scroll_y = 0
        cur_x = 0
        cur_y = 0
        self.dirty_lines = set() # Lines that need redrawing on next draw_screen
        if buff:
            self.buff = buff # Temp: buff = buffer_lines
            # in future, will be Buffer obj supporting operations

    def draw_screen(self):
        for ln in dirty_lines:
            line = self.buff[self.scroll_y + ln]
            _draw_line(line, self.scroll_y + self.cur_y, self.cur_y)


    def _draw_line(line, text_y, screen_y):
        cur_x = 0
        self.screen.move(screen_y, 0)
        self.screen.clrtoeol()
        for char in line.rstrip():
            if ord(char) == 9:
                cur_x += 1
                continue
            if cur_x < self.width and screen_y < self.height:
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
