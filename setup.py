#!/usr/bin/env python



from distutils.core import setup
import setuptools


package_list = setuptools.find_packages(exclude=['*scripts*'])


setup(
    name='PtychoTools',
    version="0.1.0",
    author='Aaron Parsons and Benedikt Daurer',
    description='Wrappers for the ptypy framework',
    package_dir={'ptychotools': 'ptychotools'},
    packages=package_list,
    package_data={'test' : ['resource/*']},
    scripts=['scripts/ptychotools.propagate',
             'scripts/ptychotools.add_flat_dark',
             'scripts/ptychotools.mapping_plot',
             'scripts/ptychotools.propagate',
             'scripts/ptychotools.ptypy_launcher',
             'scripts/ptychotools.ptypy_mpi_recipe',
             'scripts/ptychotools.run',
             'scripts/ptychotools.slice_select_skip',
             'scripts/ptychotools.update_mask_file',
             'scripts/ptychotools.write_dawn_processing_bean',
             'scripts/ptychotools.j08_preproc',
             'scripts/ptychotools.utils',
             'scripts/ptychotools.combine_spectro_scans',
             'scripts/ptychotools.combine_tomo_scans']
)

