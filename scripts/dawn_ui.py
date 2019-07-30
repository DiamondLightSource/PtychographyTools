'''
THis is a hack to work with the dawn gui
'''


import sys
import logging
from datetime import datetime
import subprocess
import scisoftpy as dnp
import os
import time
import numpy as np
from scipy.linalg import eig
import h5py as h5
import logging
import procrunner
import glob


def cabs2(A):
    """
    Squared absolute value for an arraobject_y `A`.
    If `A` is compleobject_x, the returned value is compleobject_x as well, with the
    imaginarobject_y part of zero.
    """
    return A * A.conj()


def abs2(A):
    """
    Squared absolute value for an arraobject_y `A`.
    """
    return cabs2(A).real

def norm2(A):
    """
    Squared norm
    """
    return np.sum(abs2(A))

def ortho(modes):
    """\
    Orthogonalize the given list of modes or ndarraobject_y along first aobject_xis.
    **specifobject_y procedure**

    Parameters
    ----------
    modes : arraobject_y-like or list
        List equallobject_y shaped arraobject_ys or arraobject_y of higher dimension

    Returns
    -------
    amp : vector
        relative power of each mode
    nplist : list
        List of modes, sorted in descending order
    """
    N = len(modes)
    A = np.array([[np.vdot(p2,p1) for p1 in modes] for p2 in modes])
    e, v = eig(A)
    ei = (-e).argsort()
    nplist = [sum(modes[i] * v[i,j] for i in range(N)) for j in ei]
    amp = np.array([norm2(npi) for npi in nplist])
    amp /= amp.sum()
    return amp, nplist

