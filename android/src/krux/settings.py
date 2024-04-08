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
#
# Removed SDHandler dependency, we check for SD remount, just before entering
# the settings view
# from .sd_card import SDHandler

try:
    import ujson as json
except ImportError:
    import json

from kivy.storage.jsonstore import JsonStore

import os
import board  # Custom for Android

SETTINGS_FILENAME = "settings.json"
SD_PATH = "sd"
FLASH_PATH = "flash"


class SettingsNamespace:
    """Represents a settings namespace containing settings and child namespaces"""

    def label(self, attr):
        """Returns a label for UI when given a setting name or namespace"""
        raise NotImplementedError()

    def namespace_list(self):
        """Returns the list of child SettingsNamespace objects"""
        namespaces = [
            ns for ns in self.__dict__.values() if isinstance(ns, SettingsNamespace)
        ]
        namespaces.sort(key=lambda ns: str(ns.__class__.__name__))
        return namespaces

    def setting_list(self):
        """Returns the list of child Setting objects"""
        settings = [
            getattr(self.__class__, setting)
            for setting in dir(self.__class__)
            if isinstance(getattr(self.__class__, setting), Setting)
        ]
        settings.sort(key=lambda s: s.attr)
        return settings


class Setting:
    """Implements the descriptor protocol for reading and writing a single setting"""

    def __init__(self, attr, default_value):
        self.attr = attr
        self.default_value = default_value

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return store.get(obj.namespace, self.attr, self.default_value)

    def __set__(self, obj, value):
        if self.attr == "location":
            store.update_file_location(value)
        # Custom for Android
        if board.config["type"] == "android":
            try:
                store.set_value(obj.namespace, self.attr, value) # Will edit json key
            except:
                store.set(obj.namespace, self.attr, value)  # Will create json key
        elif value == self.default_value:
            store.delete(obj.namespace, self.attr)  # do not store defaults


class CategorySetting(Setting):
    """Setting that can be one of N categories"""

    def __init__(self, attr, default_value, categories):
        super().__init__(attr, default_value)
        self.categories = categories


class NumberSetting(Setting):
    """Setting that can be a number within a defined range"""

    def __init__(self, numtype, attr, default_value, value_range):
        super().__init__(attr, default_value)
        self.numtype = numtype
        self.value_range = value_range


class Store:
    """Acts as a simple JSON file store for settings, falling back to an in-memory dict if no SD"""

    def __init__(self):
        self.settings = {}
        self.file_location = "/" + FLASH_PATH + "/"
        self.dirty = False

        # Check for the correct settings persist location
        try:
            with open(self.file_location + SETTINGS_FILENAME, "r") as f:
                self.settings = json.loads(f.read())
        except:
            pass

        self.file_location = (
            self.settings.get("settings", {})
            .get("persist", {})
            .get("location", "undefined")
        )

        # Settings file not found on flash, or key is missing
        if self.file_location != FLASH_PATH:
            self.file_location = "/" + SD_PATH + "/"
            try:
                with open(self.file_location + SETTINGS_FILENAME, "r") as f:
                    self.settings = json.loads(f.read())
            except:
                pass

        # Settings file location points to what is defined in SETTINGS_FILENAME or defaults to flash
        self.file_location = (
            "/"
            + self.settings.get("settings", {})
            .get("persist", {})
            .get("location", FLASH_PATH)
            + "/"
        )

    def get(self, namespace, setting_name, default_value):
        """Returns a setting value under the given namespace, or default value if not set"""
        s = json.loads(
            json.dumps(self.settings)
        )  # deepcopy to avoid building out namespaces
        for level in namespace.split("."):
            s[level] = s.get(level, {})
            s = s[level]
        if setting_name not in s:
            return default_value
        return s[setting_name]

    def set(self, namespace, setting_name, setting_value):
        """Stores a setting value under the given namespace if new/changed.
        Does NOT automatically save settings to flash or sd!
        """
        s = self.settings
        for level in namespace.split("."):
            s[level] = s.get(level, {})
            s = s[level]
        old_value = s.get(setting_name, None)
        if old_value != setting_value:
            s[setting_name] = setting_value
            self.dirty = True

    def delete(self, namespace, setting_name):
        """Deletes dict storage in self.settings for namespace.setting_name,
        also deletes storage for setting_name's parent namespace nodes, if empty.
        """
        s = self.settings
        levels = []
        for level in namespace.split("."):
            s[level] = s.get(level, {})
            levels.append([s, level])
            s = s[level]
        if setting_name in s:
            del s[setting_name]
            self.dirty = True
        for s, level in reversed(levels):
            if not s[level]:
                del s[level]
                self.dirty = True

    def update_file_location(self, location):
        """Assumes settings.persist.location will be changed to location:
        tries to delete current persistent settings file
        then updates file_location attribute
        """
        if "/" + location + "/" != self.file_location:
            try:
                if os.stat(self.file_location + SETTINGS_FILENAME):
                    os.remove(self.file_location + SETTINGS_FILENAME)
            except:
                pass
            self.file_location = "/" + location + "/"

    def save_settings(self):
        """Helper to persist SETTINGS_FILENAME where user selected"""
        persisted = False

        if self.dirty:
            settings_filename = self.file_location + SETTINGS_FILENAME
            new_contents = json.dumps(self.settings)
            old_contents = "{}"
            try:
                with open(settings_filename, "r") as f:
                    old_contents = f.read()
            except:
                pass
            # Compare old and new file contents, if different, write new content
            if new_contents != old_contents:
                try:
                    with open(settings_filename, "w") as f:
                        f.write(new_contents)
                    persisted = True
                except:
                    pass
            self.dirty = False


class AndroidStore:
    """Acts as a simple JSON file store for settings for Android apps"""

    def __init__(self):
        self.settings = JsonStore(SETTINGS_FILENAME)

    def get(self, namespace, setting_name, default_value):
        """Loads a setting under the given namespace, returning the default value if not set"""
        if not namespace in self.settings.keys():
            self.set(namespace, setting_name, default_value)
        if not setting_name in self.settings.get(namespace):
            self.set_value(namespace, setting_name, default_value)
        return self.settings.get(namespace)[setting_name]
    
    def set(self, namespace, setting_name, setting_value):
        """Stores a setting value under the given namespace"""
        print("Setting", namespace, setting_name, setting_value)
        # print(self.settings[namespace])
        self.settings[namespace] = {setting_name : setting_value}

    def set_value(self,namespace, setting_name, setting_value):
        """
        Stores a setting value under the given namespace,
        creating the namespace if it doesn't exist
        """
        self.settings[namespace][setting_name] = setting_value
        # This weird line below will save to the file
        self.settings[namespace] = self.settings[namespace]

    def restore_defaults(self):
        self.settings.clear()

    def save_settings(self):
        return True



# Initialize singleton
store = AndroidStore()
