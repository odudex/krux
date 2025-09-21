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

from .. import Menu, LETTERS, MENU_CONTINUE, MENU_EXIT
from ..login import MnemonicLoader
from ...krux_settings import t
from ...display import BOTTOM_PROMPT_LINE, FONT_HEIGHT


class MnemonicXOR(MnemonicLoader):
    """
    UI to apply a exclusive-or operation between the current mnemonic entropy with
    chosen mnemonic entropies
    """

    # See implementation reference at
    # https://github.com/Coldcard/firmware/blob/2445b4d4350d0aad0f4ef8f966697a67ab9ecbdc/shared/utils.py#L752
    @staticmethod
    def _xor_bytes(a: bytes, b: bytes) -> bytearray:
        """XOR two byte sequences of equal length"""

        # All sequences should have same lenght because it would
        # reveal the last bytes from the longer bytestring as they are.
        # In the case of mnemonics, it might reveal last 12 words.
        if len(a) != len(b):
            raise ValueError("Sequences should have same length")

        out = bytearray(len(b))
        for i in range(len(b)):
            out[i] = a[i] ^ b[i]

        return out

    @staticmethod
    def _validate_entropy(entropy: bytes | bytearray) -> None:
        """Check for low entropy (all zeros or all ones)"""
        # TODO: apply a shannon low entropy check for XOR
        # pylint: disable=consider-using-in
        if entropy == len(entropy) * b"\x00" or entropy == len(entropy) * b"\xff":
            raise ValueError("Low entropy mnemonic")

    def xor_with_current_mnemonic(self, part: str) -> str:
        """XOR current mnemonic with a new part following SeedXOR implementation"""
        from embit.bip39 import mnemonic_from_bytes, mnemonic_to_bytes

        # Validate same word count
        current_words = self.ctx.wallet.key.mnemonic.split(" ")
        part_words = part.split(" ")
        if len(current_words) != len(part_words):
            raise ValueError("Mnemonics should have same length")

        # Convert and validate entropies
        entropy_a = mnemonic_to_bytes(self.ctx.wallet.key.mnemonic)
        entropy_b = mnemonic_to_bytes(part)
        self._validate_entropy(entropy_a)
        self._validate_entropy(entropy_b)

        # XOR and validate result
        new_entropy = self._xor_bytes(entropy_a, entropy_b)
        self._validate_entropy(new_entropy)

        return mnemonic_from_bytes(new_entropy)

    def load(self):
        """Menu for XOR the current mnemonic with a share"""
        menu = Menu(
            self.ctx,
            [
                (t("Via Camera"), self.load_key_from_camera),
                (t("Via Manual Input"), self.load_key_from_manual_input),
                (t("From Storage"), self.load_mnemonic_from_storage),
            ],
        )

        menu.run_loop()
        return MENU_EXIT

    def _load_key_from_words(self, words, charset=LETTERS, new=False):
        """
        Similar method from krux.pages.login.Login without loading a key,
        instead, it add the bytes from a mnemonic's entropy to the list of entropies
        """
        from ...key import Key
        from ...krux_settings import Settings
        from ...themes import theme

        # Memorize the current finger print to use it after
        old_fingerprint = self.ctx.wallet.key.fingerprint_hex_str(True)

        # Show part before XOR, using the same
        # policy, network, account_index and script_type
        # (they will not be relevant, it's just to load
        # a key and it's fingerprint). Also, check if
        # we will show all mnemonic or only it's fingerprint.
        part_words = " ".join(words)
        part_key = Key(
            part_words,
            self.ctx.wallet.key.policy_type,
            self.ctx.wallet.key.network,
            "",
            self.ctx.wallet.key.account_index,
            self.ctx.wallet.key.script_type,
        )
        # Memorize the part fingerprint to use it after
        part_fingerprint = part_key.fingerprint_hex_str(True)

        # If hide_mnemonic is set, do not show words
        if not Settings().security.hide_mnemonic:
            self.display_mnemonic(
                part_words,
                title=t("XOR With") + ":",
                fingerprint=part_key.fingerprint_hex_str(True),
            )
        else:
            self.ctx.display.clear()
            self.ctx.display.draw_centered_text(
                t("XOR With") + ": " + part_key.fingerprint_hex_str(True),
                color=theme.highlight_color,
            )

        if not self.prompt(t("Proceed?"), BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE

        # Show XORed operation between current mnemonic with
        # part mnemonic, but do not load it yet (i.e. replacing
        # the current with this one). Show it before and ask if
        # the user want to replace.
        xored_mnemonic = self.xor_with_current_mnemonic(part_key.mnemonic)
        xored_key = Key(
            xored_mnemonic,
            self.ctx.wallet.key.policy_type,
            self.ctx.wallet.key.network,
            "",
            self.ctx.wallet.key.account_index,
            self.ctx.wallet.key.script_type,
        )

        # Display some informations about the math used
        # during XOR. The xor operation occurs on entropy
        # and not with the fingerprints. But use fingerprints
        # since they are shorter and could give a hint if the
        # operation occurs as expected.
        offset_y = self.ctx.display.height() // 2
        self.ctx.display.clear()
        for i, element in enumerate(
            [
                old_fingerprint,
                "XOR",
                part_fingerprint,
                "=",
                xored_key.fingerprint_hex_str(True),
            ]
        ):
            self.ctx.display.draw_hcentered_text(
                element,
                offset_y=offset_y + (FONT_HEIGHT * i),
                color=theme.fg_color if i < 4 else theme.highlight_color,
            )

        if not self.prompt(t("Proceed?"), BOTTOM_PROMPT_LINE):
            return MENU_CONTINUE

        # Now replace the current key with with xored one
        if not Settings().security.hide_mnemonic:
            self.display_mnemonic(
                xored_mnemonic,
                title=t("XOR Result") + ":",
                fingerprint=xored_key.fingerprint_hex_str(True),
            )
        else:
            self.ctx.display.clear()
            self.ctx.display.draw_centered_text(
                t("XOR Result") + ": " + xored_key.fingerprint_hex_str(True),
                color=theme.highlight_color,
            )

        if self.prompt(t("Load?"), BOTTOM_PROMPT_LINE):
            from ...wallet import Wallet

            self.ctx.wallet = Wallet(xored_key)
            self.flash_text(
                t("%s: loaded!") % xored_key.fingerprint_hex_str(True),
                highlight_prefix=":",
            )

        return MENU_EXIT
