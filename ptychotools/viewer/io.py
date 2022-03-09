#!/usr/bin/env python
import glob, h5py, time
import sys, os
import numpy as np
from PyQt5 import Qt

# Interface with EPICS
from p4p.client.thread import Context

class DataHandler(Qt.QObject):
    """
    Data I/O class.

    listens to data provided by EPICS pvAccess.
    """
    newframe = Qt.pyqtSignal()
    connected = Qt.pyqtSignal()
    disconnected = Qt.pyqtSignal()
    def __init__(self):
        super(DataHandler, self).__init__()
        self.ctx = Context("pva", nt=False)
        self.src = None
        self.sub = None
        self.frame = None

    def start_service(self):
        """
        Start listening to data from EPICS
        """
        print("Start")
        self.sub = self.ctx.monitor(self.src, self.process_frame)
        self.connected.emit()

    def stop_service(self):
        """
        Stop listening to data from EPICS
        """
        print("Stop")
        if self.sub is not None:
            self.sub.close()
            self.disconnected.emit()
        
    def source_updated(self, src):
        """
        Check the source string
        """
        print("Source = ", src)
        self.src = src
        
    def save_dark_frame(self):
        """
        Save the current frame as dark
        """
        print("Save dark")

    def process_frame(self, pv):
        """
        Receive detector frame from EPICS PV 
        and process it
        """
        shape = (pv["dimension"][0]["size"], pv["dimension"][1]["size"])
        self.frame = np.array(pv["value"]).reshape(shape)
        self.newframe.emit()
        

    # def init_rundict_from_path(self):
    #     self.latest = 0
    #     self.flist = glob.glob(self.path + "/*.ptyr")
    #     self.flist.sort(key=os.path.getmtime)
    #     tlist = []
    #     for fname in self.flist:
    #         print("Reading", fname)
    #         try:
    #             with h5py.File(fname, "r") as f:
    #                 t = self.convert_time(f['content/runtime/start'][...])
    #                 if t > self.latest:
    #                     self.latest = t
    #                 tlist.append(t)
    #             print(fname, time.ctime(os.path.getmtime(fname)), time.ctime(t))
    #         except:
    #             continue
    #     self.flist = [f for f,t in zip(self.flist, tlist) if (t == self.latest)]
    #     self.flist.sort(key=os.path.getmtime)
    #     self.iteration = []
    #     self.errors = []
    #     for fname in self.flist:
    #         with h5py.File(fname, "r") as f:
    #             i, e, d = self.get_iter_info(f)
    #             self.iteration.append(i)
    #             self.errors.append(e)
    #     self.prshape = self.get_probe(self.flist[0]).shape
    #     self.obshape = self.get_object(self.flist[0]).shape
    #     self.lasttime = os.path.getmtime(self.flist[-1])
    #     print("Latest", time.ctime(self.lasttime), self.flist[-1])
    #     print("Found {:d} files in {:s}".format(len(self.flist), self.path))

    # def convert_time(self, arr):
    #     return time.mktime(time.strptime(str(arr.astype(str))))

    # def get_iter_info(self, f):
    #     iterdict = {}
    #     info = f["content/runtime/iter_info"]
    #     iterdict["fname"] = f.filename
    #     if not len(info):
    #         return 0, np.array([0,0,0]), iterdict
    #     id = list(info.keys())[0]
    #     for k,v in info[id].items():
    #         iterdict[k] = v[...]
    #     return int(iterdict["iteration"]), iterdict["error"], iterdict

    # def check(self):
    #     self.check_for_new_files_in_path()

    # def check_for_new_files_in_path(self):
    #     curfiles = glob.glob(self.path + "/*.ptyr")
    #     curfiles.sort(key=os.path.getmtime)
    #     for cf in curfiles:
    #         ct = os.path.getmtime(cf)
    #         if ct <= self.lasttime:
    #             continue
    #         if cf in self.flist:
    #             #print("file list: ", self.flist)
    #             #print("latest: ", self.flist[-1])
    #             #print("found existing file: ", cf, ct>self.lasttime)
    #             if (ct - self.lasttime) > 20:
    #                 print("new recons has started")
    #                 time.sleep(5)
    #                 self.init_rundict_from_path()
    #                 self.newiter.emit(-1)
    #                 return            
    #             continue
    #         if (time.time() - ct) < 1:
    #             continue
    #         #with h5py.File(cf, "r") as f:
    #         #    t = self.convert_time(f["content/runtime/start"][...])
    #         try:
    #             with h5py.File(cf, "r") as f:
    #                 i, e, d = self.get_iter_info(f)
    #             self.flist.append(cf)
    #             self.iteration.append(i)
    #             self.errors.append(e)
    #             self.lasttime = ct
    #             self.newiter.emit(-1)
    #         except:
    #             continue

    # def get_object(self, fname):
    #     with h5py.File(fname, "r") as f:
    #         obh = f["content/obj"]
    #         return obh[list(obh)[0]]["data"][:]

    # def get_probe(self, fname):
    #     with h5py.File(fname, "r") as f:
    #         prh = f["content/probe"]
    #         return prh[list(prh)[0]]["data"][:]
