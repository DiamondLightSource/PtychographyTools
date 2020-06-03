'''
Useful operations for ptypy_parameters
'''

import json
import ptypy.utils as u
from ptypy.core import Ptycho
import logging
import json
import yaml
from .io import get_output_folder_name

def paramtree_to_json(paramtree, basefile, filepath):
    '''
    generates a json file from a param tree
    :param paramtree: The ptypy parameter tree to save out.
    :param basefile: An existing ptyr file that we are basing this tree on.
    :param filepath: the path the json file
    :return: a Param based structure.
    '''

    save_dict = {}
    save_dict['base_file'] = basefile
    save_dict['parameter_tree'] = paramtree._to_dict(Recursive=True)
    to_write_json = json.dumps(save_dict, indent=4, sort_keys=True)
    with open(filepath, 'w') as f:
        f.write(to_write_json)


def paramtree_to_yaml(paramtree, basefile, filepath):
    '''
    generates a yaml file from a param tree
    :param paramtree: The ptypy parameter tree to save out.
    :param basefile: An existing ptyr file that we are basing this tree on.
    :param filepath: the path the json file
    :return: a Param based structure.
    '''

    save_dict = {}
    save_dict['base_file'] = basefile
    save_dict['parameter_tree'] = paramtree._to_dict(Recursive=True)
    to_write_yaml = yaml.dump(save_dict)#, Dumper=yaml.SafeDumper)
    with open(filepath, 'w') as f:
        f.write(to_write_yaml)


def paramtree_from_yaml(yaml_file):
    '''
    generates a ptypy param tree from a yaml file
    :param json_file: the path the json file
    :return: a Param based structure.
    '''
    in_dict = yaml.load(open(yaml_file), Loader=yaml.FullLoader)
    parameters_to_run = u.Param()
    if in_dict['base_file'] is not None:
        logging.debug("Basing this scan off of the scan in {}".format(in_dict['base_file']))
        previous_scan = Ptycho.load_run(in_dict['base_file'], False)  # load in the run but without the data
        previous_parameters = previous_scan.p
        parameters_to_run.update(previous_parameters)
    if in_dict['parameter_tree'] is not None:
        parameters_to_run.update(in_dict['parameter_tree'], Convert=True)
    return parameters_to_run


def paramtree_from_json(json_file):
    '''
    generates a ptypy param tree from a json file
    :param json_file: the path the json file
    :return: a Param based structure.
    '''
    in_dict = json.load(open(json_file))#, object_hook=byteify)
    parameters_to_run = u.Param()
    if in_dict['base_file'] is not None:
        logging.debug("Basing this scan off of the scan in {}".format(in_dict['base_file']))
        previous_scan = Ptycho.load_run(in_dict['base_file'], False)  # load in the run but without the data
        previous_parameters = previous_scan.p
        parameters_to_run.update(previous_parameters)
    if in_dict['parameter_tree'] is not None:
        parameters_to_run.update(in_dict['parameter_tree'], Convert=True)
    return parameters_to_run


def parse_param_data_paths_with_paramtree(paramtree, args):
    '''
    This does a string replacement in any str paths in the .data subtree using
    items like .run in the top level tree.
    :param json_file: the path the json file
    :return: a Param based structure.
    '''
    for scan_key, scan in paramtree.scans.items():
        data_entry = scan.data
        scan.data.dfile = "%s/scan_%s.ptyd" % (get_output_folder_name(args), str(paramtree.run))
        for sub_entry_key, sub_entry in data_entry.items():
            if isinstance(sub_entry, dict):
                for dict_entry_key, dict_entry in sub_entry.items():
                    if isinstance(dict_entry, str):
                        sub_entry[dict_entry_key] = dict_entry % paramtree
            elif isinstance(sub_entry, str):
                data_entry[sub_entry_key] = sub_entry % paramtree
