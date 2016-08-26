#!/usr/bin/python

# Galicaster 2.x UCT - LectureSight plugin
# Adds metrics-*.json file as a mediapackage attachment

import os
from shutil import copyfile
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
        dispatcher.connect('recorder-started', clear_lecturesight_metrics)
        dispatcher.connect('recorder-stopped', add_lecturesight_metrics)
        logger.info("Registered")

    except ValueError:
        logger.info("Error")
        pass

def clear_lecturesight_metrics(self, mpIdentifier):

    # Don't need to do anything here for now
    logger.info('Recording started: ' + mpIdentifier)

def add_lecturesight_metrics(self, mpIdentifier):
    tmp = None
    done = False

    # Give Lecturesight time to write out the file
    time.sleep(3)

    # First look for a file that has the ID in it
    metricsFile = lsPath + '/metrics-' + mpIdentifier + '.json'

    # if not os.path.isfile(metricsFile):
    #    metricsFile = lsPath + '/metrics.json'

    if not os.path.isfile(metricsFile):
        logger.info("No metrics file found for event " + mpIdentifier)
        return

    mp_list = context.get_repository()
    mp = mp_list.get(mpIdentifier)

    metricsMpFile = mp.getURI() + '/' + metricsTargetName

    logger.info('Importing metrics from ' + metricsFile + ' to ' + metricsMpFile + ' for mediapackage ' + mpIdentifier)
    copyfile(metricsFile, metricsMpFile)

    mp.add(metricsMpFile, flavor='lecturesight/metrics', etype=mediapackage.TYPE_ATTACHMENT, identifier='lecturesight', mime='application/json', tags=["metrics"])
    mp_list.update(mp)

    logger.info("Finished")

