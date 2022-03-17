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
    def __init__(self, cmap="gray", log=False):
        super(Canvas, self).__init__()
        self.setupUi(self)
        self.vmin = None
        self.vmax = None
        self.islog = log
        self.original = None
        self.transformed = None
        self.setupScene()
        self.setColormap(cmap)

    def setupScene(self):
        self.scene = self.frameview.scene()
        self.view = pg.ViewBox(lockAspect=True, enableMouse=True, invertY=True, enableMenu=True)
        self.view.suggestPadding = lambda *_: 0.0
        self.frameview.setCentralItem(self.view)
        self.im = pg.ImageItem(np.ones((128,128)), autoDownsample=True)
        self.view.addItem(self.im)
        self.frameview.setMouseTracking(True)
                
    def setColormap(self, cmap):
        self.cmap = getattr(cm, cmap)(np.arange(256))[:,:3] * 255
        self.replot()

    def setLogarithmic(self, status):
        self.islog = status
        self.replot()

    def transform(self, value):
        if self.islog:
            trans = np.log(value+1e-5)
        else:
            trans = value
        return trans

    def drawFrame(self, frame):
        self.original = frame
        self.replot()

    def replot(self):
        if self.original is None:
            return
        self.transformed = self.transform(self.original)
        #if self.vmin is None:
        self.vmin = self.transformed.min()
        #if self.vmax is None:
        self.vmax = self.transformed.max()

        self.im.setImage(self.transformed.transpose(), autolevels=False, lut=self.cmap)
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
