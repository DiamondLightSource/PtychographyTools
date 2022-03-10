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
    darkframe = Qt.pyqtSignal(int)
    connected = Qt.pyqtSignal()
    disconnected = Qt.pyqtSignal()
    def __init__(self, src=None):
        super(DataHandler, self).__init__()
        self.ctx = Context("pva", nt=False)
        self.src = src
        self.dark = None
        self.sub = None
        self.frame = None
        self.processed = False
        self.livefft = False

    def start_service(self):
        """
        Start listening to data from EPICS
        """
        self.sub = self.ctx.monitor(self.src, self.process_frame)
        self.connected.emit()

    def stop_service(self):
        """
        Stop listening to data from EPICS
        """
        if self.sub is not None:
            self.sub.close()
            self.disconnected.emit()
        
    def source_updated(self, src):
        """
        Check the source string
        """
        self.src = src
        
    def update_processed(self, state):
        """
        Toggle status for processed
        """
        self.processed = (state == 2)

    def update_live_fft(self, state):
        """
        Toggle status for live fft
        """
        self.livefft = (state == 2)

    def save_dark_frame(self):
        """
        Save the current frame as dark
        """
        if self.frame is not None:
            self.dark = np.copy(self.frame)
            self.darkframe.emit(time.time())

    def process_frame(self, pv):
        """
        Receive detector frame from EPICS PV 
        and process it
        """
        shape = (pv["dimension"][0]["size"], pv["dimension"][1]["size"])
        self.frame = np.array(pv["value"]).reshape(shape)
        if self.processed and (self.dark is not None):
            corrected = self.frame - self.dark
            corrected[self.frame<self.dark] = 0
            self.frame = corrected
        if self.livefft:
            self.frame = np.abs(np.fft.ifft2(self.frame))
        self.newframe.emit()
