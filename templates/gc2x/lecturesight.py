#!/usr/bin/python

# Galicaster 2.x UCT - LectureSight plugin
# Adds metrics-*.json file as a mediapackage attachment

import os
import sys
from shutil import copyfile
import telnetlib
import time

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

def init():

    global lsPath, metricsTargetName
    lsPath = '/opt/ls/metrics'

    if not os.path.exists(lsPath):
	logger.info("LectureSight not installed, or metrics not enabled")
	return

    # Target name for the json file in the mediapackage
    metricsTargetName = 'lecturesight-metrics.json'

    logger.info('Start LectureSight plugin: recording metrics from ' + lsPath)

    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('recorder-started', lecturesight_start)
        dispatcher.connect('recorder-stopped', add_lecturesight_metrics)
        logger.info("Registered")

    except ValueError:
        logger.info("Error")
        pass

def lecturesight_start(self, mpIdentifier):

    # Is this a scheduled or ad-hoc recording?
    mp_list = context.get_repository()
    mp = mp_list.get(mpIdentifier)

    if mp is None:
        logger.info('Unscheduled recording started: ' + mpIdentifier)

	# Start Lecturesight
        tn = telnetlib.Telnet("localhost", 2501)
        tn.read_until("g!")
        tn.write("scheduler:start\n")
        time.sleep(1)
        tn.close()
    else:
        logger.info('Scheduled recording started: ' + mp.getTitle() + ' (' + mpIdentifier + ')')
        # No need to start Lecturesight as it would have started from the iCal entry

def add_lecturesight_metrics(self, mpIdentifier):
    tmp = None
    done = False

    mp_list = context.get_repository()
    mp = mp_list.get(mpIdentifier)

    logger.info('Recording stopped: ' + mp.getTitle() + ' (' + mpIdentifier + ')')

    # Stop Lecturesight if it's a manual recording
    if "Recording started at" in mp.getTitle():
        tn = telnetlib.Telnet("localhost", 2501)
        tn.read_until("g!")
        tn.write("scheduler:stop\n")
        time.sleep(1)
        tn.close()

    # Give Lecturesight time to write out the file
    time.sleep(3)

    # First look for a file that has the ID in it
    metricsFile = lsPath + '/metrics-' + mpIdentifier + '.json'

    # if not os.path.isfile(metricsFile):
    #    metricsFile = lsPath + '/metrics.json'

    if not os.path.isfile(metricsFile):
        logger.info("No metrics file found for event " + mpIdentifier)
        return

    metricsMpFile = mp.getURI() + '/' + metricsTargetName

    logger.info('Importing metrics from ' + metricsFile + ' to ' + metricsMpFile + ' for mediapackage ' + mpIdentifier)
    copyfile(metricsFile, metricsMpFile)

    mp.add(metricsMpFile, flavor='lecturesight/metrics', etype=mediapackage.TYPE_ATTACHMENT, identifier='lecturesight', mime='application/json', tags=["metrics"])
    mp_list.update(mp)

    logger.info("Finished")

