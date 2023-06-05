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

from ..sd_card import SDHandler
#import uos
import time
from ..krux_settings import t
from ..printers import create_printer
from ..themes import theme
from ..qr import FORMAT_NONE
from . import (
    Page,
    Menu,
    MENU_CONTINUE,
    MENU_EXIT,
    SD_ROOT_PATH,
    ESC_KEY,
    LETTERS,
    UPPERCASE_LETTERS,
    NUM_SPECIAL_1,
    NUM_SPECIAL_2,
)


class Tools(Page):
    """Krux generic tools"""

    def __init__(self, ctx):
        super().__init__(
            ctx,
            Menu(
                ctx,
                [
                    # (t("Check SD Card"), self.sd_check),
                    (t("Delete Mnemonic"), self.del_stored_mnemonic),
                    # (t("Print Test QR"), self.print_test),
                    (t("Create QR Code"), self.create_qr),
                    (t("Back"), lambda: MENU_EXIT),
                ],
            ),
        )
        self.ctx = ctx

    def sd_check(self):
        """Handler for the 'SD Check' menu item"""
        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(t("Checking for SD card.."))
        try:
            # Check for SD hot-plug
            with SDHandler():
                sd_status = uos.statvfs(SD_ROOT_PATH)
                sd_total = int(sd_status[2] * sd_status[1] / 1024 / 1024)
                sd_free = int(sd_status[4] * sd_status[1] / 1024 / 1024)

                self.ctx.display.clear()
                self.ctx.display.draw_hcentered_text(
                    t("SD card")
                    + "\n\n"
                    + t("Size: ")
                    + "{:,}".format(sd_total)
                    + " MB"
                    + "\n\n"
                    + t("Used: ")
                    + "{:,}".format(sd_total - sd_free)
                    + " MB"
                    + "\n\n"
                    + t("Free: ")
                    + "{:,}".format(sd_free)
                    + " MB"
                )
                if self.prompt(
                    t("Explore files?"), self.ctx.display.bottom_prompt_line
                ):
                    self.select_file(select_file_handler=self._show_file_details)
        except OSError:
            self.ctx.display.flash_text(t("SD card not detected"), theme.error_color)

        return MENU_CONTINUE

    def _show_file_details(self, file):
        """Handler to print file info when selecting a file in the file explorer"""
        if SDHandler.dir_exists(file):
            return MENU_EXIT

        stats = uos.stat(file)
        size = stats[6] / 1024
        size_deximal_places = str(int(size * 100))[-2:]
        created = time.localtime(stats[9])
        modified = time.localtime(stats[8])
        file = file[4:]  # remove "/sd/" prefix
        self.ctx.display.clear()
        self.ctx.display.draw_hcentered_text(
            file
            + "\n\n"
            + t("Size: ")
            + "{:,}".format(int(size))
            + "."
            + size_deximal_places
            + " KB"
            + "\n\n"
            + t("Created: ")
            + "%s-%s-%s %s:%s"
            % (created[0], created[1], created[2], created[3], created[4])
            + "\n\n"
            + t("Modified: ")
            + "%s-%s-%s %s:%s"
            % (modified[0], modified[1], modified[2], modified[3], modified[4])
        )
        self.ctx.input.wait_for_button()
        # if self.prompt(t("Delete File?"), self.ctx.display.bottom_prompt_line):
        #     with SDHandler() as sd:
        #         sd.delete(file)
        #     return MENU_EXIT
        return MENU_CONTINUE

    def del_stored_mnemonic(self):
        """Lists and allow deletion of stored mnemonics"""
        from ..encryption import MnemonicStorage

        while True:
            mnemonic_storage = MnemonicStorage()
            mnemonic_ids_menu = []
            has_sd = mnemonic_storage.has_sd_card
            mnemonics = mnemonic_storage.list_mnemonics()
            sd_mnemonics = mnemonic_storage.list_mnemonics(sd_card=True)
            del mnemonic_storage

            for mnemonic_id in mnemonics:
                mnemonic_ids_menu.append(
                    (
                        mnemonic_id + "(flash)",
                        lambda m_id=mnemonic_id: self._delete_encrypted_mnemonic(m_id),
                    )
                )
            if has_sd:
                for mnemonic_id in sd_mnemonics:
                    mnemonic_ids_menu.append(
                        (
                            mnemonic_id + "(SD card)",
                            lambda m_id=mnemonic_id: self._delete_encrypted_mnemonic(
                                m_id, sd_card=True
                            ),
                        )
                    )
            mnemonic_ids_menu.append((t("Back"), lambda: MENU_EXIT))
            submenu = Menu(self.ctx, mnemonic_ids_menu)
            index, _ = submenu.run_loop()
            if index == len(submenu.menu) - 1:
                return MENU_CONTINUE

    def _delete_encrypted_mnemonic(self, mnemonic_id, sd_card=False):
        """Deletes a mnemonic"""
        from ..encryption import MnemonicStorage

        mnemonic_storage = MnemonicStorage()
        self.ctx.display.clear()
        if self.prompt(t("Delete %s?" % mnemonic_id), self.ctx.display.height() // 2):
            mnemonic_storage.del_mnemonic(mnemonic_id, sd_card)
        del mnemonic_storage

    def print_test(self):
        """Handler for the 'Print Test QR' menu item"""
        try:
            self.ctx.printer = create_printer()
            if not self.ctx.printer:
                self.ctx.display.flash_text(
                    t("Printer Driver not set!"), theme.error_color
                )
                return MENU_CONTINUE
        except:
            self.ctx.log.exception("Exception occurred connecting to printer")
            raise

        title = t("Krux Printer Test QR")
        self.display_qr_codes(title, FORMAT_NONE, title, allow_any_btn=True)
        self.print_qr_prompt(title, FORMAT_NONE, title)

        return MENU_CONTINUE

    def create_qr(self):
        """Handler for the 'Create QR Code' menu item"""
        if self.prompt(
            t("Create QR code from text?"),
            self.ctx.display.height() // 2,
        ):
            text = self.capture_from_keypad(
                t("Text"), [LETTERS, UPPERCASE_LETTERS, NUM_SPECIAL_1, NUM_SPECIAL_2]
            )
            if text in ("", ESC_KEY):
                return MENU_CONTINUE

            try:
                self.ctx.printer = create_printer()
            except:
                self.ctx.log.exception("Exception occurred connecting to printer")

            from .qr_view import SeedQRView
            import qrcode

            code = qrcode.encode_to_string(text)
            seed_qr_view = SeedQRView(self.ctx, code=code, title="Custom QR Code")
            return seed_qr_view.display_seed_qr()
        return MENU_CONTINUE
