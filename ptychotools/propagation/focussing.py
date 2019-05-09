'''

Focussing related tools

'''


import numpy as np
from ptypy.core import Base, geometry
import ptypy.utils as u
from scipy import constants as const


def propagate_probe(probe, psize, energy, distance, zrange, NPTS=1024):
    '''
    generates an array that describes the complex propagated probe array.
    :param probe: The 2D numpy array containing the complex valued probe that we are to propagate,
    :param psize: The real pixel size of this probe in metres.
    :param energy: The energy of the probe in keV.
    :param distance: the distance to the measurement detector (why do we need this?).
    :param zrange: A tuple (zmin, zmax) of the distance we plan to propagate the probe over.
    :param NPTS: The number of z positions we want to evaluate the probe at. Default: 1024.
    :return: (propagated_projection, xaxis, yaxis, zaxis)
        propagated_projection: a 3D complex valued numpy array of the propagated probe.
        xaxis, yaxis, zaxis, the relative axes for the array
    '''
    xsize, ysize = probe.shape

    xaxis = ((np.arange(xsize) - xsize // 2) * psize[0])
    yaxis = ((np.arange(ysize) - ysize // 2) * psize[0])
    zaxis = np.linspace(zrange[0], zrange[1], NPTS)
    outshape = (len(zaxis),) + probe.shape

    propagated_projections = np.empty(outshape, dtype=np.complex)
    P = Base()
    g = u.Param()
    g.energy = None
    g.lam = const.h * const.c / (const.e * energy * 1e3)
    g.distance = distance
    g.psize = psize
    g.shape = xsize
    g.propagation = "nearfield"

    for idx, z in enumerate(zaxis):
        if (z==0.0):
            propagated_projections[idx] = probe
        else:
            g.distance = z
            G = geometry.Geo(owner=P, pars=g)
            propagated_projections[idx] = G.propagator.bw(probe)
    return propagated_projections, zaxis, yaxis, xaxis

