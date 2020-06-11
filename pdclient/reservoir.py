"""Drivers for reservoir behavior

The board definition returned from the `get_board_definition` RPC call provides
descriptions of reservoirs on the electrode board, including a type name. This
module provides sensible default drivers for performing reservoir actions, and
also allows the user to register handlers either to modify the behavior or to 
support different types of reservoir. 

Generally, the reservior driver is created by calling the get_reservoir() 
method on a PdClient object, not instantiated directly.
"""
import time
from typing import Dict, Type, TYPE_CHECKING

from .drop import Drop

if TYPE_CHECKING:
    from pdclient import PdClient


class ReservoirDriver(object):
    """Abstract class for ReservoirDrivers
    """
    def __init__(self, descriptor: dict, client: 'PdClient'):
        self.descriptor = descriptor
        self.client = client

    def dispense(self) -> Drop:
        raise RuntimeError("Abstract method")
    
    def ingest(self):
        raise RuntimeError("Abstract method")
    
    def pin(self, id: str):
        # Exit is a special pin id; each reservoir has just one
        if id == 'exit':
            return self.descriptor['exit']
        for electrode in self.descriptor['electrodes']:
            if electrode['id'] == id:
                return electrode['pin']
        raise ValueError(f"Reservoir (type={self.descriptor['type']}) has no pin with id={id}")

class ReservoirA(ReservoirDriver):
    def __init__(self, descriptor: dict, client: 'PdClient'):
        super().__init__(descriptor, client)
    
    def dispense(self) -> Drop:
        SEQUENCE = [
            (('A', 'B', 'C', 'D', 'E', 'exit'), 1.0),
            (('B', 'C', 'D', 'E', 'exit'), 1.0),
            (('A', 'B', 'C', 'D', 'E', 'exit'), 1.0),
            (('B', 'C', 'D', 'E', 'exit'), 1.0),
            (('B', 'C', 'exit'), 0.8),
            (('A', 'B', 'exit'), 0.7),
            (('A', 'exit'), 0.7),
            (('exit',), 0.2),
        ]

        for step in SEQUENCE:
            pins = [self.pin(name) for name in step[0]]
            delay = step[1]
            self.client.enable_pins(pins)
            time.sleep(delay)
        self.client.enable_pins([])

        exit_pin = self.pin('exit')
        exit_loc = self.client.get_grid_location(exit_pin)
        if exit_loc is None:
            raise ValueError(f"The exit pin ({exit_pin}) for reservoir {self.descriptor['id']} is not in the grid")

        return Drop(exit_loc, (1, 1), self.client)

    def ingest(self):
        raise RuntimeError("Unimplemented")

class ReservoirB(ReservoirDriver):
    def __init__(self, descriptor, client):
        super().__init__(descriptor, client)
    
    def dispense(self):
        raise RuntimeError("Unimplemented")

    def ingest(self):
        raise RuntimeError("Unimplemented")

RESERVOIR_HANDLER_TABLE = {
    "reservoirA": ReservoirA,
    "reservoirB": ReservoirB
}

def register_driver(type_name: str, driver_type: Type):
    """Register a custom handler for a type of reservoir

    This will override any previously registered or default handlers for that type.

    Arguments: 
        - type_name: The typename, as provided in the board definition file, for 
        which this driver applies
        - driver_type: A class which will be instantiated for reservoirs of this type
    """
    RESERVOIR_HANDLER_TABLE[type_name] = driver_type

def create_driver(reservoir_descriptor: Dict, client: 'PdClient') -> ReservoirDriver:
    if 'type' not in reservoir_descriptor:
        raise ValueError("Reservoir descriptor contains no type field")

    type_name = reservoir_descriptor['type']
    if type_name not in RESERVOIR_HANDLER_TABLE:
        raise ValueError(f"No reservoir driver registered for type='{type_name}'")

    return RESERVOIR_HANDLER_TABLE[type_name](reservoir_descriptor, client)