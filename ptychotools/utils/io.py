'''
Contains useful io tools
'''

rmpr = None
uw = None


def convert_ptyr_to_mapping(file_path, border=80):
    '''
    :param file_path: path the ptypy ptyr
    :param border: The pixel border to trim from the object reconstruction
    :return: dictionary with lists containing paths to 'complex', 'magnitude' and 'phase' nexus formatted file paths
    '''

    import numpy as np
    import h5py as h5

    fread = h5.File(file_path, 'r')
    obj_keys = '/content/obj'
    magnitudes_paths = []
    phase_paths = []
    complex_paths = []
    for obj_name, obj in fread[obj_keys].iteritems():
        magnitudes_path = file_path.split('.')[0] +obj_name +'_mag.nxs'
        magnitudes_paths.append(magnitudes_path)
        fout1 = h5.File(magnitudes_path, 'w')
        out_entry = fout1.create_group('entry')
        out_entry.attrs['NX_class'] = 'NXentry'

        x, y = obj['grids'][...]
        x = x[0, :, 0] / 1e-3 # get them into mm
        y = y[0, 0, :] / 1e-3 # get them into mm
        x = x[border:-border]
        y = y[border:-border]
        data = obj['data'][...].squeeze()
        data = data[border:-border, border:-border]
        # data = rmphaseramp(data)
        data = data.reshape(data.shape+(1, 1))

        abs_data = out_entry.create_group("mag_"+obj_name)
        abs_data.attrs['NX_class'] = 'NXdata'
        abs_data.attrs['SampleY_value_set_indices'] = np.int32(0)
        abs_data.attrs['SampleX_value_set_indices'] = np.int32(1)
        abs_data.attrs['axes'] = ['SampleY_value_set', 'SampleX_value_set', '.', '.']
        abs_data.attrs['signal'] = 'data'
        abs_data['SampleY_value_set'] = x
        abs_data['SampleY_value_set'].attrs['units'] = 'mm'
        abs_data['SampleX_value_set'] = y
        abs_data['SampleX_value_set'].attrs['units'] = 'mm'

        abs_data['data'] = np.float64(np.abs(data))

        fout1.close()


        phase_path = file_path.split('.')[0] +obj_name+'_phase.nxs'
        fout2 = h5.File(phase_path, 'w')
        phase_paths.append(phase_path)
        out_entry = fout2.create_group('entry')
        out_entry.attrs['NX_class'] = 'NXentry'

        phase_data = out_entry.create_group("phase_"+obj_name)
        phase_data.attrs['NX_class'] = 'NXdata'
        phase_data.attrs['SampleY_value_set_indices'] = np.int32(0)
        phase_data.attrs['SampleX_value_set_indices'] = np.int32(1)
        phase_data.attrs['axes'] = ['SampleY_value_set', 'SampleX_value_set', '.', '.']
        phase_data.attrs['signal'] = 'data'
        phase_data['SampleY_value_set'] = x
        phase_data['SampleY_value_set'].attrs['units'] = 'mm'
        phase_data['SampleX_value_set'] = y
        phase_data['SampleX_value_set'].attrs['units'] = 'mm'
        phase = np.float64(np.angle(data))
        phase_data['data'] = phase
        fout2.close()


        complex_path = file_path.split('.')[0] +obj_name+'_complex.nxs'
        complex_paths.append(complex_path)
        fout3 = h5.File(complex_path, 'w')
        out_entry = fout3.create_group('entry')
        out_entry.attrs['NX_class'] = 'NXentry'

        complex_data = out_entry.create_group("complex"+obj_name)
        complex_data.attrs['NX_class'] = 'NXdata'
        complex_data.attrs['SampleY_indices'] = 0
        complex_data.attrs['SampleX_indices'] = 1
        complex_data.attrs['axes'] = ['SampleY_value_set', 'SampleX_value_set', '.', '.']
        complex_data.attrs['signal'] = 'data'
        complex_data['SampleY_value_set'] = x
        complex_data['SampleY_value_set'].attrs['units'] = 'mm'
        complex_data['SampleX_value_set'] = y
        complex_data['SampleX_value_set'].attrs['units'] = 'mm'
        complex_data['data'] = data
        fout3.close()
    return {'complex': complex_path, 'phase': phase_path, 'magnitude': magnitudes_path}
