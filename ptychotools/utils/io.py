'''
Contains useful io tools
'''

import os
from . import log
import numpy as np
import h5py as h5

try:
    import ptypy.utils as u
    from ptypy.utils import ortho
except ImportError:
    print("Could not import ptypy.")
    
rmpr = None  # ramp removal
uw = None  # unwrapping


def get_common_id(identifier):
    if isinstance(identifier, list):
        common_id = str(identifier[0]) + "_" + str(identifier[-1])
    else:
        common_id = str(identifier)
    return common_id

def get_output_folder_name(args):
    from datetime import datetime
    now = datetime.now()
    id = get_common_id(args.identifier)
    #id = args.identifier[0] if isinstance(args.identifier, list) else args.identifier
    if args.identifier is not None:
        output_path = os.path.join(args.output_folder, "scan_{}".format(id))
    else:
        output_path = os.path.join(args.output_folder, "scan_{}".format(now.strftime("%Y%m%d%H%M%S")))
    log(3, "Output is going in: {}".format(output_path))
    return output_path


def two_floats(value):
    '''
    Since '-' is reserved for option parsing, we have to do this to get around it.
    '''
    values = value.split()
    if len(values) != 2:
        raise ValueError("Value:%s has the wrong length. Should not be longer than 2" % str(values))
    values = list(map(float, values))
    return values


def write_dataset_to_file(data, file_path,  obj_name, x, y, tag, dtype=np.float64):
    with h5.File(file_path, 'w') as f:
        out_entry = f.create_group('entry')
        out_entry.attrs['NX_class'] = 'NXentry'
        dataset = out_entry.create_group(tag + obj_name)
        dataset.attrs['NX_class'] = 'NXdata'
        dataset.attrs['SampleY_value_indices'] = np.int32(0)
        dataset.attrs['SampleX_value_indices'] = np.int32(1)
        dataset.attrs['axes'] = ['SampleY_value', 'SampleX_value', '.', '.']
        dataset.attrs['signal'] = 'data'
        dataset['SampleY_value'] = x
        dataset['SampleY_value'].attrs['units'] = 'mm'
        dataset['SampleX_value'] = y
        dataset['SampleX_value'].attrs['units'] = 'mm'
        dataset['data'] = data.astype(dtype)


