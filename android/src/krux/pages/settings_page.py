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
# pylint: disable=C2801

import board
import lcd
from ..display import FONT_HEIGHT, FONT_WIDTH, PORTRAIT
from ..themes import theme, GREEN, ORANGE
from ..settings import (
    CategorySetting,
    NumberSetting,
    store,
    SD_PATH,
    FLASH_PATH,
    SETTINGS_FILENAME,
)
from ..krux_settings import (
    Settings,
    MAIN_TXT,
    TEST_TXT,
    TouchSettings,
    ButtonsSettings,
    t,
)
from ..input import BUTTON_ENTER, BUTTON_PAGE, BUTTON_PAGE_PREV, BUTTON_TOUCH
from ..sd_card import SDHandler
from ..encryption import QR_CODE_ITER_MULTIPLE
from . import (
    Page,
    Menu,
    MENU_CONTINUE,
    MENU_EXIT,
    MENU_SHUTDOWN,  # Android
    ESC_KEY,
    DEFAULT_PADDING,
)
import os

DIGITS = "0123456789"

PERSIST_MSG_TIME = 2500
DISPLAY_TEST_TIME = 5000  # 5 seconds

CATEGORY_SETTING_COLOR_DICT = {
    MAIN_TXT: ORANGE,
    TEST_TXT: GREEN,
}


