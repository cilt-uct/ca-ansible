#!/usr/bin/python

# Galicaster 2.x UCT - Analyse audio and select best track before ingest

import os
import subprocess
import re

from galicaster.core import context
from galicaster.core import worker
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

# Audio flavor
audio_flavor = 'presenter/source'

# Threshold for max volume
threshold_max_volume = -50

# Threshold for mean volume
threshold_mean_volume = -50

# Location of ffmpeg
ffmpeg_bin = 'ffmpeg-3.3-static'

def init():

    ffmpeg_version = ''

    try:
        ffmpeg_version = subprocess.check_output([ffmpeg_bin,'-version'])
    except:
        logger.error('Unable to run ffmpeg executable: %s', ffmpeg_bin)

    if (ffmpeg_version.split(' ')[0] == 'ffmpeg'):

       logger.info('ffmpeg version %s', ffmpeg_version.split(' ')[2])

       try:
           dispatcher = context.get_dispatcher()
           dispatcher.connect("operation-started", check_channels)
           logger.info("Registered")

       except ValueError:
           logger.info("Error")
           pass

    else:
       logger.warn('ffmpeg not available: plugin will not run')

def check_channels(sender, operation_code, mp):

    global threshold_max_volume, threshold_mean_volume

    # Does nothing if the operation is not INGEST
    if operation_code != worker.INGEST_CODE:
        return

    # Get the mediapackage
    mp_repo = context.get_repository()

    changed_mp = False
    working_track = None
    volume_left = dict({ "max" : -100, "mean" : -100})
    volume_right = dict({ "max" : -100, "mean" : -100})

    mpIdentifier = mp.getIdentifier()
    new_presenter = os.path.join(mp.getURI(),"new_presenter.mkv")

    logger.info('Checking audio channels tracks for MP {}'.format(mpIdentifier))

    # Loop through the tracks
    for t in mp.getTracks():

        type = t.getFlavor()

        logger.info('   Checking {0}'.format(type))
        if type == audio_flavor:
            working_track = t
            working_file = t.getURI()
            working_file_duration = t.getDuration()

            logger.info('   working_file {}'.format(t.getURI()))

            # get Left Channel Details > volume_left
            volume_left = __detect_channel_volume(working_file, "FL")
            logger.info('   volume_left {}|{}|{}|'.format(volume_left, threshold_mean_volume, threshold_max_volume))

            # get Right Channel Details > volume_right
            volume_right = __detect_channel_volume(working_file, "FR")
            logger.info('   volume_right {}|{}|{}|'.format(volume_right, threshold_mean_volume, threshold_max_volume))

            if (volume_left['mean'] < threshold_mean_volume) and (volume_right['mean'] < threshold_mean_volume):
                changed_mp = False # do nothing :D
                logger.info("do nothing")

            elif (volume_left['mean'] < threshold_mean_volume):
                # create new presenter with right Channel
                logger.info('Left channel {} is below  {}, using Right channel'.format(volume_left['mean'], threshold_mean_volume))
                result = __execute_command([ffmpeg_bin, '-y', '-i', working_file, '-af', 'pan=mono|c0=FR', '-vc', 'copy', new_presenter ])
                if (result[0] == "ERR"):
                    logger.error("Error right channel")
                    changed_mp = False
                else:
                    changed_mp = True
                    mp.remove(working_track, True) # remove old one first
                    mp.add(new_presenter, mediapackage.TYPE_TRACK, flavor="presenter/source", mime="video/mkv", duration=working_file_duration)

            elif (volume_right['mean'] < threshold_mean_volume):
                # create new presenter with left Channel
                logger.info('Right channel {} is below  {}, using Left channel'.format(volume_right['mean'], threshold_mean_volume))
                result = __execute_command([ffmpeg_bin, '-y', '-i', working_file, '-af', 'pan=mono|c0=FL', '-vc', 'copy', new_presenter ])
                if (result[0] == "ERR"):
                    logger.error("Error left channel")
                    changed_mp = False
                else:
                    changed_mp = True
                    mp.remove(working_track, True) # remove old one first
                    mp.add(new_presenter, mediapackage.TYPE_TRACK, flavor="presenter/source", mime="video/mkv", duration=working_file_duration)

            # else:
            #     logger.info("create presenter, new audio for left and other for right")
            #
            #     success = True
            #     new_audio = os.path.join(mp.getURI(),"new_audio.flac")
            #     other_audio = os.path.join(mp.getURI(),"other_audio.flac")
            #
            #     # create 3 tracks so that the muxing workflow can be used to select the correct audio
            #     result = __execute_command([ffmpeg_bin, '-y', '-i', working_file, '-an', '-vc', 'copy', new_presenter ])
            #     if (result[0] == "ERR"):
            #         logger.error("Error presenter")
            #         success = False
            #     else:
            #         mp.add(new_presenter, mediapackage.TYPE_TRACK, flavor="presenter/source", mime="video/mkv", duration=working_file_duration)
            #
            #     result = __execute_command([ffmpeg_bin, '-y', '-i', working_file, '-vn', '-af', 'pan=mono|c0=FL', new_audio ])
            #     if (result[0] == "ERR"):
            #         logger.error("Error audio")
            #         success = False
            #     else:
            #         mp.add(new_audio, mediapackage.TYPE_TRACK, flavor="presenter/source", mime="audio/flac", duration=working_file_duration)
            #
            #     result = __execute_command([ffmpeg_bin, '-y', '-i', working_file, '-vn', '-af', 'pan=mono|c0=FR', other_audio ])
            #     if (result[0] == "ERR"):
            #         logger.error("Error other audio")
            #         success = False
            #     else:
            #         mp.add(other_audio, mediapackage.TYPE_TRACK, flavor="other/audio", mime="audio/flac", duration=working_file_duration)
            #
            #     changed_mp = success
            #     if success:
            #        mp.remove(working_track, True) # remove old one first
            #        logger.info('Constructing new presenter, audio and other')

            # Update the MP if something changed
            if changed_mp:
               logger.info('Updating MP {}'.format(mpIdentifier))
               mp.add(working_file, mediapackage.TYPE_TRACK, flavor="other/video", mime="video/mkv", duration=working_file_duration) # original stereo is preserved and ingested
               mp_repo.update(mp)

    logger.info("Finished")


