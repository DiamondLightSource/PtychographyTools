'''
Contains useful io tools
'''

import os
from . import log
import numpy as np
import h5py as h5

rmpr = None  # ramp removal
uw = None  # unwrapping


def get_output_folder_name(args):
    from datetime import datetime
    now = datetime.now()
    id = args.identifier[0] if isinstance(args.identifier, list) else args.identifier
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


def convert_ptyr_to_mapping(file_path, border=80):
    '''
    :param file_path: path the ptypy ptyr
    :param border: The pixel border to trim from the object reconstruction
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
