#!/usr/bin/python

# Galicaster 2.x UCT

import os
import subprocess

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

def init():
    logger.info("Start dropemptypresentations plugin")

    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('recorder-stopped', dropempty_presentations)
        logger.info("Registered")

    except ValueError:
        logger.info("Error")
        pass
	
def dropempty_presentations(self, mpIdentifier):
    flavor = 'presentation/source'
    tmp = None
    done = False

    bitrate_threshold = 100

    # Get the mediapackage
    mp_list = context.get_repository()
    mp = mp_list.get(mpIdentifier)

    if mp is None:
        logger.info('Mediapackage not found: ' + mpIdentifier)
    else:
        logger.info('Checking tracks of mp ' + mpIdentifier)
        done = True

        for t in mp.getTracks():
           type = t.getFlavor()

           if type == 'presentation/source':

             # ffprobe -v error -show_entries format=bit_rate -of default=noprint_wrappers=1 ./gc_menz11_20170403T12h36m23/presentation.avi
             # Output: "bit_rate=59565"

             ff_bitrate = subprocess.check_output(['ffprobe','-v', 'error','-show_entries','format=bit_rate','-of','default=noprint_wrappers=1', t.getURI()])
             bitrate = int(ff_bitrate.split('=')[1])

             logger.info('Bitrate for track %s is %i bps', t.getURI(), bitrate)

             if (bitrate < bitrate_threshold):
                mp.remove(t)
                mp_list.update(mp);
                logger.info('Presentation file: ' + os.path.basename(t.getURI()) + ' is probably empty - removed')

    logger.info("Finished")

