import curses

class Screen:
    def __init__(self, x, y, width, height, screen, buff=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.curses_screen = screen
        self.scroll_x = 0  # Scroll positions
        self.scroll_y = 0
        self.cur_x = 0
        self.cur_x_preferred = 0
        self.cur_y = 0
        self.dirty_lines = set() # Lines that need redrawing on next draw_screen
        if buff:
            self.buff = buff # Temp: buff = buffer_lines
            # in future, will be Buffer obj supporting operations

    def _cursor_wrap_text(self, wanted_x, wanted_y):
        """
        This function moves the cursor so that it is always in valid text. (horizontally)
        """
        # Vertical cursor movement
        # Basically make it not go below where text ends in small files, or
        # when scrolling too far.
        if self.scroll_y + wanted_y >= len(self.buff):
            wanted_y = min(wanted_y, len(self.buff) - 1 - self.scroll_y)
        # Get current line for horizontal movement check.
        if len(self.buff) > 0:
            current_line = self.buff[self.scroll_y+wanted_y]
        else:
            return 0, wanted_y # no text, and wrap to beginning
        # Horizontal cursor movement
        if len(current_line) > 0 and (wanted_x > len(current_line) - 1 or \
           self.cur_x_preferred > len(current_line) - 1):
            wanted_x = len(current_line) - 1  # Move to end of line
        elif len(current_line) == 0:
            wanted_x = 0
        else:
            wanted_x = self.cur_x_preferred
        return wanted_x, wanted_y


    def put_cursor(self):
        """
        Put the terminal cursor at the virtual screen cursor position.
        Used for user comfort so they can see where they are typing.
        """
        self.curses_screen.move(self.cur_y, self.cur_x)
        self.curses_screen.refresh()


    def move_cursor(self, x, y, relative=False):
        """
        Move the cursor around.
        With relative=True, compute new coords and move them there.
        Note: this function will automatically wrap the cursor to the text,
        and prevent the cursor from moving outside the screen etc. and scroll
        the screen where appropriate.
        Returns False if move failed and True if successful.
        """
        if relative:
            wanted_x = self.cur_x + x
            wanted_y = self.cur_y + y
        else:
            wanted_x = x
            wanted_y = y

        # Bounds check
        # > 0
        wanted_x = max(0, wanted_x)
        wanted_y = max(0, wanted_y)
        # < height and so is handled by cursor_wrap_text

        if relative and x != 0:
            self.cur_x_preferred = wanted_x
        
        wanted_x, wanted_y = self._cursor_wrap_text(wanted_x, wanted_y)

        # Update preferred cursor X if only horizontal
        if relative and y == 0:
            self.cur_x_preferred = self.cur_x

        self.cur_x = wanted_x
        self.cur_y = wanted_y
        

    def draw_screen(self, redraw=False):
        if redraw:
            lines_to_draw = range(self.height)
        else:
            lines_to_draw = self.dirty_lines
        
        for ln in lines_to_draw:
            if ln <= len(self.buff) - 1:
                line = self.buff[self.scroll_y + ln]
                self._draw_line(line, self.scroll_y + ln, ln)
        self.dirty_lines = set()
        self.curses_screen.refresh()


    def _draw_line(self, line, text_y, screen_y):
        cur_x = 0
        self.curses_screen.move(screen_y, 0)
        self.curses_screen.clrtoeol()
        for char in line.rstrip():
            if ord(char) == 9:
                cur_x += 1
                continue
            if cur_x < self.width and screen_y < self.height:
                try:
                    self.curses_screen.addch(screen_y, cur_x, char)
                except curses.error as e:
                    if cur_x != state.editor_width - 1 or screen_y != state.editor_height - 1:
                        # raise an exception only if the cur pos is irregular
                        # ncurses raises exception if drawing to bottom right corner for some reason.
                        raise Exception(f"could not draw char {repr(char)}: {e}\nDEBUG INFO:\n{_debug_info(state)}")
                cur_x += 1
            else:
                break
