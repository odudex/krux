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

import time

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.label import CoreLabel
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.graphics import Rotate
from kivy.clock import mainthread
from unittest.mock import MagicMock

COLOR_BLACK = (0, 0, 0, 1)
COLOR_WHITE = (1, 1, 1, 1)
COLOR_RED = (1, 0, 0, 1)
COLOR_BLUE = (0, 0, 1, 1)
COLOR_GREEN = (0, 1, 0, 1)
COLOR_ORANGE = (1, 0.647, 0, 1)
COLOR_MAGENTA = (1, 0, 1, 1)
COLOR_DARKGREY = (0.3, 0.3, 0.3, 1)
COLOR_SLATEGREY = (0.5, 0.5, 0.5, 1)
COLOR_LIGHTGREY = (0.8, 0.8, 0.8, 1)
COLOR_LIGHTBLACK = (0.1, 0.1, 0.2, 1)

class LCD(Widget):

    pressed = ListProperty([0, 0])
    released = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.BLACK = COLOR_BLACK
        self.WHITE = COLOR_WHITE
        self.RED = COLOR_RED
        self.BLUE = COLOR_BLUE
        self.GREEN = COLOR_GREEN
        self.ORANGE = COLOR_ORANGE
        self.MAGENTA = COLOR_MAGENTA
        self.DARKGREY = COLOR_DARKGREY
        self.LIGHTGREY = COLOR_LIGHTGREY
        self.SLATEGREY = COLOR_SLATEGREY
        self.LIGHTBLACK = COLOR_LIGHTBLACK
        self.touch_release = False
        self.landscape = False
        self.frame_counter = 0
        _, window_height = Window.size
        self.font_size = window_height * 0.04
        
    @mainthread
    def clear(self):
        self.canvas.clear()

    @mainthread
    def draw_string(self, x, y, s, color=COLOR_WHITE, bgcolor=COLOR_BLACK):
        label = CoreLabel(text=s, font_size=self.font_size, color=color, font_name='Ubuntu' )
        label.refresh()
        text = label.texture
        if self.landscape:
            y = self._height() - y - text.size[1]
            x -= (self._height() - self._width() + self.font_size)//2
            y += (self._height() - self._width())//2
            self.canvas.add(Rectangle(size=text.size, pos=(x,y), texture=text))
        else:
            y = self._height() - y - text.size[1]
            self.canvas.add(Rectangle(size=text.size, pos=(x,y), texture=text))

    @mainthread
    def fill_rectangle(self, x, y, w, h, color=COLOR_LIGHTGREY):
        y = self._height() - y - h
        self.canvas.add(Color(color[0], color[1], color[2], color[3]))
        self.canvas.add(Rectangle(pos=(x, y), size=(w, h)))
        self.canvas.add(Color(1,1,1)) #come back to default white
    
    @mainthread
    def rotation(self, r):
        if r == 2:
            with self.canvas:
                # PushMatrix()
                Rotate(origin=self.center, angle=-90)
                # PopMatrix()
            self.landscape = True
        else:
            with self.canvas:
                # PushMatrix()
                Rotate(origin=self.center, angle=90)
                # PopMatrix()
            self.landscape = False
        time.sleep(0.01)
 

    def _width(self):
        return int(self.width)

    def _height(self):
        if self.height > 200:
            return int(self.height)
        # widget size not ready at boot, so gets window size
        _, window_height = Window.size
        return window_height
    
    @mainthread
    def draw_qr_code(self, offset_y, code_str, max_width, dark_color=COLOR_BLACK, light_color=COLOR_WHITE):
        starting_size = 2
        while code_str[starting_size] != "\n":
            starting_size += 1
        # starting size is the amount of blocks per line
        max_width = min(self._width(), self._height())
        # scale is how many pixels per block
        scale = max_width // starting_size
        # qr_width is total QR width in pixels
        qr_width = starting_size * scale
        #texture = Texture.create(size=(starting_size, starting_size), colorfmt='rgb')
        texture = Texture.create(size=(starting_size, starting_size), colorfmt='rgb')
        # buf_size = starting_size * starting_size
        buf_size = starting_size * starting_size
        buf_size *= 3
        buf = [0 for x in range(buf_size)]
        pixel_index = 0
        for inverted_y in range(starting_size): # vertical blocks loop
            y = starting_size - inverted_y - 1
            for x in range(starting_size): # horizontal blocks loop
                xy_index = y * (starting_size+1) + x  # individual block index
                color = dark_color if code_str[xy_index] == "1" else light_color
                if isinstance(color, int):
                    color = int(str(color),16)
                    red = color//256
                    green = red
                    blue = red
                else:
                    red, green, blue, _ = color
                    red *= 255
                    green *= 255
                    blue *= 255
                buf[pixel_index*3] = int(red)
                buf[pixel_index*3+1] = int(green)
                buf[pixel_index*3+2] = int(blue)
                pixel_index += 1
        # offset will be used only in position for Android
        offset = (max_width - qr_width) // 2      
        buf = bytes(buf)
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        texture.mag_filter = 'nearest'

        with self.canvas:
            Rectangle(
                texture=texture,
                pos=(offset + 0, self._height() - offset - qr_width),
                size=(starting_size*scale, starting_size*scale)
            )
        
    @mainthread
    def display(self, img, oft=None, roi=None):
        return
        self.frame_counter += 1
        # self.clear()
        self.draw_string(50,50, str(self.frame_counter))
        frame = img.get_frame()
        if not isinstance(frame, MagicMock):
            buf = frame.tostring()
            image_texture = Texture.create(
                size=(self._width(), self._height()), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.texture = image_texture
            with self.canvas:
                Rectangle(texture=image_texture, pos=self.pos, size=(self._width(), self._height()))

    def on_touch_down(self, touch):
        x, y = touch.pos
        y = self._height() - y
        if self.pressed == ([x, y]):
            x +=1 #force event if touches in same place as before
        self.pressed = ([x, y])
        return True

    def on_touch_up(self, touch):
        x, y = touch.pos
        y = self._height() - y
        if self.released == ([x, y]):
            x +=1 #force event if touches in same place as before
        self.released = ([x, y])
        return True

