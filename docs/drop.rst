Drop
====

The Drop class provides a convenient wrapper to encapsulate the state of a drop
on the device, and to move it using up, down, left, right commands. It makes use
of the `move_drop` API to perform moves. 

An example of using the `Drop` class: ::

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
  drop.move(Dir.LEFT)

API Reference 
-------------

.. autoclass:: pdclient.drop.Drop
   :members: