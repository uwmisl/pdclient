from typing import Iterator, List, Optional, Sequence, Union

class MoveCommand(object):
    def __init__(self,
                 start_pins: Sequence[int],
                 end_pins: Sequence[int],
                 timeout: Optional[Union[float, int]]=None,
                 post_capture_time: Optional[Union[float, int]]=None,
                 low_gain: Optional[bool]=None,
                 threshold: Optional[float]=None,
                 ):
        """Represents a move argument passed to the `move_drops` method
        """
        self.start_pins = start_pins
        self.end_pins = end_pins
        self.timeout = timeout
        self.post_capture_time = post_capture_time
        self.low_gain = low_gain
        self.threshold = threshold

    def to_dict(self):
        d = {
            'start_pins': self.start_pins,
            'end_pins': self.end_pins,
        }
        if self.timeout is not None:
            d['timeout'] = self.timeout
        if self.post_capture_time is not None:
            d['post_capture_time'] = self.post_capture_time
        if self.low_gain is not None:
            d['low_gain'] = self.low_gain
        if self.threshold is not None:
            d['threshold'] = self.threshold
        return d

class Grid(object):
    """Represents a grid in the board layout for PdClient
    """
    def __init__(self, pins, pitch=1.0, origin=(0.0, 0.0)):
        if len(origin) != 2:
            raise ValueError("Origin must be a 2-tuple containing (x, y)")
        self.pins = pins
        self.pitch = pitch
        self.origin = tuple(origin)

    def __getitem__(self, key) -> List[int]:
        """Override indexer so a row of the grid can be accessed directly,
        treating the Grid object as an array
        """
        return self.pins[key]

    def __len__(self) -> int:
        return len(self.pins)

    def __iter__(self) -> Iterator[List[int]]:
        for row in self.pins:
            yield row
