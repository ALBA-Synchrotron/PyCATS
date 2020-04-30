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
