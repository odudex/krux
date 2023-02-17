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
import board
from Maix import GPIO
from fpioa_manager import fm


class Light:
    """Light is a singleton interface for interacting with the device's LED light"""

    def __init__(self):
        fm.register(board.config["krux"]["pins"]["LED_W"], fm.fpioa.GPIO3)
        self.led_w = GPIO(GPIO.GPIO3, GPIO.OUT)
        self.turn_off()

    def is_on(self):
        """Returns a boolean indicating if the light is currently on"""
        return self.led_w.value() == 0

    def turn_on(self):
        """Turns on the light"""
        self.led_w.value(0)

    def turn_off(self):
        """Turns off the light"""
        self.led_w.value(1)

    def toggle(self):
        """Toggles the light on or off"""
        if self.is_on():
            self.turn_off()
        else:
            self.turn_on()
