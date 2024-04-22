import sys 
import threading
sys.path.append("./src")

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.utils import platform
from kivy.clock import Clock
from kivy.clock import mainthread

from android_permissions import AndroidPermissions

import mocks.load_mocks
from  mocks.ft6x36 import touch_control
from src.krux.power import power_manager
from src.krux.context import Context
from src.krux.pages.login import Login
from src.krux.pages.home_pages.home import Home

Builder.load_string("""
<RootWidget>:
    label_1: label_1
    but_1: but_1

    Label:
        id: label_1
        font_size: root.height // 30
        font_name: 'JetBrainsMono-Medium.ttf'
        size_hint: 1, 0.8
        pos_hint: {'top': 1}
        text_size: self.width, None
        height: self.texture_size[1]
        text: 'Krux Android app is intended for learning about Krux and Bitcoin air-gapped transactions.\\nDue to many possible vulnerabilities inherent in phones such as the lack of control of the OS, libraries and hardware peripherals, Krux app should NOT be used to manage wallets containing savings or important keys and mnemonics. For that, a dedicated device is recommended.'
        halign: 'center'

    Button:
        id: but_1
        font_size: root.height // 30
        font_name: 'JetBrainsMono-Medium.ttf'
        background_color: 0, 0, 0, 1
        color: 0, 1, 0, 1
        halign: 'center'
        text: '| Start Krux |'
        size_hint: 1, 0.2
        pos_hint: {'y': 0}
        on_release: root.start_thread()  
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

class RootWidget(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.stop = False
        self.touch_control = touch_control
        self.lcd_widget = mocks.load_mocks.lcd
        self.camera_widget = mocks.load_mocks.main_sensor.qrreader

    @mainthread
    def btn_pressed(self, instance, pos):
        self.touch_control.feed_position(pos)

    @mainthread
    def btn_released(self, instance, pos):
        self.touch_control.feed_position(pos, release=True)
        self.touch_control.release()

    def camera_release(self, event):
        self.touch_control.release()
        self.touch_control.feed_position(None)

    def camera_pressed(self, instance, pos):
        self.touch_control.feed_position((1,1))
        self.camera_widget.pressed = False
        Clock.schedule_once(self.camera_release, 0.1)

    
    @mainthread
    def camera_on(self, instance, on):
        if on:
            # Set up and add the camera widget
            self.camera_widget.__init__()
            self.camera_widget.size_hint = (1, 0.8)  # Full width, 80% height
            self.camera_widget.pos = (0, self.height * 0.2)
            self.camera_widget.connect_camera(
                enable_photo = False,
                analyze_pixels_resolution = 640,
                enable_analyze_pixels = True,
            )
            self.add_widget(self.camera_widget)
        else:
            # Remove the camera widget and reset LCD widget
            self.camera_widget.disconnect_camera()
            self.remove_widget(self.camera_widget)

    def android_back_click(self, window,key,*largs):
        if key in [27, 1001]:
            return True
        
    def start_thread(self):
        Window.bind(on_keyboard=self.android_back_click)
        self.lcd_widget.bind(pressed=self.btn_pressed)
        self.lcd_widget.bind(released=self.btn_released)
        self.camera_widget.bind(pressed=self.camera_pressed)
        mocks.load_mocks.main_sensor.bind(running=self.camera_on)
        self.remove_widget(self.label_1)
        self.remove_widget(self.but_1)
        self.add_widget(self.lcd_widget)
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
LabelBase.register(name='JetBrainsMono-Medium',
                   fn_regular='JetBrainsMono-Medium.ttf')

KruxApp().run()
