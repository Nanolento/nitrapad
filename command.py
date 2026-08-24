# This file contains the commands neot uses for its functionality. The default behaviors are programmed here.

TAB_WIDTH = 4

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

# Insert commands
def insert_tab(editor):
    width_needed = TAB_WIDTH - ((editor.screen.buff.cur_x) % TAB_WIDTH)
    for i in range(width_needed):
        editor.screen.buff.insert_char(editor.screen.buff.cur_x, editor.screen.buff.cur_y,
                                       " ")
        editor.screen.dirty_lines.add(editor.screen.cur_y)
    editor.screen.move_cursor(width_needed, 0)

def insert_newline(editor):
    editor.screen.buff.add_newline(editor.screen.buff.cur_x,
                                   editor.screen.buff.cur_y)
    cur_x_diff = -editor.screen.cur_x - editor.screen.scroll_x
    editor.screen.dirty_lines.update(range(editor.screen.cur_y,
                                           editor.screen.edit_height))
    editor.screen.move_cursor(cur_x_diff, 1)

insert_tab_cmd = Command("insert-tab", insert_tab)
insert_newline_cmd = Command("insert-newline", insert_newline)

# Deletion commands

def delete_line(editor):
    cur_y_diff = 0
    cur_x_diff = 0
    if len(editor.screen.buff) > 1:
        del editor.screen.buff.lines[editor.screen.buff.cur_y]
        editor.screen.dirty_lines.update(range(editor.screen.cur_y, editor.screen.edit_height))
        if editor.screen.buff.cur_y >= len(editor.screen.buff) - 1 and editor.screen.buff.cur_y > 0:
            cur_y_diff = 1
    else:
        cur_x_diff = -editor.screen.buff.cur_x
        editor.screen.buff.lines[0] = ""
        editor.screen.dirty_lines.add(0)
    editor.screen.move_cursor(cur_x_diff, cur_y_diff)

delete_line_cmd = Command("delete-line", delete_line)
