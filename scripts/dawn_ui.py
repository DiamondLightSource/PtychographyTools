'''
THis is a hack to work with the dawn gui
'''


import sys
import scisoftpy as dnp
import os
import time
import numpy as np
from scipy.linalg import eig
import h5py as h5
import logging
import procrunner
import glob
import re

#sys.path.insert(0, "/dls/science/users/clb02321/DAWN_nightly_broke/latest_master/build/lib")
# sys.path.insert(0, "/dls_sw/apps/ptypy/latest_rhel7/lib.linux-x86_64-2.7")
sys.path.insert(0, "/dls_sw/apps/ptypy/latest_rhel7/lib")
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

def rmphaseramp(a, weight=None, return_phaseramp=False):
    """
    Attempts to remove the phase ramp in a two-dimensional complex array
    ``a``.

    Parameters
    ----------
    a : ndarray
        Input image as complex 2D-array.

    weight : ndarray, str, optional
        Pass weighting array or use ``'abs'`` for a modulus-weighted
        phaseramp and ``Non`` for no weights.

    return_phaseramp : bool, optional
        Use True to get also the phaseramp array ``p``.

    Returns
    -------
    out : ndarray
        Modified 2D-array, ``out=a*p``
    p : ndarray, optional
        Phaseramp if ``return_phaseramp = True``, otherwise omitted

    Examples
    --------
    >>> b = rmphaseramp(image)
    >>> b, p = rmphaseramp(image , return_phaseramp=True)
    """

    useweight = True
    if weight is None:
        useweight = False
    elif weight == 'abs':
        weight = np.abs(a)

    ph = np.exp(1j*np.angle(a))
    [gx, gy] = np.gradient(ph)
    gx = -np.real(1j*gx/ph)
    gy = -np.real(1j*gy/ph)

    if useweight:
        nrm = weight.sum()
        agx = (gx*weight).sum() / nrm
        agy = (gy*weight).sum() / nrm
    else:
        agx = gx.mean()
        agy = gy.mean()

    (xx, yy) = np.indices(a.shape)
    p = np.exp(-1j*(agx*xx + agy*yy))

    if return_phaseramp:
        return a*p, p
    else:
        return a*p

def remove_ramp(unwrapped_phase):
    def make_plane(xsc, xoff, ysc, yoff, const, shape):
        Y, X = np.meshgrid(np.arange(shape[1]), np.arange(shape[0]))
        plane = (xsc * X - xoff) + (ysc * Y + yoff) + const
        return plane

    def resid(x, *args):
        data = args[0]
        pl = make_plane(*x, shape=data.shape)
        return (data - pl).flatten()
    x0 = np.ones((5,))
    from scipy.optimize import leastsq
    fit = leastsq(resid, x0, (unwrapped_phase,), full_output=True)
    pl = make_plane(*fit[0], shape=unwrapped_phase.shape)
    return unwrapped_phase - pl

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
    phase_obj = np.angle(obj_data)
    from skimage.restoration import unwrap_phase
    print("unwrapping phase")
    phase_obj = unwrap_phase(phase_obj)
    phase_obj = remove_ramp(phase_obj)
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