def convert_ptyr_to_mapping(file_path, border=80, rmramp=True, rmradius=0.5, rmiter=2, phaseshift=0.0):
    '''
    :param file_path: path the ptypy ptyr
    :param border: The pixel border to trim from the object reconstruction
    :param rmramp: Remove phase ramp 
    :return: dictionary with lists containing paths to 'complex', 'magnitude' and 'phase' nexus formatted file paths
    '''

    fread = h5.File(file_path, 'r')
    obj_keys = '/content/obj'
    complex_paths = []
    phase_paths = []
    magnitudes_paths = []
    for obj_name, obj in fread[obj_keys].items():
        x, y = obj['grids'][...]
        x = x[0, :, 0] / 1e-3  # get them into mm
        y = y[0, 0, :] / 1e-3  # get them into mm
        x = x[border:-border]
        y = y[border:-border]
        data = obj['data'][...].squeeze()
        data = data[border:-border, border:-border]
        if rmramp:
            ny,nx = data.shape
            XX,YY = np.meshgrid(np.arange(nx) - nx//2, np.arange(ny) - ny//2)
            W = np.sqrt(XX**2 + YY**2) < (rmradius * (nx+ny) / 4)
            for i in range(rmiter):
                data = u.rmphaseramp(data, weight=W)
        data *= np.exp(1j * phaseshift)
        data = data.reshape(data.shape+(1, 1))

        magnitudes_path = file_path.split('.')[0] + obj_name + '_mag.nxs'
        write_dataset_to_file(np.abs(data), magnitudes_path, obj_name, x, y, tag='mag_')

        phase_path = file_path.split('.')[0] + obj_name+'_phase.nxs'
        write_dataset_to_file(np.angle(data), phase_path, obj_name, x, y, tag='phase_')

        complex_path = file_path.split('.')[0] + obj_name+'_complex.nxs'
        write_dataset_to_file(data, complex_path, obj_name, x, y, tag='complex_', dtype=np.complex128)

        complex_paths.append(complex_path)
        phase_paths.append(phase_paths)
        magnitudes_paths.append(magnitudes_path)

    return {'complex': complex_paths, 'phase': phase_paths, 'magnitude': magnitudes_paths}


def create_nxstxm_file(filename, energies, shape, N, dtype=np.float64):
    f = h5.File(filename, 'w')
    entry = f.create_group('entry1')
    entry['definition'] = np.array(['NXstxm'], dtype='<S6')
    entry.attrs['NX_class'] = 'NXentry'
    counter = entry.create_group('Counter1')
    counter.attrs['NX_class'] = 'NXdata'
    counter['scan_type'] = 'Sample'
    counter['count_time'] = np.array([0.05]*(N))
    counter.create_dataset('data', data=np.zeros((N,) + shape, dtype=dtype), dtype=dtype)
    counter.create_dataset('photon_energy', data=energies, dtype=np.float64)
    counter['photon_energy'].attrs['axis'] = 1
    counter.create_dataset('sample_x', data=np.arange(shape[1]), dtype=np.float64)
    counter['sample_x'].attrs['axis'] = 3
    counter.create_dataset('sample_y', data=np.arange(shape[0]), dtype=np.float64)
    counter['sample_y'].attrs['axis'] = 2
    return f

def create_nxtomo_file(filename, angles, shape, N, name='default'):
    f = h5.File(filename, 'w')
    entry = f.create_group('entry1')
    entry['definition'] = np.array(['NXtomo'], dtype='<S6')
    entry.attrs['NX_class'] = 'NXentry'
    instrument = entry.create_group('instrument')
    instrument.attrs['NX_class'] = 'NXinstrument'
    detector = instrument.create_group('detector')
    detector.attrs['NX_class'] = 'NXdetector'
    detector.create_dataset('data', data=np.zeros((N,) + shape), dtype=np.float32)
    detector.create_dataset('image_key', data=np.zeros(N), dtype=int)
    sample = entry.create_group('sample')
    sample.attrs['NX_class'] = 'NXsample'
    sample['name'] = np.array([name], dtype='<S6')
    sample.create_dataset('rotation_angle', data=angles, dtype=np.float64)
    entry['data'] = h5.SoftLink("/entry1/instrument/detector/data")
    entry['rotation_angle'] = h5.SoftLink("/entry1/sample/rotation_angle")
    entry['image_key'] = h5.SoftLink("/entry1/instrument/detector/image_key")
    return f


def write_multiple_ptyr_to_nxstxm(file_paths, out_path, prefix="", border=80, norm=True, rescale=True, rmramp=True, rmradius=0.5, rmiter=1):

    out_phase    = out_path + "/" + prefix + "phase.nxs"
    out_odensity = out_path + "/" + prefix + "optical_density.nxs"
    out_amplitude = out_path + "/" + prefix + "amplitude.nxs"
    out_probe_intensity = out_path + "/" + prefix + "probe_intensity.nxs"
    out_complex = out_path + "/" + prefix + "complex.nxs"

    shapes = []
    energy = []
    objs   = []
    prbs   = []
    nfiles = len(file_paths)
    for idx in range(nfiles):
        fread = h5.File(file_paths[idx], 'r')
        obj_keys = '/content/obj'
        obj = list(fread[obj_keys].values())[0]
        enrg = obj['_energy'][...]
        data = obj['data'][0]
        if border > 0:
            data = data[border:-border,border:-border]
        sh = data.shape
        objs.append(data)
        energy.append(enrg)
        shapes.append(np.array(sh))
        probe_keys = '/content/probe'
        probe = list(fread[probe_keys].values())[0]
        probe_shape = tuple(np.array(probe['data'].shape[1:]))
        prbs.append(np.abs(ortho(probe['data'][:])[1][0]))
    energy = np.array(energy)*1e3 # convert to eV
    prb_int_mean = (np.array(prbs)**2).mean(axis=(1,2))
    #print("Probe amplitude means", prb_mean)
    log(3, "The energy ranges from {} to {} eV".format(energy[0], energy[-1]))
    shapes = np.array(shapes)
    full_shape = np.max(shapes[:, 0]), np.max(shapes[:, 1])
    log(3, "The common full shape of the object is {}".format(full_shape))
    
    # Create Mantis/Nexus files for phase and optical density
    fp = create_nxstxm_file(out_phase, energy, full_shape, nfiles)
    fo = create_nxstxm_file(out_odensity, energy, full_shape, nfiles)
    fa = create_nxstxm_file(out_amplitude, energy, full_shape, nfiles)
    fi = create_nxstxm_file(out_probe_intensity, energy, probe_shape, nfiles)
    fc = create_nxstxm_file(out_complex, energy, full_shape, nfiles, dtype='complex')

    ctr = 0
    for idx in range(nfiles):
        slow_top = shapes[idx, 0]
        fast_top = shapes[idx, 1]
        O = objs[idx].squeeze()
        if rmramp:
            ny,nx = O.shape
            XX,YY = np.meshgrid(np.arange(nx) - nx//2, np.arange(ny) - ny//2)
            W = np.sqrt(XX**2 + YY**2) < (rmradius * (nx+ny) / 4)
            for i in range(rmiter):
                O = u.rmphaseramp(O, weight=W)
        if norm:
            O *= np.exp(-1j*np.median(np.angle(O)))
        phase = np.angle(O)
        if rescale:
            O *= np.sqrt(prb_int_mean[idx] / prb_int_mean.mean())
        odensity = -np.log(np.abs(O)**2)
        odensity[np.isinf(odensity)] = 0
        if norm:
            odensity -= np.median(odensity)
        amplitude = np.abs(O)
        #print("probe intensity before: ", (prbs[idx]**2).mean())
        probeint = prbs[idx]**2 / (prb_int_mean[idx] / prb_int_mean.mean())
        #print("probe intensity after: ", (probeint).mean())
        fp['entry1/Counter1/data'][ctr, :slow_top, :fast_top] = phase
        fo['entry1/Counter1/data'][ctr, :slow_top, :fast_top] = odensity
        fa['entry1/Counter1/data'][ctr, :slow_top, :fast_top] = amplitude
        fi['entry1/Counter1/data'][ctr] = probeint
        fc['entry1/Counter1/data'][ctr, :slow_top, :fast_top] = O
        ctr += 1
    fp.close()
    fo.close()
    fa.close()
    fi.close()
    fc.close()
    log(3, "Saved phase to {}".format(out_phase))
    log(3, "Saved optical density to {}".format(out_odensity))
    log(3, "Saved amplitude to {}".format(out_amplitude))
    log(3, "Saved probe intensity to {}".format(out_probe_intensity))
    log(3, "Saved complex to {}".format(out_complex))

def write_single_ptyr_to_nxstxm(file_path, out_path, prefix="", border=80, rmramp=True, norm=True, rmradius=0.5, rmiter=1):

    out_phase     = out_path + "/" + prefix + "phase.nxs"
    out_odensity  = out_path + "/" + prefix + "optical_density.nxs"
    out_amplitude = out_path + "/" + prefix + "amplitude.nxs"

    shapes = []
    energy = []
    objs   = []
    fread = h5.File(file_path, 'r')
    obj_keys = '/content/obj'
    scan_keys = list(fread[obj_keys].keys())
    for obj in fread[obj_keys].values():
        enrg = obj['_energy'][...]
        data = obj['data'][0]
        if border > 0:
            data = data[border:-border,border:-border]
        sh = data.shape
        objs.append(data)
        energy.append(enrg)
        shapes.append(np.array(sh))
    energy = np.array(energy)*1e3 # convert to eV
    log(3, "The energy ranges from {} to {} eV".format(energy[0], energy[-1]))
    shapes = np.array(shapes)
    full_shape = np.max(shapes[:, 0]), np.max(shapes[:, 1])
    log(3, "The common full shape of the object is {}".format(full_shape))
    
    # Create Mantis/Nexus files for phase and optical density
    fp = create_nxstxm_file(out_phase, energy, full_shape, len(scan_keys))
    fo = create_nxstxm_file(out_odensity, energy, full_shape, len(scan_keys))
    fa = create_nxstxm_file(out_amplitude, energy, full_shape, len(scan_keys))
    
    ctr = 0
    for idx in range(len(scan_keys)):
        slow_top = shapes[idx, 0]
        fast_top = shapes[idx, 1]
        O = objs[idx].squeeze()
        if rmramp:
            ny,nx = O.shape
            XX,YY = np.meshgrid(np.arange(nx) - nx//2, np.arange(ny) - ny//2)
            W = np.sqrt(XX**2 + YY**2) < (rmradius * (nx+ny) / 4)
            for i in range(rmiter):
                O = u.rmphaseramp(O, weight=W)
        if norm:
            O *= np.exp(-1j*np.median(np.angle(O)))
        phase = np.angle(O)
        odensity = -np.log(np.abs(O)**2)
        odensity[np.isinf(odensity)] = 0
        if norm:
            odensity -= np.median(odensity)
        amplitude = np.abs(O)
        fp['entry1/Counter1/data'][ctr, :slow_top, :fast_top] = phase
        fo['entry1/Counter1/data'][ctr, :slow_top, :fast_top] = odensity
        fa['entry1/Counter1/data'][ctr, :slow_top, :fast_top] = amplitude
        ctr += 1
    fp.close()
    fo.close()
    fa.close()
    log(3, "Saved phase to {}".format(out_phase))
    log(3, "Saved optical density to {}".format(out_odensity))
    log(3, "Saved amplitude to {}".format(out_amplitude))


def write_multiple_ptyr_to_nxtomo(file_paths, angles, out_path, prefix="", border=80, norm=True, rmramp=True, rmradius=0.5, rmiter=1, save_odens=False, save_complex=False):

    out_phase  = out_path + "/" + prefix + "tomo_phase.nxs"
    if save_odens:
        out_odens  = out_path + "/" + prefix + "tomo_odens.nxs"
    if save_complex:
        out_complex = out_path + "/" + prefix + "tomo_complex.nxs"

    shapes = []
    nfiles = len(file_paths)
    for idx in range(nfiles):
        fread = h5.File(file_paths[idx], 'r')
        obj_keys = '/content/obj'
        obj = list(fread[obj_keys].values())[0]
        sh = obj['data'].shape[1:]
        if border > 0:
            sh = (sh[0] - 2*border, sh[1] - 2*border)
        shapes.append(np.array(sh))
    log(3, "The tomographic angles range from {} to {} degress".format(angles[0], angles[-1]))
    shapes = np.array(shapes)
    full_shape = np.max(shapes[:, 0]), np.max(shapes[:, 1])
    log(3, "The common full shape of the object is {}".format(full_shape))
    
    # Create Nexus files for phase
    fp = create_nxtomo_file(out_phase,   angles, full_shape, nfiles)
    if save_odens:
        fo = create_nxtomo_file(out_odens,   angles, full_shape, nfiles)
    if save_complex:
        fc = create_nxtomo_file(out_complex, angles, full_shape, nfiles, dtype=np.complex64)
    
    ctr = 0
    for idx in range(nfiles):
        print("Projection %03d/%03d" %(idx, nfiles), end='\r', flush=True)
        slow_top = shapes[idx, 0]
        fast_top = shapes[idx, 1]
        fread = h5.File(file_paths[idx], 'r')
        obj_keys = '/content/obj'
        obj = list(fread[obj_keys].values())[0]
        e,v  = ortho(obj['data'])
        O = v[0] # select most dominant orthogonal object mode
        if border > 0:
            O = O[border:-border,border:-border]
        if rmramp:
            ny,nx = O.shape
            XX,YY = np.meshgrid(np.arange(nx) - nx//2, np.arange(ny) - ny//2)
            W = np.sqrt(XX**2 + YY**2) < (rmradius * (nx+ny) / 4)
            for i in range(rmiter):
                O = u.rmphaseramp(O, weight=W)
        if norm:
            O *= np.exp(-1j*np.median(np.angle(O)))
        phase = np.angle(O)
        odens = -np.log(np.abs(O)**2)
        if norm:
            odens -= np.median(odens)
        fp['entry1/data'][ctr, :slow_top, :fast_top] = phase
        if save_odens:
            fo['entry1/data'][ctr, :slow_top, :fast_top] = odens
        if save_complex:
            fc['entry1/data'][ctr, :slow_top, :fast_top] = O
        ctr += 1
    fp.close()
    log(3, "Saved phase to {}".format(out_phase))
    if save_odens:
        fo.close()
        log(3, "Saved optical density to {}".format(out_odens))
    if save_complex:
        fc.close()
        log(3, "Saved complex object to {}".format(out_complex))




def write_propagated_output(output_filename, propagated_projections, probe_x, probe_y, probe, zaxis, obj_x, obj_y, obj):
    with h5.File(output_filename, 'w') as fout:
        fout.create_group('entry')
        fout.attrs['NX_class'] = 'NXentry'
        # the focus propagation
        propagated = fout['entry'].create_group('propagated')

        # need to add reconstructed probe and object into this.
        fout['entry/propagated/x/data'] = probe_x
        fout['entry/propagated/y/data'] = probe_y
        fout['entry/propagated/z/data'] = zaxis
        chunks = (50, 50, 50)

        abs_probe = propagated.create_group('abs_probe')
        abs_probe.attrs["NX_class"] = 'NXdata'
        abs_probe.create_dataset('data', data=np.abs(propagated_projections), chunks=chunks)
        abs_probe.attrs['axes'] = ["z", "y", "x"]
        abs_probe['x'] = fout['entry/propagated/x/data'][...]
        abs_probe['y'] = fout['entry/propagated/y/data'][...]
        abs_probe['z'] = fout['entry/propagated/z/data'][...]
        abs_probe.attrs['x_indices'] = 2
        abs_probe.attrs['y_indices'] = 1
        abs_probe.attrs['z_indices'] = 0
        abs_probe.attrs['signal'] = 'data'

        phase_probe = propagated.create_group('phase_probe')
        phase_probe.attrs["NX_class"] = 'NXdata'
        phase_probe.create_dataset('data', data=np.angle(propagated_projections), chunks=chunks)
        phase_probe.attrs['axes'] = ["z", "y", "x"]
        phase_probe['x'] = fout['entry/propagated/x/data'][...]
        phase_probe['y'] = fout['entry/propagated/y/data'][...]
        phase_probe['z'] = fout['entry/propagated/z/data'][...]
        phase_probe.attrs['x_indices'] = 2
        phase_probe.attrs['y_indices'] = 1
        phase_probe.attrs['z_indices'] = 0
        phase_probe.attrs['signal'] = 'data'

        complex_probe = propagated.create_group('complex_probe')
        complex_probe.attrs["NX_class"] = 'NXdata'
        complex_probe.create_dataset('data', data=propagated_projections, chunks=chunks)
        complex_probe.attrs['axes'] = ["z", "y", "x"]
        complex_probe['x'] = fout['entry/propagated/x/data'][...]
        complex_probe['y'] = fout['entry/propagated/y/data'][...]
        complex_probe['z'] = fout['entry/propagated/z/data'][...]
        complex_probe.attrs['x_indices'] = 2
        complex_probe.attrs['y_indices'] = 1
        complex_probe.attrs['z_indices'] = 0
        complex_probe.attrs['signal'] = 'data'

        # now the 2D reconstructions
        reconstructed = fout['entry'].create_group('reconstructed')
        reconstructed.create_group('obj_x')
        reconstructed.create_group('obj_y')
        reconstructed['obj_x'].create_dataset('data', data=obj_x)
        reconstructed['obj_y'].create_dataset('data', data=obj_y)

        fout['entry/reconstructed/x/data'] = fout['entry/propagated/x/data'][...]
        fout['entry/reconstructed/y/data'] = fout['entry/propagated/y/data'][...]

        reconstructed_abs_probe = reconstructed.create_group('abs_probe')
        reconstructed_abs_probe.attrs["NX_class"] = 'NXdata'
        reconstructed_abs_probe.create_dataset('data', data=np.abs(probe))
        reconstructed_abs_probe['x'] = fout['entry/reconstructed/x/data'][...]
        reconstructed_abs_probe['y'] = fout['entry/reconstructed/y/data'][...]
        reconstructed_abs_probe.attrs['axes'] = ["y", "x"]
        reconstructed_abs_probe.attrs['x_indices'] = 1
        reconstructed_abs_probe.attrs['y_indices'] = 0
        reconstructed_abs_probe.attrs['signal'] = 'data'

        reconstructed_phase_probe = reconstructed.create_group('angle_probe')
        reconstructed_phase_probe.attrs["NX_class"] = 'NXdata'
        reconstructed_phase_probe.create_dataset('data', data=np.angle(probe))
        reconstructed_phase_probe['x'] = fout['entry/reconstructed/x/data'][...]
        reconstructed_phase_probe['y'] = fout['entry/reconstructed/y/data'][...]
        reconstructed_phase_probe.attrs['axes'] = ["y", "x"]
        reconstructed_phase_probe.attrs['x_indices'] = 1
        reconstructed_phase_probe.attrs['y_indices'] = 0
        reconstructed_phase_probe.attrs['signal'] = 'data'

        reconstructed_abs_obj = reconstructed.create_group('abs_obj')
        reconstructed_abs_obj.attrs["NX_class"] = 'NXdata'
        reconstructed_abs_obj.create_dataset('data', data=np.abs(obj))
        reconstructed_abs_obj['obj_x'] = fout['entry/reconstructed/obj_x/data'][...]
        reconstructed_abs_obj['obj_y'] = fout['entry/reconstructed/obj_y/data'][...]
        reconstructed_abs_obj.attrs['axes'] = ["obj_x", "obj_y"]
        reconstructed_abs_obj.attrs['obj_x_indices'] = 0
        reconstructed_abs_obj.attrs['obj_y_indices'] = 1
        reconstructed_abs_obj.attrs['signal'] = 'data'

        reconstructed_phase_obj = reconstructed.create_group('phase_obj')
        reconstructed_phase_obj.attrs["NX_class"] = 'NXdata'
        reconstructed_phase_obj.create_dataset('data', data=np.angle(obj))
        reconstructed_phase_obj['obj_x'] = fout['entry/reconstructed/obj_x/data'][...]
        reconstructed_phase_obj['obj_y'] = fout['entry/reconstructed/obj_y/data'][...]
        reconstructed_phase_obj.attrs['axes'] = ["obj_x", "obj_y"]
        reconstructed_phase_obj.attrs['obj_x_indices'] = 0
        reconstructed_phase_obj.attrs['obj_y_indices'] = 1
        reconstructed_phase_obj.attrs['signal'] = 'data'

        reconstructed_complex_obj = reconstructed.create_group('complex_obj')
        reconstructed_complex_obj.attrs["NX_class"] = 'NXdata'
        reconstructed_complex_obj.create_dataset('data', data=obj)
        reconstructed_complex_obj['complex_obj_x'] = fout['entry/reconstructed/obj_x/data'][...]
        reconstructed_complex_obj['complex_obj_y'] = fout['entry/reconstructed/obj_y/data'][...]
        reconstructed_complex_obj.attrs['axes'] = ["complex_obj_x", "complex_obj_y"]
        reconstructed_complex_obj.attrs['complex_obj_x_indices'] = 0
        reconstructed_complex_obj.attrs['complex_obj_y_indices'] = 1
        reconstructed_complex_obj.attrs['signal'] = 'data'
