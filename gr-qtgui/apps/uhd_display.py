#!/usr/bin/env python
#
# Copyright 2009,2011,2018 Free Software Foundation, Inc.
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

from gnuradio import gr
from gnuradio import filter
from gnuradio import blocks
from gnuradio import uhd
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import sys

try:
    from gnuradio import qtgui
    from PyQt5 import QtWidgets, Qt
    import sip
except ImportError:
    sys.stderr.write("Error: Program requires PyQt5 and gr-qtgui.\n")
    sys.exit(1)

try:
    from usrp_display_qtgui import Ui_MainWindow
except ImportError:
    print "Error: could not find usrp_display_qtgui.py:"
    print "\t\"pyuic4 usrp_display_qtgui.ui -o usrp_display_qtgui.py\""
    sys.exit(1)


# ////////////////////////////////////////////////////////////////////
#        Define the QT Interface and Control Dialog
# ////////////////////////////////////////////////////////////////////


class main_window(QtWidgets.QMainWindow):
    def __init__(self, snk, fg, parent=None):

        QtWidgets.QWidget.__init__(self, parent)
        self.gui = Ui_MainWindow()
        self.gui.setupUi(self)

        self.fg = fg

        # Add the qtsnk widgets to the layout box
        self.gui.sinkLayout.addWidget(snk)

        self.gui.dcGainEdit.setText("{0}".format(0.001))

        # Connect up some signals
        self.gui.pauseButton.clicked.connect(self.pauseFg)
        self.gui.frequencyEdit.editingFinished.connect(self.frequencyEditText)
        self.gui.gainEdit.editingFinished.connect(self.gainEditText)
        self.gui.bandwidthEdit.editingFinished.connect(self.bandwidthEditText)
        self.gui.amplifierEdit.editingFinished.connect(self.amplifierEditText)

        self.gui.actionSaveData.activated.connect(self.saveData)
        self.gui.actionSaveData.setShortcut(QtWidgets.QKeySequence.Save)

        self.gui.dcGainEdit.editingFinished.connect(self.dcGainEditText)
        self.gui.dcCancelCheckBox.clicked.connect(self.dcCancelClicked)

    def pauseFg(self):
        if(self.gui.pauseButton.text() == "Pause"):
            self.fg.stop()
            self.fg.wait()
            self.gui.pauseButton.setText("Unpause")
        else:
            self.fg.start()
            self.gui.pauseButton.setText("Pause")


    # Functions to set the values in the GUI
    def set_frequency(self, freq):
        self.freq = freq
        sfreq = eng_notation.num_to_str(self.freq)
        self.gui.frequencyEdit.setText("{0}".format(sfreq))

    def set_gain(self, gain):
        self.gain = gain
        self.gui.gainEdit.setText("{0}".format(self.gain))

    def set_bandwidth(self, bw):
        self.bw = bw
        sbw = eng_notation.num_to_str(self.bw)
        self.gui.bandwidthEdit.setText("{0}".format(sbw))

    def set_amplifier(self, amp):
        self.amp = amp
        self.gui.amplifierEdit.setText("{0}".format(self.amp))


    # Functions called when signals are triggered in the GUI
    def frequencyEditText(self):
        try:
            freq = eng_notation.str_to_num(self.gui.frequencyEdit.text().toAscii())
            self.fg.set_frequency(freq)
            self.freq = freq
        except RuntimeError:
            pass

    def gainEditText(self):
        try:
            gain = float(self.gui.gainEdit.text())
            self.fg.set_gain(gain)
            self.gain = gain
        except ValueError:
            pass

    def bandwidthEditText(self):
        try:
            bw = eng_notation.str_to_num(self.gui.bandwidthEdit.text().toAscii())
            self.fg.set_bandwidth(bw)
            self.bw = bw
        except ValueError:
            pass

    def amplifierEditText(self):
        try:
            amp = float(self.gui.amplifierEdit.text())
            self.fg.set_amplifier_gain(amp)
            self.amp = amp
        except ValueError:
            pass

    def saveData(self):
        fileName = QtWidgets.QFileDialog.getSaveFileName(self, "Save data to file", ".");
        if(len(fileName)):
            self.fg.save_to_file(str(fileName))

    def dcGainEditText(self):
        gain = float(self.gui.dcGainEdit.text())
        self.fg.set_dc_gain(gain)

    def dcCancelClicked(self, state):
        self.dcGainEditText()
        self.fg.cancel_dc(state)



