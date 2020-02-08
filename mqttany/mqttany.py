"""
*******
MQTTany
*******

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

import version as mqttanyversion
__version__ = mqttanyversion.__version__

import time, argparse
import multiprocessing as mproc
from queue import Empty as QueueEmptyError

import logger, modules
from common import SignalHook

log = logger.get_logger()
queue = mproc.Queue()


def get_args():
    """
    Get arguments
    """
    parser = argparse.ArgumentParser(description="MQTTany allows you to connect things to MQTT")
    parser.add_argument("-v", "--verbose", action="count", help="turn on debug logging", default=0)
    parser.add_argument("config_file", nargs='?', default="/etc/mqttany/mqttany.yml", metavar="CONFIG_FILE", help="path to configuration file (default '/etc/mqttany/mqttany.yml')")
    parser.add_argument("-V", "--version", action="version", version="MQTTany {}".format(__version__), help="show version and exit")
    return parser.parse_args()


if __name__ == '__main__':
    signal = SignalHook()
    args = get_args()
    if args.verbose > 1:
        logger.set_level(logger.TRACE)
    elif args.verbose > 0:
        logger.set_level(logger.DEBUG)

    mproc.current_process().name = "mqttany"
    poison_pill = False

    log.info("MQTTany {version} starting".format(version=__version__))

    if len(__version__.split("-")) > 1:
        log.warn("")
        log.warn("########  DEVELOPMENT VERSION  ########")
        log.warn("#                                     #")
        log.warn("#  This is a development version and  #")
        log.warn("#    may be incomplete or unstable    #")
        log.warn("#                                     #")
        log.warn("#######################################")
        log.warn("")

    try:
        if modules.load(args.config_file):
            while not signal.exit:
                try: # to get an item from the queue
                    message = queue.get_nowait()
                except QueueEmptyError:
                    time.sleep(0.1) # 100ms
                else:
                    poison_pill = True
                    log.debug("Received poison pill")
        else:
            poison_pill = True

    except:
        logger.log_traceback(log)
        poison_pill = True

    else:
        if signal.signal == signal.SIGINT: print() # newline after '^C'
        modules.unload()

        if poison_pill:
            log.warn("MQTTany exiting with errors")
        else:
            log.info("MQTTany stopped")

        logger.uninit()
        exit(int(poison_pill))
