import os

class File:
    def __init__(self, filepath):
        self.path = filepath
        self.filename = os.path.basename(self.path)

    def load(self):
        """
        Return buffer lines read from the file belonging to this File class.
        """
        if os.path.isfile(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    buff = [line.rstrip("\r\n") for line in f.readlines()]
            except UnicodeDecodeError:
                print("E1: This is most likely not a text file, since Unicode decoding failed!\n"
                      "Nitra only supports UTF-8 encoded text files only (at least for now).")
                return False
            return buff
        else:
            print("W1: file does not exist, returning empty")
            return [""]

    def save(self, lines):
        """
        Write the given text lines to this file.
        """
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                for line in lines:
                    print(line, file=f)
            return True
        except OSError as e:
            print("E2: Error while writing to file: {e}")
            return False
