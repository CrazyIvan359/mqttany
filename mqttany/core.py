"""
************
MQTTany Core
************

:Author: Michael Murton
"""
# Copyright (c) 2019-2025 MQTTany contributors
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

import multiprocessing as mproc
import time
import types
import typing as t
from importlib import import_module
from queue import Empty as QueueEmptyError

import bus
import logger
from common import BusMessage, PoisonPill, PublishMessage, SignalHook, SubscribeMessage
from config import load_config
from logger import log_traceback
from modules import (
    ATTR_CBTRANSMIT,
    ATTR_LOAD,
    ATTR_LOG,
    ATTR_NODES,
    ATTR_QRESEND,
    ATTR_QSUBSCRIBE,
    ATTR_QTRANSMIT,
    ATTR_START,
    ATTR_STOP,
    ATTR_TXREADY,
    ATTR_TYPE,
    ModuleType,
    call,
)

log = logger.get_logger("core")
communication_modules: t.List[types.ModuleType] = []
interface_modules: t.List[types.ModuleType] = []


def _loop_comm(module: types.ModuleType) -> None:
    def _get_message(queue_name: str) -> t.Union[BusMessage, None]:
        try:
            return getattr(module, queue_name).get_nowait()
        except QueueEmptyError:
            return None

    def _queue_resend(msg: BusMessage) -> None:
        messages: t.List[BusMessage] = [msg]
        message = _get_message(ATTR_QRESEND)
        while message:
            messages.append(message)
            message = _get_message(ATTR_QRESEND)
        for message in messages:
            getattr(module, ATTR_QRESEND).put_nowait(message)

    signal = SignalHook()
    call(module, ATTR_START)

    message: t.Union[BusMessage, None] = None
    while (not isinstance(message, PoisonPill)) and signal.signal != signal.SIGTERM:
        message = None
        if call(module, ATTR_TXREADY):
            # check for messages in the resend queue first
            message = _get_message(ATTR_QRESEND)
            # if it is empty then we can get a new message from the transmit queue
            message = message if message else _get_message(ATTR_QTRANSMIT)

            if isinstance(message, PublishMessage):
                # TODO convert modules to classes
                module.log.trace("Message received to transmit: %s", message)  # type: ignore
                if not call(module, ATTR_CBTRANSMIT, message=message):
                    # transmit failed
                    # TODO convert modules to classes
                    module.log.debug(  # type: ignore
                        "Failed to send message, queued for retransmission"
                    )
                    _queue_resend(message)
                    time.sleep(0.5)  # 500ms
            elif (not isinstance(message, PoisonPill)) and message is not None:
                try:
                    # TODO convert modules to classes
                    module.log.warn("Got unrecognized message to transmit: %s", message)  # type: ignore
                except:
                    # TODO convert modules to classes
                    module.log.warn("Got unrecognized message to transmit")  # type: ignore
        else:
            # module not ready to transmit, but check transmit queue in case exit is requested
            message = _get_message(ATTR_QTRANSMIT)
            if isinstance(message, PublishMessage):
                # TODO convert modules to classes
                module.log.debug("Not ready to send, message queued for retransmission")  # type: ignore
                _queue_resend(message)
                time.sleep(0.5)  # 500ms

        if not message:
            time.sleep(0.025)  # 25ms
        elif isinstance(message, PoisonPill):
            # TODO convert modules to classes
            module.log.trace("Module stopping")  # type: ignore

    if signal.signal == signal.SIGTERM:
        # TODO convert modules to classes
        module.log.trace("Received %s", signal.signal.name)  # type: ignore

    call(module, ATTR_STOP)


def _loop_interface(module: types.ModuleType) -> None:
    signal = SignalHook()
    call(module, ATTR_START)

    message: t.Union[BusMessage, None] = None
    while (not isinstance(message, PoisonPill)) and signal.signal != signal.SIGTERM:
        try:
            message = getattr(module, ATTR_QSUBSCRIBE).get(timeout=1)
        except QueueEmptyError:
            pass
        else:
            if isinstance(message, SubscribeMessage):
                # TODO convert modules to classes
                module.log.trace("Message received on subscribe queue: %s", message)  # type: ignore
                call(module, message.callback, message=message)
            elif isinstance(message, PoisonPill):
                # TODO convert modules to classes
                module.log.trace("Module stopping")  # type: ignore
            else:
                try:
                    # TODO convert modules to classes
                    module.log.warn(  # type: ignore
                        "Got unrecognized message on subscribe queue: %s", message
                    )
                except:
                    # TODO convert modules to classes
                    module.log.warn("Got unrecognized message on subscribe queue")  # type: ignore

    if signal.signal == signal.SIGTERM:
        # TODO convert modules to classes
        module.log.trace("Received %s", signal.signal.name)  # type: ignore

    call(module, ATTR_STOP)


