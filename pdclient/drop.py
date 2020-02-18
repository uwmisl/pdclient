from enum import Enum

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
    def __init__(self, pos, size, client):
        self.pos = pos
        self.size = size
        self.client = client
        self.history = []

    def move(self, dir):
        response = self.client.move_drop(self.pos, self.size, dir2str(dir))
        self.pos = move(self.pos, dir)
        return response

    def move_up(self):
        return self.move(Dir.UP)

    def move_down(self):
        return self.move(Dir.DOWN)

    def move_left(self):
        return self.move(Dir.LEFT)

    def move_right(self):
        return self.move(Dir.RIGHT)