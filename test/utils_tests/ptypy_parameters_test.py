'''
testing for the ptypy_parameters module
'''


import unittest
import os
import tempfile
import shutil

from test import utils as tu
from ptychotools.utils.ptypy_parameters import *


class PtypyParametersTest(unittest.TestCase):
    def setUp(self):
        self.output_directory = tempfile.mkdtemp(prefix='PtypyParametersTest')

    def tearDown(self):
        shutil.rmtree(self.output_directory)

    def test_paramtree_to_json(self):
        p = tu.generate_test_param_tree()
        output_json_path = os.path.join(self.output_directory, 'test.json')
        paramtree_to_json(p, basefile=None, filepath=output_json_path)
        expected_result = open(tu.test_json_path(), 'r').read()
        actual_result = open(output_json_path).read()
        self.assertEqual(expected_result, actual_result, msg="There was a problem converting the paramtree to json."
                                                             "\n expected_result: %s \n\n actual_result: %s \n\n" % (repr(expected_result), repr(actual_result)))

    def test_paramtree_to_yaml(self):
        p = tu.generate_test_param_tree()
        output_yaml_path = os.path.join(self.output_directory, 'test.yml')
        paramtree_to_yaml(p, basefile=None, filepath=output_yaml_path)
        expected_result = open(tu.test_yaml_path(), 'r').read()
        actual_result = open(output_yaml_path).read()
        self.assertEqual(expected_result, actual_result, msg="There was a problem converting the paramtree to yaml."
                                                             "\n expected_result: %s \n\n actual_result: %s \n\n" % (repr(expected_result), repr(actual_result)))

    def test_paramtree_from_json(self):
        expected_paramtree = tu.generate_test_param_tree()
        real_paramtree = paramtree_from_json(tu.test_json_path())
        self.assertEqual(expected_paramtree, real_paramtree, msg="There was a problem converting the json to paramtree."
                                                                 "\n expected_result: %s \n\n actual_result: %s \n\n" % (repr(expected_paramtree), repr(real_paramtree)))

    def test_paramtree_from_yaml(self):
        expected_paramtree = tu.generate_test_param_tree()
        real_paramtree = paramtree_from_yaml(tu.test_yaml_path())
        self.assertEqual(expected_paramtree, real_paramtree, msg="There was a problem converting the yaml to paramtree."
                                                                 "\n expected_result: %s \n\n actual_result: %s \n\n" % (
                                                                     repr(expected_paramtree), repr(real_paramtree)))

    def test_parse_param_data_paths_with_paramtree(self):
        dfile_preset_answer = 'cheesecake'
        paramtree = tu.generate_test_param_tree()
        paramtree.run = "1234"
        paramtree.scans.MF.data.dfile = dfile_preset_answer
        paramtree.scans.MF.data.something = "cheese_%(run)s"

        class Args: pass
        args = Args()
        args.output_folder = self.output_directory
        args.identifier = paramtree.run

        parse_param_data_paths_with_paramtree(paramtree, args)

        self.assertNotEqual(paramtree.scans.MF.data.dfile, dfile_preset_answer, msg="The dfile entry has not been changed."
                                                                                    "\n dfile=%s" % paramtree.scans.MF.data.dfile)
        self.assertTrue(paramtree.run in paramtree.scans.MF.data.something, msg="the data tree has not been parsed with the .run value"
                                                                                "\n paramtree.scans.MF.data.something=%s" % paramtree.scans.MF.data.something)


if __name__ == '__main__':
    unittest.main()
