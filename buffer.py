
from file import File

class Buffer:
    def __init__(self, file=None):
        self.lines = [""]
        if file:
            self.file = file
            lines = file.load()
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
