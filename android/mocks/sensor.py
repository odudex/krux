# The MIT License (MIT)

# Copyright (c) 2021-2022 Krux contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from kivy.uix.widget import Widget
from .qrreader import QRReader
from unittest import mock
from kivy.properties import ObjectProperty

class Mockhistogram_threshold:
    def value(self):
        return 1


class Mockhistogram:
    def get_threshold(self):
        return Mockhistogram_threshold()


class Sensor(Widget):
    RGB565 = 0
    QVGA = 0

    running = ObjectProperty()

    def __init__(self) -> None:
        self.camera = None
        self.qrreader = QRReader(letterbox_color='black',
                                 aspect_ratio='4:3')
        self.codes = []
        self.m = mock.MagicMock()
        self.m.get_frame.return_value = None
        self.m.get_histogram.return_value = Mockhistogram()
        self.m.find_qrcodes.return_value = []
        # self.running = ObjectProperty()

    def reset(self, dual_buff=False):
        pass


    def run(self, on):
        if on:
            self.running = True
            # self.qrreader.connect_camera(analyze_pixels_resolution = 640,
            #                          enable_analyze_pixels = True)
        else:
            self.running = False
            # self.qrreader.disconnect_camera()

    def snapshot(self):
        codes = self.qrreader.pick_annotations()
        self.m.get_frame.return_value = None
        self.m.get_histogram.return_value = Mockhistogram()
        self.m.find_qrcodes.return_value = codes
        self.m.to_bytes.return_value = self.qrreader.pick_snapshot_bytes()
        return self.m

    def get_id(self):
        return 0x7742

    def skip_frames(self, frames=None):
        pass

    def set_pixformat(self, format):
        pass

    def set_framesize(self, format):
        pass

    def _Camera__write_reg(self, reg, data):
        pass

