"""
************
MQTTany Core
************

:Author: Michael Murton
"""
# Copyright (c) 2019-2020 MQTTany contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__all__ = ["start", "stop"]

import time
from importlib import import_module
import multiprocessing as mproc
from queue import Empty as QueueEmptyError

import logger
from logger import log_traceback
import bus
from config import load_config
from common import _call, POISON_PILL, SignalHook, BusMessage
from modules import (
    ModuleType,
    ATTR_TYPE,
    ATTR_LOG,
    ATTR_LOAD,
    ATTR_START,
    ATTR_STOP,
    ATTR_QTRANSMIT,
    ATTR_CBTRANSMIT,
    ATTR_QRESEND,
    ATTR_TXREADY,
    ATTR_QSUBSCRIBE,
    ATTR_NODES,
)

log = logger.get_module_logger("core")
communication_modules = []
interface_modules = []


def _loop_comm(module):
    def _get_message(queue_name):
        try:
            return getattr(module, queue_name).get_nowait()
        except QueueEmptyError:
            return None

    def _queue_resend(msg):
        messages = [msg]
        message = _get_message(ATTR_QRESEND)
        while message:
            messages.append(message)
            message = _get_message(ATTR_QRESEND)
        for message in messages:
            getattr(module, ATTR_QRESEND).put_nowait(message)

    signal = SignalHook()
    _call(module, ATTR_START)

    message = None
    while message != POISON_PILL and signal.signal != signal.SIGTERM:
        message = None
        if _call(module, ATTR_TXREADY):
            # check for messages in the resend queue first
            message = _get_message(ATTR_QRESEND)
            # if it is empty then we can get a new message from the transmit queue
            message = message if message else _get_message(ATTR_QTRANSMIT)

            if isinstance(message, BusMessage):
                module.log.trace("Message received to transmit: %s", message)
                if not _call(module, ATTR_CBTRANSMIT, message=message):
                    # transmit failed
                    module.log.debug(
                        "Failed to send message, queued for retransmission"
                    )
                    _queue_resend(message)
                    time.sleep(0.5)  # 500ms
            elif message != POISON_PILL and message is not None:
                try:
                    module.log.warn("Got unrecognized message to transmit: %s", message)
                except:
                    module.log.warn("Got unrecognized message to transmit")
        else:
            # module not ready to transmit, but check transmit queue in case exit is requested
            message = _get_message(ATTR_QTRANSMIT)
            if isinstance(message, BusMessage):
                module.log.debug("Not ready to send, message queued for retransmission")
                _queue_resend(message)
                time.sleep(0.5)  # 500ms

        if not message:
            time.sleep(0.025)  # 25ms
        elif message == POISON_PILL:
            module.log.trace("Module stopping")

    if signal.signal == signal.SIGTERM:
        module.log.trace("Received %s", signal.signal.name)

    _call(module, ATTR_STOP)


def _loop_interface(module):
    signal = SignalHook()
    _call(module, ATTR_START)

    message = None
    while message != POISON_PILL and signal.signal != signal.SIGTERM:
        try:
            message = getattr(module, ATTR_QSUBSCRIBE).get(timeout=1)
        except QueueEmptyError:
            pass
        else:
            if isinstance(message, BusMessage):
                module.log.trace("Message received on subscribe queue: %s", message)
                _call(module, message.callback, message=message)
            elif message == POISON_PILL:
                module.log.trace("Module stopping")
            else:
                try:
                    module.log.warn(
                        "Got unrecognized message on subscribe queue: %s", message
                    )
                except:
                    module.log.warn("Got unrecognized message on subscribe queue")

    if signal.signal == signal.SIGTERM:
        module.log.trace("Received %s", signal.signal.name)

    _call(module, ATTR_STOP)


def _validate_module(module):
    module_name = module.__name__.split(".")[-1]
    valid = True

    def check_function(name, required=True):
        func_valid = True
        log_func = getattr(log, "error" if required else "debug")
        cb = getattr(module, name, None)
        if cb is None:
            log_func("Module '%s' has no '%s' function", module_name, name)
            func_valid = False
        elif not callable(cb):
            log.warn(
                "Module '%s' does not have a callable '%s' function", module_name, name
            )
            func_valid = False
        return func_valid if required else True

    if isinstance(getattr(module, ATTR_TYPE, None), ModuleType):
        # Not working? type(logging.Logger) == <class 'type'>
        # if isinstance(getattr(module, ATTR_LOG), logger.logging.Logger):
        if type(getattr(module, ATTR_LOG)) == "<class 'logging.Logger'>":
            log.error(
                "Module '%s' does not have a valid logger assigned to '%s'",
                module_name,
                ATTR_LOG,
            )
            valid = False

        valid &= check_function(ATTR_LOAD)
        valid &= check_function(ATTR_START, False)
        valid &= check_function(ATTR_STOP, False)

        if getattr(module, ATTR_TYPE) == ModuleType.COMMUNICATION:
            log.debug("Module '%s' is a communication module", module_name)
            valid &= check_function(ATTR_TXREADY)
            valid &= check_function(ATTR_CBTRANSMIT)

        elif getattr(module, ATTR_TYPE) == ModuleType.INTERFACE:
            log.debug("Module '%s' is an interface module", module_name)
            if not hasattr(module, ATTR_NODES):
                log.error("Module '%s' is missing '%s'", module_name, ATTR_NODES)
                valid = False

    elif hasattr(module, ATTR_TYPE):
        log.error(
            "Module '%s' has an invalid module type and will not be loaded", module_name
        )
        valid = False
    else:
        log.error("Module '%s' has no module type and will not be loaded", module_name)
        valid = False

    return valid


