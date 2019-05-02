'''
Useful operations for ptypy_parameters

'''
import json
import ptypy.utils as u
from ptypy.core import Ptycho
import logging
import json
import yaml


def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data


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
    generates a json file from a param tree
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
    generates a ptypy param tree from a json file
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
    in_dict = json.load(open(json_file), object_hook=_byteify)
    parameters_to_run = u.Param()
    if in_dict['base_file'] is not None:
        logging.debug("Basing this scan off of the scan in {}".format(in_dict['base_file']))
        previous_scan = Ptycho.load_run(in_dict['base_file'], False)  # load in the run but without the data
        previous_parameters = previous_scan.p
        parameters_to_run.update(previous_parameters)
    if in_dict['parameter_tree'] is not None:
        parameters_to_run.update(in_dict['parameter_tree'], Convert=True)
    return parameters_to_run

def parse_param_data_paths_with_paramtree(paramtree):
    '''
    This does a string replacement in any str paths in the .data subtree using
    items like .run in the top level tree.
    :param json_file: the path the json file
    :return: a Param based structure.
    '''
    for scan_key, scan in paramtree.scans.iteritems():
        data_entry = scan.data
        for sub_entry_key, sub_entry in data_entry.iteritems():
            if isinstance(sub_entry, dict):
                for dict_entry_key, dict_entry in sub_entry.iteritems():
                    if isinstance(dict_entry, str):
                        sub_entry[dict_entry_key] = dict_entry % paramtree
            elif isinstance(sub_entry, str):
                data_entry[sub_entry_key] = sub_entry % paramtree