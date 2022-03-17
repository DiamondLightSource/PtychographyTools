#!/usr/bin/env python
from PyQt5 import QtWidgets, QtCore, Qt,  uic
import os, sys, time
import matplotlib.cm as cm
import pyqtgraph as pg
import numpy as np

# Load UIs
curdir = os.path.dirname(os.path.realpath(__file__))
UiControlWidget, _ = uic.loadUiType(curdir + '/ui/control.ui')
UiCanvasWidget, _ = uic.loadUiType(curdir + '/ui/canvas.ui')
#UiParamWidget, _ = uic.loadUiType(curdir + '/ui/params.ui')

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
            self.source.setText(src)
    def update_dark(self, timestamp):
        self.save_dark_status.setText("Latest dark frame: %s" %(time.ctime(timestamp)))
        self.processed.setEnabled(True)

class Canvas(QtWidgets.QWidget, UiCanvasWidget):
    """
    Canvas widget class.

    Displaying images.
    """
    def __init__(self, cmap="gray"):
        super(Canvas, self).__init__()
        self.setupUi(self)
        self.setColormap(cmap)
        self.setupScene()
        self.vmin = None
        self.vmax = None

    def setupScene(self):
        self.scene = self.frameview.scene()
        self.view = pg.ViewBox(lockAspect=True, enableMouse=True, invertY=True, enableMenu=True)
        self.view.suggestPadding = lambda *_: 0.0
        self.frameview.setCentralItem(self.view)
        self.im = pg.ImageItem(np.zeros((128,128)), autoDownsample=True, lut=self.cmap)
        self.view.addItem(self.im)
        self.frameview.setMouseTracking(True)
        #self.frameview.setContentsMargins(QtCore.QMargins())
                
    def setColormap(self, cmap):
        #N = 1000
        #X = np.linspace(1,N*10,N)
        C = np.arange(256)
        #C = 255 * (X / X.max())
        self.cmap = getattr(cm, cmap)(C)[:,:3] * 255
        #clog = np.log(getattr(cm, cmap)(C)[:,:3])
        #self.cmap = 255 * (clog / clog.max())
        #print(np.log(getattr(cm, cmap)(C)[:,:3]))

    def drawFrame(self, frame):
        #if self.vmin is None:
        self.vmin = frame.min()
        #if self.vmax is None:
        self.vmax = frame.max()
        self.im.setImage(frame.transpose(), autolevels=False, lut=self.cmap)
        self.im.setLevels((self.vmin, self.vmax))

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
