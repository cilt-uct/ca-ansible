#!/usr/bin/python

# Galicaster 2.x UCT

import os
import subprocess

from galicaster.core import context
from galicaster.core import worker
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

def init():
    logger.info("Start pcheck plugin")

    ffprobe_version = subprocess.check_output(['ffprobe','-version'])

    if (ffprobe_version.split(' ')[0] == 'ffprobe'):

       logger.info('ffprobe version %s', ffprobe_version.split(' ')[2])

       try:
           dispatcher = context.get_dispatcher()
           dispatcher.connect("operation-started", drop_presentations)
           logger.info("Registered")

       except ValueError:
           logger.info("Error")
           pass

    else:
       logger.error('ffprobe not installed')
	
def drop_presentations(sender, operation_code, mp):

    # Does nothing if the operation is not INGEST 
    if operation_code != worker.INGEST_CODE: 
        return

    flavor_p1 = 'presentation/source'
    flavor_p2 = 'presentation2/source'

    # Threshold for considering a presentation track empty is 47.5kbps (Datapath "No signal" plus clock)
    bitrate_threshold = 47500

    # Bitrate threshold to compare contents for similar videos is 5%
    bitrate_diff_threshold = 0.05

    # Similarity threshold for dropping a video is 90%
    similarity_threshold = 90

    # Get the mediapackage
    mp_repo = context.get_repository()

    track_p1 = None
    track_p2 = None
    bitrate_p1 = 0
    bitrate_p2 = 0
    removed = False

    mpIdentifier = mp.getIdentifier()
    logger.info('Checking presentation tracks for MP ' + mpIdentifier)

    # Remove any empty tracks
    for t in mp.getTracks():

           type = t.getFlavor()

           if type == flavor_p1 or type == flavor_p2:

             # ffprobe -v error -show_entries format=bit_rate -of default=noprint_wrappers=1 presentation.avi
             # Output: "bit_rate=59565"

             ff_bitrate = subprocess.check_output(['ffprobe','-v', 'error','-show_entries','format=bit_rate','-of',
                'default=nokey=1:noprint_wrappers=1', t.getURI()]).replace("\n", "")

             bitrate = 0

             try:
                bitrate = int(ff_bitrate)
                logger.info('bitrate for track %s: %i bps', t.getURI(), bitrate)
             except ValueError:
                # ffprobe will return "N/A" for unknown bitrate (where the file was not closed properly)
                logger.info('Unknown bitrate for track %s: %s', t.getURI(), ff_bitrate)

             if type == flavor_p1:
                track_p1 = t
                bitrate_p1 = bitrate

             if type == flavor_p2:
                track_p2 = t
                bitrate_p2 = bitrate

             if (bitrate > 0) and (bitrate < bitrate_threshold):
                mp.remove(t)
                mp_repo.update(mp);
                removed = True
                logger.info('Presentation file ' + os.path.basename(t.getURI()) + ' is probably empty - removed')

    # Check for duplicate tracks
    if (removed == False) and (bitrate_p1 > 0) and (bitrate_p2 > 0):

           logger.info('Checking whether presentation tracks are the same')
           bitrate_diff = abs(1 - bitrate_p1 / float(bitrate_p2))
           logger.info('Bitrates vary by %.3f%%', bitrate_diff * 100)

           if (bitrate_diff < bitrate_diff_threshold):
             logger.info('Presentation files have similar bitrates: comparing content')
             match_result = subprocess.check_output(['/home/galicaster/videomatch.pl', track_p1.getURI(), track_p2.getURI()])

             match_result_i = 0

             try:
                match_result_i = int(match_result)
                logger.info('Frame Similarity: %i%%', match_result_i)
             except ValueError:
                logger.info('Unknown frame similarity result: %s', match_result)

             if (match_result_i) > similarity_threshold:
                 logger.info('Presentation files are substantially the same (%s%%): removing %s', match_result, os.path.basename(track_p2.getURI()))
                 mp.remove(track_p2)
                 mp_repo.update(mp)

           else:
             logger.info('Presentation files differ in bitrate, not comparing')

    logger.info("Finished")

