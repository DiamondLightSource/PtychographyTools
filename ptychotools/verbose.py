'''
Contains everything to do with logging
'''

import logging
FORMAT = '%(asctime)s:%(message)s'
logging.basicConfig(format=FORMAT)

logger = logging.getLogger('ptychotools')