class SettingsPage(Page):
    """Class to manage settings interface"""

    def __init__(self, ctx):
        super().__init__(ctx, None)
        self.ctx = ctx

    def settings(self):
        """Handler for the settings"""
        location = Settings().persist.location
        if location == SD_PATH:
            if self.has_sd_card():
                self.flash_text(
                    t("Your changes will be kept on the SD card."),
                    duration=PERSIST_MSG_TIME,
                )
            else:
                self.flash_text(
                    t("SD card not detected.")
                    + "\n\n"
                    + t("Changes will last until shutdown."),
                    duration=PERSIST_MSG_TIME,
                )
        else:
            try:
                # Check for flash
                # os.listdir("/" + FLASH_PATH + "/.")  # Android Custom
                self.flash_text(
                    t("Your changes will be kept on device flash storage."),
                    duration=PERSIST_MSG_TIME,
                )
            except OSError:
                self.flash_text(
                    t("Device flash storage not detected.")
                    + "\n\n"
                    + t("Changes will last until shutdown."),
                    duration=PERSIST_MSG_TIME,
                )

        return self.namespace(Settings())()

    def _draw_settings_pad(self):
        """Draws buttons to change settings with touch"""
        if self.ctx.input.touch is not None:
            self.ctx.input.touch.clear_regions()
            offset_y = self.ctx.display.height() * 2 // 3
            self.ctx.input.touch.add_y_delimiter(offset_y)
            self.ctx.input.touch.add_y_delimiter(offset_y + FONT_HEIGHT * 3)
            button_width = (self.ctx.display.width() - 2 * DEFAULT_PADDING) // 3
            for i in range(4):
                self.ctx.input.touch.add_x_delimiter(DEFAULT_PADDING + button_width * i)
            offset_y += FONT_HEIGHT
            keys = ["<", t("Go"), ">"]
            for i, x in enumerate(self.ctx.input.touch.x_regions[:-1]):
                self.ctx.display.outline(
                    x,
                    self.ctx.input.touch.y_regions[0],
                    button_width - 1,
                    FONT_HEIGHT * 3,
                    theme.frame_color,
                )
                offset_x = x
                offset_x += (button_width - lcd.string_width_px(keys[i])) // 2
                self.ctx.display.draw_string(
                    offset_x, offset_y, keys[i], theme.fg_color, theme.bg_color
                )

    def _touch_to_physical(self, index):
        """Mimics touch presses into physical button presses"""
        if index == 0:
            return BUTTON_PAGE_PREV
        if index == 1:
            return BUTTON_ENTER
        return BUTTON_PAGE

    def restore_settings(self):
        """Restore default settings by deleting the settings files"""
        self.ctx.display.clear()
        if self.prompt(
            t("Restore factory settings and reboot?"), self.ctx.display.height() // 2
        ):
            self.ctx.display.clear()
            # Custom for Android
            from ..settings import store

            store.restore_defaults()
            return MENU_SHUTDOWN
            try:
                # Delete settings from SD
                with SDHandler() as sd:
                    sd.delete(SETTINGS_FILENAME)
            except:
                pass
            try:
                # Delete settings from flash
                os.remove("/%s/%s" % (FLASH_PATH, SETTINGS_FILENAME))
            except:
                pass
            self.ctx.power_manager.reboot()
        return MENU_CONTINUE

    def _settings_exit_check(self):
        """Handler for the 'Back' on settings screen"""

        # If user selected to persist on SD, we will try to remout and save
        # flash is always mounted, so settings is always persisted
        if Settings().persist.location == SD_PATH:
            self.ctx.display.clear()
            self.ctx.display.draw_centered_text(t("Checking for SD card.."))
            try:
                # Check for SD hot-plug
                with SDHandler():
                    if store.save_settings():
                        self.flash_text(
                            t("Changes persisted to SD card!"),
                            duration=PERSIST_MSG_TIME,
                        )
            except OSError:
                self.flash_text(
                    t("SD card not detected.")
                    + "\n\n"
                    + t("Changes will last until shutdown."),
                    duration=PERSIST_MSG_TIME,
                )
        else:
            self.ctx.display.clear()
            try:
                if store.save_settings():
                    self.flash_text(
                        t("Changes persisted to Flash!"),
                        duration=PERSIST_MSG_TIME,
                    )
            except:
                self.flash_text(
                    t("Unexpected error saving to Flash.")
                    + "\n\n"
                    + t("Changes will last until shutdown."),
                    duration=PERSIST_MSG_TIME,
                )

        return MENU_EXIT

    def namespace(self, settings_namespace):
        """Handler for navigating a particular settings namespace"""

        def handler():
            setting_list = settings_namespace.setting_list()
            namespace_list = settings_namespace.namespace_list()
            # Android Custom
            items = []
            for ns in namespace_list:
                # Avoid disabled (comented) settings, Android Only
                try:
                    name_space_label = settings_namespace.label(ns.namespace.split(".")[-1])
                except:
                    name_space_label = None
                if name_space_label is not None:
                    items.extend(
                        [
                            (
                                name_space_label,
                                self.namespace(ns),
                            )
                        ]
                    )
            items.extend(
                [
                    (
                        settings_namespace.label(setting.attr),
                        self.setting(settings_namespace, setting),
                    )
                    for setting in setting_list
                ]
            )

            # If there is only one item in the namespace, don't show a submenu
            # and instead jump straight to the item's menu
            if len(items) == 1:
                return items[0][1]()

            back_status = lambda: MENU_EXIT  # pylint: disable=C3001
            # Case for "Back" on the main Settings
            if settings_namespace.namespace == Settings.namespace:
                items.append((t("Factory Settings"), self.restore_settings))
                back_status = self._settings_exit_check

            submenu = Menu(self.ctx, items, back_status=back_status)
            index, status = submenu.run_loop()
            if index == len(submenu.menu) - 1:
                return MENU_CONTINUE
            return status

        return handler

    def setting(self, settings_namespace, setting):
        """Handler for viewing and editing a particular setting"""

        def handler():
            if isinstance(setting, CategorySetting):
                return self.category_setting(settings_namespace, setting)

            if isinstance(setting, NumberSetting):
                self.number_setting(settings_namespace, setting)
                if settings_namespace.namespace == TouchSettings.namespace:
                    self._touch_threshold_exit_check()
                elif settings_namespace.namespace == ButtonsSettings.namespace:
                    self._buttons_debounce_exit_check()

            return MENU_CONTINUE

        return handler

    def _touch_threshold_exit_check(self):
        """Handler for the 'Back' on touch settings screen"""

        # Update touch detection threshold
        if self.ctx.input.touch is not None:
            self.ctx.input.touch.touch_driver.threshold(
                Settings().hardware.touch.threshold
            )

    def _buttons_debounce_exit_check(self):
        """Handler for the 'Back' on buttons debounce settings screen"""

        # Update buttons debounce time
        self.ctx.input.debounce_value = Settings().hardware.buttons.debounce
        if "ENCODER" in board.config["krux"]["pins"]:
            from ..rotary import encoder

            encoder.debounce = Settings().hardware.buttons.debounce

    def _amigo_lcd_reconfigure(self):
        """reconfigure the display after re-initializing it"""
        lcd.mirror(True)
        lcd.bgr_to_rgb(Settings().hardware.display.bgr_colors)
        lcd.rotation(PORTRAIT)  # Portrait mode

    def category_setting(self, settings_namespace, setting):
        """Handler for viewing and editing a CategorySetting"""
        categories = setting.categories

        starting_category = setting.__get__(settings_namespace)
        while True:
            current_category = setting.__get__(settings_namespace)
            color = CATEGORY_SETTING_COLOR_DICT.get(current_category, theme.fg_color)
            self.ctx.display.clear()
            if setting.attr == "flipped_x":
                self.ctx.display.draw_string(
                    self.ctx.display.width() // 4,
                    DEFAULT_PADDING,
                    t("Left"),
                )
                self.ctx.display.draw_string(
                    (3 * self.ctx.display.width() // 4) - 5 * FONT_WIDTH,
                    DEFAULT_PADDING,
                    t("Right"),
                )
            self.ctx.display.draw_centered_text(
                settings_namespace.label(setting.attr) + "\n" + str(current_category),
                color,
                theme.bg_color,
            )
            self._draw_settings_pad()
            btn = self.ctx.input.wait_for_button()
            if btn == BUTTON_TOUCH:
                btn = self._touch_to_physical(self.ctx.input.touch.current_index())
            if btn == BUTTON_ENTER:
                break
            new_category = current_category
            for i, category in enumerate(categories):
                if current_category == category:
                    if btn in (BUTTON_PAGE, None):
                        new_category = categories[(i + 1) % len(categories)]
                    elif btn == BUTTON_PAGE_PREV:
                        new_category = categories[(i - 1) % len(categories)]
                    setting.__set__(settings_namespace, new_category)
                    break
            if setting.attr == "theme":
                theme.update()
            if setting.attr == "brightness":
                if board.config["type"] == "cube":
                    self.ctx.display.gpio_backlight_ctrl(new_category)
                elif board.config["type"] == "m5stickv":
                    self.ctx.display.set_pmu_backlight(new_category)
            if setting.attr == "flipped_x" and new_category is not None:
                self.ctx.display.flipped_x_coordinates = new_category
            if setting.attr == "bgr_colors" and new_category is not None:
                lcd.bgr_to_rgb(new_category)
            if setting.attr == "inverted_colors" and new_category is not None:
                lcd.init(
                    invert=new_category, lcd_type=Settings().hardware.display.lcd_type
                )
                self._amigo_lcd_reconfigure()

            if setting.attr == "lcd_type" and new_category is not None:
                self.ctx.display.clear()
                self.ctx.display.draw_centered_text(
                    t(
                        "If your device display does not work after this change, "
                        "it will automatically reboot with previous settings after 5 seconds."
                    )
                )
                self.ctx.input.wait_for_button()
                lcd.init(
                    invert=Settings().hardware.display.inverted_colors,
                    lcd_type=new_category,
                )
                self._amigo_lcd_reconfigure()

                self.ctx.display.clear()
                self.ctx.display.draw_centered_text(
                    t('Press "PREVIOUS" (up arrow) button to keep this setting.')
                )
                btn = self.ctx.input.wait_for_button(
                    block=False, wait_duration=DISPLAY_TEST_TIME
                )
                if btn != BUTTON_PAGE_PREV:
                    self.ctx.power_manager.reboot()

        # When changing locale, exit Login to force recreate with new locale
        if (
            setting.attr == "locale"
            and setting.__get__(settings_namespace) != starting_category
        ):
            return MENU_EXIT
        if setting.attr == "theme":
            self.ctx.display.clear()
            if self.prompt(
                t("Change theme and reboot?"), self.ctx.display.height() // 2
            ):
                self._settings_exit_check()
                self.ctx.display.clear()
                return MENU_SHUTDOWN  # Android custom
            else:
                # Restore previous theme
                setting.__set__(settings_namespace, starting_category)
                theme.update()

        return MENU_CONTINUE

    def number_setting(self, settings_namespace, setting):
        """Handler for viewing and editing a NumberSetting"""

        starting_value = setting.numtype(setting.__get__(settings_namespace))

        numerals = DIGITS
        # add the dot symbol when number type is float
        if setting.numtype == float:
            numerals += "."

        new_value = self.capture_from_keypad(
            self.fit_to_line(settings_namespace.label(setting.attr)),
            [numerals],
            starting_buffer=str(starting_value),
            esc_prompt=False,
        )
        if new_value in (ESC_KEY, ""):
            return MENU_CONTINUE

        new_value = setting.numtype(new_value)
        if setting.value_range[0] <= new_value <= setting.value_range[1]:
            if (
                setting.attr == "pbkdf2_iterations"
                and (new_value % QR_CODE_ITER_MULTIPLE) != 0
            ):
                self.flash_error(
                    t("Value must be multiple of %s") % QR_CODE_ITER_MULTIPLE
                )
            else:
                setting.__set__(settings_namespace, new_value)
        else:
            self.flash_error(
                t("Value %s out of range: [%s, %s]")
                % (new_value, setting.value_range[0], setting.value_range[1])
            )

        if setting.attr == "auto_shutdown" and starting_value != new_value:
            from ..auto_shutdown import auto_shutdown

            auto_shutdown.init_timer(new_value)

        return MENU_CONTINUE
