'''
tests ptychotools.run
'''

import unittest
import tempfile
import shutil
import os
from test import utils as tu
import procrunner
import h5py as h5
import pytest

## needs to test
#1. config file with identifier
#3. config file with 2 or more identifiers
#4. config file with 2 or more identifiers sharing the probe

# checks
# right number of probes and objects in the files
# right contents of nexus files
# the failure case is caught and raises correctly

# These tests will assume that ptypy works as expected, we are just checking the arguments are passed correctly.
# We won't check anything about image quality, or even mostly that the file content is correct, just that they exist.

@pytest.mark.ptypy
class RunTest(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.mkdtemp(prefix='run_test')
        build_path = os.path.dirname(os.path.abspath(__file__)).split('lib')[0]
        self.ptychotools_run = os.path.join(build_path, "scripts-2.7/ptychotools.run") # need to find this automatically
        self.resources = tu.get_moonflower_info()
    #
    # def tearDown(self):
    #     shutil.rmtree(self.working_directory)

    def test_single_identifier(self):

        inputs = {}
        inputs['run_scripts'] = self.ptychotools_run
        inputs['config'] = self.resources['config']
        inputs['working_directory'] = self.working_directory
        inputs['identifier'] = 'scan1'
        command = "%(run_scripts)s %(config)s -O %(working_directory)s -I %(identifier)s \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command, working_directory=self.working_directory)
        self.assertEqual(out['exitcode'], 0)

        expected_number_of_objects = 1
        expected_number_of_probes = 1
        self.validate_output_files(expected_number_of_objects, expected_number_of_probes)

    def test_two_identifiers_fails(self):

        inputs = {}
        inputs['run_scripts'] = self.ptychotools_run
        inputs['config'] = self.resources['config']
        inputs['working_directory'] = self.working_directory
        inputs['identifier'] = 'scan1 scan2'

        command = "%(run_scripts)s %(config)s -O %(working_directory)s -I %(identifier)s \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command, working_directory=self.working_directory)
        self.assertEqual(out['exitcode'], 0)

        # should fail and print runtime error to stderr
        self.assertTrue("raise RuntimeError(\'If you pass a list of arguments you must share the probe between them. Set -S option.\')" in out["stderr"])

    def test_two_identifiers_with_linking(self):

        inputs = {}
        inputs['run_scripts'] = self.ptychotools_run
        inputs['config'] = self.resources['config']
        inputs['working_directory'] = self.working_directory
        inputs['identifier'] = 'scan1 scan2'


        command = "%(run_scripts)s %(config)s -O %(working_directory)s -I %(identifier)s -S \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command, working_directory=self.working_directory)

        #did it run ok?
        self.assertEqual(out['exitcode'], 0, msg="The run command returned a non zero exit code: %s" % str(out))
        expected_number_of_objects = 2
        expected_number_of_probes = 1
        self.validate_output_files(expected_number_of_objects, expected_number_of_probes)

    def validate_output_files(self, expected_number_of_objects, expected_number_of_probes):
        # now check the output
        output_path = os.path.join(self.working_directory, 'scan_scan1/scan_scan1.ptyr')
        output_file = h5.File(output_path, 'r')

        object_ids = output_file['content/obj'].keys()
        self.assertEqual(len(object_ids), expected_number_of_objects,
                         msg="Output ptyr file %s does not have the expected number of objects: %s" % (output_file,
                                                                                                       expected_number_of_objects))

        self.assertEqual(len(output_file['content/probe'].keys()), expected_number_of_probes,
                         msg="Output ptyr file %s does not have the expected number of probes: %s" % (output_file,
                                                                                                      expected_number_of_probes))

        # check that the ptyd file was written.
        self.assertTrue(os.path.exists(os.path.join(self.working_directory, 'scan_scan1/scan_scan1.ptyd')),
                        msg="The ptyd file doesn't exist")

        for id in object_ids:
            phase_nexus = os.path.join(self.working_directory, 'scan_scan1/scan_scan1%s_phase.nxs' % id)
            self.assertTrue(os.path.exists(phase_nexus),
                            msg="The phase nexus file: %s does not exist" % phase_nexus)
            mag_nexus = os.path.join(self.working_directory, 'scan_scan1/scan_scan1%s_mag.nxs' % id)
            self.assertTrue(os.path.exists(mag_nexus),
                            msg="The mag nexus file: %s does not exist" % mag_nexus)
            complex_nexus = os.path.join(self.working_directory, 'scan_scan1/scan_scan1%s_complex.nxs' % id)
            self.assertTrue(os.path.exists(complex_nexus),
                            msg="The complex valued nexus file: %s does not exist" % complex_nexus)



if __name__ == '__main__':
    unittest.main()
