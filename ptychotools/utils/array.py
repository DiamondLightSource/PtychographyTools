import numpy as np
import scipy.ndimage.morphology as morph
try:
    import ptypy.utils as u
except ImportError:
    print("Could not import ptypy.")

def recons_auto_mask(obj, weight='abs', percent=10, morph_iter=10):
    if weight == 'abs':
        absobj = np.abs(obj)
        med = np.median(absobj)
        low  = med * (1-percent/100.)
        high = med * (1+percent/100.)
        mask = ((absobj > low) & (absobj < high)).astype(np.float)
        mask = morph.binary_opening(morph.binary_erosion(mask,iterations=morph_iter), iterations=morph_iter)
    elif weight == 'phase':
        phobj = np.angle(obj)
        med = np.median(phobj)
        low  = med * (1-percent/100.)
        high = med * (1+percent/100.)
        mask = ((phobj > low) & (phobj < high)).astype(np.float)
        mask = morph.binary_opening(morph.binary_erosion(mask,iterations=morph_iter), iterations=morph_iter)
    return mask

def recons_auto_correct(obj, weight=None):
    if weight is None:
        mask = recons_auto_mask(obj)
    else:
        mask = weight
    obj = u.rmphaseramp(obj, weight=mask)
    obj *= np.exp(-1j * np.median(np.angle(obj)[mask]))
    return obj
