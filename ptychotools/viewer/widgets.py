#!/usr/bin/env python
from PyQt5 import QtWidgets, Qt,  uic
import os, sys
import matplotlib.cm as cm
import pyqtgraph as pg
import numpy as np

# Load UIs
curdir = os.path.dirname(os.path.realpath(__file__))
UiControlWidget, _ = uic.loadUiType(curdir + '/ui/control.ui')
UiCanvasWidget, _ = uic.loadUiType(curdir + '/ui/canvas.ui')
#UiParamWidget, _ = uic.loadUiType(curdir + '/ui/params.ui')
#UiProbeWidget, _ = uic.loadUiType(curdir + '/ui/probeview.ui')
#UiRuntimeWidget, _ = uic.loadUiType(curdir + '/ui/runtimeview.ui')

# Control widget class - the interaction panel
class ControlView(QtWidgets.QWidget, UiControlWidget):
    """
    Control widget class.

    User interaction.
    """
    def __init__(self):
        super(ControlView, self).__init__()
        self.setupUi(self)
    def update_source(self, src):
        if src is not None:
            print("Setting source", src)
            self.source.setText(src)
    def processed_changed(self, checked):
        self.processed.setEnabled(checked)
    def live_fft_changed(self, checked):
        self.live_fft.setEnabled(checked)

# Canvas widget class - the frame viewer
class Canvas(QtWidgets.QWidget, UiCanvasWidget):
    """
    Object widget class.

    Displays the current object(s).
    """
    def __init__(self, cmap="viridis"):
        super(Canvas, self).__init__()
        self.setupUi(self)
        self.setColormap(cmap)
        self.setViewBox()
        self.vmin = None
        self.vmax = None

    def setViewBox(self):
        vb = self.frameview.addViewBox(row=0, col=0, lockAspect=True, enableMouse=True, invertY=True)
        self.im = pg.ImageItem(np.zeros((128,128)), autoDownsample=True, lut=self.cmap)
        vb.addItem(self.im)
            
    def setColormap(self, cmap):
        self.cmap = getattr(cm, cmap)(np.arange(256))[:,:3] * 255

    def drawFrame(self, frame):
        if self.vmin is None:
            self.vmin = frame.min()
        if self.vmax is None:
            self.vmax = frame.max()
        self.im.setImage(frame.transpose(), autolevels=False, lut=self.cmap)
        self.im.setLevels((self.vmin, self.vmax))

# # Param widget class - the parameter display
# class ParamView(QtWidgets.QWidget, UiParamWidget):
#     """
#     Param widget class.

#     Displays all ptypy parameters.
#     """
#     def __init__(self):
#         super(ParamView, self).__init__()
#         self.setupUi(self)


# # Probe widget class - the probe display
# class ProbeView(QtWidgets.QWidget, UiProbeWidget):
#     """
#     Probe widget class.

#     Displays the current probe(s).
#     """
#     def __init__(self, **kwargs):
#         super(ProbeView, self).__init__()
#         self.setupUi(self)
#         self.complex = View(self.complexview, **kwargs)


# # Runtime widget class - the runtime display
# class RuntimeView(QtWidgets.QWidget, UiRuntimeWidget):
#     """
#     Runtime widget class.

#     Displays the current runtime errors.
#     """
#     def __init__(self):
#         super(RuntimeView, self).__init__()
#         self.setupUi(self)
#         self.canvas.setLogMode(y=True)
        
#     def draw_errors(self, iterations, errors):
#         self.canvas.plot(x=iterations[1:], y=errors[1:,0]/errors[:,0].max(), 
#                          clear=True,  pen=(0,255,255))
#         self.canvas.plot(x=iterations[1:], y=errors[1:,1]/errors[:,1].max(), 
#                          clear=False, pen=(0,0,255))
#         self.canvas.plot(x=iterations[1:], y=errors[1:,2]/errors[:,2].max(), 
#                          clear=False, pen=(255,255,0))
