# Module Templates

In this directory you will find templates to help you write your own module. There are
simple examples for small, single file modules and also for more complex package modules.
Please read through this document and the notes in the simple modules, even if you plan
to make a larger module and structure it as a package as it is important to understand
certain concepts.

## Module Types

There are two types of modules in MQTTany:

* **Communication modules** generally connect to servers to send and receive control
  and status information from an outside controller.
* **Interface modules** provide access to things like GPIO pins or other hardware.

## Multi-Processing

The first thing you must understand is that MQTTany uses multiprocessing, this makes for
some interesting complications! The reason behind doing this is performance, the starting
point for MQTTany was to interface GPIO pins to MQTT. I wanted to leverage the multi-core
processors that SBCs have these days in order to keep IO bound operations like GPIO
access fast.

The core runs on the main process and spawns a process for each module, you don't need
to worry about that part. Before forking a new process for the module the core will
inject a few objects that allow the module to send and receive messages, see the module
templates for more details, especially for package style modules.

## Message Bus

An internal message bus is responsible for moving messages between modules. This is done
using multiprocessing queues to move messages between processes. All messages on the bus
should be `BusMessage` objects.

Communication modules consume messages on a transmit queue and put received messages in
a receive queue. The bus thread will look after reattempting transmission of a message
as needed based on the return value of the transmit method.

Interface modules consume messages on a subscribe queue and put messages to be
transmitted on a publish queue. On load these modules must provide a description of the
data they provide and can receive, described by nodes and properties.

## [Configuration](configuration.md)

A configuration parser has been built into MQTTany that looks after typing and other
checks for configuration values, this greatly simplifies loading the configuration in
modules as they are only required to perform the more complex validations. All basic
Python types can be used, along with a few special ones. A
[separate document](configuration.md) covers how to describe your configuration options
as this is a fairly lengthly subject.

## GPIO Access

MQTTany requires that modules lock GPIO pins before attempting to use them. This was
done in an effort to reduce errors and access conflicts. Modules must successfully get
a lock on a GPIO pin before doing any operations on it, if the lock is not acquired they
must not access the pin at all.

```python
from common import lock_gpio

if lock_gpio(0):
    # ok to use pin, continue
    pass
else:
    # pin is locked already, do not access!
    return
```
