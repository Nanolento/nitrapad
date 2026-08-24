# This file contains the commands neot uses for its functionality. The default behaviors are programmed here.


class Command:
    name: str

    def __init__(self, name, function):
        self.name = name
        self.function = function

    def execute(self, editor):
        self.function(editor)


class CommandRegistry:
    commands: dict

    def __init__(self):
        self.commands = {}

    def register(self, command: Command):
        if command.name in self.commands:
            raise Exception(f"Cannot register command {command.name}: Already registered!")
        else:
            self.commands[command.name] = command

    def resolve(self, name):
        """
        Get a command from the command registry by name.
        Returns the command object if found, else returns False.
        """
        if name in self.commands:
            return self.commands[name]
        else:
            return False

    def execute(self, name, editor):
        """
        Execute a command from the registry by name.
        By design, commands can NOT have arguments as they are
        intended to be used by the user to manipulate the editor and
        are not intended to be used by program code.
        Provide the editor context to be used with the command.
        """
        cmd = self.resolve(name)
        if cmd:
            cmd.execute(editor)
        else:
            raise Exception(f"Cannot execute command {name}: Does not exist!")


# Movement commands
def move_left(editor):
    editor.screen.move_cursor(-1, 0)

def move_right(editor):
    editor.screen.move_cursor(1, 0)

def move_up(editor):
    editor.screen.move_cursor(0, -1)

def move_down(editor):
    editor.screen.move_cursor(0, 1)

move_left_cmd = Command("move-left", move_left)
move_right_cmd = Command("move-right", move_right)
move_up_cmd = Command("move-up", move_up)
move_down_cmd = Command("move-down", move_down)
