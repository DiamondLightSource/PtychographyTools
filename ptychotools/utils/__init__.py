'''
need to test for the ptypy import here
'''

try:
    from ptypy.utils.verbose import log
    from ptypy.utils import parallel
except ImportError as e:
    print("Couldn't import ptypy verbose or parallel. Exception was %s. Falling back to ptychotools modules" % e)
    from verbose import log
    import parallel

