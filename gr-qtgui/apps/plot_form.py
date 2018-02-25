#!/usr/bin/env python
#
# Copyright 2012,2018 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

try:
    from PyQt5 import QtWidgets, Qt
    import sip
except ImportError:
    import sys
    sys.stderr.write("Error: Program requires PyQt5.\n")
    sys.exit(1)

import numpy

class plot_form(QtWidgets.QWidget):
    def __init__(self, top_block, title='', scale=1):
        QtWidgets.QWidget.__init__(self, None)

        self._start = 0
        self._end = 0
        self._y_min = 0
        self._y_max = 0
        self._pos_scale = scale

        self.top_block = top_block
        self.top_block.gui_y_axis = self.gui_y_axis

        self.setWindowTitle(title)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(top_block.get_gui(), 1,2,1,2)

        # Create a save action
        self.save_act = QtWidgets.QAction("Save", self)
        self.save_act.setShortcut(QtWidgets.QKeySequence.Save)
        self.save_act.triggered.connect(self.save_figure)

        # Create an exit action
        self.exit_act = QtWidgets.QAction("Exit", self)
        self.exit_act.setShortcut(QtWidgets.QKeySequence.Close)
        self.exit_act.triggered.connect(self.close)

        # Create a menu for the window
        self.menu = QtWidgets.QToolBar("Menu", self)
        self.menu.addAction(self.save_act)
        self.menu.addAction(self.exit_act)

        self.layout.addWidget(self.menu, 0,0,1,4)

        self.left_col_form = QtWidgets.QFormLayout()
        self.layout.addLayout(self.left_col_form, 1,0,1,1)
        self.layout.setColumnStretch(0, 0)
        self.layout.setColumnStretch(2, 1)

        # Create Edit boxes for X-axis start/stop
        self.size_val = QtWidgets.QIntValidator(0, top_block._max_nsamps, self)

        self.start_edit = QtWidgets.QLineEdit(self)
        self.start_edit.setMinimumWidth(100)
        self.start_edit.setMaximumWidth(100)
        self.start_edit.setText("{0}".format(top_block._start))
        self.start_edit.setValidator(self.size_val)
        self.left_col_form.addRow("Start:", self.start_edit)
        self.start_edit.returnPressed.connect(self.update_xaxis_pos)

        end = top_block._start + top_block._nsamps
        self.end_edit = QtWidgets.QLineEdit(self)
        self.end_edit.setMinimumWidth(100)
        self.end_edit.setMaximumWidth(100)
        self.end_edit.setText("{0}".format(end))
        self.end_edit.setValidator(self.size_val)
        self.left_col_form.addRow("End:", self.end_edit)
        self.end_edit.returnPressed.connect(self.update_xaxis_pos)

        # Create a slider to move the position in the file
        self.posbar = QtWidgets.QSlider(Qt.Qt.Horizontal, self)
        self.posbar.setMaximum(self.top_block._max_nsamps)
        self.posbar.setPageStep(self.top_block._nsamps)
        self.posbar.valueChanged.connect(self.update_xaxis_slider)
        self.layout.addWidget(self.posbar, 2,2,1,1)

        # Create Edit boxes for Y-axis min/max
        self.y_max_edit = QtWidgets.QLineEdit(self)
        self.y_max_edit.setMinimumWidth(100)
        self.y_max_edit.setMaximumWidth(100)
        self.left_col_form.addRow("Y Max:", self.y_max_edit)
        self.y_max_edit.editingFinished.connect(self.update_yaxis_pos)

        self.y_min_edit = QtWidgets.QLineEdit(self)
        self.y_min_edit.setMinimumWidth(100)
        self.y_min_edit.setMaximumWidth(100)
        self.left_col_form.addRow("Y Min:", self.y_min_edit)
        self.y_min_edit.editingFinished.connect(self.update_yaxis_pos)

        self.grid_check = QtWidgets.QCheckBox("Grid", self)
        self.grid_check.stateChanged.connect(self.set_grid_check)
        self.left_col_form.addWidget(self.grid_check)

        # Create a slider to move the plot's y-axis offset
        _ymax = numpy.int32(min(numpy.iinfo(numpy.int32).max, self.top_block._y_max))
        _ymin = numpy.int32(max(numpy.iinfo(numpy.int32).min, self.top_block._y_min))
        _yrng = numpy.int32(min(numpy.iinfo(numpy.int32).max, self.top_block._y_range))
        _yval = numpy.int32(min(numpy.iinfo(numpy.int32).max, self.top_block._y_value))
        self.ybar = QtWidgets.QSlider(Qt.Qt.Vertical, self)
        self.ybar.setMinimum(self._pos_scale*_ymin)
        self.ybar.setMaximum(self._pos_scale*_ymax)
        self.ybar.setSingleStep(self._pos_scale*(_yrng/10))
        self.ybar.setPageStep(self._pos_scale*(_yrng/2))
        self.ybar.setValue(self._pos_scale*_ymax)
        self.ybar.valueChanged.connect(self.update_yaxis_slider)
        self.layout.addWidget(self.ybar, 1,1,1,1)

        self.gui_y_axis(top_block._y_value-top_block._y_range, top_block._y_value)

        # Create an edit box for the Sample Rate
        sr = top_block._samp_rate
        self.samp_rate_edit = QtWidgets.QLineEdit(self)
        self.samp_rate_edit.setMinimumWidth(100)
        self.samp_rate_edit.setMaximumWidth(100)
        self.samp_rate_edit.setText("{0}".format(sr))
        self.left_col_form.addRow("Sample Rate:", self.samp_rate_edit)
        self.samp_rate_edit.returnPressed.connect(self.update_samp_rate)

        # Create an edit box for the center frequency
        freq = top_block._center_freq
        self.freq_edit = QtWidgets.QLineEdit(self)
        self.freq_edit.setMinimumWidth(100)
        self.freq_edit.setMaximumWidth(100)
        self.freq_edit.setText("{0}".format(freq))
        self.left_col_form.addRow("Frequency:", self.freq_edit)
        self.freq_edit.returnPressed.connect(self.update_samp_rate)

        self.resize(1000, 500)

    def add_line_control(self, layout):
        self._line_tabs = QtWidgets.QTabWidget()

        self._line_pages = []
        self._line_forms = []
        self._label_edit = []
        self._size_edit = []
        self._color_edit = []
        self._style_edit = []
        self._marker_edit = []
        self._alpha_edit = []
        for n in xrange(self.top_block._nsigs):
            self._line_pages.append(QtWidgets.QDialog())
            self._line_forms.append(QtWidgets.QFormLayout(self._line_pages[-1]))

            label = self.top_block.gui_snk.line_label(n)
            self._label_edit.append(QtWidgets.QLineEdit(self))
            self._label_edit[-1].setMinimumWidth(125)
            self._label_edit[-1].setMaximumWidth(125)
            self._label_edit[-1].setText("{0}".format(label))
            self._line_forms[-1].addRow("Label:", self._label_edit[-1])
            self._label_edit[-1].returnPressed.connect(self.update_line_label)

            width_val = QtWidgets.QIntValidator(1, 20, self)
            self._size_edit.append(QtWidgets.QLineEdit(self))
            self._size_edit[-1].setValidator(width_val)
            self._size_edit[-1].setMinimumWidth(100)
            self._size_edit[-1].setMaximumWidth(100)
            self._size_edit[-1].setText("{0}".format(1))
            self._line_forms[-1].addRow("Width:", self._size_edit[-1])
            self._size_edit[-1].returnPressed.connect(self.update_line_size)

            color = self.top_block.gui_snk.line_color(n)
            self._color_edit.append(QtWidgets.QLineEdit(self))
            self._color_edit[-1].setMinimumWidth(100)
            self._color_edit[-1].setMaximumWidth(100)
            self._color_edit[-1].setText("{0}".format(color))
            self._line_forms[-1].addRow("Color:", self._color_edit[-1])
            self._color_edit[-1].returnPressed.connect(self.update_line_color)

            self._qtstyles = {"None": Qt.Qt.NoPen,
                              "Solid": Qt.Qt.SolidLine,
                              "Dash": Qt.Qt.DashLine,
                              "Dot": Qt.Qt.DotLine,
                              "DashDot": Qt.Qt.DashDotLine,
                              "DashDotDot": Qt.Qt.DashDotDotLine}
            self._style_edit.append(QtWidgets.QComboBox(self))
            self._style_edit[-1].addItems(["None", "Solid", "Dash",
                                          "Dot", "DashDot", "DashDotDot"])
            self._style_edit[-1].setCurrentIndex(1)
            self._line_forms[-1].addRow("Style:", self._style_edit[-1])
            self._style_edit[-1].currentIndexChanged.connect(self.update_line_style)

            # A bit dangerous, this. If QWT ever changes the lineup,
            # we will have to adjust this, too. But we also can't
            # really rely on PyQwt right now.
            self._qwtmarkers = {"None": -1,
                                "Circle": 0,
                                "Rectangle": 1,
                                "Diamond": 2,
                                "Triangle": 3,
                                "Down Triangle": 4,
                                "Left Triangle": 6,
                                "Right Triangle": 7,
                                "Cross": 8,
                                "X-Cross": 9,
                                "Horiz. Line": 10,
                                "Vert. Line": 11,
                                "Star 1": 12,
                                "Star 2": 13,
                                "Hexagon": 14}
            self._marker_edit.append(QtWidgets.QComboBox(self))
            self._marker_edit[-1].addItems(["None", "Circle", "Rectangle", "Diamond",
                                            "Triangle", "Down Triangle", "Left Triangle",
                                            "Right Triangle", "Cross", "X-Cross",
                                            "Horiz. Line", "Vert. Line", "Star 1",
                                            "Star 2", "Hexagon"])
            self._line_forms[-1].addRow("Marker:", self._marker_edit[-1])
            self._marker_edit[-1].currentIndexChanged.connect(self.update_line_marker)

            alpha_val = QtWidgets.QDoubleValidator(0, 1.0, 2, self)
            alpha_val.setTop(1.0)
            alpha = self.top_block.gui_snk.line_alpha(n)
            self._alpha_edit.append(QtWidgets.QLineEdit(self))
            self._alpha_edit[-1].setMinimumWidth(50)
            self._alpha_edit[-1].setMaximumWidth(100)
            self._alpha_edit[-1].setText("{0]".format(alpha))
            self._alpha_edit[-1].setValidator(alpha_val)
            self._line_forms[-1].addRow("Alpha:", self._alpha_edit[-1])
            self._alpha_edit[-1].returnPressed.connect(self.update_line_alpha)

            self._line_tabs.addTab(self._line_pages[-1], "{0}".format(label))

        layout.addWidget(self._line_tabs)

    def update_line_label(self):
        index = self._line_tabs.currentIndex()
        label = self._label_edit[index].text()
        self._line_tabs.setTabText(index, label)
        self.top_block.gui_snk.set_line_label(index, str(label))

    def update_line_size(self):
        index = self._line_tabs.currentIndex()
        width = self._size_edit[index].text().toUInt()[0]
        self.top_block.gui_snk.set_line_width(index, width)
        self.update_line_alpha()

    def update_line_color(self):
        index = self._line_tabs.currentIndex()
        color = str(self._color_edit[index].text())
        self.top_block.gui_snk.set_line_color(index, color)
        self.update_line_alpha()

    def update_line_style(self, s_index):
        index = self._line_tabs.currentIndex()
        style_str = self._style_edit[index].itemText(s_index)
        style = self._qtstyles[str(style_str)]
        self.top_block.gui_snk.set_line_style(index, int(style))

    def update_line_marker(self, m_index):
        index = self._line_tabs.currentIndex()
        marker_str = self._marker_edit[index].itemText(m_index)
        marker = self._qwtmarkers[str(marker_str)]
        self.top_block.gui_snk.set_line_marker(index, int(marker))

    def update_line_alpha(self):
        index = self._line_tabs.currentIndex()
        alpha = self._alpha_edit[index].text().toDouble()[0]
        self.top_block.gui_snk.set_line_alpha(index, alpha)

    def update_xaxis_pos(self):
        newstart = self.start_edit.text().toUInt()[0]
        newend = self.end_edit.text().toUInt()[0]
        if(newstart != self._start or newend != self._end):
            if(newend < newstart):
                QtWidgets.QMessageBox.information(
                    self, "Warning",
                    "End sample is less than start sample.",
                    QtWidgets.QMessageBox.Ok);
            else:
                newnsamps = newend - newstart
                self.top_block.reset(newstart, newnsamps)
        self._start = newstart
        self._end = newend
        self.posbar.setPageStep(self.top_block._nsamps)
        self.posbar.setValue(self._start)

    def update_xaxis_slider(self, value):
        self._start = value
        self._end = value + self.posbar.pageStep()

        self.start_edit.setText("{0}".format(self._start))
        self.end_edit.setText("{0}".format(self._end))

        if(value != self.top_block._max_nsamps):
            self.top_block.reset(self._start, self.posbar.pageStep())

    def update_yaxis_pos(self):
        if(not self.top_block._auto_scale):
            newmin = self.y_min_edit.text().toDouble()[0]
            newmax = self.y_max_edit.text().toDouble()[0]
            if(newmin != self._y_min or newmax != self._y_max):
                self._y_min = newmin
                self._y_max = newmax
                self.top_block._y_range = newmax - newmin
                self.top_block.set_y_axis(self._y_min, self._y_max)
                self.ybar.setValue(self._y_max*self._pos_scale)
        else:
            self.y_min_edit.setText("{0:.2f}".format(self._y_min))
            self.y_max_edit.setText("{0:.2f}".format(self._y_max))

    def update_yaxis_slider(self, value):
        if(not self.top_block._auto_scale):
            value = value/self._pos_scale
            self.top_block._y_value = value
            self._y_min = value - self.top_block._y_range
            self._y_max = value

            ret = self.top_block.set_y_axis(self._y_min, self._y_max)
            if(ret):
                self._y_min = ret[0]
                self._y_max = ret[1]

                self.gui_y_axis(self._y_min, self._y_max)
        else:
            self.ybar.setValue(self._y_max*self._pos_scale)

    def update_samp_rate(self):
        sr = self.samp_rate_edit.text().toDouble()[0]
        fr = self.freq_edit.text().toDouble()[0]
        self.top_block.gui_snk.set_frequency_range(fr, sr)
        self.top_block._samp_rate = sr
        self.top_block.reset(self.top_block._start,
                             self.top_block._nsamps)

    def gui_y_axis(self, ymin, ymax):
        self.y_min_edit.setText("{0:.2f}".format(ymin))
        self.y_max_edit.setText("{0:.2f}".format(ymax))
        self._y_min = ymin
        self._y_max = ymax
        self.ybar.setValue(self._pos_scale*ymax)

    def set_grid_check(self, state):
        if(state):
            self.top_block.gui_snk.enable_grid(True)
        else:
            self.top_block.gui_snk.enable_grid(False)

    def save_figure(self):
        qpix = QtWidgets.QPixmap.grabWidget(self.top_block.pyWin)
        types = "JPEG file (*.jpg);;" + \
            "Portable Network Graphics file (*.png);;" + \
            "Bitmap file (*.bmp);;" + \
            "TIFF file (*.tiff)"
        filebox = QtWidgets.QFileDialog(self, "Save Image", "./", types)
        filebox.setViewMode(QtWidgets.QFileDialog.Detail)
        if(filebox.exec_()):
            filename = filebox.selectedFiles()[0]
            filetype = filebox.selectedNameFilter()
        else:
            return

        if(filetype.contains(".jpg")):
            qpix.save(filename, "JPEG");
        elif(filetype.contains(".png")):
            qpix.save(filename, "PNG");
        elif(filetype.contains(".bmp")):
            qpix.save(filename, "BMP");
        elif(filetype.contains(".tiff")):
            qpix.save(filename, "TIFF");
        else:
            qpix.save(filename, "JPEG");
