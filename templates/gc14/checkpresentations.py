#!/usr/bin/python

import os

from galicaster.core import context
from galicaster.mediapackage import mediapackage

logger = context.get_logger()

def init():
    try:
        dispatcher = context.get_dispatcher()
        dispatcher.connect('recording-closed', check_presentations)

    except ValueError:
        pass

def check_presentations(self, mpUri):
    flavor = 'presentation/source'
    tmp = None

    mp_list = context.get_repository()
    for uid,mp in mp_list.iteritems():
        if mp.getURI() == mpUri:

            for t in mp.getTracks():
               type = t.getFlavor()
               if type == 'presentation/source':

                 if tmp is None :
                    tmp = t

                 elif os.path.getsize(tmp.getURI()) > os.path.getsize(t.getURI()):
                    mp.remove(t)
                    logger.info('Presentation file: ' + os.path.basename(t.getURI()) + ' removed')
                    break

                 else:
                    mp.remove(tmp)
                    logger.info('Presentation file: ' + os.path.basename(tmp.getURI()) + ' removed')
                    break

