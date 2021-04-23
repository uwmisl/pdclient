from enum import Enum
import json
import requests
import time
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

import pdclient.reservoir as reservoir

class FeedbackMode(Enum):
    """Enumeration of feedback modes for set_feedback_command function
    """
    DISABLED = 0
    NORMAL = 1
    DIFFERENTIAL = 2

class CapacitanceGroupSetting(Enum):
    """Enumeration of the drive group settings
    """
    HIGHGAIN = 0
    LOWGAIN = 1

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

class PdClient(object):
    """A PdClient object provides the interface for accessing PurpleDrop via RPC calls
    """
    def __init__(self, host: str):
        """Create a new PdClient object

        Args:
            host: The RPC host URI, for example 'http://purpledrophost:7000/rpc'
        """
        self._board: Optional[Dict] = None
        self.client = RpcClient(host)

    def layout(self) -> dict:
        """Get the layout object from the electrode board definition
        """
        if self._board is None:
            self._board = self.client.get_board_definition()

        return self._board['layout']

    def grid(self, idx: int=0) -> Grid:
        """Get the one grid object from the electrode board definition

        idx: Index indicating which grid to return for board with multiple grids
        """
        layout = self.layout()

        if 'grid' in layout:
            if idx > 0:
                raise ValueError(f"Grid {idx} not found in board layout")
            return Grid(pins=layout['grid'])
        elif 'grids' in layout:
            if idx > len(layout['grids']):
                raise ValueError(f"Grid {idx} not found in board layout")
            return Grid(
                pins=layout['grids'][idx]['pins'],
                pitch=layout['grids'][idx]['pitch'],
                origin=layout['grids'][idx]['origin'],
            )
        else:
            raise ValueError("No grid found in board layout")

    def grids(self) -> List[Grid]:
        """Get all grids in the electrode board layout
        """
        layout = self.layout()
        if 'grid' in layout:
            return [self.grid(0)]
        elif 'grids' in layout:
            return [self.grid(i) for i in range(len(layout['grids']))]
        else:
            return []

    def get_pin(self, location: Sequence[int], grid: int=0) -> int:
        """Get the electrode pin number from a grid location using the layout

        location: (x, y) coordinate of the electrode to lookup
        grid: Index indicating which grid is to be used for a board with 
          multiple grids 
        """
        p = location
        try:
            g = self.grid(grid)
            pin = g[p[1]][p[0]]
        except IndexError:
            raise ValueError(
                "Invalid position (%d, %d), it is outside of the layout range"
                 % (p[0], p[1]))

        if pin is None:
            raise ValueError(
                "In valid position (%d, %d), no electrode is present at this location"
                 % (p[0], p[1]))

        return pin

    def get_grid_location(self, pin: int) -> Optional[Tuple[Tuple, int]]:
        """Get the grid location for a pin number

        Returns: ((x, y), grid_idx) if the pin is located, or None if the pin
        is not found in the grid definition
        """
        
        for grid_idx, g in enumerate(self.grids()):
            for y, row in enumerate(g):
                for x, electrode in enumerate(row):
                    if electrode == pin:
                        return ((x, y), grid_idx)
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

            The return dict is of the form: 

              {
                  "success": bool,
                  "closed_loop": bool,
                  "closed_loop_result": {
                      "pre_capacitance": float,
                      "post_capacitance": float,
                      "time_series": List[float],
                      "capacitance_series": List[float]
                  }
              }

            closed_loop_result is only present when "closed_loop" is true. It 
            will always be true for devices that support capacitance sensing,
            but is present to allow devices without sensing to implement an 
            open-loop `move_drop` function.
        """
        return self.client.move_drop(start, size, dir)

    def enable_positions(self, positions):
        """Enable the specified set of electrodes by grid location

        positions: List of 2-tuples of (x, y) electrode grid coordinates, e.g.
        [(0, 0), (0, 1), (1, 0), (1, 1)]
        """
        pins = [self.get_pin(p) for p in positions]
        self.enable_pins(pins)

    def enable_pins(self, pins: Sequence[int], group_id: int=0, duty_cycle: int=255):
        """Enable the specified set of electrodes by pin number

        PurpleDrop supports two drive groups which can be driven independently,
        with different duty cycles. Adjusting the duty cycle is primarily used
        for feedback control performed on the device, but can be set remotely
        via RPC calls. 
        
        For most use cases, drive group 0 can be used exclusively. But when 
        using feedback control, e.g. for drop splitting, pins for drive group 0
        and drive group 1 must be setup prior to enabling feedback control. 

        Unused drive groups should be disabled by setting an empty pin list.

        Arguments: 

          - pins: List of integers, giving pin numbers to enable
          - group_id: Drive group index
          - duty_cycle: On duty cycle to drive (0-255), 255 being max duty cycle, and 0 min
        """
        self.client.set_electrode_pins(pins, group_id, duty_cycle)

    def set_feedback_command(self, target, mode, input_groups_p_mask, input_groups_n_mask, baseline):
        """Update feedback control settings

        When enabled, the purpledrop controller will adjust the duty cycle of
        electrode drive groups based on capacitance measurements.

        Arguments:
            - target: The controller target in counts
            - mode:
                - 0: Disabled
                - 1: Normal
                - 2: Differential
            - input_groups_p_mask: Bit mask indicating which capacitance groups to 
              sum for positive input (e.g. for groups 0 and 2: 5)
            - input_groups_n_mask: Bit mask for negative input groups (used in differential mode)
            - baseline: The duty cycle to apply to both drive groups when no error signal is 
              present (0-255)
        """
        self.client.set_feedback_command(target, mode, input_groups_p_mask, input_groups_n_mask, baseline)

    def active_capacitance(self) -> float:
        """Get the most recent capacitance for active electrodes
        """
        return self.client.get_active_capacitance()

    def bulk_capacitance(self) -> List[float]:
        """Get the most recent scan of electrode capacitance

        This function is deprecated, and may be removed in a future version. Use get_scan_capacitance instead.
        """
        return self.client.get_scan_capacitance()['calibrated']

    def scan_capacitance(self) -> Dict[str, List]:
        """Get the most recent capacitance scan result

        Returns: capacitance scan data for all electrodes in the form of a dict
        containing two lists.

          {
              "raw": List[float],
              "calibrated": List[float]
          }
        """
        return self.client.get_scan_capacitance()

    def group_capacitance(self) -> Dict[str, List]:
        """Get the most recent group capacitance measurements

        Returns: dict containins the raw and calibrated values for all 
        capacitance groups. 

        Example: 

            {
                "raw": [10, 11, 400, 10, 9],
                "calibrated": [0.0, 0.0, 2.9, 0.0, 0.0],
            }

        """
        return self.client.get_group_capacitance()

    def set_capacitance_group(self, pins: Sequence[int], group_id: int, setting: int):
        """Set configuration for a capacitance group

        Purpledrop support 5 different group scans. Each group defines a set of electrodes
        which are measured together after each AC drive cycle. To disable a
        group, set the pins to an empty list.

        Arguments:
          - pins: A list of pins included in the group (may be empty to disable the group)
          - group_id: The group number to set (0-4)
          - setting: 0 - high gain, 1 - low gain
        """
        self.client.set_capacitance_group(pins, group_id, setting)

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