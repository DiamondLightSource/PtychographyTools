'''

'''

import os




def test_json_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "resource/test.json")


def test_yaml_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "resource/test.yml")


def generate_test_param_tree():
    '''
    essential minimal prep and run. Contains enough variety to test things
    '''
    from ptypy import utils as u
    paramtree = u.Param()

    # for verbose output
    paramtree.verbose_level = 3

    # set home path
    paramtree.io = u.Param()
    paramtree.io.home = "/tmp/ptypy/"
    paramtree.io.autosave = u.Param(active=False)

    # max 200 frames (128x128px) of diffraction data
    paramtree.scans = u.Param()
    paramtree.scans.MF = u.Param()
    # now you have to specify which ScanModel to use with scans.XX.name,
    # just as you have to give 'name' for engines and PtyScan subclasses.
    paramtree.scans.MF.name = 'BlockVanilla' # or 'Full'
    paramtree.scans.MF.data= u.Param()
    paramtree.scans.MF.data.name = 'MoonFlowerScan'
    paramtree.scans.MF.data.shape = 128
    paramtree.scans.MF.data.num_frames = 200
    paramtree.scans.MF.data.save = None

    # position distance in fraction of illumination frame
    paramtree.scans.MF.data.density = 0.2
    # total number of photon in empty beam
    paramtree.scans.MF.data.photons = 1e8
    # Gaussian FWHM of possible detector blurring
    paramtree.scans.MF.data.psf = 0.

    # attach a reconstrucion engine
    paramtree.engines = u.Param()
    paramtree.engines.engine00 = u.Param()
    paramtree.engines.engine00.name = 'DM'
    paramtree.engines.engine00.numiter = 80
    return paramtree
