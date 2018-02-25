#!/usr/bin/env python
#
# Copyright 2013,2018 Free Software Foundation, Inc.
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

import sys, math
from gnuradio import filter

try:
    from PyQt5 import QtWidgets, Qt
    import sip
except ImportError:
    sys.stderr.write("Error: Program requires PyQt5 and gr-qtgui.\n")
    sys.exit(1)

try:
    from gnuradio.qtgui.plot_from import plot_form
except ImportError:
    from plot_form import plot_form

class plot_time_raster_form(plot_form):
    def __init__(self, top_block, title='', scale=1):
        plot_form.__init__(self, top_block, title, scale)

        self.right_col_layout = QtWidgets.QVBoxLayout()
        self.right_col_form = QtWidgets.QFormLayout()
        self.right_col_layout.addLayout(self.right_col_form)
        self.layout.addLayout(self.right_col_layout, 1,4,1,1)

        self.auto_scale = QtWidgets.QCheckBox("Auto Scale", self)
        if(self.top_block._auto_scale):
            self.auto_scale.setChecked(self.top_block._auto_scale)
        self.auto_scale.stateChanged.connect(self.set_auto_scale)
        self.right_col_layout.addWidget(self.auto_scale)

        self.ncols_edit = QtWidgets.QLineEdit(self)
        self.ncols_edit.setMinimumWidth(100)
        self.ncols_edit.setMaximumWidth(100)
        self.ncols_edit.setText("{0}".format(top_block._ncols))
        self.right_col_form.addRow("Num. Cols.", self.ncols_edit)
        self.ncols_edit.returnPressed.connect(self.ncols_update)

        self.nrows_edit = QtWidgets.QLineEdit(self)
        self.nrows_edit.setMinimumWidth(100)
        self.nrows_edit.setMaximumWidth(100)
        self.nrows_edit.setText("{0}".format(top_block._nrows))
        self.right_col_form.addRow("Num. Rows.", self.nrows_edit)
        self.nrows_edit.returnPressed.connect(self.nrows_update)

        self.add_raster_control(self.right_col_layout)

    def add_raster_control(self, layout):
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

            self._qtcolormaps = ["Multi Color", "White Hot",
                                 "Black Hot", "Incandescent"]
            self._color_edit.append(QtWidgets.QComboBox(self))
            self._color_edit[-1].addItems(self._qtcolormaps)
            self._color_edit[-1].setCurrentIndex(1)
            self._line_forms[-1].addRow("Color Map:", self._color_edit[-1])
            self._color_edit[-1].currentIndexChanged.connect(self.update_color_map)

            alpha_val = QtWidgets.QDoubleValidator(0, 1.0, 2, self)
            alpha_val.setTop(1.0)
            alpha = self.top_block.gui_snk.line_alpha(n)
            self._alpha_edit.append(QtWidgets.QLineEdit(self))
            self._alpha_edit[-1].setMinimumWidth(50)
            self._alpha_edit[-1].setMaximumWidth(100)
            self._alpha_edit[-1].setText("{0}".format(alpha))
            self._alpha_edit[-1].setValidator(alpha_val)
            self._line_forms[-1].addRow("Alpha:", self._alpha_edit[-1])
            self._alpha_edit[-1].returnPressed.connect(self.update_line_alpha)

            self._line_tabs.addTab(self._line_pages[-1], "{0}".format(label))

        layout.addWidget(self._line_tabs)

    def update_color_map(self, c_index):
        index = self._line_tabs.currentIndex()
        self.top_block.gui_snk.set_color_map(index, c_index)
        self.update_line_alpha()

    def set_auto_scale(self, state):
        if(state):
            self.top_block.auto_scale(True)
        else:
            self.top_block.auto_scale(False)

    def update_samp_rate(self):
        sr = self.samp_rate_edit.text().toDouble()[0]
        self.top_block.gui_snk.set_samp_rate(sr)

        nsamps = int(math.ceil((self.top_block._nrows+1)*self.top_block._ncols))
        self.top_block.reset(self._start, nsamps)

    def ncols_update(self):
        n = self.ncols_edit.text().toDouble()[0]
        self.top_block.gui_snk.set_num_cols(n)
        self.top_block._ncols = n

        nsamps = int(math.ceil((self.top_block._nrows+1)*n))
        self.top_block.reset(self._start, nsamps)

    def nrows_update(self):
        n = self.nrows_edit.text().toInt()[0]
        self.top_block.gui_snk.set_num_rows(n)
        self.top_block._nrows = n

        nsamps = int(math.ceil(self.top_block._ncols*(n+1)))
        self.top_block.reset(self._start, nsamps)
