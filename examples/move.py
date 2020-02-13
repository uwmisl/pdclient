import pdclient
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
    
RPCURL = "http://10.144.112.21/rpc"
class Drop(object):
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
        self.history = []

    def move(self, dir):
        c = pdclient.client.RpcClient(RPCURL)
        response = c.callrpc('move_drop', self.pos, self.size, dir2str(dir))
        self.pos = move(self.pos, dir)
        self.history.append(response)
        return response


    

