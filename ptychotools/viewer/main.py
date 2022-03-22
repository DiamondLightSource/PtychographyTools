#!/usr/bin/env python
from PyQt5 import QtGui, QtCore, QtWidgets, Qt, uic
import numpy as np
import os, sys, time

# Import widgets
from .widgets import ControlView, Canvas

# Import modules
from .io import DataHandler

# Load UI
curdir = os.path.dirname(os.path.realpath(__file__))
UiMainWindow, _ = uic.loadUiType(curdir + '/ui/main.ui')

# Main viewer class - the main window
class Viewer(QtWidgets.QMainWindow, UiMainWindow):
    """
    Main viewer class.

    contains only the layout of all the sub-widgets.
    """
    def __init__(self, args):
        super(Viewer, self).__init__()
        self.setupUi(self)
        Viewer.instance = self

        # Data handler
        self.dh = DataHandler(args.source)

        # Control panel
        self.controlFrame.layout().removeWidget(self.controlWidget)
        self.controlWidget.setParent(None)
        self.controlView = ControlView()
        self.controlFrame.layout().addWidget(self.controlView)
        self.controlView.update_source(args.source)

        # Frame panel
        self.canvasFrame.layout().removeWidget(self.canvasWidget)
        self.canvasWidget.setParent(None)
        self.canvas = Canvas(cmap=self.controlView.colormap.currentText(), log=self.controlView.logarithmic.isChecked())
        self.canvasFrame.layout().addWidget(self.canvas)
        self.controlView.histitem.setImageItem(self.canvas.im)

        # Connections
        self.set_connections()
        
        # GUI Style
        self.style = args.style
        self.set_stylesheets()

        # If source has been provided start the service
        if args.source is not None:
            self.dh.start_service()

    def set_stylesheets(self):
        """
        Set stylesheet for all widgets.
        """
        for w in [self, self.controlView]:
            w.setStyleSheet(open(curdir + "/qss/{:s}.qss".format(self.style)).read())

    def set_connections(self):
        """
        Set connections for all widgets and modules.
        """
        self.dh.connected.connect(self.service_started)
        self.dh.disconnected.connect(self.service_stopped)
        self.dh.newframe.connect(self.draw)
        self.dh.darkframe.connect(self.controlView.update_dark)
        self.dh.saturated.connect(self.controlView.update_saturated)
        self.controlView.start.released.connect(self.dh.start_service)
        self.controlView.stop.released.connect(self.dh.stop_service)
        self.controlView.source.textChanged.connect(self.dh.source_updated)
        self.controlView.save_dark.released.connect(self.dh.save_dark_frame)
        self.controlView.processed.stateChanged.connect(self.dh.update_processed)
        self.controlView.live_fft.stateChanged.connect(self.dh.update_live_fft)
        self.controlView.colormap.currentTextChanged.connect(self.canvas.setColormap)
        self.controlView.logarithmic.toggled.connect(self.canvas.setLogarithmic)
        self.controlView.minimum_check.stateChanged.connect(self.canvas.setAutoMin)
        self.controlView.maximum_check.stateChanged.connect(self.canvas.setAutoMax)
        self.controlView.minimum_edit.valueChanged.connect(self.canvas.setLevelMin)
        self.controlView.maximum_edit.valueChanged.connect(self.canvas.setLevelMax)
        self.controlView.check_saturated.stateChanged.connect(self.dh.update_saturated)
        self.canvas.scene.sigMouseMoved.connect(self.onMouseMoved)
        self.canvas.vmin_changed.connect(self.controlView.edit_minimum)
        self.canvas.vmax_changed.connect(self.controlView.edit_maximum)

    def service_started(self):
        """
        Callback once service has been started.
        """
        self.controlView.start.setEnabled(False)
        self.controlView.stop.setEnabled(True)
        self.controlView.save_dark.setEnabled(True)
        self.controlView.live_fft.setEnabled(True)
        self.controlView.live_fft.setChecked(False)
        self.controlView.processed.setChecked(False)

    def service_stopped(self):
        """
        Callback once service has been stoped.
        """
        self.controlView.start.setEnabled(True)
        self.controlView.stop.setEnabled(False)
        self.controlView.save_dark.setEnabled(False)
        self.controlView.processed.setEnabled(False)
        self.controlView.live_fft.setEnabled(False)
        self.dh.clear_dark_frame()

    def draw(self):
        """
        Update image
        """
        self.canvas.drawFrame(self.dh.frame)

    def onMouseMoved(self, pos):
        """
        Track mouse position and display current value
        """
        xy = self.canvas.view.mapToView(pos)
        xy = self.canvas.im.transform().map(xy)
        y  = int(xy.x())
        x  = int(xy.y())
        sh = self.dh.frame.shape
        if (x<0) or (y<0):
            return
        if (x>=sh[1]) or (y>=sh[0]):
            return
        v = self.dh.frame[y,x]
        self.controlView.pixelinfo.setText("x=%d,\ty=%d,\tvalue=%.1f" %(x,y,float(v)))

    def cleanup(self):
        """
        Cleaning up before exiting the programm
        """
        self.dh.stop_service()
