import sys 
import threading
import time
sys.path.append("")
sys.path.append(".")

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.clock import Clock
from kivy.clock import mainthread

from android_permissions import AndroidPermissions

import mocks.load_mocks
from  mocks.ft6x36 import ft6x36_singleton
from src.krux.power import power_manager
from src.krux.context import Context
from src.krux.pages.login import Login
from src.krux.pages.home import Home

import sensor

Builder.load_string("""
<RootWidget>:
    but_1: but_1
    label_1: label_1

    Label:
        id: label_1
        font_size: 50
        size_hint_y: 1
        text_size: self.width, None
        height: self.texture_size[1]
        text: 'Krux Android app is intended for learning about and experience Krux, signing Bitcoin transactions, messages or Nostr events.\\nDue to the multiple possible vulnerabilities inherent to phones, like lack of control of OS, libraries and hardware peripherals, Krux app should NOT be used to manage wallets containing savings or other important keys. For that a dedicated device is recommended.'
        halign: 'center'

    Button:
        id: but_1
        font_size: 60
        background_color: 0, 0, 0, 1
        font_name: 'ubuntu.ttf'
        color: 0, 1, 0, 1
        halign: 'center'
        text: '| Start Krux |'
        size_hint: 1, 0.3
        on_press: root.start_thread()  
""")

if platform == 'android':
    from jnius import autoclass
    from android.runnable import run_on_ui_thread
    from android import mActivity
    View = autoclass('android.view.View')

    @run_on_ui_thread
    def hide_landscape_status_bar(instance, width, height):
        # width,height gives false layout events, on pinch/spread 
        # so use Window.width and Window.height
        if Window.width > Window.height: 
            # Hide status bar
            option = View.SYSTEM_UI_FLAG_FULLSCREEN
        else:
            # Show status bar 
            option = View.SYSTEM_UI_FLAG_VISIBLE
        mActivity.getWindow().getDecorView().setSystemUiVisibility(option)
elif platform != 'ios':
    # Dispose of that nasty red dot, required for gestures4kivy.
    from kivy.config import Config 
    Config.set('input', 'mouse', 'mouse, disable_multitouch')

class PhysicalButtons(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.add_widget(Button(text='↓'))
        self.add_widget(Button(text='↑'))
        self.add_widget(Button(text='↳'))
        self.size_hint= (1, 0.3)

class RootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.stop = False

    @mainthread
    def btn_pressed(self, instance, pos):
        ft6x36_singleton.feed_position(position=pos)

    @mainthread
    def btn_released(self, instance, pos):
        ft6x36_singleton.feed_position(position=pos)
        ft6x36_singleton.release()

    def camera_release(self, event):
        ft6x36_singleton.release()

    def camera_pressed(self, instance, pos):
        ft6x36_singleton.feed_position(position=(1,1))
        mocks.load_mocks.main_sensor.qrreader.pressed = False
        Clock.schedule_once(self.camera_release, 0.1)

    
    @mainthread
    def camera_on(self, instance, on):
        if on:
            self.remove_widget(mocks.load_mocks.lcd)
            mocks.load_mocks.main_sensor.qrreader.__init__()
            self.add_widget(mocks.load_mocks.main_sensor.qrreader)
            mocks.load_mocks.main_sensor.qrreader.connect_camera(analyze_pixels_resolution = 640,
                                     enable_analyze_pixels = True,
                                     enable_focus_gesture = False)
        else:
            mocks.load_mocks.main_sensor.qrreader.disconnect_camera()
            self.remove_widget(sensor.qrreader)
            self.add_widget(mocks.load_mocks.lcd)

    def android_back_click(self, window,key,*largs):
        if key in [27, 1001]:
            return True
        
    def start_thread(self):
        Window.bind(on_keyboard=self.android_back_click)
        mocks.load_mocks.lcd.bind(pressed=self.btn_pressed)
        mocks.load_mocks.lcd.bind(released=self.btn_released)
        mocks.load_mocks.main_sensor.qrreader.bind(pressed=self.camera_pressed)
        mocks.load_mocks.main_sensor.bind(running=self.camera_on)
        self.remove_widget(self.label_1)
        self.remove_widget(self.but_1)
        self.add_widget(mocks.load_mocks.lcd)
        # Add dummy position to avoid fake initial click
        ft6x36_singleton.feed_position(position=(0,0))
        self.ctx = Context()
        self.ctx.power_manager = power_manager
        self.ctx.input.touch.index -= 1
        self.t = threading.Thread(target=self.main_loop)
        Clock.schedule_once(self.start_mainloop, 0.1)
        Clock.schedule_interval(self.shut_down_monitor, 1)

    def shut_down_monitor(self, dt):
        if self.stop:
            # self.qrreader.disconnect_camera()
            App.get_running_app().stop()

    def start_mainloop(self, dt):
        self.t.start()

    def main_loop(self):
        while True:
            if not Login(self.ctx).run():
                break

            if self.ctx.wallet is None:
                continue

            if not Home(self.ctx).run():
                break
        self.stop = True
        from src.krux.krux_settings import t
        self.ctx.display.clear()
        self.ctx.display.draw_centered_text(t("Shutting down.."))

class KruxApp(App):
    
    def build(self):
        
        if platform == 'android':
            Window.bind(on_resize=hide_landscape_status_bar)
        return RootWidget()

    def on_start(self):
        self.dont_gc = AndroidPermissions(self.start_app)

    def start_app(self):
        self.dont_gc = None
        # Can't connect camera till after on_start()

# registering our new custom fontstyle
LabelBase.register(name='Ubuntu',
                   fn_regular='ubuntu.ttf')

KruxApp().run()
