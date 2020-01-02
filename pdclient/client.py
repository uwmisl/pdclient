import requests

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
        print(response)
        if 'result' in response:
            return response['result']
        else:
            raise RuntimeError("Unexpected response: %s" % response)

    def get_board_definition(self):
        return self.callrpc("get_board_definition")

    def set_electrode_pins(self, pins):
        return self.callrpc('set_electrode_pins', pins)

class PdClient(object):
    def __init__(self, host):
        self._layout = None
        self._client = RpcClient(host)

    def layout(self):
        if self._layout is None:
            self._layout = self._client.get_board_definition()['layout']

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
        print("Setting pins: %s" % electrode_numbers)
        resp = self._client.set_electrode_pins(electrode_numbers)
        print(resp)

