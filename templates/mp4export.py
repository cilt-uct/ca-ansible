#!/usr/bin/python

# Galicaster 2.x UCT - Create MP4 file for immediate use after ingest.


import os
import subprocess
import datetime

from galicaster.core import context
from galicaster.core import worker
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

# Source flavor
src_flavor = 'presenter/source'

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
           dispatcher.connect("operation-started", mp4_export)
           logger.info("Registered")

       except ValueError:
           logger.info("Error")
           pass

    else:
       logger.warn('ffmpeg not available: plugin will not run')

def mp4_export(sender, operation_code, mp):

    # Does nothing if the operation is not INGEST
    if operation_code != worker.INGEST_CODE:
        return

    myhost = os.uname()[1]
    current_date = datetime.datetime.today().strftime ('%Y%m%d-%H%M')

    # Get the mediapackage
    mp_repo = context.get_repository()
    export_file = os.path.join(mp.getURI(), '{}-{}.mp4'.format(myhost, current_date))

    logger.info('Exporting MP4 for MP {}'.format(mp.getIdentifier()))

    # Loop through the tracks
    for t in mp.getTracks():

        type = t.getFlavor()

        logger.info('   Checking {0}'.format(type))
        if type == src_flavor:
            working_file = t.getURI()

            logger.info('   working_file {}'.format(working_file))
            logger.info('    export_file {}'.format(export_file))

            # Do the encoding
            result = __execute_command([ffmpeg_bin, '-y', '-i', working_file, '-ss', '1', '-c:v', 'copy', '-c:a', 'copy', export_file ])
            #result = __execute_command([ffmpeg_bin, '-y', '-i', working_file, '-c:v', 'copy', '-c:a', 'copy', export_file ])
            if (result[0] == "ERR"):
                logger.error("Error encoding")
            else:
                logger.error("Success encoding")

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

    #logger.info('    CMD:{}\n\nOUT:{}\n\nALT:{}\n\nRC:{}\n\n'.format(command, output, alt, rc))
    return [output, alt]
