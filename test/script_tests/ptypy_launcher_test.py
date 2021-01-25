'''
ptypy_launcher_test

this is specific to diamond arch
needs to check much the same as the other two (parameter passing is different), but mostly should be checking that the
multinode reconstructions work.

'''

import unittest
import tempfile
import shutil
import os
import pytest
import time
import procrunner

from test import utils as tu


@pytest.mark.ptypy
@pytest.mark.cluster
class PtypyLauncherTest(unittest.TestCase):
    def setUp(self):
        self.working_directory = tempfile.mkdtemp(prefix='run_test')
        build_path = os.path.dirname(os.path.abspath(__file__)).split('lib')[0]
        self.launcher_script = os.path.join(build_path, "scripts-3.7/ptychotools.ptypy_launcher")
        self.resources = tu.get_moonflower_info()

    # def tearDown(self):
    #     shutil.rmtree(self.working_directory)

    def test_single_node(self):
        param_dict = {'ptypy_version': 'ptycho-tools/stable',
                      'cluster_queue': 'HAMILTON',
                      'total_num_processors': 40,
                      'num_gpus_per_node': 4,
                      'gpu_arch': 'Pascal',
                      'project': 'i08-1',
                      'log_directory': self.working_directory,
                      'single_threaded': 'false'}
        config_path = os.path.join(self.working_directory, 'test_config.txt')
        write_cluster_config_file(config_path, param_dict)

        inputs = {}
        inputs['run_scripts'] = self.launcher_script
        inputs['config'] = self.resources['config']
        inputs['working_directory'] = self.working_directory
        inputs['identifier'] = 'scan1'
        inputs['cluster_config'] = config_path
        command = "%(run_scripts)s -c %(cluster_config)s -j %(config)s -o %(working_directory)s -i %(identifier)s \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command.encode('utf-8'), working_directory=self.working_directory)

        self.assertEqual(out['exitcode'], 0)
        # magic to extract the job id from the stdout
        job_id = [ix for ix in out['stdout'].split(b'\n') if b'jobid' in ix][0].split(b'jobid:')[-1]
        print(job_id)


        out_dict = grab_qacct(self.working_directory, job_id, sleeptime=10, ntries=10)

        self.assertEqual(out_dict[b'failed'], b'0', msg="The job failed, with qacct.failed !=0. Was: %s" % out_dict[b'failed'])
        self.assertEqual(out_dict[b'exit_status'], b'0', msg="The exit status was !=0. Was %s" % out_dict[b'exit_status'])

    def test_multinode(self):
        param_dict = {'ptypy_version': 'ptycho-tools/stable',
                      'cluster_queue': 'HAMILTON',
                      'total_num_processors': 80,
                      'num_gpus_per_node': 4,
                      'gpu_arch': 'Pascal',
                      'project': 'i08-1',
                      'log_directory': self.working_directory,
                      'single_threaded': 'false'}
        config_path = os.path.join(self.working_directory, 'test_config.txt')
        write_cluster_config_file(config_path, param_dict)

        inputs = {}
        inputs['run_scripts'] = self.launcher_script
        inputs['config'] = self.resources['config']
        inputs['working_directory'] = self.working_directory
        inputs['identifier'] = 'scan1'
        inputs['cluster_config'] = config_path
        command = "%(run_scripts)s -c %(cluster_config)s -j %(config)s -o %(working_directory)s -i %(identifier)s \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command.encode('utf-8'), working_directory=self.working_directory)
        self.assertEqual(out['exitcode'], 0)
        # magic to extract the job id from the stdout
        job_id = [ix for ix in out['stdout'].split(b'\n') if b'jobid' in ix][0].split(b'jobid:')[-1]

        print(job_id)

        # print("Waiting for job id %s" % job_id)
        out_dict = grab_qacct(self.working_directory, job_id, sleeptime=10, ntries=10)

        self.assertEqual(out_dict[b'failed'], b'0', msg="The job failed, with qacct.failed !=0. Was: %s" % out_dict[b'failed'])
        self.assertEqual(out_dict[b'exit_status'], b'0', msg="The exit status was !=0. Was %s" % out_dict[b'exit_status'])


    def test_batch_submission(self):
        param_dict = {'ptypy_version': 'ptycho-tools/stable',
                      'cluster_queue': 'HAMILTON',
                      'total_num_processors': 40,
                      'num_gpus_per_node': 4,
                      'gpu_arch': 'Pascal',
                      'project': 'i08-1',
                      'log_directory': self.working_directory,
                      'single_threaded': 'false'}
        config_path = os.path.join(self.working_directory, 'test_config.txt')
        write_cluster_config_file(config_path, param_dict)

        # write a .ptypy file
        ptypy_batch_file = os.path.join(self.working_directory, 'batch_numbers.ptypy')
        with open(ptypy_batch_file, 'w') as f:
            f.write('scan1\nscan2\n')


        inputs = {}
        inputs['run_scripts'] = self.launcher_script
        inputs['config'] = self.resources['config']
        inputs['working_directory'] = self.working_directory
        inputs['identifier'] = ptypy_batch_file
        inputs['cluster_config'] = config_path
        command = "%(run_scripts)s -c %(cluster_config)s -j %(config)s -o %(working_directory)s -i %(identifier)s \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command.encode('utf-8'), working_directory=self.working_directory)

        self.assertEqual(out['exitcode'], 0)
        # magic to extract the job id from the stdout


        lines_with_job_ids_in = [ix for ix in out['stdout'].split(b'\n') if b'jobid' in ix]
        job_ids = [ix.split(b'jobid:')[-1] for ix in lines_with_job_ids_in]
        print(job_ids)

        for job_id in job_ids:
            out_dict = grab_qacct(self.working_directory, job_id, sleeptime=10, ntries=10)
            self.assertEqual(out_dict[b'failed'], b'0', msg="The job failed, with qacct.failed !=0. Was: %s" % out_dict[b'failed'])
            self.assertEqual(out_dict[b'exit_status'], b'0', msg="The exit status was !=0. Was %s" % out_dict[b'exit_status'])

    def test_linked_submission(self):
        param_dict = {'ptypy_version': 'ptycho-tools/dlsSD12020',
                      'cluster_queue': 'HAMILTON',
                      'total_num_processors': 40,
                      'num_gpus_per_node': 4,
                      'gpu_arch': 'Pascal',
                      'project': 'i08-1',
                      'log_directory': self.working_directory,
                      'single_threaded': 'false'}
        config_path = os.path.join(self.working_directory, 'test_config.txt')
        write_cluster_config_file(config_path, param_dict)

        # write a .ptypy file
        ptypy_batch_file = os.path.join(self.working_directory, 'batch_numbers.ptypy')
        with open(ptypy_batch_file, 'w') as f:
            f.write('scan1\nscan2\n')


        inputs = {}
        inputs['run_scripts'] = self.launcher_script
        inputs['config'] = self.resources['config']
        inputs['working_directory'] = self.working_directory
        inputs['identifier'] = ptypy_batch_file
        inputs['cluster_config'] = config_path
        # this gains a -l for linking the submissions

        command = "%(run_scripts)s -c %(cluster_config)s -j %(config)s -o %(working_directory)s -i %(identifier)s -l \n" % inputs

        print(command)
        out = procrunner.run(["/bin/bash"], stdin=command.encode('utf-8'), working_directory=self.working_directory)

        self.assertEqual(out['exitcode'], 0)
        # magic to extract the job id from the stdout
        lines_with_job_ids_in = [ix for ix in out['stdout'].split(b'\n') if b'jobid' in ix]
        job_ids = [ix.split(b'jobid:')[-1] for ix in lines_with_job_ids_in]
        print(job_ids)
        njobs = len(job_ids)
        self.assertEqual(njobs, 1, msg="More than one job was submitted. Linking probably isn't failing.%s jobs submitted." % njobs)
        print(job_ids)
        # should only be one job
        out_dict = grab_qacct(self.working_directory, job_ids[0], sleeptime=10, ntries=10)
        self.assertEqual(out_dict[b'failed'], b'0', msg="The job failed, with qacct.failed !=0. Was: %s" % out_dict[b'failed'])
        self.assertEqual(out_dict[b'exit_status'], b'0', msg="The exit status was !=0. Was %s" % out_dict[b'exit_status'])



