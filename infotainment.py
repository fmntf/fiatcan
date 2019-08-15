import can
import os
import time
from BluetoothPlayer import BluetoothPlayer
from BodyComputerManager import BodyComputerManager
from CanOneHertzLoop import CanOneHertzLoop
from InstrumentPanel import InstrumentPanel
from Menu import Menu
from PhoneManager import PhoneManager
from TextMessage import TextMessage

can_interface = 'vcan0' if os.uname()[4] == 'x86_64' else 'can0'
bus = can.ThreadSafeBus(interface="socketcan", channel=can_interface, bitrate=50000)

body_manager = BodyComputerManager(bus)
body_manager.start()

onehz_loop = CanOneHertzLoop(bus)
onehz_loop.start()

textmessage = TextMessage(bus)
menu = Menu()
player = BluetoothPlayer(textmessage)
phone = PhoneManager()
buttons = body_manager.buttons
instpanel = InstrumentPanel(textmessage)

body_manager.on_event('audio_channel', player.on_audio_channel)

menu.on_event('item', instpanel.on_menu)

instpanel.on_event('menu_opened', onehz_loop.on_menu_opened)
instpanel.on_event('menu_opened', buttons.on_menu_opened)

player.on_event('position', onehz_loop.on_bt_position)
player.on_event('playing', onehz_loop.on_bt_playing)

buttons.on_event('menu',  menu.on_button)
buttons.on_event('media', player.on_button)
buttons.on_event('phone', phone.on_button)

phone.on_event('call', onehz_loop.on_phone)
phone.on_event('call', buttons.on_phone)
phone.on_event('call', instpanel.on_phone)

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
