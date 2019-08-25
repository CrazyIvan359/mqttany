"""
MQTTany
"""

import signal, time, sys
import multiprocessing as mproc
from queue import Empty as QueueEmptyError

import logger, modules
log = logger.get_logger()

queue = mproc.Queue()

class GracefulKiller:
    """ handles SIGINT and SIGTERM """
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True



if __name__ == '__main__':
    killer = GracefulKiller()
    poison_pill = False

    if len(sys.argv)>1 and sys.argv[1] == "-v":
        logger.set_level(logger.DEBUG)

    log.info("MQTTany starting")
    if not modules.load(): exit(1)

    while not killer.kill_now:
        try: # to get an item from the queue
            message = queue.get_nowait()
        except QueueEmptyError:
            time.sleep(0.1) # 100ms
        else:
            poison_pill = True
            log.debug("Received poison pill")

    log.info("MQTTany stopping")
    modules.unload()
    exit(1 if poison_pill else 0)
