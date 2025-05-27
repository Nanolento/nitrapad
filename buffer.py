
from file import File

class Buffer:
    def __init__(self, screen, file=None):
        self.lines = [""]
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
