'''
propagate test

'''

import unittest
import tempfile
import shutil
import os
import pytest
import time
import procrunner
import h5py as h5
from test import utils as tu
from ptychotools.utils.io import two_floats

# we test the propagation routine and file writing else where. This really is just testing the script produces a file


@pytest.mark.ptypy
class PropagateTest(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.mkdtemp(prefix='run_test')
        build_path = os.path.dirname(os.path.abspath(__file__)).split('lib')[0]
        self.propagate = os.path.join(build_path, "scripts-3.7/ptychotools.propagate")
        print("working directory: %s" % self.working_directory)

    def tearDown(self):
        shutil.rmtree(self.working_directory)

    def test_propagate_script(self):
        inputs = {}
        inputs['run_scripts'] = self.propagate
        inputs['input_file'] = tu.get_ptyr_path()
        inputs['scan_number'] = 'scan1'
        inputs['output_folder'] = self.working_directory
        inputs['zrange'] = '"-0.5e-3 0.5e-3"'  # needs to be in quote in command
        command = "%(run_scripts)s -i %(input_file)s -o %(output_folder)s -z %(zrange)s \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command.encode('utf-8'), working_directory=self.working_directory)
        self.assertEqual(out['exitcode'], 0)
        inputs['minz'], inputs['maxz'] = two_floats(inputs['zrange'].strip("\""))

        output_nexus = os.path.join(self.working_directory, '%(scan_number)s_propagated_%(minz)s_%(maxz)s.nxs' % inputs)

        self.assertTrue(os.path.exists(output_nexus), msg="The output nexus file: %s was not created." % output_nexus)


if __name__ == '__main__':
    unittest.main()
