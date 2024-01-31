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
import lcd
import board
from .themes import theme

DEFAULT_PADDING = 10
FONT_WIDTH, FONT_HEIGHT = board.config["krux"]["display"]["font"]
PORTRAIT, LANDSCAPE = [1, 2]
QR_DARK_COLOR, QR_LIGHT_COLOR = board.config["krux"]["display"]["qr_colors"]

DEFAULT_BACKLIGHT = 1

# Splash will use h. centered text plots. This spaces are used to align without being
SPLASH = [
    "██   ",
    "██   ",
    "██   ",
    "██████   ",
    "██   ",
    " ██  ██",
    "██ ██",
    "████ ",
    "██ ██",
    " ██  ██",
    "  ██   ██",
]


class Display:
    """Display is a singleton interface for interacting with the device's display"""

    def __init__(self):
        self.portrait = True
        self.font_width = FONT_WIDTH
        self.font_height = FONT_HEIGHT
        # Custom for Android
        self.total_lines = self.height() // FONT_HEIGHT
        self.bottom_line = (self.total_lines - 1) * FONT_HEIGHT
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
            self.set_backlight(DEFAULT_BACKLIGHT)
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

    def qr_offset(self):
        """Retuns y offset to subtitle QR codes"""
        return self.width() + DEFAULT_PADDING // 2

    def width(self):
        """Returns the width of the display, taking into account rotation"""
        if self.portrait:
            return lcd._width()  # Custom for Android
        return lcd._height()  # Custom for Android

    def usable_width(self):
        """Returns available width considering side padding"""
        return self.width() - 2 * DEFAULT_PADDING

    def height(self):
        """Returns the height of the display, taking into account rotation"""
        if self.portrait:
            return lcd._height()  # Custom for Android
        return lcd._width()  # Custom for Android

    def qr_data_width(self):
        """Returns a smaller width for the QR to be generated
        within, which will then be scaled up to fit the display's width.
        We do this because the QR would be too dense to be readable
        by most devices otherwise.
        """
        if self.width() > 300:
            return self.width() // 6  # reduce density even more on larger screens
        if self.width() > 200:
            return self.width() // 5
        return self.width() // 4

    def to_landscape(self):
        """Changes the rotation of the display to landscape"""
        lcd.rotation(LANDSCAPE)
        self.portrait = False

    def to_portrait(self):
        """Changes the rotation of the display to portrait"""
        lcd.rotation(PORTRAIT)
        self.portrait = True

    def to_lines(self, text, max_lines=None):
        """Takes a string of text and converts it to lines to display on
        the screen
        """
        lines = []
        start = 0
        line_count = 0
        if self.width() > 135:
            columns = self.usable_width() // self.font_width
        else:
            columns = self.width() // self.font_width

        # Quick return if content fits in one line
        if len(text) <= columns and "\n" not in text:
            return [text]

        if not max_lines:
            max_lines = self.total_lines

        while start < len(text) and line_count < max_lines:
            # Find the next line break, if any
            line_break = text.find("\n", start)
            if line_break == -1:
                next_break = len(text)
            else:
                next_break = min(line_break, len(text))

            end = start + columns
            # If next segment fits on one line, add it and continue
            if end >= next_break:
                lines.append(text[start:next_break].rstrip())
                start = next_break + 1
                line_count += 1
                continue

            # If the end of the line is in the middle of a word,
            # move the end back to the end of the previous word
            if text[end] != " " and text[end] != "\n":
                end = text.rfind(" ", start, end)

            # If there is no space, force break the word
            if end == -1 or end < start:
                end = start + columns

            lines.append(text[start:end].rstrip())
            # don't jump space if we're breaking a word
            jump_space = 1 if text[end] == " " else 0
            start = end + jump_space
            line_count += 1

        # Replace last line with ellipsis if we didn't finish the text
        if line_count == max_lines and start < len(text):
            lines[-1] = lines[-1][: columns - 3] + "..."

        return lines

    def clear(self):
        """Clears the display"""
        lcd.clear(theme.bg_color)

    def outline(self, x, y, width, height, color=theme.fg_color):
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

    def draw_string(self, x, y, text, color=theme.fg_color, bg_color=theme.bg_color):
        """Draws a string to the screen"""
        if board.config["krux"]["display"]["inverted_coordinates"]:
            x = self.width() - x
            x -= len(text) * self.font_width
        lcd.draw_string(x, y, text, color, bg_color)

    def draw_hcentered_text(
        self,
        text,
        offset_y=DEFAULT_PADDING,
        color=theme.fg_color,
        bg_color=theme.bg_color,
        info_box=False,
        max_lines=None,
    ):
        """Draws text horizontally-centered on the display, at the given offset_y"""
        lines = (
            text if isinstance(text, list) else self.to_lines(text, max_lines=max_lines)
        )
        if info_box:
            bg_color = theme.disabled_color
            self.fill_rectangle(
                DEFAULT_PADDING - 3,
                offset_y - 1,
                self.usable_width() + 6,
                (len(lines)) * self.font_height + 2,
                bg_color,
            )
        for i, line in enumerate(lines):
            if len(line) > 0:
                offset_x = max(0, (self.width() - self.font_width * len(line)) // 2)
                self.draw_string(
                    offset_x, offset_y + (i * self.font_height), line, color, bg_color
                )
        return len(lines)  # return number of lines drawn

    def draw_centered_text(self, text, color=theme.fg_color, bg_color=theme.bg_color):
        """Draws text horizontally and vertically centered on the display"""
        lines = text if isinstance(text, list) else self.to_lines(text)
        lines_height = len(lines) * self.font_height
        offset_y = max(0, (self.height() - lines_height) // 2)
        self.draw_hcentered_text(text, offset_y, color, bg_color)

    def draw_qr_code(
        self, offset_y, qr_code, dark_color=QR_DARK_COLOR, light_color=QR_LIGHT_COLOR
    ):
        """Draws a QR code on the screen"""
        lcd.draw_qr_code_binary(
            offset_y, qr_code, self.width(), dark_color, light_color, light_color
        )

    def set_backlight(self, level):
        """Sets the backlight of the display to the given power level, from 0 to 8"""

        from .power import power_manager

        power_manager.set_screen_brightness(level)

    def max_menu_lines(self, line_offset=0):
        """Maximum menu items the display can fit"""
        pad = DEFAULT_PADDING if line_offset else 2 * DEFAULT_PADDING
        return (self.height() - pad - line_offset) // (2 * self.font_height)
