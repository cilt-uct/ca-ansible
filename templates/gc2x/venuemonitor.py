#!/usr/bin/python

# Galicaster 2.x UCT - venuemonitor plugin
# Automated unscheduled recordings based on day/time pattern

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

    logger.info('Start venuemonitor plugin')

    global recorder, dispatcher
    dispatcher = context.get_dispatcher()
    recorder = context.get_recorder()

    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('timer-long', monitor_timer_action)
        logger.info("Registered")

    except ValueError:
        logger.info("Error")
        pass

def monitor_timer_action(sender=None):

    global monitor_active

    conf = context.get_conf()

    # Is a recording currently active?
    logger.info("Long timer tick")

    now = datetime.datetime.now()
    # print now.year, now.month, now.day, now.hour, now.minute, now.second

    logger.info("Hour=%i minute=%i", now.hour, now.minute)

    # TODO - Consult timetable for scheduled events

    # 8am - 5pm Mon-Fri
    if (now.hour >= 8) and (now.hour <= 16) and (now.minute == 01) and (datetime.datetime.today().weekday() < 6):
        # Check whether to start an ad-hoc recording: is there a recording active now?
        if recorder.is_recording() == False:
	    start_venuemonitor_recording()
            monitor_active = True
        else:
            logger.info("Recording active - not starting venuemonitor recording")

    if (now.hour >= 8) and (now.hour <= 16) and (now.minute == 58):
        logger.info("Checking stop")
        # Check whether to stop an ad-hoc recording
        if recorder.is_recording() and monitor_active:
	    stop_venuemonitor_recording()
            monitor_active = False

def start_venuemonitor_recording():

    logger.info("Start venuemonitor recording")

    now = datetime.datetime.now().replace(microsecond=0)
    title = "Venue monitoring started at {0}".format(now.isoformat())

    # Create mediapackage
    mp = mediapackage.Mediapackage(title=title, date=now)
   
    # Start recording
    recorder.record(mp)

def stop_venuemonitor_recording():

    logger.info("Stop venuemonitor recording")

    # Stop recording
    recorder.stop()

    # TODO - drop everything except the video (presenter)

