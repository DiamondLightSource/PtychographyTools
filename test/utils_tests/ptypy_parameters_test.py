'''
testing for the ptypy_parameters module
'''


import unittest
import pytest
import os
import tempfile
import shutil
import numpy as np
from test import utils as tu


@pytest.mark.ptypy
class PtypyParametersTest(unittest.TestCase):
    def setUp(self):
        self.output_directory = tempfile.mkdtemp(prefix='PtypyParametersTest')

    def tearDown(self):
        shutil.rmtree(self.output_directory)

    def test_paramtree_to_json(self):
        import ptychotools.utils.ptypy_parameters as pp
        p = tu.generate_test_param_tree()
        output_json_path = os.path.join(self.output_directory, 'test.json')
        pp.paramtree_to_json(p, basefile=None, filepath=output_json_path)
        expected_result = open(tu.get_json_path(), 'r').read()
        actual_result = open(output_json_path).read()
        self.assertEqual(expected_result, actual_result, msg="There was a problem converting the paramtree to json."
                                                             "\n expected_result: %s \n\n actual_result: %s \n\n" % (repr(expected_result), repr(actual_result)))

    def test_paramtree_to_yaml(self):
        import ptychotools.utils.ptypy_parameters as pp
        p = tu.generate_test_param_tree()
        output_yaml_path = os.path.join(self.output_directory, 'test.yml')
        pp.paramtree_to_yaml(p, basefile=None, filepath=output_yaml_path)
        expected_result = open(tu.get_yaml_path(), 'r').read()
        actual_result = open(output_yaml_path).read()
        self.assertEqual(expected_result, actual_result, msg="There was a problem converting the paramtree to yaml."
                                                             "\n expected_result: %s \n\n actual_result: %s \n\n" % (repr(expected_result), repr(actual_result)))

    def test_paramtree_from_json(self):
        import ptychotools.utils.ptypy_parameters as pp
        expected_paramtree = tu.generate_test_param_tree()
        real_paramtree = pp.paramtree_from_json(tu.get_json_path())
        self.assertEqual(expected_paramtree, real_paramtree, msg="There was a problem converting the json to paramtree."
                                                                 "\n expected_result: %s \n\n actual_result: %s \n\n" % (repr(expected_paramtree), repr(real_paramtree)))

    def test_paramtree_from_yaml(self):
        import ptychotools.utils.ptypy_parameters as pp
        expected_paramtree = tu.generate_test_param_tree()
        real_paramtree = pp.paramtree_from_yaml(tu.get_yaml_path())
        self.assertEqual(expected_paramtree, real_paramtree, msg="There was a problem converting the yaml to paramtree."
                                                                 "\n expected_result: %s \n\n actual_result: %s \n\n" % (
                                                                     repr(expected_paramtree), repr(real_paramtree)))

    def test_parse_param_data_paths_with_paramtree(self):
        import ptychotools.utils.ptypy_parameters as pp
        dfile_preset_answer = 'cheesecake'
        paramtree = tu.generate_test_param_tree()
        paramtree.run = "1234"
        paramtree.scans.MF.data.dfile = dfile_preset_answer
        paramtree.scans.MF.data.something = "cheese_%(run)s"

        class Args: pass
        args = Args()
        args.output_folder = self.output_directory
        args.identifier = paramtree.run

        pp.parse_param_data_paths_with_paramtree(paramtree, args)

        self.assertNotEqual(paramtree.scans.MF.data.dfile, dfile_preset_answer, msg="The dfile entry has not been changed."
                                                                                    "\n dfile=%s" % paramtree.scans.MF.data.dfile)
        self.assertTrue(paramtree.run in paramtree.scans.MF.data.something, msg="the data tree has not been parsed with the .run value"
                                                                                "\n paramtree.scans.MF.data.something=%s" % paramtree.scans.MF.data.something)

    def test_byteify(self):
        import ptychotools.utils.ptypy_parameters as pp

        inputs = {'unicode_string': u'\u03B8 cheese \u03BA',
                  'list_of_unicode': [u'\u03B8 cheese \u03BA', u'\u03B9 cake \u03BB']
                  }
        expected_outputs = {'unicode_string' : '\xce\xb8 cheese \xce\xba',
                            'list_of_unicode': ['\xce\xb8 cheese \xce\xba', '\xce\xb9 cake \xce\xbb']
                            }

        # first lets test the basic inputs
        for key, val in inputs.iteritems():
            print(key)
            np.testing.assert_equal(expected_outputs[key], pp.byteify(val), err_msg="Could not convert %s" % key)

        # now a dictionary
        output_dict = pp.byteify(inputs)
        self.assertDictEqual(output_dict, expected_outputs)


if __name__ == '__main__':
    unittest.main()
