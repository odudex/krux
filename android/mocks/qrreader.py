# The MIT License (MIT)

# Copyright (c) 2021-2023 Krux contributors

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

from kivy.clock import mainthread
from kivy.metrics import dp
from kivy.graphics import Line, Color, Rectangle

from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from PIL import Image

from kivy.properties import ObjectProperty
from gestures4kivy import CommonGestures
from camera4kivy import Preview

class Mockqrcode:
    def __init__(self, data):
        self.data = data

    def payload(self):
        return self.data

class QRReader(Preview, CommonGestures):

    pressed = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.annotations = []
        self.snapshot_bytes = bytes()        

    ####################################
    # Analyze a Frame - NOT on UI Thread
    ####################################
    
    def analyze_pixels_callback(self, pixels, image_size, image_pos, scale, mirror):
        # pixels : Kivy Texture pixels
        # image_size   : pixels size (w,h)
        # image_pos    : location of Texture in Preview Widget (letterbox)
        # scale  : scale from Analysis resolution to Preview resolution
        # mirror : true if Preview is mirrored
        pil_image = Image.frombytes(mode='RGBA', size=image_size, data= pixels)
        barcodes = pyzbar.decode(pil_image, symbols=[ZBarSymbol.QRCODE])
        codes = []
        if barcodes:
            codes.append(Mockqrcode(barcodes[0].data.decode()))
        self.make_thread_safe(codes, pixels) ## A COPY of the list

    @mainthread
    def make_thread_safe(self, found, image_bytes):
        self.annotations = found
        if len(image_bytes) > 0:
            self.snapshot_bytes = image_bytes

    def pick_annotations(self):
        annotations = self.annotations
        found = []
        snapshot_bytes = bytes()
        self.make_thread_safe(found, snapshot_bytes)
        return annotations
    
    def pick_snapshot_bytes(self):
        snapshot_bytes = self.snapshot_bytes
        print(len(self.snapshot_bytes))
        return snapshot_bytes

        
    #################################
    # User Touch Event - on UI Thread
    #################################

    def cgb_primary(self, touch, focus_x, focus_y):
        self.pressed = True