def write_cluster_config_file(fpath, parameters_dict):
    cluster_config = 'PTYPY_VERSION=%(ptypy_version)s\n' \
                     'CLUSTER_QUEUE=%(cluster_queue)s\n' \
                     'TOTAL_NUM_PROCESSORS=%(total_num_processors)s\n' \
                     'NUM_GPUS_PER_NODE=%(num_gpus_per_node)s\n' \
                     'GPU_ARCH=%(gpu_arch)s\n' \
                     'PROJECT=%(project)s\n' \
                     'LOG_DIRECTORY=%(log_directory)s\n' \
                     'SINGLE_THREADED=%(single_threaded)s\n' \
                     '\n' % parameters_dict
    with open(fpath, 'w') as f:
        f.write(cluster_config)


def grab_qacct(working_directory, job_id, sleeptime, ntries=1):

    qacct_params = " ".join(["qacct", "-j", job_id.decode('utf-8')])
    k = 0
    arrived = False
    command = "\n".join([". /etc/profile.d/modules.sh", "module load hamilton-quiet", qacct_params])

    while (not arrived) and (k < ntries):
        # try this
        out = procrunner.run(["/bin/bash"],
                             stdin=command.encode('utf-8'),
                             working_directory=working_directory)

        if not out['stdout']:
            # oh well sleep and try again unless we are out of tries?
            print("Not arrived.")
            k += 1
            time.sleep(sleeptime)
            continue
        else:
            # dump to a file for further inspection
            arrived = out['stdout'].split(b'\n')

    # now parse the outputs
    outputs = {}
    # print("arrived")
    # print(arrived)
    # print(type(arrived))
    for line in arrived:
        if len(line) > 0:
            if line[0] == b"#":
                continue
            a = line.strip().split(b" ")
            key = a[0]
            val = a[-1]
            outputs[key] = val
    return outputs


if __name__ == '__main__':
    unittest.main()
