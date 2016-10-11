# -*- coding:utf-8 -*-
# Galicaster 2.x plugin
#
#       galicaster/plugins/checkspace
#

"""

"""
from galicaster.core import context
from galicaster.recorder.service import ERROR_STATUS
from galicaster.recorder.service import PREVIEW_STATUS

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

    minfree = None
    try:
        minfree = int(conf.get('checkspace', 'minfreespace'))
    except Exception as exc:
        raise Exception("Wrong parameter minfreespace: {}".format(exc))

    if minfree:
        logger.info("Parameter 'minfreespace' set to {} GB".format(minfree))
        dispatcher.connect('timer-nightly', check_space)
        dispatcher.connect('recorder-status', check_space_status)

        oninit = conf.get('checkspace', 'checkoninit')
        if oninit in ["True", "true"]:
            check_space(None)
    else:
        raise Exception("Parameter minfreespace not configured")

def check_space_status(sender, status):

    if status == PREVIEW_STATUS:
	    # Get free space in GB
	    freespace = repo.get_free_space() / (1024*1024*1024)
	    if (freespace < minfree):
	        logger.warning("Low repository space: repo has {} GB free space available". format(freespace))

def check_space(sender=None):

    # Get free space in GB
    logger.info("Checking for minimum {} GB free space".format(minfree))
    freespace = repo.get_free_space() / (1024*1024*1024)

    logger.info("Repository has {} GB free space available". format(freespace))

    if (freespace < minfree):
        logger.warning("Free space available in repository is less than minimum required")

