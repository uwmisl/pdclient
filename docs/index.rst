PurpleDrop Client Documentation
====================================

The `pdclient` package provides a python client library for controlling a 
PurpleDrop from python scripts. This client controls a PurpleDrop via a running
`pdserver` instance, which it communicates with through HTTP calls. 

Here's a simple example:
::

   import pdclient
   import time
   client = pdclient.PdClient('http://localhost:7000/rpc')

   # Turn on electrodes at location [0, 1] and  [0, 2] 
   # (i.e. x=0, y=1 and x=0, y=2)
   client.enable_positions([(0, 1), (0, 2)])

   # Wait briefly, and read the capacitance of the active electrodes
   time.sleep(0.1)
   active_cap = client.active_capacitance()
   print(f'Active capacitance: {active_cap}')


Higher Level Functions
----------------------
Some higher level functionality is also provided by the library, such as heating
control, drop movement, and reservoir dispensing.  

.. toctree::
   :hidden:

   self

.. toctree::
   :hidden:
   :maxdepth: 2

   pdclient
   drop
   heater