def _validate_module(module: types.ModuleType) -> bool:
    module_name = module.__name__.split(".")[-1]
    valid = True

    def check_function(name: str, required: t.Optional[bool] = True) -> bool:
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


def _load_modules(
    config_file: str, core_queue: "mproc.Queue[str]"
) -> t.List[types.ModuleType]:
    """
    Loads each module with a section in the config and spawns a process for them
    """
    config = load_config(config_file)

    if not config:
        return []

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
                # call module load
                if not call(module, ATTR_LOAD, config_raw=config[module_name]):
                    log.warn("Module '%s' load failed", module_name)
                    continue
                else:
                    log.debug("Module '%s' loaded successfully", module_name)

                if getattr(module, ATTR_TYPE) == ModuleType.COMMUNICATION:
                    bus.setup_comm_module(module, core_queue)
                    communication_modules.append(module)

                elif getattr(module, ATTR_TYPE) == ModuleType.INTERFACE:
                    bus.setup_interface_module(module)
                    if not getattr(module, ATTR_NODES, None):
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


def _start_modules() -> None:
    """
    Starts a subprocess for each module that was loaded.
    """

    for module in communication_modules + interface_modules:
        module_name = module.__name__.split(".")[-1]
        try:
            log.trace("Creating process for '%s'", module_name)
            if getattr(module, ATTR_TYPE) == ModuleType.COMMUNICATION:
                target = _loop_comm
            else:  # if getattr(module, ATTR_TYPE) == ModuleType.INTERFACE:
                target = _loop_interface
            # TODO convert modules to classes
            module.process = mproc.Process(  # type: ignore
                name=module_name, target=target, args=(module,), daemon=False
            )
        except Exception as err:  # pylint: disable=broad-except
            log.error("Failed to create process for module '%s'", module_name)
            log.error("  %s", err)
        else:
            log.trace("Process created successfully for module '%s'", module_name)
            try:
                log.trace("Starting process for '%s'", module_name)
                # TODO convert modules to classes
                module.process.start()  # type: ignore
            except Exception as err:  # pylint: disable=broad-except
                log.error("Failed to start process for module '%s'", module_name)
                log.error("  %s", err)
            else:
                log.info("Module '%s' started successfully", module_name)


def _stop_modules() -> None:
    """
    Unloads each module that was loaded and terminates processes
    """
    for module in interface_modules + communication_modules:
        module_name = module.__name__.split(".")[-1]
        if module:
            if hasattr(module, "process"):
                # TODO convert modules to classes
                if module.process.is_alive():  # type: ignore
                    log.trace(
                        "Stopping subprocess for '%s' with 10s timeout", module_name
                    )
                    if hasattr(module, "transmit_queue"):
                        # TODO convert modules to classes
                        module.transmit_queue.put_nowait(PoisonPill())  # type: ignore
                    else:
                        # TODO convert modules to classes
                        module.subscribe_queue.put_nowait(PoisonPill())  # type: ignore
                    # TODO convert modules to classes
                    module.process.join(10)  # type: ignore
                    if module.process.is_alive():  # type: ignore
                        log.warn(
                            "Subprocess for module '%s' did not stop when requested, "
                            "terminating forcefully",
                            module_name,
                        )
                        # TODO convert modules to classes
                        module.process.terminate()  # type: ignore
                        # make sure cleanup is done
                        # TODO convert modules to classes
                        module.process.join(10)  # type: ignore
                        log.warn(
                            "Subprocess terminated forcefully for module '%s'",
                            module_name,
                        )
                    else:
                        log.debug(
                            "Subproccess for module '%s' stopped cleanly", module_name
                        )
                else:
                    # TODO convert modules to classes
                    module.process.join(10)  # type: ignore
                    log.warn("Subprocess for module '%s' was not running", module_name)
            else:
                log.warn("Module '%s' does not have a subprocess", module_name)
            log.info("Module '%s' unloaded", module_name)


def start(core_queue: "mproc.Queue[str]", config_file: str) -> None:
    def check_import(name: str) -> bool:
        try:
            lib = import_module(name)
            del lib
        except ModuleNotFoundError:
            log.error("Missing import: %s", name)
            return False
        else:
            return True

    missing_imports = 0
    for name in ["yaml", "yamlloader", "mprop", "adafruit_platformdetect", "periphery"]:
        missing_imports += int(not check_import(name))

    if missing_imports > 0:
        log.error("Please see the wiki for instructions on how to install requirements")
        core_queue.put_nowait(__name__)
    else:
        import gpio

        gpio.init()

        if _load_modules(config_file, core_queue):
            _start_modules()
            bus.start()
        else:
            core_queue.put_nowait(__name__)


def stop() -> None:
    _stop_modules()
    bus.stop()
