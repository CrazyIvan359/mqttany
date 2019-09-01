"""
*************
Module Loader
*************

:Author: Michael Murton
"""
# Copyright (c) 2019 MQTTany contributors
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

import sys
from importlib import import_module
import multiprocessing as mproc

import logger
log = logger.get_logger()
from config import load_config
from common import POISON_PILL

all = [ "load", "unload" ]

ATTR_INIT = "init"
ATTR_UNINIT = "uninit"
ATTR_LOOP = "loop"
ATTR_STOP = "stop"
ATTR_QUEUE = "queue"

modules_loaded = []
module_queues = {}


def load():
    """
    Loads each module in ``modules_list`` and spawns a process for them
    """
    config = load_config()

    for module_name in [key for key in config if isinstance(config[key], dict)]:
        log.debug("Loading module '{name}'".format(name=module_name))
        try:
            module = import_module("modules.{}".format(module_name))
        except ImportError as err:
            log.error("Failed to import module '{name}'".format(name=module_name))
            log.error("  {error}".format(error=err))
            log.error("Module '{name}' was not loaded".format(name=module_name))
        except ImportWarning as err:
            log.warn("Warnings occured when importing module '{name}'".format(name=module_name))
            log.warn("  {error}".format(error=err))
            log.error("Module '{name}' was not loaded".format(name=module_name))
        else:
            if not _validate_module(module):
                log.error("Module '{name}' is not valid, skipping".format(name=module.__name__[8:]))
                continue

            module_queues[module_name] = mproc.Queue()
            sys.modules[module.__name__].queue = module_queues[module_name]

            if not _call_func(module, ATTR_INIT, config_data=config[module_name]): # call module init
                log.warn("Module '{name}' not initialized".format(name=module.__name__[8:]))
                continue

            log.info("Module '{name}' loaded successfully".format(name=module.__name__[8:]))
            modules_loaded.append(module)

    for i in range(len(modules_loaded)):
        module = modules_loaded[i]
        if _start_proc(module): # start subprocess
            log.info("Process started for module '{name}'".format(name=module.__name__[8:]))
        else:
            log.error("Failed to start process for module '{name}'".format(name=module.__name__[8:]))
            continue

    return modules_loaded


def unload():
    """
    Unloads each module in ``modules_loaded`` and terminates processes
    """
    for i in range(len(modules_loaded)-1, -1, -1): # reverse order in case of dependecies
        module = modules_loaded[i]
        if module:
            log.debug("Unloading module '{name}'".format(name=module.__name__[8:]))
            _stop_proc(module)
            _call_func(module, ATTR_UNINIT)
            log.info("Module '{name}' unloaded".format(name=module.__name__[8:]))


def _validate_module(module):
    """
    Confirms that a module has all required functions
    """
    valid = True

    init = getattr(module, ATTR_INIT, None)
    if init is None or not callable(init):
        log.debug("Module '{name}' has no function called 'init'".format(name=module.__name__[8:]))

    uninit = getattr(module, ATTR_UNINIT, None)
    if uninit is None or not callable(uninit):
        log.debug("Module '{name}' has no function called 'uninit'".format(name=module.__name__[8:]))

    loop = getattr(module, ATTR_LOOP, None)
    if loop is None or not callable(loop):
        log.error("Module '{name}' has no function called 'loop'".format(name=module.__name__[8:]))
        valid = False

    queue = getattr(module, ATTR_QUEUE, None)
    if queue is None or not isinstance(queue, mproc.queues.Queue):
        log.error("Module '{name}' has no Queue called 'queue'".format(name=module.__name__[8:]))
        valid = False

    return valid


def _call_func(module, name, **kwargs):
    """
    Calls ``name`` if define in ``module``
    """
    func = getattr(module, name, None)
    if func is not None:
        if callable(func):
            return func(**kwargs)


def _start_proc(module):
    """
    Starts a subprocess for ``module``
    """
    try:
        log.debug("Creating process for '{name}'".format(name=module.__name__[8:]))
        module.process = mproc.Process(target=getattr(module, ATTR_LOOP), name=module.__name__)
    except Exception as err:
        log.error("Failed to create process for module '{name}'".format(name=module.__name__[8:]))
        log.error("  {}".format(err))
        return False
    else:
        log.debug("Process created successfully for module '{name}'".format(name=module.__name__[8:]))
        try:
            log.debug("Starting process for '{name}'".format(name=module.__name__[8:]))
            module.process.start()
        except Exception as err:
            log.error("Failed to start process for module '{name}'".format(name=module.__name__[8:]))
            log.error("  {}".format(err))
            return False
        else:
            log.debug("Process started successfully for module '{name}'".format(name=module.__name__[8:]))
            return True


def _stop_proc(module):
    """
    Stops the subprocess for ``module``
    """
    if hasattr(module, "process"):
        if module.process.is_alive():
            log.debug("Stopping subprocess for '{name}' with 10s timeout".format(name=module.__name__[8:]))
            module.queue.put_nowait(POISON_PILL)
            module.process.join(10)
            if module.process.is_alive():
                log.warn("Subprocess for module '{name}' did not stop when requested, terminating forcefully".format(name=module.__name__[8:]))
                module.process.terminate()
                module.process.join(10) # make sure cleanup is done
                log.debug("Subprocess terminated forcefully for module '{name}'".format(name=module.__name__[8:]))
            else:
                log.debug("Subproccess for module '{name}' stopped cleanly".format(name=module.__name__[8:]))
        else:
            module.process.join(10)
            log.warn("Subprocess for module '{name}' was not running".format(name=module.__name__[8:]))
    else:
        log.debug("Module '{name}' does not have a subprocess".format(name=module.__name__[8:]))
