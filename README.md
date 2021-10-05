# pyCATS
[![Anaconda-Server Badge](https://anaconda.org/alba-controls/pyCATS/badges/version.svg)](https://anaconda.org/alba-controls/pyCATS)
[![Anaconda-Server Badge](https://anaconda.org/alba-controls/pyCATS/badges/latest_release_date.svg)](https://anaconda.org/alba-controls/pyCATS)
[![Anaconda-Server Badge](https://anaconda.org/alba-controls/pyCATS/badges/platforms.svg)](https://anaconda.org/alba-controls/pyCATS)
[![Anaconda-Server Badge](https://anaconda.org/alba-controls/pyCATS/badges/license.svg)](https://anaconda.org/alba-controls/pyCATS)

This library provides a python communication layer with the CATS server.
    
In addition, two applications are provided: A Tango DS and a Qt application
 based on the tango layer. 

## Tango Device Server

The core of the server is an internal thread that updates the status dictionary based on a
fast polling on the CATS registers and push change events for the tango attributes..

To run the server you need to define 4 device properties:

    host: CATS system hostname
    port_monitor: socket port to monitor the CATS system
    port_operate: socket port to operate the CATS system
    update_freq_ms: time in ms to update the TangoDS status from the monitor socket.

## Cats monitor

This is a graphical application in PyQt5 which monitors the tango attributes
from the Tango DS.

## Cats/Isara compatibility

PyCATS device server now support ISARA Model (Vicente Rey / July 2017)
ISARA accepts a new tool:  number 5 for tool parameter is "double gripper"

### sample addresses

       CATS: lid, sample_no
           sample_no is regarding that lid
           (for example for 3rd sample in 2nd puck of a 3puck lid with 10 samples each
                   sample_no is 23 )

       ISARA:  puck, sample_no
           there is only one big lid in ISARA model
              puck number is given instead of lid number
              sample number is number of sample in that puck


### some new syntax for ISARA:
       toolcal is always zero for ISARA. For commands using it the value provided is ignored

       back(tool) - ISARA
       back(tool, toolcal)  - CATS

       soak(tool) - ISARA
       soak(tool, lid)  - CATS

### commands CATS only

       - transfer()
       - rd_position()
       - rd_load()
       - goto_well()
       - adjust()
       - collect()
       - focus()
       - expose()
       - setplateangle()
