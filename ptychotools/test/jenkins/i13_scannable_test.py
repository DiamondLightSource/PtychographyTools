'''
Test the code used in the i13 scannable.

'''

import unittest
import subprocess
import os

class I13ScannableTest(unittest.TestCase):
    def setUp(self):
        self.data_dir = '/dls/science/groups/das/ExampleData/ptypy_beamline_tests/i13-1/scannable'
        self.binary = '/bin/bash'
        self.output_path = os.path.join(self.data_dir, 'test_output')
        print self.output_path


    def test_launcher(self):
        # launcher_file = '/dls_sw/apps/ptypy/i13_test/cluster_scripts/ptypy_launcher.sh'
        os.environ['BEAMLINE'] = 'i13-1'
        launcher_file = '/dls_sw/apps/ptychography_tools/master/scripts/ptypy_launcher'
        cluster_configuration = '/dls_sw/apps/ptychography_tools/cluster_configurations/i13-1.txt'
        identifier = '174389'
        parameter_file = os.path.join(self.data_dir, 'i13_silicon.json')
        print "here"
        print os.environ['BEAMLINE']
        subprocess.check_call(['module load', 'ptycho-tools'], shell=True)
        print "did this"
        args = [self.binary, launcher_file, '-c', cluster_configuration,'-j', parameter_file, '-i', identifier, '-o', self.output_path]
        print "the args are", args
        subprocess.check_call(args)

        print "here now"
        print " "

if __name__ == '__main__':
    unittest.main()