def __execute_command(command):
    output = ""
    alt = ""
    rc = 99

    # logger.info('    {}'.format(command))
    try:
        child = subprocess.Popen(
                            command, universal_newlines=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, alt = child.communicate()
        rc = child.returncode
        # Check alt for failure
        if rc == 1:
            output = "ERR"

    except ValueError:
        logger.info('Unknown emptiness result for track {}'.format(command[3]))
        output = "ERR"

    except subprocess.CalledProcessError:
        logger.info('{} error for {}'.format(command[0], command[3]))
        output = "ERR"

#    logger.info('    CMD:{}\n\nOUT:{}\n\nALT:{}\n\nRC:{}\n\n'.format(command, output, alt, rc))
    return [output, alt]


def __extract(s):
    m = re.search('\] (.*)_volume: (.+?) dB', s)
    if m:
        return { m.group(1): m.group(2) }
    return ''

# Get the max and mean for a channel
def __detect_channel_volume(track, channel):

    result = dict({ "max" : -100, "mean" : -100})

    command = [ffmpeg_bin, '-hide_banner', '-i', track,'-af','pan=mono|c0={},volumedetect'.format(channel),'-vn','-f','null','-']
    ar  = __execute_command(command)

    # OUTPUT = ar[0]
    # ALT    = ar[1]
    if (ar[0] == "") and (ar[1] != ""):
         regex = re.compile(r'mean_volume|max_volume')
         o2 = filter(regex.search, [s.strip() for s in ar[1].splitlines()])
         if (len(o2) > 0):
             a = map(lambda x: __extract(x), o2)
             a[0].update(a[1])
             result = a[0]

    for keys in result:
        result[keys] = float(result[keys])

    logger.info('   __detect_channel_volume {}'.format(result))
    return result;
