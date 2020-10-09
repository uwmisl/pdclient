
PdClient
========

The PdClient class provides access to the low-level RPC calls that can be made
to the `pdserver` gateway. 

Accessing unimplemented RPC methods
-----------------------------------

The purpledrop driver is under active development, and there may be RPC calls
available which have not yet been added to the client, and are therefor not 
documented here. The `client` attribute on the PdClient object can be used to 
make arbitrary RPC calls by method name. For example, to call the RPC method 
named `my_test_method` with two arguments (a string and an int):
:: 

   c = pdclient.PdClient(RPC_URL)
   return_value = c.client.my_test_method('argument1', 2)

A full list of the available rpc methods can be seen by accessing the `/rpc/map` 
route on a running `pdserver` instance. 

API Reference 
-------------

.. autoclass:: pdclient.PdClient
   :members:
