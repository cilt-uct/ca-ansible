#!/usr/bin/python

# Galicaster 2.x UCT - rapidrec plugin
# Record 1 minute recordings continuously

import os
from shutil import copyfile
import time
import datetime

from galicaster.core import context
from galicaster.mediapackage import mediapackage
from galicaster.utils.i18n import _

logger = context.get_logger()

monitor_active = False

def init():

    logger.info('Start rapidrec plugin')

    global recorder, dispatcher
    dispatcher = context.get_dispatcher()
    recorder = context.get_recorder()

    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('timer-short', monitor_timer_action)
        logger.info("Registered")

    except ValueError:
        logger.info("Error")
        pass

def monitor_timer_action(sender=None):

    global monitor_active

    conf = context.get_conf()

    # Is a recording currently active?
    logger.info("Short timer tick")

    now = datetime.datetime.now()
    # print now.year, now.month, now.day, now.hour, now.minute, now.second

    logger.info("Hour=%i minute=%i", now.hour, now.minute)

    # 8am - 5pm Mon-Fri
    if (now.minute % 2) == 1:
        # Check whether to start an ad-hoc recording: is there a recording active now?
        if recorder.is_recording() == False:
	    start_rapidrec_recording()
            monitor_active = True
        else:
            logger.info("Recording active - not starting rapidrec recording")

    if (now.minute %2) == 0:
        logger.info("Checking stop")
        # Check whether to stop an ad-hoc recording
        if recorder.is_recording() and monitor_active:
	    stop_rapidrec_recording()
            monitor_active = False

def start_rapidrec_recording():

    logger.info("Start rapidrec recording")

    now = datetime.datetime.now().replace(microsecond=0)
    title = "RapidRec started at {0}".format(now.isoformat())

    # Create mediapackage
    mp = mediapackage.Mediapackage(title=title, date=now)
   
    # Start recording
    recorder.record(mp)

def stop_rapidrec_recording():

    logger.info("Stop rapidrec recording")

    # Stop recording
    recorder.stop()

