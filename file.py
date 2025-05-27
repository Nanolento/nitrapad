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
                return False, "E1: This is most likely not a text file, since Unicode decoding failed!\n" + \
                    "Nitra only supports UTF-8 encoded text files only (at least for now)."
            return buff, f"Loaded in file {self.path}"
        else:
            return [""], "W1: specified file does not exist, will be created when saved"

    def save(self, lines):
        """
        Write the given text lines to this file.
        """
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                for line in lines:
                    print(line, file=f)
            return True, f"Wrote to {self.path}"
        except OSError as e:
            if e.errno == 13:
                return False, f"E2: Permission denied for writing to {self.path}"
            else:
                return False, f"E3: Error while writing to file: {e}"