class my_top_block(gr.top_block):
    def __init__(self, options):
        gr.top_block.__init__(self)

        self.options = options
        self.show_debug_info = True

        self.qapp = QtWidgets.QApplication(sys.argv)

        self.u = uhd.usrp_source(device_addr=options.address, stream_args=uhd.stream_args('fc32'))

        if(options.antenna):
            self.u.set_antenna(options.antenna, 0)

        self.set_bandwidth(options.samp_rate)

        if options.gain is None:
            # if no gain was specified, use the mid-point in dB
            g = self.u.get_gain_range()
            options.gain = float(g.start()+g.stop())/2
        self.set_gain(options.gain)

        if options.freq is None:
            # if no freq was specified, use the mid-point
            r = self.u.get_freq_range()
            options.freq = float(r.start()+r.stop())/2
        self.set_frequency(options.freq)

        self._fftsize = options.fft_size

        self.snk = qtgui.sink_c(options.fft_size,
                                filter.firdes.WIN_BLACKMAN_hARRIS,
                                self._freq, self._bandwidth,
                                "UHD Display",
                                True, True, True, False)

        # Set up internal amplifier
        self.amp = blocks.multiply_const_cc(0.0)
        self.set_amplifier_gain(100)

        # Create a single-pole IIR filter to remove DC
        #   but don't connect it yet
        self.dc_gain = 0.001
        self.dc = filter.single_pole_iir_filter_cc(self.dc_gain)
        self.dc_sub = blocks.sub_cc()

        self.connect(self.u, self.amp, self.snk)

        if self.show_debug_info:
            print "Bandwidth: ", self.u.get_samp_rate()
            print "Center Freq: ", self.u.get_center_freq()
            print "Freq Range: ", self.u.get_freq_range()

        # Get the reference pointer to the SpectrumDisplayForm QWidget
        # Wrap the pointer as a PyQt SIP object
        #     This can now be manipulated as a PyQt5.QtWidgets.QWidget
        self.pysink = sip.wrapinstance(self.snk.pyqwidget(), QtWidgets.QWidget)

        self.main_win = main_window(self.pysink, self)

        self.main_win.set_frequency(self._freq)
        self.main_win.set_gain(self._gain)
        self.main_win.set_bandwidth(self._bandwidth)
        self.main_win.set_amplifier(self._amp_value)

        self.main_win.show()


    def save_to_file(self, name):
        self.lock()

        # Add file sink to save data
        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex, name)
        self.connect(self.amp, self.file_sink)

        self.unlock()

    def set_gain(self, gain):
        self._gain = gain
        self.u.set_gain(self._gain)

    def set_frequency(self, freq):
        self._freq = freq
        r = self.u.set_center_freq(freq)

        try:
            self.snk.set_frequency_range(self._freq, self._bandwidth)
        except:
            pass

    def set_bandwidth(self, bw):
        self._bandwidth = bw
        self.u.set_samp_rate(self._bandwidth)

        try:
            self.snk.set_frequency_range(self._freq, self._bandwidth)
        except:
            pass

    def set_amplifier_gain(self, amp):
        self._amp_value = amp
        self.amp.set_k(self._amp_value)

    def set_dc_gain(self, gain):
        self.dc.set_taps(gain)

    def cancel_dc(self, state):
        self.lock()

        if(state):
            self.disconnect(self.u, self.amp)
            self.connect(self.u, (self.dc_sub,0))
            self.connect(self.u, self.dc, (self.dc_sub,1))
            self.connect(self.dc_sub, self.amp)
        else:
            self.disconnect(self.dc_sub, self.amp)
            self.disconnect(self.dc, (self.dc_sub,1))
            self.disconnect(self.u, self.dc)
            self.disconnect(self.u, (self.dc_sub,0))
            self.connect(self.u, self.amp)

        self.unlock()

def main ():
    parser = OptionParser(option_class=eng_option)
    parser.add_option("-a", "--address", type="string", default="addr=192.168.10.2",
                      help="Address of UHD device, [default=%default]")
    parser.add_option("-A", "--antenna", type="string", default=None,
                      help="select Rx Antenna where appropriate")
    parser.add_option("-s", "--samp-rate", type="eng_float", default=1e6,
                      help="set sample rate (bandwidth) [default=%default]")
    parser.add_option("-f", "--freq", type="eng_float", default=2412e6,
                      help="set frequency to FREQ", metavar="FREQ")
    parser.add_option("-g", "--gain", type="eng_float", default=None,
                      help="set gain in dB (default is midpoint)")
    parser.add_option("--fft-size", type="int", default=2048,
                      help="Set number of FFT bins [default=%default]")
    (options, args) = parser.parse_args()

    if len(args) != 0:
        parser.print_help()
        sys.exit(1)

    tb = my_top_block(options)
    tb.start()
    tb.snk.exec_();

if __name__ == '__main__':
    try:
        main ()
    except KeyboardInterrupt:
        pass

