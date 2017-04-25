#!/usr/bin/python

# Galicaster 2.x UCT

import os
import subprocess

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

def init():
    logger.info("Start dropemptypresentations plugin")

    ffprobe_version = subprocess.check_output(['ffprobe','-version'])

    if (ffprobe_version.split(' ')[0] == 'ffprobe'):

       logger.info('ffprobe version %s', ffprobe_version.split(' ')[2])

       try:
           dispatcher = context.get_dispatcher()
           dispatcher.connect('recorder-stopped', dropempty_presentations)
           logger.info("Registered")

       except ValueError:
           logger.info("Error")
           pass

    else:
       logger.error('ffprobe not installed')
	
def dropempty_presentations(self, mpIdentifier):

    flavor_p1 = 'presentation/source'
    flavor_p2 = 'presentation2/source'

    # Threshold for considering a presentation track empty is 47.5kbps (Datapath "No signal" plus clock)
    bitrate_threshold = 47500

    # Get the mediapackage
    mp_list = context.get_repository()
    mp = mp_list.get(mpIdentifier)

    if mp is None:
        logger.info('Mediapackage not found: ' + mpIdentifier)
    else:
        logger.info('Checking tracks of mp ' + mpIdentifier)

        for t in mp.getTracks():

           type = t.getFlavor()

           if type == flavor_p1 or type == flavor_p2:

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

