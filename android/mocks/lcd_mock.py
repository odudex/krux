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
import math

from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.uix.label import CoreLabel
from kivy.core.window import Window
from kivy.properties import ListProperty
from kivy.graphics import Rotate
from kivy.clock import mainthread

COLOR_BLACK = (0, 0, 0, 1)
COLOR_WHITE = (1, 1, 1, 1)

class LCD(Widget):

    pressed = ListProperty([0, 0])
    released = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.landscape = False
        self.frame_counter = 0
        _, window_height = Window.size
        self.font_size = window_height // 30

    def rgb565torgb111(self, color):
        """convert from gggbbbbbrrrrrggg to tuple"""
        MASK5 = 0b11111
        MASK3 = 0b111

        red = ((color >> 3) & MASK5)
        red /= 31
        green = color >> 13
        green += (color & MASK3) << 3
        green /= 63
        blue = ((color >> 8) & MASK5)
        blue /= 31
        return (red, green, blue, 1)
        
    @mainthread
    def clear(self, color):
        color = self.rgb565torgb111(color)
        Window.clearcolor = color
        self.canvas.clear()

    @mainthread
    def draw_string(self, x, y, s, color=COLOR_WHITE, bgcolor=COLOR_BLACK):

        color = self.rgb565torgb111(color)
        bgcolor = self.rgb565torgb111(bgcolor)
        label = CoreLabel(text=s, font_size=self.font_size, color=color, font_name='JetBrainsMono-Medium' )
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
    def fill_rectangle(self, x, y, w, h, color=COLOR_WHITE):
        color = self.rgb565torgb111(color)
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
    def draw_qr_code(self, offset_y, code_str, max_width, dark_color=COLOR_BLACK, light_color=COLOR_WHITE, bg_color=COLOR_BLACK):
        dark_color = self.rgb565torgb111(dark_color)
        light_color = self.rgb565torgb111(light_color)
        starting_size = 2
        # starting size is the amount of blocks per line
        while code_str[starting_size] != "\n":
            starting_size += 1
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
                pos=(offset, self._height() - offset - qr_width),
                size=(starting_size*scale, starting_size*scale)
            )

    @mainthread
    def draw_qr_code_binary(self, offset_y, code_bin, max_width, dark_color=COLOR_BLACK, light_color=COLOR_WHITE, bg_color=COLOR_BLACK):
        starting_size = int(math.sqrt(len(code_bin) * 8))
        block_size_divisor = starting_size + 2;  # adds 2 to create room for a 1 block border
        # scale is how many pixels per block
        scale = max_width // block_size_divisor
        # qr_width is total QR width in pixels
        qr_width = starting_size * scale
        border_size = (max_width - qr_width) // 2
        opposite_border_offset = border_size + qr_width
        dark_color = self.rgb565torgb111(dark_color)
        light_color = self.rgb565torgb111(light_color)

        #Draw borders
        self.canvas.add(Color(light_color[0], light_color[1], light_color[2], light_color[3]))
        borders = [
            # Top border
            [0,0,max_width,border_size],
            # Bottom border
            [0,opposite_border_offset,max_width,border_size],
            # Left border
            [0,border_size,border_size,qr_width],
            # Right border
            [opposite_border_offset,border_size,border_size + 1,qr_width],
        ]
        for border in borders:
            y = self._height() - border[1] - border[3]
            self.canvas.add(Rectangle(pos=(border[0], y), size=(border[2], border[3])))
        self.canvas.add(Color(1,1,1)) #come back to default: white
        
        texture = Texture.create(size=(starting_size, starting_size), colorfmt='rgb')
        buf_size = starting_size * starting_size
        buf_size *= 3
        buf = [0 for x in range(buf_size)]
        pixel_index = 0
        for inverted_y in range(starting_size): # vertical blocks loop
            y = starting_size - inverted_y - 1
            for x in range(starting_size): # horizontal blocks loop
                xy_index = y * (starting_size) + x  # individual block index
                color_byte = code_bin[xy_index >> 3]
                color_byte &= (1 << (xy_index % 8))
                color = dark_color if color_byte else light_color
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
                pos=(offset, self._height() - offset - qr_width),
                size=(starting_size*scale, starting_size*scale)
            )
        
    @mainthread
    def display(self, img, oft=None, roi=None):
        return

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

