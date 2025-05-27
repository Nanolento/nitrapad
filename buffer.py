
from file import File

class Buffer:
    def __init__(self, screen, file=None):
        self.lines = [""]

        # Buffer cursor (logical, rather than visual)
        self.cur_x = 0
        self.cur_y = 0

        # File handling
        if file:
            self.file = file
            lines, result_msg = file.load()
            screen.draw_status_message(result_msg)
            if lines:
                self.lines = lines
        else:
            self.file = None

    def __len__(self):
        return len(self.lines)

    def _cursor_wrap_text(self, wanted_x, wanted_y):
        """
        This function moves the logical cursor so that it is always in valid text.
        """
        # Vertical cursor movement
        # Basically make it not go below where text ends in small files, or
        # when scrolling too far.
        if wanted_y >= len(self.lines):
            wanted_y = min(wanted_y, len(self.lines) - 1)
        # Get current line for horizontal movement check.
        current_line = self.lines[wanted_y]
        # Horizontal cursor movement
        if len(current_line) == 0:
            wanted_x = 0
        elif len(current_line) > 0 and wanted_x > len(current_line) - 1:
            wanted_x = len(current_line)  # Move to end of line
        return wanted_x, wanted_y

    def move_cursor(self, x, y, relative=True):
        """
        Move the logical cursor of the buffer around.
        """
        if relative:
            x = self.cur_x + x
            y = self.cur_y + y
        
        # Bounds checks
        x = max(0, x)
        y = max(0, y)
        y = min(len(self.lines), y)
        
        wanted_x, wanted_y = self._cursor_wrap_text(x, y)

        self.cur_x = wanted_x
        self.cur_y = wanted_y

    def insert_char(self, x, y, char):
        """
        Inserts the given character into the buffer at the given position.
        Will also update the screen if needed.
        """
        self.lines[y] = self.lines[y][:x] + char + self.lines[y][x:]

    def delete_char(self, x, y):
        """
        Delete the char at the given position.
        """
        self.lines[y] = self.lines[y][:x] + self.lines[y][x+1:]

    def add_newline(self, x, y):
        """
        Add a newline at the given position.
        1. Deletes to the end of the line from the position given.
        2. Puts that content on a new line below the current given one.
        """
        content_after = self.lines[y][x:]
        self.lines[y] = self.lines[y][:x]
        self.lines.insert(y+1, content_after)

    def save(self):
        """
        Order this buffer to save its contents to its file, or ask the user
        to pick a file to save to (unimplemented) if there is no file.
        """
        if self.file:
            result, result_msg = self.file.save(self.lines)
            return result, result_msg
        else:
            return False, "WD: No file attached (temporary)!"
