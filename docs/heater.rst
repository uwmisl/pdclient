Heater
======

Some electrode boards provide heating and temperature sensing functionality to
control the temperature of a drop at a particular location on the board. 

For example, electrode board v4 has a 2x2 grid of heated electrodes, each 
connected by an array of vias to a temperature sensor and a heating resistor
underneath the board. 


The PurpleDrop has four temperature sensor inputs, and four PWM driven 
high-current switch outputs for driving the heater elements, which can be 
accessed/controlled by the `get_temperatures` and `set_pwm_duty_cycle` RPC calls
respectively. 

Feedback control of the temperature must be performed by the user script, but 
the `heater` module provides utilities to simplify this common task. The 
`TemperatureControl` class instantiates a separate PID loop for each
heater/sensor pair. Because the temperature sensor is located on the opposite 
side of the board, not directly on the drop, there will be some temperature drop
from the sensors to the drop. The `k_drop` paramater is a calibration constant
to account for this drop, and can be determined by setting up an experiment with
a temperature sensor placed directly in the drop. The temperature setpoint and 
the estimated drop temperature reported in the `drop_temperature` attribute are 
calibrated values representing the actual drop temperature. The PID controllers 
will actually be set to a slightly higher temperature behind-the-scenes to 
account for the estimated temperature delta from sensor to water drop. 

The current temperature estimate is derived from a low-pass filtered average of 
all four temperature sensors, and can be read from the `drop_temperature` 
attribute.

As the TemperatureControl class requires a number of parameters that are 
generally dependent on the physical characteristics of the electrode board
being controlled, factory functions are used to codify these parameters once
they have been determined; e.g. :func:`~pdclient.heater.get_v4_controller`. 


API Reference 
-------------

.. autofunction:: pdclient.heater.get_v4_controller

.. autoclass:: pdclient.heater.TemperatureControl
   :members: