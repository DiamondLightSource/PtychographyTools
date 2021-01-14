# -*- coding: utf-8 -*-
"""
Difference Map reconstruction engine that uses GLAD CUDA library.

This engine was extracted from PtyPy package.
"""

import time

from ptypy.utils import parallel
from ptypy.engines import register
from ptypy import defaults_tree
from ptypy.core.manager import Full, Vanilla, BlockFull, BlockVanilla
from glad.cuda.constraints import difference_map_fourier_constraint, difference_map_overlap_update
from glad.cuda import FLOAT_TYPE
from .DM_glad_array import DM_glad_array

import numpy as np

__all__ = ['DM_glad_cuda']


def difference_map_iterator(diffraction, obj, object_weights, cfact_object, mask, probe, cfact_probe, probe_support,
                            probe_weights, exit_wave, addr, pre_fft, post_fft, pbound, overlap_max_iterations, update_object_first,
                            obj_smooth_std, overlap_converge_factor, probe_center_tol, probe_update_start, alpha=1,
                            clip_object=None, LL_error=False, num_iterations=1):
    curiter = 0
    errors = np.zeros((num_iterations, 3, len(diffraction)), dtype=FLOAT_TYPE)
    for it in range(num_iterations):
        if (((it+1) % 10) == 0) and (it>0):
            print("iteration:%s" % (it+1)) 
        errors[it] = difference_map_fourier_constraint(mask,
                                                   diffraction,
                                                   obj,
                                                   probe,
                                                   exit_wave,
                                                   addr,
                                                   prefilter=pre_fft,
                                                   postfilter=post_fft,
                                                   pbound=pbound,
                                                   alpha=alpha,
                                                   LL_error=LL_error)
        do_update_probe = (probe_update_start <= curiter)
        difference_map_overlap_update(addr,
                                      cfact_object,
                                      cfact_probe,
                                      do_update_probe,
                                      exit_wave,
                                      obj,
                                      object_weights,
                                      probe,
                                      probe_support,
                                      probe_weights,
                                      overlap_max_iterations,
                                      update_object_first,
                                      obj_smooth_std,
                                      overlap_converge_factor,
                                      probe_center_tol,
                                      clip_object=clip_object)
        curiter += 1
    return errors

@register()
class DM_glad_cuda(DM_glad_array):
    """
    A full-fledged Difference Map engine that uses numpy arrays instead of iteration.


    Defaults:

    [name]
    default = DM_glad_cuda
    type = str
    help =
    doc =

    [alpha]
    default = 1
    type = float
    lowlim = 0.0
    help = Difference map parameter

    [probe_update_start]
    default = 2
    type = int
    lowlim = 0
    help = Number of iterations before probe update starts

    [subpix_start]
    default = 0
    type = int
    lowlim = 0
    help = Number of iterations before starting subpixel interpolation

    [subpix]
    default = 'linear'
    type = str
    help = Subpixel interpolation; 'fourier','linear' or None for no interpolation

    [update_object_first]
    default = True
    type = bool
    help = If True update object before probe

    [overlap_converge_factor]
    default = 0.05
    type = float
    lowlim = 0.0
    help = Threshold for interruption of the inner overlap loop
    doc = The inner overlap loop refines the probe and the object simultaneously. This loop is escaped as soon as the overall change in probe, relative to the first iteration, is less than this value.

    [overlap_max_iterations]
    default = 10
    type = int
    lowlim = 1
    help = Maximum of iterations for the overlap constraint inner loop

    [probe_inertia]
    default = 1e-9
    type = float
    lowlim = 0.0
    help = Weight of the current probe estimate in the update

    [object_inertia]
    default = 1e-4
    type = float
    lowlim = 0.0
    help = Weight of the current object in the update

    [fourier_relax_factor]
    default = 0.05
    type = float
    lowlim = 0.0
    help = If rms error of model vs diffraction data is smaller than this fraction, Fourier constraint is met
    doc = Set this value higher for noisy data.

    [obj_smooth_std]
    default = None
    type = int
    lowlim = 0
    help = Gaussian smoothing (pixel) of the current object prior to update
    doc = If None, smoothing is deactivated. This smoothing can be used to reduce the amplitude of spurious pixels in the outer, least constrained areas of the object.

    [clip_object]
    default = None
    type = tuple
    help = Clip object amplitude into this interval

    [probe_center_tol]
    default = None
    type = float
    lowlim = 0.0
    help = Pixel radius around optical axes that the probe mass center must reside in

    """

    SUPPORTED_MODELS = [Vanilla, Full, BlockFull, BlockVanilla]

    def __init__(self, ptycho_parent, pars=None):
        """
        Difference map reconstruction engine.
        """
        super(DM_glad_cuda, self).__init__(ptycho_parent, pars)

    def engine_iterate(self, num=1):
        """
        Compute `num` iterations.
        """

        for dID, _diffs in self.di.S.items():

            cfact_probe = (self.p.probe_inertia * len(self.vectorised_scan[dID]['meta']['addr']) /
                           self.vectorised_scan[dID]['probe'].shape[0]) * np.ones_like(self.vectorised_scan[dID]['probe'])


            cfact_object = self.p.object_inertia * self.mean_power * (self.vectorised_scan[dID]['object viewcover'] + 1.)


            pre_fft = self.propagator[dID].pre_fft
            post_fft = self.propagator[dID].post_fft
            psupp = self._probe_support[self.vectorised_scan[dID]['meta']['poe_IDs'][0]].astype(np.complex64)

            errors = difference_map_iterator(diffraction=self.vectorised_scan[dID]['diffraction'],
                                             obj=self.vectorised_scan[dID]['obj'],
                                             object_weights=self.vectorised_scan[dID]['object weights'].astype(np.float32),
                                             cfact_object=cfact_object,
                                             mask=self.vectorised_scan[dID]['mask'],
                                             probe=self.vectorised_scan[dID]['probe'],
                                             cfact_probe=cfact_probe,
                                             probe_support=psupp, #self.probe_support[self.vectorised_scan[dID]['meta']['poe_IDs'][0]],
                                             probe_weights=self.vectorised_scan[dID]['probe weights'].astype(np.float32),
                                             exit_wave=self.vectorised_scan[dID]['exit wave'],
                                             addr=self.vectorised_scan[dID]['meta']['addr'],
                                             pre_fft=pre_fft,
                                             post_fft=post_fft,
                                             pbound=self.pbound_scan[dID],
                                             overlap_max_iterations=self.p.overlap_max_iterations,
                                             update_object_first=self.p.update_object_first,
                                             obj_smooth_std=self.p.obj_smooth_std,
                                             overlap_converge_factor=self.p.overlap_converge_factor,
                                             probe_center_tol=self.p.probe_center_tol,
                                             probe_update_start=0,
                                             alpha=self.p.alpha,
                                             clip_object=self.p.clip_object,
                                             LL_error=True,
                                             num_iterations=num)


            #yuk yuk yuk
            error_dct = {}
            for jx in range(num):
                for k,idx in enumerate(self.vectorised_scan[dID]['meta']['view_IDs']):
                    error_dct[idx] = np.ascontiguousarray(errors[jx, :, k])
                error = parallel.gather_dict(error_dct)

        # count up
        self.curiter += num

        return error

    
