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


if __name__ == "__main__":
    unittest.main()
