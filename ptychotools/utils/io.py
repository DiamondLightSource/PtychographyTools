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


def write_dataset_to_file(data, file_path,  obj_name, x, y, tag, dtype=np.float64):
    with h5.File(file_path, 'w') as f:
        out_entry = f.create_group('entry')
        out_entry.attrs['NX_class'] = 'NXentry'
        dataset = out_entry.create_group(tag + obj_name)
        dataset.attrs['NX_class'] = 'NXdata'
        dataset.attrs['SampleY_value_set_indices'] = np.int32(0)
        dataset.attrs['SampleX_value_set_indices'] = np.int32(1)
        dataset.attrs['axes'] = ['SampleY_value_set', 'SampleX_value_set', '.', '.']
        dataset.attrs['signal'] = 'data'
        dataset['SampleY_value_set'] = x
        dataset['SampleY_value_set'].attrs['units'] = 'mm'
        dataset['SampleX_value_set'] = y
        dataset['SampleX_value_set'].attrs['units'] = 'mm'
        dataset['data'] = dtype(data)


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
    for obj_name, obj in fread[obj_keys].iteritems():
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


