'''
Reports on the status of things

'''

from ptypy.io import h5read


def report_ptypy_file(ptyr_filepath, verbose=False):

    properties = h5read(ptyr_filepath)

    if verbose:
        print properties

    return properties