# The MIT License (MIT)

# Copyright (c) 2021-2024 Krux contributors

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
import sys
from unittest import mock


class FT6X36:
    def __init__(self):
        self.irq_point = None
        self.touch_position = None
        self.release_flag = False
        self.event_flag = False


    def activate_irq(self, irq_pin):
        pass

    def feed_position(self, position, release = False):
        self.touch_position = position
        if not release:
            self.release_flag = False
            self.trigger_event()

    def release(self):
        self.release_flag = True

    def current_point(self):
        if not self.touch_position:
            return None
        position = tuple(self.touch_position)
        if self.release_flag:
            self.release_flag = False
            self.touch_position = None
        return position
    
    def trigger_event(self):
        """Called by IRQ handler to set event flag and capture touch point"""
        self.event_flag = True
        self.irq_point = self.current_point()
    
    def event(self):
        flag = self.event_flag
        self.event_flag = False  # Always clean event flag
        return flag

    def threshold(self):
        pass

touch_control = FT6X36()

if "krux.touchscreens.ft6x36" not in sys.modules:
    sys.modules["krux.touchscreens.ft6x36"] = mock.MagicMock(
        touch_control=touch_control,
    )
