# The MIT License (MIT)

# Copyright (c) 2021-2025 Krux contributors

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

from ...krux_settings import t
from .. import (
    Page,
    Menu,
    MENU_CONTINUE,
)
from ...qr import FORMAT_NONE

class PGPUI(Page):
    """UI to explore PGP options"""

    def pgp_menu(self):
        """Handler for the 'pgp' menu item"""

        submenu = Menu(
            self.ctx,
            [
                (t("PGP Public Key"), self.pubkey_menu),
                (t("Sign File"), None),
                (t("Encrypt Message"), None),
                (t("Decrypt Message"), None),
            ],
        )
        submenu.run_loop()
        return MENU_CONTINUE

    def pubkey_menu(self):
        """Handler for the 'PGP Public Key' menu item"""
        submenu = Menu(
            self.ctx,
            [
                (t("Encryption Key"), self.encryption_key),
                (t("Signature Key"), None),
            ],
        )
        submenu.run_loop()
    
    def encryption_key(self):
        """Export Encryption Key"""
        from ...pgp import KruxPGP

        pub_key = KruxPGP().public_encryption_key(self.ctx.wallet.key.root)
        self.display_qr_codes(pub_key, FORMAT_NONE, "PGP Public Key")