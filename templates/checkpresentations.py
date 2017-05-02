#!/usr/bin/python

# Galicaster 2.x UCT - Drop empty and/or duplicate presentation tracks before ingest
# Requires ffprobe and videomatch.pl (which requires ffmpeg and ffprobe >= 3.3)

import os
import subprocess

from galicaster.core import context
from galicaster.core import worker
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

# Presentation flavors
flavor_p1 = 'presentation/source'
flavor_p2 = 'presentation2/source'

# Threshold for considering a presentation track empty is 47.5kbps (Datapath "No signal" plus clock)
bitrate_upper_threshold = 47500
bitrate_lower_threshold = 15000

# Bitrate threshold to compare contents for similar videos is 5%
bitrate_diff_threshold = 0.05

# Similarity threshold for dropping a video is 90%
similarity_threshold = 90

# Emptiness threshold for intermediate bitrate tracks
empty_threshold = 90

# Location of ffprobe and videomatch
ffprobe_bin = 'ffprobe-3.3-static'
videomatch_bin = 'videomatch.pl'

def init():

    ffprobe_version = ''
    videomatch_version = ''

    try:
        ffprobe_version = subprocess.check_output([ffprobe_bin,'-version'])
    except:
        logger.error('Unable to run ffprobe executable: %s', ffprobe_bin)

    try:
        videomatch_version = subprocess.check_output([videomatch_bin,'-version'])
    except:
        logger.error('Unable to run videomatch executable: %s', videomatch_bin)

    if (ffprobe_version.split(' ')[0] == 'ffprobe') and (videomatch_version.split(' ')[0] == 'videomatch.pl'):

       logger.info('ffprobe version %s', ffprobe_version.split(' ')[2])
       logger.info('videomatch version %s', videomatch_version.split(' ')[2])

       try:
           dispatcher = context.get_dispatcher()
           dispatcher.connect("operation-started", drop_presentations)
           logger.info("Registered")

       except ValueError:
           logger.info("Error")
           pass

    else:
       logger.warn('ffprobe and/or videomatch not available: plugin will not run')

def drop_presentations(sender, operation_code, mp):

    # Does nothing if the operation is not INGEST
    if operation_code != worker.INGEST_CODE:
        return

    # Get the mediapackage
    mp_repo = context.get_repository()

    track_p1 = None
    track_p2 = None
    bitrate_p1 = 0
    bitrate_p2 = 0
    removed = False

    mpIdentifier = mp.getIdentifier()
    logger.info('Checking presentation tracks for MP ' + mpIdentifier)

    # Get track bitrates
    for t in mp.getTracks():

       type = t.getFlavor()
       if type == flavor_p1 or type == flavor_p2:

             # ffprobe -v error -show_entries format=bit_rate -of default=noprint_wrappers=1 presentation.avi
             # Output: "bit_rate=59565"

             ff_bitrate = subprocess.check_output([ffprobe_bin,'-v','error','-show_entries','format=bit_rate','-of',
                'default=nokey=1:noprint_wrappers=1', t.getURI()]).replace("\n", "")

             bitrate = 0

             try:
                bitrate = int(ff_bitrate)
                logger.info('bitrate for track %s: %i bps', t.getURI(), bitrate)
             except ValueError:
                # ffprobe will return "N/A" for unknown bitrate (where the file was not closed properly)
                logger.info('Unknown bitrate for track %s: %s', t.getURI(), ff_bitrate)
                bitrate = -1

             if type == flavor_p1:
                track_p1 = t
                bitrate_p1 = bitrate

             if type == flavor_p2:
                track_p2 = t
                bitrate_p2 = bitrate

    # Remove tracks with bitrate below lower threshold

    if (bitrate_p1 > 0) and (bitrate_p1 < bitrate_lower_threshold):
       mp.remove(track_p1)
       removed = True
       logger.info('Presentation track ' + os.path.basename(track_p1.getURI()) + ' is probably empty and has been removed')

    if (bitrate_p2 > 0) and (bitrate_p2 < bitrate_lower_threshold):
       mp.remove(track_p2)
       removed = True
       logger.info('Presentation track ' + os.path.basename(track_p2.getURI()) + ' is probably empty and has been removed')

    # If the bitrate is unknown or intermediate, check percentage empty

    if (bitrate_p1 < 0) or ((bitrate_p1 >= bitrate_lower_threshold) and (bitrate_p1 < bitrate_upper_threshold)):
       empty_p1 = __track_empty(track_p1)
       if (empty_p1 > empty_threshold):
          mp.remove(track_p1)
          removed = True
          logger.info('Presentation track ' + os.path.basename(track_p1.getURI()) + ' is %i%% empty and has been removed', empty_p1)

    if (bitrate_p2 < 0) or ((bitrate_p2 >= bitrate_lower_threshold) and (bitrate_p2 < bitrate_upper_threshold)):
       empty_p2 = __track_empty(track_p2)
       if (empty_p2 > empty_threshold):
          mp.remove(track_p2)
          removed = True
          logger.info('Presentation track ' + os.path.basename(track_p2.getURI()) + ' is %i%% empty and has been removed', empty_p2)

    # Check for duplicate tracks

    if (removed == False) and (bitrate_p1 > 0) and (bitrate_p2 > 0):

           logger.info('Checking whether presentation tracks are the same')
           bitrate_diff = abs(1 - bitrate_p1 / float(bitrate_p2))
           logger.info('Presentation track bitrates vary by %.3f%%', bitrate_diff * 100)

           if (bitrate_diff < bitrate_diff_threshold):
             logger.info('Presentation files have similar bitrates: comparing content')
             match_result = subprocess.check_output([videomatch_bin, track_p1.getURI(), track_p2.getURI()]).replace("\n", "")

             match_result_i = 0

             try:
                match_result_i = int(match_result)
                logger.info('Frame similarity between presentation tracks: %i%%', match_result_i)
             except ValueError:
                logger.info('Unknown frame similarity result: %s', match_result)

             if (match_result_i) > similarity_threshold:
                 logger.info('Presentation files are substantially the same (%s%%): removing %s', match_result, os.path.basename(track_p2.getURI()))
                 mp.remove(track_p2)
                 removed = True

           else:
             logger.info('Presentation files differ in bitrate, not comparing')

    # Update the MP if something changed
    if removed:
       logger.info('Updating MP ' + mpIdentifier)
       mp_repo.update(mp)

    logger.info("Finished")

# Get the percentage blank score
def __track_empty(t):

    empty_result = subprocess.check_output([videomatch_bin, '--empty', t.getURI()]).replace("\n", "")
    empty_result_i = 0

    try:
       empty_result_i = int(empty_result)
       logger.info('Presentation track %s is %i%% empty', os.path.basename(t.getURI()), empty_result_i)
    except ValueError:
       logger.info('Unknown emptiness result for track %s: %s', empty_result)

    return empty_result_i;

