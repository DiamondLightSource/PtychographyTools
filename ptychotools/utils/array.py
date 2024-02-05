import numpy as np
import scipy.stats
import scipy.ndimage.morphology as morph
try:
    import ptypy.utils as u
except ImportError:
    print("Could not import ptypy.")


def recons_auto_mask(obj, weight='crop', percent=10, closing=5, erosion=10):
    if weight == 'abs':
        absobj = np.abs(obj)
        med = scipy.stats.mode(absobj, axis=None)[0][0]
        low  = med * (1-percent/100.)
        high = med * (1+percent/100.)
        mask = ((absobj > low) & (absobj < high)).astype(float)
        mask = morph.binary_erosion(morph.binary_closing(mask,iterations=closing), iterations=erosion)
    elif weight == 'phase':
        phobj = np.angle(obj)
        med = scipy.stats.mode(phobj, axis=None)[0][0]
        low  = med * (1-percent/100.)
        high = med * (1+percent/100.)
        mask = ((phobj > low) & (phobj < high)).astype(float)
        mask = morph.binary_erosion(morph.binary_closing(mask,iterations=closing), iterations=erosion)
    elif weight == 'crop':
        cx = int(obj.shape[0] * percent / 100.)
        cy = int(obj.shape[1] * percent / 100.)
        mask = np.zeros(obj.shape, dtype=bool)
        mask[cy:-cy,cx:-cx] = True
    return mask

def recons_auto_correct(obj, weight=None, **kwargs):
    if weight is None:
        mask = recons_auto_mask(obj, **kwargs)
    else:
        mask = weight
    obj = u.rmphaseramp(obj, weight=mask)
    obj *= np.exp(-1j * np.median(np.angle(obj)[mask]))
    return obj
