'''
tests the io module
'''

import unittest
import tempfile
import os
import numpy as np
import time
import shutil

from ptychotools.utils.io import *


class IoTest(unittest.TestCase):
    def setUp(self):
        self.output_directory = tempfile.mkdtemp(prefix='PtypyParametersTest')

    def tearDown(self):
        shutil.rmtree(self.output_directory)

    def test_get_output_folder_name(self):
        class Args: pass
        args = Args()

        args.output_folder = self.output_directory

        args.identifier = None

        # multiple calls should give different paths
        output_paths = []
        ncalls = 5
        for i in range(ncalls):
            time.sleep(1.)  # time stamp is only down to the second.
            output_paths.append(get_output_folder_name(args))
        # check they are all unique
        number_unique_paths = len(set(output_paths))
        np.testing.assert_equal(number_unique_paths, ncalls, err_msg="When the identifier is None, we are not getting unique directory generation."
                                                                     "\n number_unique_paths=%s for ncalls=%s" % (len(output_paths), ncalls))

        args.identifier = 1234
        # multiple calls should give the same path
        output_paths = []
        ncalls = 5
        for i in range(ncalls):
            time.sleep(1.)  # time stamp is only down to the second.
            output_paths.append(get_output_folder_name(args))
        # check they are not unique
        number_unique_paths = len(set(output_paths))
        self.assertEqual(number_unique_paths, 1, msg="When the identifier is not None, we are unique directory generation when we expect the same directory")

    def test_two_floats(self):
        exception_raiser = "-0.5e-3 0.5e-3 0.5e-3"
        self.assertRaises(ValueError, two_floats, exception_raiser)

        valid_string = "-0.5e-3 0.5e-3"
        expected_output = [-0.0005, 0.0005]
        output = two_floats(valid_string)
        self.assertListEqual(output, expected_output, msg="returned list %s was not the same as expected %s" %
                                                          (str(output), str(expected_output)))

    def test_write_dataset_to_file(self):
        # this is just a smoke test to see if it runs. At the moment testing more would be overbaord.
        dtypes = [np.complex, np.float]
        for dtype in dtypes:
            data = np.ones((10, 20, 30), dtype=dtype)
            x = np.arange(data.shape[-1])
            y = np.arange(data.shape[-2])
            file_path = os.path.join(self.output_directory, "test.h5")
            write_dataset_to_file(data, file_path, 'test_object', x, y, tag='test_tag', dtype=dtype)
            self.assertTrue(os.path.exists(file_path), msg="data was not written to file: %s" % file_path)

    def test_write_propagated_output(self):
        # this is just a smoke test to see if it runs. At the moment testing more would be overbaord.

        output_filename = os.path.join(self.output_directory, "test.h5")
        A = 100
        B = 200
        C = 300

        D = 400
        E = 500
        F = 600

        propagated_projections = np.ones((A, B, C), dtype=np.complex)
        probe = np.zeros((B, C))
        probe_x = np.arange(B)
        probe_y = np.arange(C)
        obj = np.zeros((D, E))
        obj_x = np.arange(D)
        obj_y = np.arange(E)
        zaxis = np.arange(F)
        write_propagated_output(output_filename, propagated_projections, probe_x, probe_y, probe, zaxis, obj_x, obj_y, obj)
        self.assertTrue(os.path.exists(output_filename), msg="The output file %s was not written." % output_filename)


if __name__ == "__main__":
    unittest.main()
