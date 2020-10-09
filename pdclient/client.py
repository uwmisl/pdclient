import json
import requests
import time
from typing import List, Optional, Sequence, Tuple

import pdclient.reservoir as reservoir

class RpcClient(object):
    """General RPC call client

    Any method called on this object will be converted to an RPC call to the
    endpoint provided.
    """

    def __init__(self, url):
        self._url = url
        self._id = 0

    def callrpc(self, method, *args):
        payload = {
            "method": method,
            "params": args,
            "jsonrpc": "2.0",
            "id": self._id,
        }
        self._id += 1

        response = requests.post(self._url, json=payload).json()

        if 'result' in response:
            return response['result']
        else:
            raise RuntimeError("Unexpected response: %s" % response)

    def __getattr__(self, name):
        def f(*args):
            return self.callrpc(name, *args)
        return f

class PdClient(object):
    """A PdClient object provides the interface for accessing PurpleDrop via RPC calls
    """
    def __init__(self, host: str):
        """Create a new PdClient object

        Args:
            host: The RPC host URI, for example 'http://purpledrophost:7000/rpc'
        """
        self._board = None
        self.client = RpcClient(host)

    def layout(self) -> dict:
        """Get the layout object from the electrode board definition
        """
        if self._board is None:
            self._board = self.client.get_board_definition()

        return self._board['layout']

    def grid(self) -> List[List[int]]:
        """Get the grid object from the electrode board definition
        """
        layout = self.layout()

        # Backwards compatibility for old board definition format
        if 'pins' in layout:
            grid_key = 'pins'
        else:
            grid_key = 'grid'
        return layout[grid_key]

    def get_pin(self, location: Sequence[int]) -> int:
        """Get the electrode pin number from a grid location using the layout

        location: (x, y) coordinate of the electrode to lookup
        """
        p = location
        try:
            grid = self.grid()
            pin = grid[p[1]][p[0]]
        except IndexError:
            raise ValueError(
                "Invalid position (%d, %d), it is outside of the layout range"
                 % (p[0], p[1]))

        if pin is None:
            raise ValueError(
                "In valid position (%d, %d), no electrode is present at this location"
                 % (p[0], p[1]))

        return pin

    def get_grid_location(self, pin: int) -> Optional[Tuple]:
        """Get the grid location for a pin number

        Returns None if the pin is not found in the grid definition
        """
        for y, row in enumerate(self.grid()):
            for x, electrode in enumerate(row):
                if electrode == pin:
                    return (x, y)
        return None

    def get_reservoir(self, id: int) -> reservoir.ReservoirDriver:
        layout = self.layout()
        if 'peripherals' not in layout:
            raise ValueError("Board definition has no reservoirs")

        for definition in layout['peripherals']:
            if definition.get('class') == 'reservoir' and definition.get('id') == id:
                return reservoir.create_driver(definition, self)
        raise ValueError(f"No reservor found for id={id}")

    def move_drop(self, start: Sequence[int], size: Sequence[int], dir: str) -> dict:
        """Executes a device controlled drop movement sequence

        Args:
            start : The x,y location of the drop initial position (e.g. `[2, 3]`)
            size : The width and height of the drop (e.g. [2, 2])
            dir : One of ['up', 'down', 'left', 'right']

        Returns:
            A dict containing the results of the drop movement, including
            a success flag and a time series of capacitance data captured
            during the move.

            TODO: Include example response object
        """
        return self.client.move_drop(start, size, dir)

    def enable_positions(self, positions):
        """Enable the specified set of electrodes by grid location

        positions: List of 2-tuples of (x, y) electrode grid coordinates, e.g.
        [(0, 0), (0, 1), (1, 0), (1, 1)]
        """
        pins = [self.get_pin(p) for p in positions]
        self.enable_pins(pins)

    def enable_pins(self, electrode_numbers):
        """Enable the specified set of electrodes by pin number

        electrode_numbers: List of integers, giving pin numbers to enable
        """
        self.client.set_electrode_pins(electrode_numbers)

    def active_capacitance(self) -> float:
        """Get the most recent capacitance for active electrodes
        """
        return self.client.get_active_capacitance()

    def bulk_capacitance(self) -> List[float]:
        """Get the most recent scan of electrode capacitance
        """
        return self.client.get_bulk_capacitance()

    def temperatures(self) -> List[float]:
        """Get the most recent temperature measurements

        Returns a list of temperatures (floats) in degC

        The length of the return value depends on device configuraiton, and
        may be zero.
        """
        return self.client.get_temperatures()

    def set_pwm_duty_cycle(self, chan: int, duty_cycle: float):
        """Set duty cycle on a PWM output channel

        chan is an integer specifying which PWM channel to change
        duty_cycle is float in range 0.0 to 1.0.
        """
        return self.client.set_pwm_duty_cycle(chan, duty_cycle)