Drop
====

The Drop class provides a convenient wrapper to encapsulate the state of a drop
on the device, and to move it using up, down, left, right commands. It makes use
of the `move_drops` API method to perform moves.

An example of using the `Drop` class to move a single drop: ::

  from pdclient import PdClient
  from pdclient.drop import Drop, Dir
  client = PdClient('http://localhost:7000/rpc')
  start_pos = [4, 8]
  size = [2, 2]
  drop = Drop(start_pos, size, client)

  # Measure the sum of capacitance for all electrodes in the drop
  cap = pdclient.bulk_capacitance()
  drop_cap = sum([cap[pin] for pin in drop.pins()])

  # Enable all electrodes in the drop
  drop.activate()

  # Move the drop
  drop.move_up()

  # Move the drop with enum argument
  drop.move(Dir.LEFT)`

Drops can also be moved simultaneously, by passing several move commands to the
`move_drops` method at once. In this case, the API method will return after all
move operations are completed, and will return a separate result object for each
indicating, e.g. if the move was successful. The `pdclient.drop.move_multiple_drops`
function provides support for moving multiple Drop objects this way.


  from pdclient import PdClient
  from pdclient.drop import Drop, Dir, move_multiple_drops

  client = PdClient('http://localhost:7000/rpc')
  drop0 = Drop((0, 0), (2, 2), client)
  drop1 = Drop((5, 0), (2, 2), client)

  results = move_multiple_drops((drop0, Dir.DOWN), (drop1, Dir.DOWN))
  for i, r in enumerate(results):
      if not r['success']:
        print(f"Drop {i} failed to move")


API Reference
-------------

.. autoclass:: pdclient.drop.Drop
   :members: