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

import lcd
from embit.wordlists.bip39 import WORDLIST
from . import Page
from ..krux_settings import t
from ..display import DEFAULT_PADDING
from ..input import (
    BUTTON_ENTER,
    BUTTON_PAGE,
    BUTTON_PAGE_PREV,
    BUTTON_TOUCH,
)

STACKBIT_GO_INDEX = 38
STACKBIT_ESC_INDEX = 35
STACKBIT_MAX_INDEX = 13


class Stackbit(Page):
    """Class for handling Stackbit 1248 fomat"""

    def __init__(self, ctx):
        super().__init__(ctx, None)
        self.ctx = ctx
        self.x_offset = DEFAULT_PADDING
        self.x_pad = 2 * self.ctx.display.font_width
        self.y_offset = 2 * self.ctx.display.font_height
        self.y_pad = self.ctx.display.font_height

    def _draw_labels(self, y_offset, word_index):
        """Draws labels for import and export Stackbit 1248 UI"""
        index_x_offset = self.x_offset + self.x_pad // 2 - 1
        y_offset += (self.y_pad - self.ctx.display.font_height) // 2
        if len(str(word_index)) > 1:
            index_x_offset -= self.ctx.display.font_width
        self.ctx.display.draw_string(
            index_x_offset,
            y_offset + self.y_pad // 2,
            str(word_index),
            lcd.WHITE,
            lcd.SLATEGREY,
        )
        numbers_offset = self.x_offset + self.x_pad
        numbers_offset += (self.x_pad - self.ctx.display.font_width) // 2
        upper_numbers = [1, 1, 2, 1, 2, 1, 2]
        lower_numbers = [2, 4, 8, 4, 8, 4, 8]
        for x in range(len(upper_numbers)):
            self.ctx.display.draw_string(
                numbers_offset,
                y_offset,
                str(upper_numbers[x]),
                lcd.WHITE,
            )
            self.ctx.display.draw_string(
                numbers_offset,
                y_offset + self.y_pad,
                str(lower_numbers[x]),
                lcd.WHITE,
            )
            numbers_offset += self.x_pad

    def _draw_grid(self, y_offset):
        """Draws grid for import and export Stackbit 1248 UI"""
        y_offset -= 2
        x_bar_offset = self.x_offset
        # Horizontal lines
        width = 8 * self.x_pad + self.ctx.display.font_width // 2
        height = 2 * self.y_pad + 2

        # Word_num background
        self.ctx.display.fill_rectangle(
            x_bar_offset - self.ctx.display.font_width // 2,
            y_offset,
            self.x_pad + self.ctx.display.font_width // 2,
            height,
            lcd.SLATEGREY,
        )

        # top line
        self.ctx.display.fill_rectangle(
            x_bar_offset - self.ctx.display.font_width // 2,
            y_offset,
            width,
            1,
            lcd.DARKGREY,
        )
        # bottom line
        self.ctx.display.fill_rectangle(
            x_bar_offset - self.ctx.display.font_width // 2,
            y_offset + height,
            width,
            1,
            lcd.DARKGREY,
        )
        # Vertical lines
        # Left v line
        self.ctx.display.fill_rectangle(
            x_bar_offset - self.ctx.display.font_width // 2,
            y_offset,
            1,
            height,
            lcd.DARKGREY,
        )
        # Second left vertical line
        x_bar_offset += self.x_pad
        self.ctx.display.fill_rectangle(
            x_bar_offset,
            y_offset,
            1,
            height,
            lcd.DARKGREY,
        )
        x_bar_offset += self.x_pad
        # Next 4 vertical lines
        for _ in range(4):
            self.ctx.display.fill_rectangle(
                x_bar_offset,
                y_offset,
                1,
                height,
                lcd.DARKGREY,
            )
            x_bar_offset += 2 * self.x_pad

    def _word_to_digits(self, word):
        """Converts words to its dictionary position as 4 digit numbers"""
        word_list_index = WORDLIST.index(word) + 1
        word_list_index_str = str(word_list_index)
        while len(word_list_index_str) < 4:
            word_list_index_str = "0" + word_list_index_str
        return [int(x) for x in str(word_list_index_str)], word_list_index_str

    def _draw_punched(self, digits, y_offset, export=False):
        """Draws punched bits for import and export Stackbit UI"""
        outline_width = self.x_pad - 6
        outline_height = self.y_pad - 4
        outline_x_offset = self.x_offset + self.x_pad + 3

        # print border around numbers only on touch devices
        if not export and self.ctx.input.touch is not None:
            # x for each col
            for x in range(7):
                # y for each line
                for y in range(2):
                    self.ctx.display.outline(
                        outline_x_offset + x * self.x_pad,
                        y_offset + y * self.y_pad + 1,
                        outline_width,
                        outline_height,
                        lcd.DARKGREY,
                    )

        if digits[0] == 2:
            self.ctx.display.outline(
                outline_x_offset,
                y_offset + self.y_pad + 1,
                outline_width,
                outline_height,
                lcd.GREEN,
            )
        elif digits[0] == 1:
            self.ctx.display.outline(
                outline_x_offset,
                y_offset + 1,
                outline_width,
                outline_height,
                lcd.GREEN,
            )
        outline_x_offset += self.x_pad
        for x in range(3):
            if (digits[x + 1] >> 3) & 1:
                self.ctx.display.outline(
                    outline_x_offset + self.x_pad,
                    y_offset + self.y_pad + 1,
                    outline_width,
                    outline_height,
                    lcd.GREEN,
                )
            if (digits[x + 1] >> 2) & 1:
                self.ctx.display.outline(
                    outline_x_offset,
                    y_offset + self.y_pad + 1,
                    outline_width,
                    outline_height,
                    lcd.GREEN,
                )
            if (digits[x + 1] >> 1) & 1:
                self.ctx.display.outline(
                    outline_x_offset + self.x_pad,
                    y_offset + 1,
                    outline_width,
                    outline_height,
                    lcd.GREEN,
                )
            if digits[x + 1] & 1:
                self.ctx.display.outline(
                    outline_x_offset,
                    y_offset + 1,
                    outline_width,
                    outline_height,
                    lcd.GREEN,
                )
            outline_x_offset += 2 * self.x_pad

    def export_1248(self, word_index, y_offset, word):
        """Draws punch pattern for Stackbit 1248 seed layout"""

        self.x_offset = DEFAULT_PADDING
        # case for m5stickv
        if self.ctx.display.width() == 135:
            self.x_offset = 5
        self.x_pad = 2 * self.ctx.display.font_width
        self.y_offset = 2 * self.ctx.display.font_height
        self.y_pad = self.ctx.display.font_height

        self.ctx.display.draw_hcentered_text(t("Stackbit 1248"))
        self._draw_grid(y_offset)
        self._draw_labels(y_offset, word_index)
        digits, digits_str = self._word_to_digits(word)
        self._draw_punched(digits, y_offset, True)
        if self.ctx.display.height() > 240:
            self.ctx.display.draw_string(
                self.x_offset + 17 * self.ctx.display.font_width,
                y_offset,
                digits_str,
                lcd.LIGHTGREY,
            )
            self.ctx.display.draw_string(
                self.x_offset + 17 * self.ctx.display.font_width,
                y_offset + self.y_pad,
                word,
                lcd.LIGHTGREY,
            )

    def _toggle_bit(self, digits, index):
        """Toggle bit state according to pressed index"""
        index_to_digit_bit = [
            [0, 0],
            [1, 0],
            [1, 1],
            [2, 0],
            [2, 1],
            [3, 0],
            [3, 1],
            [0, 1],
            [1, 2],
            [1, 3],
            [2, 2],
            [2, 3],
            [3, 2],
            [3, 3],
        ]
        if index < 14:
            digit, bit = index_to_digit_bit[index]
            digits[digit] = digits[digit] ^ (1 << bit)

            # sanity check
            if digit == 0 and digits[0] > 2:
                digits[0] = 1 << bit
            elif digit != 0 and digits[digit] > 9:
                digits[digit] = 1 << bit

        return digits

    def _draw_index(self, index):
        """Outline index respective"""
        x_offset = self.x_offset + self.x_pad + 1
        width = 3 * self.x_pad
        y_position = index // 7
        y_position *= self.y_pad
        y_position += self.y_offset - 1
        if index >= STACKBIT_GO_INDEX:
            x_position = x_offset + 3 * self.x_pad
            y_position += 1
        elif index >= STACKBIT_ESC_INDEX:
            x_position = x_offset
            y_position += 1
        elif index < 14:
            x_position = index % 7
            x_position *= self.x_pad
            x_position += x_offset
            width = self.x_pad - 2
        else:
            return
        self.ctx.display.outline(
            x_position,
            y_position,
            width,
            self.y_pad,
            lcd.WHITE,
        )

    def _draw_menu(self):
        """Draws options to leave and proceed"""
        y_offset = self.y_offset + 5 * self.y_pad
        label_y_offset = (self.y_pad - self.ctx.display.font_height) // 2
        x_offset = self.x_offset + self.x_pad
        self.ctx.display.draw_string(
            x_offset + 1 * self.x_pad, y_offset + label_y_offset, t("Esc"), lcd.WHITE
        )
        self.ctx.display.draw_string(
            round(x_offset + 4.2 * self.x_pad),
            y_offset + label_y_offset,
            t("Go"),
            lcd.WHITE,
        )
        # print border around buttons only on touch devices
        if self.ctx.input.touch is not None:
            self.ctx.display.fill_rectangle(
                x_offset,
                y_offset,
                6 * self.x_pad,
                1,
                lcd.DARKGREY,
            )
            self.ctx.display.fill_rectangle(
                x_offset,
                y_offset + self.y_pad,
                6 * self.x_pad,
                1,
                lcd.DARKGREY,
            )
            for _ in range(3):
                self.ctx.display.fill_rectangle(
                    x_offset,
                    y_offset,
                    1,
                    self.y_pad,
                    lcd.DARKGREY,
                )
                x_offset += 3 * self.x_pad

    def digits_to_word(self, digits):
        """Returns seed word respective to digits BIP39 dictionaty position"""
        word_number = int("".join(str(num) for num in digits))
        if 0 < word_number <= 2048:
            return WORDLIST[word_number - 1]
        return None

    def preview_word(self, digits):
        """Draws word respective to current state"""
        preview_string = "".join(str(num) for num in digits)
        color = lcd.RED
        word = self.digits_to_word(digits)
        if word is not None:
            preview_string += ": " + word
            color = lcd.WHITE
        y_offset = self.y_offset + 3 * self.y_pad
        self.ctx.display.draw_hcentered_text(preview_string, y_offset, color=color)

    def _map_keys_array(self):
        """Maps an array of regions for keys to be placed in"""
        if self.ctx.input.touch is not None:
            self.ctx.input.touch.clear_regions()
            x_region = self.x_offset + self.x_pad
            for _ in range(8):
                self.ctx.input.touch.x_regions.append(x_region)
                x_region += self.x_pad
            y_region = self.y_offset
            for _ in range(7):
                self.ctx.input.touch.y_regions.append(y_region)
                y_region += self.y_pad

    def index(self, index, btn):
        """Calculates new index according to button press"""
        page_move = [7, 2, 8, 4, 10, 6, 12, 1, 9, 3, 11, 5, 13]
        page_prev_move = [STACKBIT_GO_INDEX, 7, 1, 9, 3, 11, 5, 0, 2, 8, 4, 10, 6, 12]
        if btn == BUTTON_PAGE:
            if index >= STACKBIT_GO_INDEX:
                return 0
            if index >= STACKBIT_ESC_INDEX:
                return STACKBIT_GO_INDEX
            if index >= STACKBIT_MAX_INDEX:
                return STACKBIT_ESC_INDEX
            return page_move[index]
        if btn == BUTTON_PAGE_PREV:
            if index <= 0:
                return STACKBIT_GO_INDEX
            if index <= STACKBIT_MAX_INDEX:
                return page_prev_move[index]
            if index <= STACKBIT_ESC_INDEX:
                return STACKBIT_MAX_INDEX
        return STACKBIT_ESC_INDEX

    def enter_1248(self):
        """UI to manually enter a Stackbit 1248"""
        if self.ctx.display.width() > 135:
            self.x_pad = 3 * self.ctx.display.font_width
        else:
            self.x_pad = 2 * self.ctx.display.font_width
        self.x_offset = self.ctx.display.width()
        self.x_offset -= 8 * self.x_pad
        self.x_offset = max(self.x_offset, DEFAULT_PADDING)
        self.x_offset //= 2
        self.y_offset = 3 * self.ctx.display.font_height
        self.y_pad = 2 * self.ctx.display.font_height
        index = 0
        digits = [0, 0, 0, 0]
        word_index = 1
        words = []
        while word_index <= 24:
            self._map_keys_array()
            self.ctx.display.draw_hcentered_text(t("Stackbit 1248"))
            y_offset = self.y_offset
            self._draw_grid(y_offset)
            self._draw_labels(y_offset, word_index)
            self._draw_menu()
            if self.ctx.input.buttons_active:
                self._draw_index(index)
            self.preview_word(digits)
            self._draw_punched(digits, y_offset)
            btn = self.ctx.input.wait_for_button()
            if btn == BUTTON_TOUCH:
                btn = BUTTON_ENTER
                index = self.ctx.input.touch.current_index()
            if btn == BUTTON_ENTER:
                if index >= STACKBIT_GO_INDEX:  # go
                    word = self.digits_to_word(digits)
                    if word is not None:
                        prompt_str = (
                            str(word_index)
                            + ".\n\n"
                            + "".join(str(num) for num in digits)
                            + ": "
                            + str(word)
                            + "\n\n"
                        )
                        digits = [0, 0, 0, 0]
                        index = 0
                        self.ctx.display.clear()
                        if self.prompt(prompt_str, self.ctx.display.height() // 2):
                            words.append(word)
                        else:
                            self.ctx.display.clear()
                            continue
                        if word_index == 12:
                            self.ctx.display.clear()
                            if self.prompt(t("Done?"), self.ctx.display.height() // 2):
                                break
                            # self._map_keys_array() #can be removed?
                        word_index += 1
                elif index >= STACKBIT_ESC_INDEX:  # ESC
                    self.ctx.display.clear()
                    if self.prompt(t("Are you sure?"), self.ctx.display.height() // 2):
                        break
                    # self._map_keys_array()
                elif index < 14:
                    digits = self._toggle_bit(digits, index)
            else:
                index = self.index(index, btn)
            self.ctx.display.clear()
        if len(words) in (12, 24):
            return words
        return None