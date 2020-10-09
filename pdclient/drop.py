from enum import Enum
from typing import List, Sequence

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pdclient import PdClient

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

def move(pos, direction):
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

    def move(self, dir: Dir):
        """Move the drop one electrode in the given direction

        If the move is successful, `self.pos` is updated to reflect the new
        position.

        Args:
            dir: One of [Dir.UP, Dir.DOWN, dir.LEFT, dir.RIGHT]

        Returns:
            The `move_drop` response object
        """
        response = self.client.move_drop(self.pos, self.size, dir2str(dir))
        if(response['success']):
            self.pos = move(self.pos, dir)
        return response

    def move_up(self):
        """Move the drop one electrode up (i.e. y = y - 1)
        """
        return self.move(Dir.UP)

    def move_down(self):
        """Move the drop one electrode down (i.e. y = y + 1)
        """
        return self.move(Dir.DOWN)

    def move_left(self):
        """Move the drop one electrode left (i.e. x = x - 1)
        """
        return self.move(Dir.LEFT)

    def move_right(self):
        """Move the drop one electrode right (i.e. x = x + 1)
        """
        return self.move(Dir.RIGHT)

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