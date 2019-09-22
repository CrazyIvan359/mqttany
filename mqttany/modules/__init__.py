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

import time, sys
from importlib import import_module
import multiprocessing as mproc
from queue import Empty as QueueEmptyError

import logger
from logger import log_traceback
from config import load_config
from common import POISON_PILL

all = [ "load", "unload" ]

ATTR_INIT = "init"
ATTR_UNINIT = "uninit"
ATTR_PRE_LOOP = "pre_loop"
ATTR_POST_LOOP = "post_loop"
ATTR_QUEUE = "queue"

log = logger.get_logger()
modules_loaded = []
module_queues = {}


def load(config_file):
    """
    Loads each module in ``modules_list`` and spawns a process for them
    """
    config = load_config(config_file)

    for module_name in [key for key in config if isinstance(config[key], dict)]:
        log.debug("Loading module '{name}'".format(name=module_name))
        try:
            module = import_module("modules.{}".format(module_name))

        except ImportError as err:
            log.error("Failed to import module '{name}'".format(name=module_name))
            log.error("  {error}".format(error=err))
            log_traceback(log)
            log.error("Module '{name}' was not loaded".format(name=module_name))

        except ImportWarning as err:
            log.warn("Warnings occured when importing module '{name}'".format(name=module_name))
            log.warn("  {error}".format(error=err))
            log_traceback(log)
            log.error("Module '{name}' was not loaded".format(name=module_name))

        else:
            module_queues[module_name] = mproc.Queue()
            sys.modules[module.__name__].queue = module_queues[module_name]

            if not _call_func(module, ATTR_INIT, config_data=config[module_name]): # call module init
                log.warn("Module '{name}' not initialized".format(name=module_name))
                continue

            log.info("Module '{name}' loaded successfully".format(name=module_name))
            modules_loaded.append(module)

    for i in range(len(modules_loaded)):
        module = modules_loaded[i]
        module_name = module.__name__.split(".")[-1]
        if not _start_proc(module): # start subprocess
            log.error("Failed to start process for module '{name}'".format(name=module_name))
            continue

    return modules_loaded


def unload():
    """
    Unloads each module in ``modules_loaded`` and terminates processes
    """
    for i in range(len(modules_loaded)-1, -1, -1): # reverse order in case of dependecies
        module = modules_loaded[i]
        module_name = module.__name__.split(".")[-1]
        if module:
            log.debug("Unloading module '{name}'".format(name=module_name))
            _stop_proc(module)
            _call_func(module, ATTR_UNINIT)
            log.info("Module '{name}' unloaded".format(name=module_name))


def _call_func(module, name, **kwargs):
    """
    Calls ``name`` if define in ``module``
    """
    func = getattr(module, name, None)
    if func is not None:
        retval = False
        if callable(func):
            try:
                retval = func(**kwargs)
            except:
                log.error("An exception occurred while running function '{func}'".format(func=getattr(func, "__name__", func)))
                log_traceback(log)
            finally:
                return retval


def _start_proc(module):
    """
    Starts a subprocess for ``module``
    """
    module_name = module.__name__.split(".")[-1]
    try:
        log.debug("Creating process for '{name}'".format(name=module_name))
        module.process = mproc.Process(name=module_name, target=_proc_loop, args=(module,), daemon=False)
    except Exception as err:
        log.error("Failed to create process for module '{name}'".format(name=module_name))
        log.error("  {}".format(err))
        return False
    else:
        log.debug("Process created successfully for module '{name}'".format(name=module_name))
        try:
            log.debug("Starting process for '{name}'".format(name=module_name))
            module.process.start()
        except Exception as err:
            log.error("Failed to start process for module '{name}'".format(name=module_name))
            log.error("  {}".format(err))
            return False
        else:
            log.info("Process started successfully for module '{name}'".format(name=module_name))
            return True


def _proc_loop(module):

    _call_func(module, ATTR_PRE_LOOP)

    poison_pill = False
    while not poison_pill:
        try:
            message = module.queue.get_nowait()
        except QueueEmptyError:
            time.sleep(0.025) # 25ms
        else:
            if message == POISON_PILL:
                poison_pill = True # terminate signal
                module.log.debug("Received poison pill")
            else:
                module.log.debug("Received message [{message}]".format(message=message))
                func = getattr(module, message["func"])
                if callable(func):
                    try:
                        func(*message.get("args", []), **message.get("kwargs", {}))
                    except:
                        log.error("An exception occurred while running function '{func}'".format(func=message.get("func", None)))
                        log_traceback(module.log)
                else:
                    module.log.warn("Unrecognized function '{func}'".format(func=message["func"]))

    _call_func(module, ATTR_POST_LOOP)


def _stop_proc(module):
    """
    Stops the subprocess for ``module``
    """
    module_name = module.__name__.split(".")[-1]
    if hasattr(module, "process"):
        if module.process.is_alive():
            log.debug("Stopping subprocess for '{name}' with 10s timeout".format(name=module_name))
            module.queue.put_nowait(POISON_PILL)
            module.process.join(10)
            if module.process.is_alive():
                log.warn("Subprocess for module '{name}' did not stop when requested, terminating forcefully".format(name=module_name))
                module.process.terminate()
                module.process.join(10) # make sure cleanup is done
                log.debug("Subprocess terminated forcefully for module '{name}'".format(name=module_name))
            else:
                log.debug("Subproccess for module '{name}' stopped cleanly".format(name=module_name))
        else:
            module.process.join(10)
            log.warn("Subprocess for module '{name}' was not running".format(name=module_name))
    else:
        log.debug("Module '{name}' does not have a subprocess".format(name=module_name))
