import time
import board
import usb_hid
from adafruit_neotrellis.neotrellis import NeoTrellis
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_led_animation import color
# from adafruit_led_animation.animation import pulse


class MyButton:
    def __init__(self, bind, keybind_type, press_color, standby_color=None):
        self.bind = bind
        self.keybind_type = keybind_type  # 1 if Keycode, 0 if ConsumerControlCode
        self.press_color = press_color
        if standby_color is not None:
            self.standby_color = standby_color
        else:
            self.standby_color = press_color

class MyMacroPad:
    def __init__(self):

        # Define devices
        i2c_bus = board.I2C()
        self.trellis = NeoTrellis(i2c_bus)
        self.kbd = Keyboard(usb_hid.devices)
        self.cc = ConsumerControl(usb_hid.devices)

        # Set constants
        self.number_of_buttons = 16
        self.active_brightness = 0.7
        self.standby_timer = 5
        self.standby_flag = False
        self.standby_brightness = 0.1
        self.sleep_timer = 60
        self.sleep_flag = False
        self.sleep_brightness = 0
        self.keypress_map = {'CCODE': 0, 'KCODE': 1, 'MACRO': 3, 'WAKE': 4}
        self.press_color_default_map = {'CCODE': color.GOLD, 'KCODE': color.CYAN, 'MACRO': color.GOLD}
        self.release_color = color.BLACK
        self.boot_color = color.AQUA
        self.no_kb_color = color.WHITE
        self.animate_color_sequence = [color.GOLD, color.AMBER, color.ORANGE]
        self.kbd_map = {}

        # Initialize
        self.trellis.brightness = self.active_brightness
        self.time_record = time.time()

        self.define_keymap()
        self.boot_sequence()

    def define_keymap(self):

        self.kbd_map = {
                0:  MyButton([Keycode.CONTROL, Keycode.S],                  self.keypress_map['KCODE'], self.press_color_default_map['KCODE']),
                2:  MyButton([Keycode.WINDOWS, Keycode.TWO],                self.keypress_map['KCODE'], color.PURPLE),
                3:  MyButton([Keycode.WINDOWS, Keycode.ONE],                self.keypress_map['KCODE'], color.RED),
                7:  MyButton([Keycode.CONTROL, Keycode.ONE],                self.keypress_map['KCODE'], color.RED),
                10: MyButton([Keycode.SHIFT, Keycode.F10],                  self.keypress_map['KCODE'], color.GREEN),
                11: MyButton([Keycode.CONTROL, Keycode.TWO],                self.keypress_map['KCODE'], color.RED),
                12: MyButton([ConsumerControlCode.MUTE],                    self.keypress_map['CCODE'], self.press_color_default_map['CCODE']),
                13: MyButton([ConsumerControlCode.SCAN_NEXT_TRACK],         self.keypress_map['CCODE'], self.press_color_default_map['CCODE']),
                14: MyButton([ConsumerControlCode.PLAY_PAUSE],              self.keypress_map['CCODE'], self.press_color_default_map['CCODE']),
                15: MyButton([ConsumerControlCode.SCAN_PREVIOUS_TRACK],     self.keypress_map['CCODE'], self.press_color_default_map['CCODE'])
                }

        for i in range(self.number_of_buttons):
            if i not in self.kbd_map:
                self.kbd_map[i] = MyButton(None, None, self.no_kb_color)

    def operation_loop(self):
        self.time_record = time.time()
        while True:
            self.trellis.sync()
            time.sleep(0.02)
            if not self.standby_flag and (time.time() - self.time_record >= self.standby_timer):
                self.trellis.brightness = self.standby_brightness
                self.standby_flag = True

            if not self.sleep_flag and (time.time() - self.time_record >= self.sleep_timer):
                self.color_wave_off()

    def button_press(self, button):
        self.time_record = time.time()
        if self.sleep_flag:    # No keycode run if waking from inactive lights to avoid accidental keypress
            self.color_wave_on()
        else:
            self.standby_flag = False
            self.trellis.brightness = self.active_brightness
            if self.kbd_map[button].keybind_type is None:  # Undefined binding
                print(f'Undefined button: {button}')
            elif self.kbd_map[button].keybind_type == self.keypress_map['KCODE']: # Keycode binding
                self.kbd.send(*self.kbd_map[button].bind)
            elif self.kbd_map[button].keybind_type == self.keypress_map['CCODE']: # ConsumerControlCode binding
                self.cc.send(*self.kbd_map[button].bind)
            elif self.kbd_map[button].keybind_type == self.keypress_map['MACRO']: # Macro binding
                self.macro_run(self.kbd_map[button].bind)
            elif self.kbd_map[button].keybind_type == self.keypress_map['WAKE']:
                pass
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
        self.trellis.brightness = 0
        self.color_cycle()
        self.trellis.brightness = self.active_brightness

    def color_cycle(self, color_value = None, sleep_time = 0.01):
        for i in range(self.number_of_buttons):
            if color_value is not None:
                self.trellis.pixels[i] = color_value
            else:
                self.trellis.pixels[i] = self.kbd_map[i].standby_color
            time.sleep(sleep_time)

    def color_wave_off(self):
        sleep_time = 0.01
        for i in range(int(self.number_of_buttons/2)):
            self.trellis.pixels[i] = self.release_color
            time.sleep(sleep_time)
            self.trellis.pixels[self.number_of_buttons - i - 1] = self.release_color
            time.sleep(sleep_time)
        self.trellis.brightness = self.sleep_brightness
        self.sleep_flag = True

    def color_wave_on(self):
        self.color_cycle(self.release_color)
        sleep_time = 0.01
        self.trellis.brightness = self.active_brightness
        for i in range(int(self.number_of_buttons/2)):
            self.trellis.pixels[i] = self.kbd_map[i].standby_color
            time.sleep(sleep_time)
            self.trellis.pixels[self.number_of_buttons - i - 1] = self.kbd_map[self.number_of_buttons - i - 1].standby_color
            time.sleep(sleep_time)
        self.standby_flag, self.sleep_flag = False, False


    def button_call_wrapper(self, event):
        button = event.number

        if event.edge == NeoTrellis.EDGE_RISING:
            self.trellis.pixels[button] = self.kbd_map[button].press_color
            self.button_press(button)

        elif event.edge == NeoTrellis.EDGE_FALLING:
            self.trellis.pixels[button] = self.kbd_map[button].standby_color

#         elif time.time() - self.time_record >= self.standby_timer:
#             self.sleep_lights()

if __name__ == "__main__":
    MPad = MyMacroPad()
    MPad.operation_loop()