def update_plot_from_ptyr(fpath, border=50):
    f = h5.File(fpath, 'r')
    obj = f['/content/obj']
    obj = obj[obj.keys()[0]]
    object_x, object_y = obj['grids'][...]
    object_x = object_x[0, :, 0]
    object_y = object_y[0, 0, :]
    object_x = object_x[border:-border]
    object_y = object_y[border:-border]
    obj_data = obj['data'][0, border:-border, border:-border]
    # print len(object_x), obj_data.shape
    dnp.plot.image(np.abs(obj_data), {'x/ mm':object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Modulus', resetaxes=True)
    dnp.plot.image(np.angle(obj_data),{'x/ mm':object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Phase', resetaxes=True)
    dnp.plot.image(obj_data, {'x/ mm': object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Complex', resetaxes=True)

    probe = f['/content/probe']
    probe = probe[probe.keys()[0]]
    probe_x, probe_y = probe['grids'][...]
    # print probe_x.shape, probe_y.shape
    probe_x = probe_x[0, :, 0]
    probe_y = probe_y[0, 0, :]
    amp_list, probe_data = ortho(probe['data'])
    probe_data = probe_data[0]
    # print probe_data.shape, probe_y.shape
    dnp.plot.image(np.angle(probe_data),{'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Phase')
    # print probe_data.shape
    dnp.plot.image(np.abs(probe_data),{'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Modulus')
    dnp.plot.image(probe_data,{'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Complex')

def initialise_dawn_windows():
    dnp.plot.window_manager.open_view('Object Modulus')
    dnp.plot.window_manager.open_view('Object Phase')
    dnp.plot.window_manager.open_view('Object Complex')

    dnp.plot.window_manager.open_view('Probe Phase')
    dnp.plot.window_manager.open_view('Probe Modulus')
    dnp.plot.window_manager.open_view('Probe Complex')


class DawnUI(object):

    def __init__(self, config_file, output_directory, identifier, beamline, launcher_script, cluster_config):
        self.log_file = None
        self._cluster_job = None
        self.config_file = config_file
        self.output_directory = output_directory
        self.identifier = identifier
        self.beamline = beamline
        self.launcher_script = launcher_script
        self._cluster_config = self.cluster_config_from_file(cluster_config)
        self.ptypy_version = self._cluster_config['PTYPY_VERSION']
        self.scan_directory = os.path.join(self.output_directory, "scan_%s" % str(self.identifier))
        self.dumps_directory = os.path.join(self.scan_directory, "dumps", self.identifier)
        self.final_file = os.path.join(self.scan_directory, "scan_%s.ptyr" % self.identifier)
        self.current_log_line_number = -1
        self.plot_files_list = []
        self.reconstruction_finished = False
        self.latest_ptyr = None
        self.create_log_file()

    def cluster_config_from_file(self, fpath):
        d = {}
        with open(fpath, 'r') as f:
            for line in f:
                if '=' in line:
                    key, val = line.split('=')
                    d[key] = val.strip('\n')
        return d

    def create_log_file(self):
        logdir = self.scan_directory
        print("Logging going in: %s" % logdir   )
        if not os.path.exists(logdir):
            os.makedirs(logdir, 0o777)
        self.log_file = os.path.join(logdir, "i14_ptypy_gui.%s" % datetime.strftime(datetime.now(), "%y%m%d_%H%M%S_%f"))
        f = open(self.log_file, 'w+')
        f.close()
        os.chmod(self.log_file, 0o775)

    def launch_cluster_job(self):
        total_processors = self._cluster_config["TOTAL_NUM_PROCESSORS"]
        qsub_params = " ".join(["qsub",
                                "-terse", " "
                                "-N", "ptypy_gui_%s" % self.beamline,
                                "-P", self.beamline,
                                "-pe", "openmpi", total_processors,
                                "-l", "exclusive",
                                "-l", "gpu=" + self._cluster_config["NUM_GPUS_PER_NODE"],
                                "-l", "gpu_arch=" + self._cluster_config["GPU_ARCH"],
                                "-o", self.log_file,
                                "-e", self.log_file,
                                "/dls_sw/apps/ptychography_tools/latest/scripts/ptypy_mpi_recipe",
                                "-j", self.config_file,
                                "-i", self.identifier,
                                "-o", self.output_directory,
                                "-v", self._cluster_config["PTYPY_VERSION"],
                                "-n", total_processors,
                                "-s", self._cluster_config["SINGLE_THREADED"],
                                "-z", self.log_file])

        commands = (". /etc/profile.d/modules.sh",
                    "module load global/hamilton",
                    qsub_params)
        sin = "\n".join(commands)
        out = procrunner.run(["/bin/bash"], stdin=sin, working_directory=self.output_directory)
        assert out['exitcode']==0
        print("Cluster job is:%s" % str(out["stdout"]))
        self._cluster_job = out["stdout"]

    def kill_cluster_job(self):
        print("trying to kill cluster job")
        qdel_command = 'qdel %s' % self._cluster_job
        commands = (". /etc/profile.d/modules.sh",
                    "module load global/hamilton",
                    qdel_command)
        out = procrunner.run(["/bin/bash"], stdin="\n".join(commands), working_directory=self.output_directory)
        assert out['exitcode']==0
        print("Cluster job killed.")

    def read_log(self):
        '''
        Could check to see the file modification time,
        '''
        print(".")
        idx = -1
        with open(self.log_file, 'r') as f:
            for line in f:
                idx += 1
                if idx > self.current_log_line_number:
                    print(line) # this should probably not be here
        self.current_log_line_number = idx

    def update_plots(self, ptyr_file):
        update_plot_from_ptyr(ptyr_file, border=50)

    def get_latest_ptyr_file(self):
        # first check to see if the final one is there
        if os.path.exists(self.final_file):
            latest_file = self.final_file
            self.reconstruction_finished = True
        else:
            files = glob.glob(os.path.join(self.dumps_directory, "*.ptyr"))
            files.sort(key=os.path.getmtime)
            if len(files)<1:
                return None
            else:
                latest_file = os.path.join(self.dumps_directory, files[-1])

        if latest_file==self.latest_ptyr:
            return None
        else:
            self.latest_ptyr = latest_file
            return latest_file


if __name__ == '__main__':
    try:
        logger = logging.getLogger()

        # Default level - should be changed as soon as possible

        logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.DEBUG)
        # Create console handler


        _name, processing_directory, config_name_in_processing_directory, scan_number = sys.argv
        beamline = os.environ['BEAMLINE']
        initialise_dawn_windows()
        config_file = os.path.join(processing_directory,  config_name_in_processing_directory)
        output_directory = os.path.join(processing_directory, "ptychography")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory, 0o777)

        launcher_script = '/dls_sw/apps/ptychography_tools/latest/scripts/ptypy_launcher'
        cluster_config = '/dls_sw/apps/ptychography_tools/cluster_configurations/%s.txt' % beamline
        dawn_job = DawnUI(config_file, output_directory, scan_number, beamline, launcher_script, cluster_config)
        dawn_job.create_log_file()
        dawn_job.launch_cluster_job()
        while True:
            dawn_job.read_log()
            latest_ptyr = dawn_job.get_latest_ptyr_file()
            if latest_ptyr is not None:
                while True:
                    try:
                        print("Trying to update plot from %s" % latest_ptyr)
                        update_plot_from_ptyr(latest_ptyr, border=50)
                        print("Found file, updated")
                        break
                    except IOError:
                        print("Couldn't read file. File system blah, sleeping for 5 seconds")
                        time.sleep(5.) # make sure the file is closed
            if dawn_job.reconstruction_finished:
                break
            time.sleep(3.)
    except KeyboardInterrupt, SystemExit:
        print("Keyboard interrupt! Killing cluster job....")
        dawn_job.kill_cluster_job()
        print("Done")
