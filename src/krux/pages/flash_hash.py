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

from . import Page, MENU_CONTINUE, DEFAULT_PADDING
from ..themes import theme
from ..krux_settings import t
from ..display import FONT_HEIGHT
from ..wdt import wdt

BLOCK_SIZE = 0x1000


class FlashHash(Page):
    """Generate a human recognizable snapshot of the flash memory tied to a PIN"""

    def __init__(self, ctx, pin_hash):
        super().__init__(ctx, None)
        self.ctx = ctx
        self.pin_hash = pin_hash
        self.image_block_size = self.ctx.display.width() // 7

    def hash_pin_with_flash(self, spiffs_region=False):
        """Hashes the pin, unique ID and flash memory together"""
        import hashlib
        import flash
        from ..firmware import FLASH_SIZE, SPIFFS_ADDR
        from machine import unique_id

        counter = SPIFFS_ADDR // BLOCK_SIZE if spiffs_region else 0
        range_begin = SPIFFS_ADDR if spiffs_region else 0
        range_end = FLASH_SIZE if spiffs_region else SPIFFS_ADDR
        percentage_offset = (
            DEFAULT_PADDING + 3 * FONT_HEIGHT + self.image_block_size * 5
        )
        if self.ctx.display.width() < self.ctx.display.height():
            percentage_offset += FONT_HEIGHT
        sha256 = hashlib.sha256()
        sha256.update(self.pin_hash)
        sha256.update(unique_id())
        for address in range(range_begin, range_end, BLOCK_SIZE):
            counter += 1
            sha256.update(flash.read(address, BLOCK_SIZE))
            if counter % 100 == 0:
                # Update progress
                self.ctx.display.draw_hcentered_text(
                    "%d%%" % (counter // 41), percentage_offset
                )
                wdt.feed()
        return sha256.digest()

    def hash_to_random_color(self, hash_bytes):
        """Generates a random color from part of the hash."""
        # Extract the last 3 bytes of the hash
        red = hash_bytes[-3] % 2  # 0 or 1
        green = hash_bytes[-2] % 2
        blue = hash_bytes[-1] % 2

        # If all components are False, pick the highest value component and make it True
        if not red and not green and not blue:
            if hash_bytes[-3] >= hash_bytes[-2] and hash_bytes[-3] >= hash_bytes[-1]:
                red = 1
            elif hash_bytes[-2] >= hash_bytes[-3] and hash_bytes[-2] >= hash_bytes[-1]:
                green = 1
            else:
                blue = 1
        red = (0xFF >> 3) << 11 if red else 0
        green = (0xFF >> 2) << 5 if green else 0
        blue = 0xFF >> 3 if blue else 0

        return red + green + blue

    def hash_to_fingerprint(self, hash_bytes, y_offset=DEFAULT_PADDING):
        """Generates a 5x5 pixelated fingerprint based on a 256-bit hash."""

        fg_color = self.hash_to_random_color(hash_bytes)
        block_size = self.image_block_size
        # Create a 5x5 grid, but we'll only compute the first 3 columns
        for row in range(5):
            for col in range(3):  # Only compute the left half and middle column
                byte_index = row * 3 + col
                bit_value = hash_bytes[byte_index] % 2  # 0 or 1

                # Set the color based on the bit value
                color = fg_color if bit_value == 0 else 0

                # Calculate the position and draw the rectangle
                x = (col + 1) * block_size
                y = y_offset + row * block_size
                self.ctx.display.fill_rectangle(x, y, block_size, block_size, color)

                if col < 2:
                    # Draw the mirrored columns (0 and 1)
                    mirrored_col = 5 - col
                    x_mirror = mirrored_col * block_size
                    self.ctx.display.fill_rectangle(
                        x_mirror, y, block_size, block_size, color
                    )

    def hash_to_words(self, hash_bytes):
        """Converts a hash to a list of words"""
        from embit.bip39 import mnemonic_from_bytes

        words = mnemonic_from_bytes(hash_bytes).split()
        return " ".join(words[:2])

    def generate(self):
        """Generates the flash hash snapshot"""
        self.ctx.display.clear()
        self.ctx.display.draw_hcentered_text(t("Generating Flash Hash.."))
        firmware_region_hash = self.hash_pin_with_flash()
        self.ctx.display.clear()
        self.ctx.display.draw_hcentered_text(t("Flash Hash"))
        y_offset = DEFAULT_PADDING + 2 * FONT_HEIGHT
        self.hash_to_fingerprint(firmware_region_hash, y_offset)
        anti_tamper_words = self.hash_to_words(firmware_region_hash)
        y_offset += self.image_block_size * 5
        if self.ctx.display.width() < self.ctx.display.height():
            y_offset += FONT_HEIGHT
        y_offset += (
            self.ctx.display.draw_hcentered_text(
                anti_tamper_words, y_offset, color=theme.highlight_color
            )
            * FONT_HEIGHT
        )
        spiffs_region_hash = self.hash_pin_with_flash(spiffs_region=True)
        anti_tamper_words = self.hash_to_words(spiffs_region_hash)
        self.ctx.display.draw_hcentered_text(anti_tamper_words, y_offset)
        self.ctx.input.wait_for_button()
        return MENU_CONTINUE