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

# Control widget class - the interaction panel
class ControlView(QtWidgets.QWidget, UiControlWidget):
    """
    Control widget class.

    User interaction.
    """
    def __init__(self):
        super(ControlView, self).__init__()
        self.setupUi(self)
        self.setupScene()
        self.minimum_check.stateChanged.connect(self.update_minimum)
        self.maximum_check.stateChanged.connect(self.update_maximum)
        self.minimum_edit.valueChanged.connect(self.update_minimum_slider)
        self.maximum_edit.valueChanged.connect(self.update_maximum_slider)
        self.minimum_slider.sliderMoved.connect(self.minimum_edit.setValue)
        self.maximum_slider.sliderMoved.connect(self.maximum_edit.setValue)
    def setupScene(self):
        #self.scene = self.histview.scene()
        self.histitem = pg.HistogramLUTItem(orientation='horizontal', gradientPosition="bottom")
        #self.histitem.disableAutoHistogramRange()
        self.histview.setCentralItem(self.histitem)
        self.histitem.vb.setMenuEnabled(False)
        self.histitem.vb.setMouseEnabled(x=False, y=False)
        self.histitem.setVisible(False)
    def update_source(self, src):
        if src is not None:
            self.source.setText(src)
    def update_dark(self, timestamp):
        if timestamp == -1:
            self.save_dark_status.setText("")
            self.processed.setEnabled(False)
        else:
            self.save_dark_status.setText("Latest dark frame: %s" %(time.ctime(timestamp)))
            self.processed.setEnabled(True)
    def update_saturated(self, count):
        if count < 0:
            self.label_saturated.setText(" -")
            self.control_group.setStyleSheet("")
        elif count == 0:
            self.label_saturated.setText("%d" %count)
            self.control_group.setStyleSheet("")
        else:
            self.label_saturated.setText("%d" %count)
            self.control_group.setStyleSheet("background-color: rgb(255,0,0)")
    def update_minimum(self, state):
        self.minimum_edit.setEnabled(state == 2)
        self.minimum_slider.setEnabled(state == 2)
    def update_maximum(self, state):
        self.maximum_edit.setEnabled(state == 2)
        self.maximum_slider.setEnabled(state == 2)
        self.maximum_slider.setValue(self.maximum_edit.value())
        self.maximum_slider.setMaximum(self.maximum_edit.value())
    def update_minimum_slider(self, value):
        if self.minimum_slider.isEnabled():
            self.minimum_slider.setValue(value)
    def update_maximum_slider(self, value):
        if self.maximum_edit.isEnabled():
            self.maximum_slider.setValue(value)
    def edit_minimum(self, value):
        self.minimum_edit.setValue(value)
    def edit_maximum(self, value):
        self.maximum_edit.setValue(value)
        #self.maximum_slider.setValue(value)
        #self.maximum_slider.setMaximum(value)

class Canvas(QtWidgets.QWidget, UiCanvasWidget):
    """
    Canvas widget class.

    Displaying images.
    """
    vmin_changed = Qt.pyqtSignal(float)
    vmax_changed = Qt.pyqtSignal(float)
    def __init__(self, cmap="gray", log=False):
        super(Canvas, self).__init__()
        self.setupUi(self)
        self.vmin = None
        self.vmax = None
        self.automax = True
        self.automin = True
        self.setmin = None
        self.setmax = None
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
        #self.replot()

    def setLogarithmic(self, status):
        self.islog = status
        #self.replot()

    def setAutoMin(self, state):
        self.automin = (state == 0)
        #self.replot()

    def setAutoMax(self, state):
        self.automax = (state == 0)
        #self.replot()

    def setLevelMin(self, value):
        self.setmin = value
        #self.replot()

    def setLevelMax(self, value):
        self.setmax = value
        #self.replot()

    def setLevels(self):
        if self.automin:
            self.vmin = np.percentile(self.transformed,0.01)
            self.vmin_changed.emit(self.inverse(self.vmin))
        else:
            self.vmin = self.transform(self.setmin)
        if self.automax:
            self.vmax = np.percentile(self.transformed,99.99)
            self.vmax_changed.emit(self.inverse(self.vmax))
        else:
            self.vmax = self.transform(self.setmax)

    def transform(self, value):
        if self.islog:
            trans = np.log(value+1e-5)
        else:
            trans = value
        return trans

    def inverse(self, value):
        if self.islog:
            orig = np.exp(value)
        else:
            orig = value
        return orig

    def drawFrame(self, frame):
        self.original = frame
        #self.replot()

    def replot(self):
        if self.original is None:
            return
        self.transformed = self.transform(self.original)
        self.setLevels()
        self.im.setImage(self.transformed.transpose(), autolevels=False, lut=self.cmap)
        self.im.setLevels((self.vmin, self.vmax))
