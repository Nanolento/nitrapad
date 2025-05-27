import curses

from buffer import Buffer

class Screen:
    def __init__(self, x, y, width, height, screen, file=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.edit_height = height - 1 # Compensate for status line
        self.curses_screen = screen
        self.scroll_x = 0  # Scroll positions
        self.scroll_y = 0
        self.cur_x = 0
        self.cur_x_preferred = 0
        self.cur_y = 0
        self.dirty_lines = set() # Lines that need redrawing on next draw_screen
        self.message_shown = False # if there is currently a status message.
        
        # Color setup
        # Error status
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
        # Warning status
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        
        if file:
            self.buff = Buffer(self, file=file)
        else:
            self.buff = Buffer(self) # self = passing ourselves as a screen, so buffer can raise messages

    def draw_status_message(self, message, tone="auto"):
        """
        Temporarily (until user presses a key, overwrite status line
        with a specified message, used to provide feedback to the user on actions that don't affect
        the buffer directly or not directly visible.
        """
        if tone == "auto":
            if message.startswith("E"):
                tone = "error"
            elif message.startswith("W") or message.startswith("WD"):
                tone = "warning"
            else:
                tone = "message"
        elif tone not in ["message", "error", "warning"]:
            raise Exception(f"Invalid status message tone: {tone}")
        if tone == "message":
            self._draw_line(message, self.height - 1, color="invert", screen_space=True)
        else:
            self._draw_line(message, self.height - 1, color=tone, screen_space=True)
        self.message_shown = True
            
    def draw_status(self):
        if self.buff.file:
            filename = self.buff.file.filename
        else:
            filename = "!new"
        status_str = f"{filename} | " + \
            f"L{self.cur_y+self.scroll_y+1} ({self.cur_y}) | " + \
            f"C{self.cur_x+self.scroll_x} ({self.cur_x}/{self.cur_x_preferred})"
        self._draw_line(status_str, self.height - 1, color="invert", screen_space=True)
        version_str = "Nitra INDEV"
        self.curses_screen.addstr(self.height - 1, self.width - len(version_str) - 1, version_str, curses.A_REVERSE)

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
        current_line = self.buff.lines[self.scroll_y+wanted_y]
        # Horizontal cursor movement
        if len(current_line) == 0 and self.scroll_x == 0:
            wanted_x = 0
        elif len(current_line) == 0 and self.scroll_x > 0:
            wanted_x = -self.scroll_x
        elif len(current_line) > 0 and (wanted_x + self.scroll_x > len(current_line) - 1 or \
           self.cur_x_preferred > len(current_line) - 1):
            wanted_x = len(current_line) - self.scroll_x  # Move to end of line
        else:
            wanted_x = self.cur_x_preferred - self.scroll_x
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

        if relative and x != 0:
            self.cur_x_preferred = wanted_x + self.scroll_x

        # Vertical scrolling
        if wanted_y > self.edit_height - 1 and wanted_y + self.scroll_y < len(self.buff):
            wanted_y = self.edit_height - 1
            self.scroll_y += 1
            self.draw_screen(redraw=True)
        elif wanted_y < 0 and self.scroll_y > 0:
            wanted_y = 0
            self.scroll_y -= 1
            self.draw_screen(redraw=True)
        elif wanted_y < 0 and self.scroll_y == 0:
            wanted_y = 0

        wanted_x, wanted_y = self._cursor_wrap_text(wanted_x, wanted_y)

        # Horizontal scrolling
        if wanted_x > self.width - 1:
            self.scroll_x += wanted_x - (self.width - 1)
            wanted_x = self.width - 1
            self.draw_screen(redraw=True)
        elif wanted_x < 0 and self.scroll_x > 0:
            self.scroll_x += wanted_x
            wanted_x = 0
            self.draw_screen(redraw=True)
        elif wanted_x < 0 and self.scroll_x == 0:
            wanted_x = 0
            
        self.cur_x = wanted_x
        self.cur_y = wanted_y
        

    def draw_screen(self, redraw=False):
        if redraw:
            lines_to_draw = range(self.edit_height)
        else:
            lines_to_draw = self.dirty_lines
        
        for ln in lines_to_draw:
            if ln <= len(self.buff) - 1:
                line = self.buff.lines[self.scroll_y + ln]
                if len(line) > self.scroll_x: # is the line on-screen at all?
                    self._draw_line(line, ln)
                else:
                    self.curses_screen.move(ln, 0)
                    self.curses_screen.clrtoeol() # Clear line
        self.dirty_lines = set()
        self.curses_screen.refresh()


    def _draw_line(self, line, screen_y, color="normal", screen_space=False):
        """
        Draw a text line on the screen.
        screen_space: if True, ignore screen scrolling when rendering, else adhere to it.
        """
        cur_x = 0
        self.curses_screen.move(screen_y, 0)
        self.curses_screen.clrtoeol()
        if not screen_space:
            chars_to_draw = line.rstrip()[self.scroll_x:]
        else:
            chars_to_draw = line.rstrip()
        for char in chars_to_draw:
            if ord(char) == 9:
                cur_x += 1
                continue
            if cur_x > self.width:
                break # No need to render characters outside of screen
            if cur_x < self.width and screen_y < self.height:
                try:
                    if color == "invert":
                        self.curses_screen.addch(screen_y, cur_x, char, curses.A_REVERSE)
                    elif color == "error":
                        self.curses_screen.addch(screen_y, cur_x, char, curses.color_pair(1))
                    elif color == "warning":
                        self.curses_screen.addch(screen_y, cur_x, char, curses.color_pair(2))
                    else:
                        self.curses_screen.addch(screen_y, cur_x, char)
                except curses.error as e:
                    if cur_x != state.editor_width - 1 or screen_y != state.editor_height - 1:
                        # raise an exception only if the cur pos is irregular
                        # ncurses raises exception if drawing to bottom right corner for some reason.
                        raise Exception(f"could not draw char {repr(char)}: {e}\nDEBUG INFO:\n{_debug_info(state)}")
                cur_x += 1
            else:
                break
