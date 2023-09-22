import time
import board
import usb_hid
from adafruit_neotrellis.neotrellis import NeoTrellis
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_led_animation import color
from adafruit_led_animation.animation import pulse


class MyButton:
    def __init__(self, bind, code_type, press_color, standby_color=None):
        self.bind = bind
        self.code_type = code_type  # 1 if Keycode, 0 if ConsumerControlCode
        self.press_color = press_color
        if standby_color is not None:
            self.standby_color = standby_color
        else:
            self.standby_color = press_color

class MyMacroPad:
    def __init__(self):

        i2c_bus = board.I2C()
        self.trellis = NeoTrellis(i2c_bus)
        
        self.active_brightness = 0.7
        self.sleep_brightness = 0.1
        
        self.trellis.brightness = self.active_brightness

        self.number_of_buttons = 16
        self.press_color_default_map = {'CCODE': color.GOLD, 'KCODE': color.CYAN, 'MACRO': color.GOLD}
        self.release_color = color.BLACK
        self.boot_color = color.AQUA
        self.no_kb_color = color.WHITE
        self.animate_color_sequence = [color.GOLD, color.AMBER, color.ORANGE]

        self.kbd = Keyboard(usb_hid.devices)
        self.cc = ConsumerControl(usb_hid.devices)

        self.code_map = {'CCODE': 0, 'KCODE': 1, 'MACRO': 3}

        self.kbd_map = {}
        self.define_keymap()
        
        self.boot_sequence()

        self.sleep_timer = 5
        self.time_record = time.time()
#         self.brightness_scaler = self.active_brightness
#         self.pulse_timer = 3

    def define_keymap(self):
        
        self.kbd_map = {
                0:  MyButton([Keycode.CONTROL, Keycode.S],                  self.code_map['KCODE'], self.press_color_default_map['KCODE']),
                2:  MyButton([Keycode.WINDOWS, Keycode.TWO],                self.code_map['KCODE'], color.PURPLE),
                3:  MyButton([Keycode.WINDOWS, Keycode.ONE],                self.code_map['KCODE'], color.RED),
                7:  MyButton([Keycode.CONTROL, Keycode.ONE],                self.code_map['KCODE'], color.RED),
                11: MyButton([Keycode.CONTROL, Keycode.TWO],                self.code_map['KCODE'], color.RED),                
                15: MyButton([ConsumerControlCode.SCAN_PREVIOUS_TRACK],     self.code_map['CCODE'], self.press_color_default_map['CCODE']),
                14: MyButton([ConsumerControlCode.PLAY_PAUSE],              self.code_map['CCODE'], self.press_color_default_map['CCODE']),
                13: MyButton([ConsumerControlCode.SCAN_NEXT_TRACK],         self.code_map['CCODE'], self.press_color_default_map['CCODE']),
                12: MyButton([ConsumerControlCode.MUTE],                    self.code_map['CCODE'], self.press_color_default_map['CCODE'])
            }

        for i in range(self.number_of_buttons):
            if i not in self.kbd_map:
                self.kbd_map[i] = MyButton(None, None, self.no_kb_color)

    def operation_loop(self):
        self.time_record = time.time()
        while True:
            self.trellis.sync()
            time.sleep(0.02)
            if time.time() - self.time_record >= self.sleep_timer:
                self.trellis.brightness = self.sleep_brightness

    def button_press(self, button):
        self.time_record = time.time()
        self.trellis.brightness = self.active_brightness
        if self.kbd_map[button].code_type is None:  # Undefined binding
            print(f'Undefined button: {button}')
        elif self.kbd_map[button].code_type == self.code_map['KCODE']: # Keycode binding
            self.kbd.send(*self.kbd_map[button].bind)
        elif self.kbd_map[button].code_type == self.code_map['CCODE']: # ConsumerControlCode binding
            self.cc.send(*self.kbd_map[button].bind)
        elif self.kbd_map[button].code_type == self.code_map['MACRO']:
            self.macro_run(self.kbd_map[button].bind)
        else:
            print(f'Button issue')

    def boot_sequence(self):
        for i in range(self.number_of_buttons):
            # activate rising edge events on all keys
            self.trellis.activate_key(i, NeoTrellis.EDGE_RISING)
            # activate falling edge events on all keys
            self.trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
            # set all keys to trigger the blink callback
            self.trellis.callbacks[i] = self.button_call_wrapper

        self.color_cycle(self.boot_color, 0.01)
        time.sleep(0.2)
        self.color_cycle(self.release_color, 0.01)
        self.color_cycle()

    def color_cycle(self, color_value = None, sleep_time = 0.01):
        for i in range(self.number_of_buttons):
            if color_value is not None:
                self.trellis.pixels[i] = color_value
            else:
                self.trellis.pixels[i] = self.kbd_map[i].standby_color
            time.sleep(sleep_time)

    def button_call_wrapper(self, event):
        button = event.number

        if event.edge == NeoTrellis.EDGE_RISING:
            self.trellis.pixels[button] = self.kbd_map[button].press_color
            self.button_press(button)

        elif event.edge == NeoTrellis.EDGE_FALLING:
            self.trellis.pixels[button] = self.kbd_map[button].standby_color

#         elif time.time() - self.time_record >= self.sleep_timer:
#             self.sleep_lights()

if __name__ == "__main__":
    MPad = MyMacroPad()
    MPad.operation_loop()

