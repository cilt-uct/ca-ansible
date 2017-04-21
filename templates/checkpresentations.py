#!/usr/bin/python

# Galicaster 2.x UCT

import os

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

def init():
    logger.info("Start checkpresentations plugin")
    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('recorder-stopped', check_presentations)
        logger.info("Registered")

    except ValueError:
        logger.info("Error")
        pass

def check_presentations(self, mpIdentifier):
    flavor_p1 = 'presentation/source'
    flavor_p2 = 'presentation2/source'
    tmp = None
    done = False

    logger.info('Checking presentation tracks in mediapackage identifier ' + mpIdentifier)

    mp_list = context.get_repository()

    for uid,mp in mp_list.iteritems():
 
        if mp.getIdentifier() == mpIdentifier:

            for t in mp.getTracks():
               type = t.getFlavor()

               if type == flavor_p1 or type == flavor_p2:

                 if tmp is None :
                    tmp = t

                 elif os.path.getsize(tmp.getURI()) > os.path.getsize(t.getURI()):
                    mp.remove(t)
                    mp_list.update(mp);
                    logger.info('Presentation file: ' + os.path.basename(t.getURI()) + ' removed')
                    done = True
                    break

                 else:
                    mp.remove(tmp)
                    mp_list.update(mp);
                    logger.info('Presentation file: ' + os.path.basename(tmp.getURI()) + ' removed')
                    done = True
                    break

        if done == True:
	    break

    logger.info("Finished")

