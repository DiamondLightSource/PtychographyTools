'''
handles logging etc..
'''

import sys
import logging

from . import parallel

__all__ = ['logger', 'log']

# custom logging level to diplay python objects (not as detailed as debug but also not that important for info)
INSPECT = 15

CONSOLE_FORMAT = {logging.ERROR : 'ERROR %(name)s - %(message)s',
                  logging.WARNING : 'WARNING %(name)s - %(message)s',
                  logging.INFO : '%(message)s',
                  INSPECT : 'INSPECT %(message)s',
                  logging.DEBUG : 'DEBUG %(pathname)s [%(lineno)d] - %(message)s'}

FILE_FORMAT = {logging.ERROR : '%(asctime)s ERROR %(name)s - %(message)s',
                  logging.WARNING : '%(asctime)s WARNING %(name)s - %(message)s',
                  logging.INFO : '%(asctime)s %(message)s',
                  INSPECT : '%(asctime)s INSPECT %(message)s',
                  logging.DEBUG : '%(asctime)s DEBUG %(pathname)s [%(lineno)d] - %(message)s'}

# How many characters per line in console
LINEMAX = 80

# Logging filter
class MPIFilter(object):
    """
    A filter that ensures that logging is done only by the master process.
    """
    def __init__(self, allprocesses=False):
        """
        A filter that stops logging for all processes except the master node.
        This behavior can be altered with allprocesses=True.
        """
        self.allprocesses = allprocesses

    def filter(self, record):
        """
        Filter method, as expected by the logging API.
        """
        # look for an extra attribute 'allprocesses' to enable logging from all processes
        # usage: logger.info('some message',extra={'allprocesses':True})
        try:
            return record.allprocesses
        except:
            return self.allprocesses or parallel.master

# Logging formatter
class CustomFormatter(logging.Formatter):
    """
    Flexible formatting, depending on the logging level.
    Adapted from http://stackoverflow.com/questions/1343227
    Will have to be updated for python > 3.2.
    """
    DEFAULT = '%(levelname)s: %(message)s'

    def __init__(self, FORMATS=None):
        logging.Formatter.__init__(self)
        self.FORMATS = {} if FORMATS is None else FORMATS

    def format(self, record):
        self._fmt = self.FORMATS.get(record.levelno, self.DEFAULT)
        return logging.Formatter.format(self, record)

# Create logger
logger = logging.getLogger()

# Default level - should be changed as soon as possible
logger.setLevel(logging.WARNING)

# Create console handler
consolehandler = logging.StreamHandler(stream = sys.stdout)
logger.addHandler(consolehandler)

# Add formatter
consoleformatter = CustomFormatter(CONSOLE_FORMAT)
consolehandler.setFormatter(consoleformatter)

# Add filter
consolefilter = MPIFilter()
logger.addFilter(consolefilter)

level_from_verbosity = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARN, 3:logging.INFO, 4: INSPECT, 5:logging.DEBUG}
level_from_string = {'CRITICAL':logging.CRITICAL, 'ERROR':logging.ERROR, 'WARN':logging.WARN, 'WARNING':logging.WARN, 'INFO':logging.INFO, 'INSPECT': INSPECT, 'DEBUG':logging.DEBUG}
vlevel_from_logging = dict([(v,k) for k,v in level_from_verbosity.items()])
slevel_from_logging = dict([(v,k) for k,v in level_from_string.items()])

def log(level,msg,parallel=False):
    if not parallel:
        logger.log(level_from_verbosity[level], msg)
    else:
        logger.log(level_from_verbosity[level], msg, extra={'allprocesses':True})

