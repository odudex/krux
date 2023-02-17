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
import time
import lcd
import board
# from machine import I2C

DEFAULT_PADDING = 10
FONT_WIDTH, FONT_HEIGHT = board.config["krux"]["display"]["font"]
PORTRAIT, LANDSCAPE = [1, 2]
QR_DARK_COLOR, QR_LIGHT_COLOR = board.config["krux"]["display"]["qr_colors"]


MAX_BACKLIGHT = 8
MIN_BACKLIGHT = 1


class Display:
    """Display is a singleton interface for interacting with the device's display"""

    def __init__(self):
        self.portrait = True
        # self.initialize_lcd()
        self.i2c = None
        self.font_width = FONT_WIDTH
        self.font_height = FONT_HEIGHT
        self.bottom_line = self.height() // FONT_HEIGHT  # total lines
        self.bottom_line -= 1
        self.bottom_line *= FONT_HEIGHT
        if board.config["type"] == "m5stickv":
            self.bottom_prompt_line = self.bottom_line - DEFAULT_PADDING
        else:
            # room left for no/yes buttons
            self.bottom_prompt_line = self.bottom_line - 3 * FONT_HEIGHT

    def initialize_lcd(self):
        """Initializes the LCD"""
        if board.config["lcd"]["lcd_type"] == 3:
            lcd.init(type=board.config["lcd"]["lcd_type"])
            lcd.register(0x3A, 0x05)
            lcd.register(0xB2, [0x05, 0x05, 0x00, 0x33, 0x33])
            lcd.register(0xB7, 0x23)
            lcd.register(0xBB, 0x22)
            lcd.register(0xC0, 0x2C)
            lcd.register(0xC2, 0x01)
            lcd.register(0xC3, 0x13)
            lcd.register(0xC4, 0x20)
            lcd.register(0xC6, 0x0F)
            lcd.register(0xD0, [0xA4, 0xA1])
            lcd.register(0xD6, 0xA1)
            lcd.register(
                0xE0,
                [
                    0x23,
                    0x70,
                    0x06,
                    0x0C,
                    0x08,
                    0x09,
                    0x27,
                    0x2E,
                    0x34,
                    0x46,
                    0x37,
                    0x13,
                    0x13,
                    0x25,
                    0x2A,
                ],
            )
            lcd.register(
                0xE1,
                [
                    0x70,
                    0x04,
                    0x08,
                    0x09,
                    0x07,
                    0x03,
                    0x2C,
                    0x42,
                    0x42,
                    0x38,
                    0x14,
                    0x14,
                    0x27,
                    0x2C,
                ],
            )
            self.initialize_backlight()
        else:
            invert = (
                board.config["type"].startswith("amigo")
                or board.config["lcd"]["invert"]
            )
            lcd.init(invert=invert)
            lcd.bgr_to_rgb(invert)
        self.to_portrait()
        if board.config["type"].startswith("amigo"):
            lcd.mirror(True)

    def initialize_backlight(self):
        """Initializes the backlight"""
        if (
            "I2C_SCL" not in board.config["krux"]["pins"]
            or "I2C_SDA" not in board.config["krux"]["pins"]
        ):
            return
        self.i2c = I2C(
            I2C.I2C0,
            freq=400000,
            scl=board.config["krux"]["pins"]["I2C_SCL"],
            sda=board.config["krux"]["pins"]["I2C_SDA"],
        )
        self.set_backlight(MIN_BACKLIGHT)

    def qr_offset(self):
        """Retuns y offset to subtitle QR codes"""
        return self.width() + DEFAULT_PADDING // 2

    def width(self):
        """Returns the width of the display, taking into account rotation"""
        if self.portrait:
            return lcd._width()
        return lcd._height()

    def usable_width(self):
        """Returns available width considering side padding"""
        return self.width() - 2 * DEFAULT_PADDING

    def height(self):
        """Returns the height of the display, taking into account rotation"""
        if self.portrait:
            return lcd._height()
        return lcd._width()

    def qr_data_width(self):
        """Returns a smaller width for the QR to be generated
        within, which will then be scaled up to fit the display's width.
        We do this because the QR would be too dense to be readable
        by most devices otherwise.
        """
        if self.width() > 300:
            return self.width() // 6  # reduce density even more on larger screens
        return self.width() // 4

    def to_landscape(self):
        """Changes the rotation of the display to landscape"""
        lcd.rotation(LANDSCAPE)
        self.portrait = False

    def to_portrait(self):
        """Changes the rotation of the display to portrait"""
        lcd.rotation(PORTRAIT)
        self.portrait = True

    def to_lines(self, text):
        """Takes a string of text and converts it to lines to display on
        the screen
        """
        if self.width() > 135:
            columns = self.usable_width() // self.font_width
        else:
            columns = self.width() // self.font_width
        words = []
        for word in text.split(" "):
            subwords = word.split("\n")
            for i, subword in enumerate(subwords):
                if len(subword) > columns:
                    j = 0
                    while j < len(subword):
                        words.append(subword[j : j + columns])
                        j += columns
                else:
                    words.append(subword)

                if len(subwords) > 1 and i < len(subwords) - 1:
                    # Only add newline to the end of the word if the word
                    # is less than the amount of columns. If it's exactly equal,
                    # a newline will be implicit.
                    if len(words[-1]) < columns:
                        words[-1] += "\n"

        num_words = len(words)

        # calculate cost of all pairs of words
        cost_between = [[0 for _ in range(num_words + 1)] for _ in range(num_words + 1)]
        for i in range(1, num_words + 1):
            for j in range(i, num_words + 1):
                for k in range(i, j + 1):
                    if words[k - 1].endswith("\n"):
                        word = words[k - 1].split("\n")[0]
                        if word != "":
                            cost_between[i][j] += len(words[k - 1]) + 1
                        if i <= k < j:
                            cost_between[i][j] += float("inf")
                    else:
                        cost_between[i][j] += len(words[k - 1]) + 1
                cost_between[i][j] -= 1
                cost_between[i][j] = columns - cost_between[i][j]
                if cost_between[i][j] < 0:
                    cost_between[i][j] = float("inf")
                cost_between[i][j] = cost_between[i][j] ** 2

        # find optimal number of words on each line
        indexes = [0 for _ in range(num_words + 1)]
        cost = [0 for _ in range(num_words + 1)]
        cost[0] = 0
        for j in range(1, num_words + 1):
            cost[j] = float("inf") * float("inf")
            for i in range(1, j + 1):
                if cost[i - 1] + cost_between[i][j] < cost[j]:
                    cost[j] = cost[i - 1] + cost_between[i][j]
                    indexes[j] = i

        def build_lines(words, num_words, indexes):
            lines = []
            start = indexes[num_words]
            end = num_words
            if start != 1:
                lines.extend(build_lines(words, start - 1, indexes))
            line = ""
            for i in range(start, end + 1):
                if words[i - 1].endswith("\n"):
                    word = words[i - 1].split("\n")[0]
                    if word != "":
                        line += (" " if len(line) > 0 else "") + word
                    lines.append(line)
                    line = ""
                else:
                    line += (" " if len(line) > 0 else "") + words[i - 1]
            if len(line) > 0:
                lines.append(line)
            return lines

        return build_lines(words, num_words, indexes)

    def clear(self):
        """Clears the display"""
        lcd.clear()

    def outline(self, x, y, width, height, color=lcd.WHITE):
        """Draws an outline rectangle from given coordinates"""
        self.fill_rectangle(x, y, width + 1, 1, color)  # up
        self.fill_rectangle(x, y + height, width + 1, 1, color)  # bottom
        self.fill_rectangle(x, y, 1, height + 1, color)  # left
        self.fill_rectangle(x + width, y, 1, height + 1, color)  # right

    def fill_rectangle(self, x, y, width, height, color):
        """Draws a rectangle to the screen"""
        if board.config["krux"]["display"]["inverted_coordinates"]:
            x = self.width() - x
            x -= width
        lcd.fill_rectangle(x, y, width, height, color)

    def draw_string(self, x, y, text, color, bg_color=lcd.BLACK):
        """Draws a string to the screen"""
        if board.config["krux"]["display"]["inverted_coordinates"]:
            x = self.width() - x
            x -= len(text) * self.font_width
        lcd.draw_string(x, y, text, color, bg_color)

    def draw_hcentered_text(
        self, text, offset_y=DEFAULT_PADDING, color=lcd.WHITE, bg_color=lcd.BLACK
    ):
        """Draws text horizontally-centered on the display, at the given offset_y"""
        lines = text if isinstance(text, list) else self.to_lines(text)
        for i, line in enumerate(lines):
            offset_x = (self.width() - self.font_width * len(line)) // 2
            offset_x = max(0, offset_x)
            self.draw_string(
                offset_x, offset_y + (i * self.font_height), line, color, bg_color
            )

    def draw_centered_text(self, text, color=lcd.WHITE, bg_color=lcd.BLACK):
        """Draws text horizontally and vertically centered on the display"""
        lines = text if isinstance(text, list) else self.to_lines(text)
        lines_height = len(lines) * self.font_height
        offset_y = max(0, (self.height() - lines_height) // 2)
        self.draw_hcentered_text(text, offset_y, color, bg_color)

    def flash_text(self, text, color=lcd.WHITE, bg_color=lcd.BLACK, duration=3000):
        """Flashes text centered on the display for duration ms"""
        self.clear()
        self.draw_centered_text(text, color, bg_color)
        time.sleep_ms(duration)
        self.clear()

    def draw_qr_code(self, offset_y, qr_code, light_color=QR_LIGHT_COLOR, region=None):
        """Draws a QR code on the screen"""
        # Add a 1 block white border around the code before displaying
        qr_code = qr_code.strip()
        lines = qr_code.split("\n")
        size = len(lines)
        size += 2
        new_lines = ["0" * size]
        for line in lines:
            new_lines.append("0" + line + "0")
        new_lines.append("0" * size)
        qr_code = "\n".join(new_lines)
        if region is None:

            region = (0,0,size,size)
        lcd.draw_qr_code(
            offset_y, qr_code, self.width(), QR_DARK_COLOR, light_color, region
        )

    def set_backlight(self, level):
        """Sets the backlight of the display to the given power level, from 0 to 8"""
        if not self.i2c:
            return
        # Ranges from 0 to 8
        level = max(0, min(level, 8))
        val = (level + 7) << 4
        self.i2c.writeto_mem(0x34, 0x91, int(val))
