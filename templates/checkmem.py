# -*- coding:utf-8 -*-
# Galicaster 2.x plugin
#
#       galicaster/plugins/checkmem
#

"""

"""

import resource

from galicaster.core import context

conf = None
minfree = None
logger = None
repo = None
ocservice = None

def init():
    global minfree, logger, repo, ocservice, dispatcher

    conf = context.get_conf()
    dispatcher = context.get_dispatcher()
    repo = context.get_repository()
    logger = context.get_logger()
    ocservice = context.get_ocservice()

    logger.info("Logging process memory use")
    dispatcher.connect('timer-long', check_mem)

def check_mem(sender=None):

    # Get process memory
    resmem = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    logger.info("Process memory size (max RSS): {} MB".format(resmem))


