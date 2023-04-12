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

from kivy.core.window import Window

try:
    import ujson as json
except ImportError:
    import json

config = json.loads("""
{
    "type": "android",
    "lcd": {
        "height": 800,
        "width": 800,
        "invert": 1,
        "dir": 40,
        "lcd_type": 2
    },
    
    "board_info": {
        "BOOT_KEY": 23,
        "LED_R": 14,
        "LED_G": 15,
        "LED_B": 17,
        "LED_W": 32,
        "BACK": 23,
        "ENTER": 16,
        "NEXT": 20,
        "WIFI_TX": 6,
        "WIFI_RX": 7,
        "WIFI_EN": 8,
        "I2S0_MCLK": 13,
        "I2S0_SCLK": 21,
        "I2S0_WS": 18,
        "I2S0_IN_D0": 35,
        "I2S0_OUT_D2": 34,
        "I2C_SDA": 27,
        "I2C_SCL": 24,
        "SPI_SCLK": 11,
        "SPI_MOSI": 10,
        "SPI_MISO": 6,
        "SPI_CS": 12
    },
    "krux": {
        "pins": {
            "BUTTON_A": 0,
            "I2C_SDA": 0,
            "I2C_SCL": 0
        },
        "display": {
            "touch": true,
            "font": [30, 60],
            "inverted_coordinates": false,
            "qr_colors": [0, 6342]
        }
    }
}
""")

_, window_height = Window.size            
config["krux"]["display"]["font"] = [window_height // 50, window_height // 25]
