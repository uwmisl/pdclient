from enum import Enum
from typing import Sequence, Tuple, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pdclient import PdClient

from pdclient.api_types import MoveCommand
from pdclient.exceptions import InvalidMoveException

class Dir(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

def dir2str(dir):
    if dir == Dir.UP:
        return "Up"
    elif dir == Dir.DOWN:
        return "Down"
    elif dir == Dir.LEFT:
        return "Left"
    elif dir == Dir.RIGHT:
        return "Right"

def str2dir(s):
    sl = s.lower()
    if sl == "up":
        return Dir.UP
    elif sl == "down":
        return Dir.DOWN
    elif sl == "left":
        return Dir.LEFT
    elif sl == "right":
        return Dir.RIGHT

    raise ValueError(f"Invalid direction string {s}")

def validate_dir(d):
    if isinstance(d, Dir):
        return d
    elif isinstance(d, str):
        return str2dir(d)

    raise ValueError("Direction must be a string ('left', 'right', 'up', 'down') or a Dir object")

def move(pos, direction: Union[str, Dir]):
    direction = validate_dir(direction)
    newpos = None
    if direction == Dir.UP:
        newpos = (pos[0], pos[1] - 1)
    elif direction == Dir.DOWN:
        newpos = (pos[0], pos[1] + 1)
    elif direction == Dir.LEFT:
        newpos = (pos[0] - 1, pos[1])
    elif direction == Dir.RIGHT:
        newpos = (pos[0] + 1, pos[1])

    return newpos

class Drop(object):
    """Represents a drop on the electrode board"""

    def __init__(self, pos: Sequence[int], size: Sequence[int], client: 'PdClient'):
        self.pos = pos
        self.size = size
        self.client = client

    def get_move_command(self, dir: Union[str, Dir], **kwargs) -> MoveCommand:
        """Returns a MoveCommand which can be passed to the move_drops method

        Raises InvalidMoveException if the current or new drop position are not
        valid on the current electrode board. For example, if the move causes
        the drop to move off the electrode grid.

        **kwargs are passed on to the MoveCommand, and can be used to set other
        move options, e.g. `timeout`, or `threshold`.
        """
        new_drop = Drop(move(self.pos, dir), self.size, self.client)
        cmd = None
        try:
            cmd = MoveCommand(self.pins(), new_drop.pins(), **kwargs)
        except ValueError:
            raise InvalidMoveException(f"Cannot move drop of size {self.size} to {new_drop.pos}")
        return cmd

    def move(self, dir: Union[str, Dir], **kwargs):
        """Move the drop one electrode in the given direction

        If the move is successful, `self.pos` is updated to reflect the new
        position.

        Args:
            dir: One of [Dir.UP, Dir.DOWN, dir.LEFT, dir.RIGHT], or (case-insensitive)
                 strings ["up", "down", "left", "right"]

        Returns:
            The `move_drop` response object from the API
        """
        cmd = self.get_move_command(dir, **kwargs)
        response = self.client.move_drops([cmd])[0]
        if(response['success']):
            self.pos = move(self.pos, dir)
        return response

    def move_up(self, **kwargs):
        """Move the drop one electrode up (i.e. y = y - 1)
        """
        return self.move(Dir.UP, **kwargs)

    def move_down(self, **kwargs):
        """Move the drop one electrode down (i.e. y = y + 1)
        """
        return self.move(Dir.DOWN, **kwargs)

    def move_left(self, **kwargs):
        """Move the drop one electrode left (i.e. x = x - 1)
        """
        return self.move(Dir.LEFT, **kwargs)

    def move_right(self, **kwargs):
        """Move the drop one electrode right (i.e. x = x + 1)
        """
        return self.move(Dir.RIGHT, **kwargs)

    def pins(self):
        """Return all pins which are part of the drop
        """
        pins = []
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                loc = (self.pos[0] + x, self.pos[1] + y)
                pins.append(self.client.get_pin(loc))
        return pins

    def activate(self):
        """Activate the electrodes for this drop
        """
        self.client.enable_pins(self.pins())

    def __str__(self):
        return f"Drop(pos={self.pos}, size={self.size})"

def move_multiple_drops(*moves: Tuple[Drop, Union[str, Dir]], **kwargs):
    """Execute concurrent device controlled moves for a set of drops

    Local state is updated for drops that are reported as successfully moved.

    Example:

        drop1 = Drop((1, 1), (2, 2), client)
        drop2 = Drop((5, 1), (2, 2), client)
        move_multiple_drops((drop1, "Right"), (drop2, "Right"))

    """
    if len(moves) == 0:
        return []
    # Get the client from the first move's drop
    client = moves[0][0].client
    commands = [drop.get_move_command(dir, **kwargs) for drop, dir in moves]
    results = client.move_drops(commands)
    for i in range(len(moves)):
        if results[i]['success']:
            drop = moves[i][0]
            dir = moves[i][1]
            drop.pos = move(drop.pos, dir)

    return results
