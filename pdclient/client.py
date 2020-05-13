import json
import requests
import time

class RpcClient(object):
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

"""A mostly thin wrapper around RpcClient to provide some convenience utilities
"""
class PdClient(object):
    def __init__(self, host):
        self._layout = None
        self.client = RpcClient(host)

    def layout(self):
        if self._layout is None:
            self._layout = self.client.get_board_definition()['layout']

        return self._layout

    def get_pin(self, p):
        """Get the electrode pin number from a grid location using the layout

        p: (x, y) coordinate of the electrode to lookup
        """
        try:
            layout = self.layout()
            pin = layout['pins'][p[1]][p[0]]
        except IndexError:
            raise ValueError(
                "Invalid position (%d, %d), it is outside of the layout range"
                 % (p[0], p[1]))

        if pin is None:
            raise ValueError(
                "In valid position (%d, %d), no electrode is present at this location"
                 % (p[0], p[1]))

        return pin

    def move_drop(self, start, size, dir):
        return self.client.move_drop(start, size, dir)

    def enable_positions(self, positions):
        """Enable the given electrodes

        positions: List of 2-tuples of (x, y) electrode grid coordinates, e.g.
        [(0, 0), (0, 1), (1, 0), (1, 1)]
        """
        pins = [self.get_pin(p) for p in positions]
        self.enable_pins(pins)

    def enable_pins(self, electrode_numbers):
        """Enable the given electrodes

        electrode_numbers: List of integers, giving pin numbers to enable
        """
        self.client.set_electrode_pins(electrode_numbers)

    def active_capacitance(self):
        """Get the most recent capacitance for all active electrodes
        """
        return self.client.get_active_capacitance()

    def bulk_capacitance(self):
        """Get the most recent scan of electrode capacitance
        """
        return self.client.get_bulk_capacitance()

    def temperatures(self):
        """Get the most recent temperature measurements

        Returns a vector of temperatures (floats) in degC

        The length of the return value depends on device configuraiton, and
        may be zero.
        """
        return self.client.get_temperatures()

    def set_pwm_duty_cycle(self, chan, duty_cycle):
        """Set duty cycle on a PWM output channel

        chan is an integer specifying which PWM channel to change
        duty_cycle is float in range 0.0 to 1.0.
        """
        return self.client.set_pwm_duty_cycle(chan, duty_cycle)