import time, board, usb_hid
from adafruit_neotrellis.neotrellis import NeoTrellis
# from adafruit_hid.keyboard import Keyboard
# from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
# from adafruit_hid.keycode import Keycode, ConsumerCode

# create the i2c object for the trellis
i2c_bus = board.I2C()  # uses board.SCL and board.SDA
# i2c_bus = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

# keyboard definitions
# macropad = 

# create the trellis
trellis = NeoTrellis(i2c_bus)

# Set the brightness value (0 to 1.0)
trellis.brightness = 0.5

# some color definitions
OFF = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)

sleep_timer = 5
sleep_time_start = time.time()

def disp_key_val(event):
    sleep_time_start = time.time()
    trellis_unsleep()
    time.sleep(1)
    if event.edge == NeoTrellis.EDGE_RISING:
        print("Event: {} press".format(event.number))
        trellis.pixels[event.number] = CYAN
    elif event.edge == NeoTrellis.EDGE_FALLING:
        print("Event: {} release".format(event.number))
        trellis.pixels[event.number] = GREEN
        time.sleep(0.5)
        trellis.pixels[event.number] = OFF
    time.sleep(1)
        
# def breathe(event):

for i in range(16):
    trellis.activate_key(i, NeoTrellis.EDGE_RISING)
    trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
    trellis.callbacks[i] = disp_key_val
    trellis.pixels[i] = PURPLE
    time.sleep(0.1)
    trellis.pixels[i] = OFF

def trellis_sleep():
    for i in range(16):
        trellis.pixels[i] = RED

def trellis_unsleep():
    for i in range(16):
        trellis.pixels[i] = OFF

while True:
    trellis.sync()
    time.sleep(0.02)
    if time.time() - sleep_time_start >= sleep_timer:
        trellis_sleep()