def _load_modules(config_file, core_queue):
    """
    Loads each module with a section in the config and spawns a process for them
    """
    config = load_config(config_file)

    if not config:
        return False

    for module_name in [key for key in config if isinstance(config[key], dict)]:
        module = None
        log.debug("Loading module '%s'", module_name)
        try:
            module = import_module(f"modules.{module_name}")

        except ImportError as err:
            log.error("Failed to import module '%s'", module_name)
            log.error("  %s", err)
            log_traceback(log)
            log.error("Module '%s' was not loaded", module_name)

        except ImportWarning as err:
            log.warn("Warnings occured when importing module '%s'", module_name)
            log.warn("  %s", err)
            log_traceback(log)
            log.error("Module '%s' was not loaded", module_name)

        else:
            if _validate_module(module):
                if not _call(
                    module, ATTR_LOAD, config_raw=config[module_name]
                ):  # call module load
                    log.warn("Module '%s' load failed", module_name)
                    continue
                else:
                    log.debug("Module '%s' loaded successfully", module_name)

                if getattr(module, ATTR_TYPE) == ModuleType.COMMUNICATION:
                    bus.setup_comm_module(module, core_queue)
                    communication_modules.append(module)

                elif getattr(module, ATTR_TYPE) == ModuleType.INTERFACE:
                    bus.setup_interface_module(module)
                    if not getattr(module, ATTR_NODES, {}):
                        log.error(
                            "Module '%s' contains no valid nodes and will not be loaded",
                            module_name,
                        )
                        continue
                    interface_modules.append(module)

        finally:
            del module

    del config
    return communication_modules + interface_modules


def _start_modules():
    """
    Starts a subprocess for each module that was loaded.
    """

    for module in communication_modules + interface_modules:
        module_name = module.__name__.split(".")[-1]
        try:
            log.trace("Creating process for '%s'", module_name)
            if getattr(module, ATTR_TYPE) == ModuleType.COMMUNICATION:
                target = _loop_comm
            elif getattr(module, ATTR_TYPE) == ModuleType.INTERFACE:
                target = _loop_interface
            module.process = mproc.Process(
                name=module_name, target=target, args=(module,), daemon=False
            )
        except Exception as err:  # pylint: disable=broad-except
            log.error("Failed to create process for module '%s'", module_name)
            log.error("  %s", err)
        else:
            log.trace("Process created successfully for module '%s'", module_name)
            try:
                log.trace("Starting process for '%s'", module_name)
                module.process.start()
            except Exception as err:  # pylint: disable=broad-except
                log.error("Failed to start process for module '%s'", module_name)
                log.error("  %s", err)
            else:
                log.info("Module '%s' started successfully", module_name)


def _stop_modules():
    """
    Unloads each module that was loaded and terminates processes
    """
    for module in interface_modules + communication_modules:
        module_name = module.__name__.split(".")[-1]
        if module:
            if hasattr(module, "process"):
                if module.process.is_alive():
                    log.trace(
                        "Stopping subprocess for '%s' with 10s timeout", module_name
                    )
                    if hasattr(module, "transmit_queue"):
                        module.transmit_queue.put_nowait(POISON_PILL)
                    else:
                        module.subscribe_queue.put_nowait(POISON_PILL)
                    module.process.join(10)
                    if module.process.is_alive():
                        log.warn(
                            "Subprocess for module '%s' did not stop when requested, "
                            "terminating forcefully",
                            module_name,
                        )
                        module.process.terminate()
                        module.process.join(10)  # make sure cleanup is done
                        log.warn(
                            "Subprocess terminated forcefully for module '%s'",
                            module_name,
                        )
                    else:
                        log.debug(
                            "Subproccess for module '%s' stopped cleanly", module_name
                        )
                else:
                    module.process.join(10)
                    log.warn("Subprocess for module '%s' was not running", module_name)
            else:
                log.warn("Module '%s' does not have a subprocess", module_name)
            log.info("Module '%s' unloaded", module_name)


def start(core_queue, config_file):
    def check_import(name):
        try:
            lib = import_module(name)
            del lib
        except ImportError:
            log.error("Missing import: %s", name)
            return False
        else:
            return True

    missing_imports = 0
    for name in ["yaml", "yamlloader", "mprop"]:
        missing_imports += int(not check_import(name))

    if missing_imports > 0:
        log.error("Please see the wiki for instructions on how to install requirements")
        core_queue.put_nowait(__name__)
    else:
        if _load_modules(config_file, core_queue):
            _start_modules()
            bus.start()
        else:
            core_queue.put_nowait(__name__)


def stop():
    bus.stop()
    _stop_modules()
