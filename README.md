# PyCATS Tango DS


This Tango DS is still under develpment, if you want to try it,
please, notify all the possible bugs you may find.

There is an internal thread that updates the status and sends events on
all the information that comes from monitoring the CATS system.


To run the server you need to define 4 properties:

**host:** CATS system hostname
**port_monitor:** socket port to monitor the CATS system
**port_operate:** socket port to operate the CATS system
**update_freq_ms:** time in ms to update the TangoDS status from the monitor socket.