def update_plot_from_zmqdp(dp, border=50):

    probe, obj, meta = dp
    if len(obj.keys())>0:
        scanname= obj.keys()[0]
        print("I am updating the plot from scan: %s" % scanname)
        obj = obj[scanname]

        try:
            obj_data = obj['data'][0, border:-border, border:-border]
            object_x, object_y = obj['grids']
            object_x = object_x[0, :, 0]
            object_y = object_y[0, 0, :]
            object_x = object_x[border:-border]
            object_y = object_y[border:-border]
            # print len(object_x), obj_data.shape
            # print("obj data shape/:%s" % str(obj_data.shape))
            phase_obj = np.angle(obj_data)

            from skimage.restoration import unwrap_phase
            # print("unwrapping phase")
            phase_obj = unwrap_phase(phase_obj)
            phase_obj = remove_ramp(phase_obj)
            # object_x = np.arange(obj_data.shape[0])
            # object_y = np.arange(obj_data.shape[1])
            dnp.plot.image(np.abs(obj_data), {'x/ mm':object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Modulus', resetaxes=True)#, {'x/ mm':object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Modulus', resetaxes=True)
            dnp.plot.image(phase_obj, {'x/ mm':object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Phase', resetaxes=True)#,{'x/ mm':object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Phase', resetaxes=True)
            dnp.plot.image(obj_data, {'x/ mm':object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Complex', resetaxes=True)#, {'x/ mm': object_y/1e-3}, {'y/ mm': object_x/1e-3}, 'Object Complex', resetaxes=True)

            probe = probe[probe.keys()[0]]
            probe_x, probe_y = probe['grids']
            # print probe_x.shape, probe_y.shape
            probe_x = probe_x[0, :, 0]
            probe_y = probe_y[0, 0, :]
            amp_list, probe_data = ortho(probe['data'])
            probe_data = probe_data[0]
            # print probe_data.shape, probe_y.shape
            # print("PLotting data")
            # probe_x = np.arange(probe_data.shape[0])
            # probe_y = np.arange(probe_data.shape[1])
            dnp.plot.image(np.angle(probe_data),{'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Phase')#,{'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Phase')
            # print probe_data.shape
            dnp.plot.image(np.abs(probe_data), {'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Modulus')#,{'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Modulus')
            dnp.plot.image(probe_data, {'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6},'Probe Complex')#,{'x/ micron':probe_y/1e-6}, {'y/ micron': probe_x/1e-6}, 'Probe Complex')
            # print("Data plotted")
        except KeyError as e:
            print("Server has no data to plot.")
            print(e)
            #raise
    else:
        print("Server has no data to plot")
        print("There are no object keys")


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
        self.interaction_ip = None
        self.interaction_port = None
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
        print("Logfile:%s" % self.log_file)

    def launch_cluster_job(self):
        if self.beamline == 'dls':
            project = 'ptychography'
        else:
            project = self.beamline

        total_processors = self._cluster_config["TOTAL_NUM_PROCESSORS"]
        qsub_params = " ".join(["qsub",
                                "-terse", " "
                                "-N", "ptypy_gui_%s" % self.beamline,
                                "-P", project,
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
        print qsub_params

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
                    if not self.interaction_ip:
                        self.interaction_ip = "tcp://"+line.split(':')[1] if re.search("Interaction is broadcast on host:", line) else None
                        self.interaction_port = line.split(':')[2].strip('\n') if re.search("Interaction is broadcast on host:", line) else None
                        # print("ip is:%s and port is: %s" % (self.interaction_ip, self.interaction_port))
        self.current_log_line_number = idx

    def update_plots(self, ptyr_file):
        update_plot_from_ptyr(ptyr_file, border=80)

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

        from datetime import datetime
        now = datetime.now()
        timstmp = now.strftime("%Y%m%d_%H%M%S")
        logger = logging.getLogger()

        # Default level - should be changed as soon as possible

        logging.basicConfig(format='%(asctime)s:%(message)s', level=logging.DEBUG)
        # Create console handler


        _name, processing_directory, config_name_in_processing_directory, scan_number = sys.argv
        beamline = os.environ['BEAMLINE']
        initialise_dawn_windows()
        config_file = os.path.join(processing_directory,  config_name_in_processing_directory)
        output_directory = os.path.join(processing_directory, "ptypy_%s_%s" % (str(scan_number), timstmp))
        if not os.path.exists(output_directory):
            os.makedirs(output_directory, 0o777)

        launcher_script = '/dls_sw/apps/ptychography_tools/latest/scripts/ptypy_launcher'
        cluster_config = '/dls_sw/apps/ptychography_tools/cluster_configurations/%s.txt' % beamline
        dawn_job = DawnUI(config_file, output_directory, scan_number, beamline, launcher_script, cluster_config)
        dawn_job.create_log_file()
        dawn_job.launch_cluster_job()
        just_changed = None
        pc = None
        while True:
            dawn_job.read_log()
            # latest_ptyr = dawn_job.get_latest_ptyr_file()
            # if latest_ptyr is not None:
            #     while True:
            #         try:
            #             print("Trying to update plot from %s" % latest_ptyr)
            #             update_plot_from_ptyr(latest_ptyr, border=50)
            #             print("Found file, updated")
            #             break
            #         except IOError:
            #             print("Couldn't read file. File system blah, sleeping for 5 seconds")
            #             time.sleep(5.) # make sure the file is closed
            if dawn_job.interaction_ip:
                if just_changed is None:
                    print("I am here")
                    from ptypy.utils import PlotClient, Param
                    clip = Param()
                    clip.port = dawn_job.interaction_port
                    clip.address = dawn_job.interaction_ip
                    pc = PlotClient(clip, in_thread=False)
                    pc.start()
                    dp = pc.get_data()
                    just_changed =True
                    update_plot_from_zmqdp(dp, border=80)
                else:
                    print("I am in the else")
                    dp = pc.get_data()
                    update_plot_from_zmqdp(dp, border=80)

            if pc is not None and pc.status == pc.STOPPED:
                break
            time.sleep(5.)
    except KeyboardInterrupt, SystemExit:
        print("Keyboard interrupt! Killing cluster job....")
        dawn_job.kill_cluster_job()
        print("Done")
