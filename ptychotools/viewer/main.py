#!/usr/bin/env python
from PyQt5 import QtGui, QtCore, QtWidgets, Qt, uic
import numpy as np
import os, sys, time

# Import widgets
from .widgets import ControlView, Canvas
#from widgets import ObjectView, ProbeView, RuntimeView, ParamView

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
        self.dh = DataHandler()

        # Control panel
        self.controlFrame.layout().removeWidget(self.controlWidget)
        self.controlWidget.setParent(None)
        self.controlView = ControlView()
        self.controlFrame.layout().addWidget(self.controlView)
        self.controlView.update_source(args.source)

        # Frame panel
        self.canvasFrame.layout().removeWidget(self.canvasWidget)
        self.canvasWidget.setParent(None)
        self.canvas = Canvas()
        self.canvasFrame.layout().addWidget(self.canvas)

        # # Params panel
        # self.paramFrame.layout().removeWidget(self.paramWidget)
        # self.paramWidget.setParent(None)
        # self.paramView = ParamView()
        # self.paramFrame.layout().addWidget(self.paramView)

        # # Probe panel
        # self.probeFrame.layout().removeWidget(self.probeWidget)
        # self.probeWidget.setParent(None)
        # self.probeView = ProbeView(N=self.recons.prshape[0], maxcol=args.maxcol)

        # self.probeFrame.layout().addWidget(self.probeView)

        # # Runtime panel
        # self.runtimeFrame.layout().removeWidget(self.runtimeWidget)
        # self.runtimeWidget.setParent(None)
        # self.runtimeView = RuntimeView()
        # self.runtimeFrame.layout().addWidget(self.runtimeView)

        # # Set timer 
        # self.timer = QtCore.QTimer()
        # self.timer.setInterval(2)
        # self.timer.timeout.connect(self.recons.check)
        # self.timer.start()

        # Connections
        self.set_connections()
        
        # GUI Style
        self.style = args.style
        self.set_stylesheets()

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
        self.controlView.start.released.connect(self.dh.start_service)
        self.controlView.stop.released.connect(self.dh.stop_service)
        self.controlView.source.textChanged.connect(self.dh.source_updated)
        self.controlView.save_dark.released.connect(self.dh.save_dark_frame)

    def service_started(self):
        """
        Callback once service has been started.
        """
        self.controlView.start.setEnabled(False)
        self.controlView.stop.setEnabled(True)

    def service_stopped(self):
        """
        Callback once service has been stoped.
        """
        self.controlView.start.setEnabled(True)
        self.controlView.stop.setEnabled(False)        

    def draw(self):
        """
        Update image
        """
        print("draw frame")
        self.canvas.drawFrame(self.dh.frame)

    def cleanup(self):
        """
        Cleaning up before exiting the programm
        """
        self.dh.stop_service()
        print("Exiting...")

    def check_for_new_events(self, check):
        """
        Start/stop timer for checking new events.
        """
        self.timer.start() if check else self.timer.stop()

    def replot(self, index=None):
        """
        Load object/probe and update all plots.
        """
        # Check if index has changed
        if index is None:
            index = self.previndex
        self.previndex = index

        # Convert negative index to positive index
        if index < 0:
            index = range(len(self.recons.iteration))[index]

        # Get current filename
        filename = self.recons.flist[index]

        # Update info in control panel
        self.update_control(index)

        # Update levels
        self.update_levels()

        # Plot object
        ob = self.recons.get_object(filename)[0]
        cr = max(int(self.controlView.crop_box.value()), 1)
        self.objectView.amplitude.paintImage(0, np.abs(ob)[cr:-cr,cr:-cr])
        self.objectView.phase.paintImage(0, np.angle(ob)[cr:-cr,cr:-cr])

        # Plot probes
        pr = self.recons.get_probe(filename)
        for i in range(pr.shape[0]):
            self.probeView.complex.paintImage(i, np.abs(pr[i]))

        # Plot errors
        err = np.array(self.recons.errors)[:index+1]
        itr = np.array(self.recons.iteration)[:index+1]
        self.runtimeView.draw_errors(itr, err)

    def update_levels(self):
        """
        Update vmin/vmax levels based what is provided from the control panel.
        """
        if self.controlView.object_vmin_box.isEnabled():
            self.objectView.phase.vmin = self.controlView.object_vmin_box.value()
        if self.controlView.object_vmax_box.isEnabled():
            self.objectView.phase.vmax = self.controlView.object_vmax_box.value()
        if not self.controlView.object_vmin_box.isEnabled():
            self.objectView.phase.vmin = None
        if not self.controlView.object_vmax_box.isEnabled():
            self.objectView.phase.vmax = None

    def update_control(self, sliderpos):
        """
        Keep control panel up to speed.
        """
        # Update iteration number
        self.controlView.iteration_number.setText("%d"%self.recons.iteration[sliderpos])
        # Update reconstruction timestamp
        self.controlView.recons_date.setText(time.ctime(self.recons.latest))
        # Disable slider if file list is empty
        self.controlView.iteration_slider.setDisabled(True) if (not self.recons.flist) else None
        # Update slider range and position
        self.controlView.iteration_slider.setRange(0, len(self.recons.iteration) - 1)
        self.controlView.iteration_slider.setSliderPosition(sliderpos)

    def slider_changed(self, pos):
        """
        Update plots if slider position has changed.
        """
        self.replot(pos)
        
