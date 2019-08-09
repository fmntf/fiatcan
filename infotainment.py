import can
import os
import time
from BluetoothPlayer import BluetoothPlayer
from BodyComputerManager import BodyComputerManager
from CanOneHertzLoop import CanOneHertzLoop
from Menu import Menu
from PhoneManager import PhoneManager


can_interface = 'vcan0' if os.uname()[4] == 'x86_64' else 'can0'
bus = can.ThreadSafeBus(interface="socketcan", channel=can_interface, bitrate=50000)

body_manager = BodyComputerManager(bus)
body_manager.start()

onehz_loop = CanOneHertzLoop(bus)
onehz_loop.start()

menu = Menu(bus)
player = BluetoothPlayer()
phone = PhoneManager()
buttons = body_manager.buttons

body_manager.on_event('bm_playing', onehz_loop.on_bm_playing)
body_manager.on_event('bm_playing', player.on_bm_playing)

menu.on_event('menu', onehz_loop.on_menu)
menu.on_event('menu', buttons.on_menu)

player.on_event('position', onehz_loop.on_bm_position)
player.on_event('playing',  onehz_loop.on_bm_playing)

buttons.on_event('menu',  menu.on_button)
buttons.on_event('media', player.on_button)
buttons.on_event('phone', phone.on_button)

phone.on_event('call', onehz_loop.on_phone)
phone.on_event('call', buttons.on_phone)

print("Entering main loop")
while True:
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        print("Shutting down...")
        body_manager.shutdown()
        onehz_loop.shutdown()
        player.shutdown()
        body_manager.join()
        onehz_loop.join()
        bus.shutdown()
        exit(0)
