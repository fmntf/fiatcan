import can
import os
import time
from BluetoothPlayer import BluetoothPlayer
from BodyComputerManager import BodyComputerManager
from CanOneHertzLoop import CanOneHertzLoop
from Menu import Menu


can_interface = 'vcan0' if os.uname()[4] == 'x86_64' else 'can0'
bus = can.ThreadSafeBus(interface="socketcan", channel=can_interface, bitrate=50000)

menu = Menu()
player = BluetoothPlayer()

body_manager = BodyComputerManager(bus)
body_manager.start()

onehz_loop = CanOneHertzLoop(bus)
onehz_loop.start()

body_manager.on_event('button',            menu.on_button)
body_manager.on_event('body_state_change', onehz_loop.on_body_state_change)
body_manager.on_event('bm_state_change',   onehz_loop.on_bm_state_change)
body_manager.on_event('bm_playing',        onehz_loop.on_bm_playing)
body_manager.on_event('bm_playing',        player.on_bm_playing)

menu.on_event('instpanel_display', body_manager.instpanel_display)
menu.on_event('instpanel_display', onehz_loop.instpanel_display)
menu.on_event('shutdown',          onehz_loop.on_shutdown)
menu.on_event('remote',            player.on_button)


player.on_event('track',    body_manager.radiounit_display)
player.on_event('position', onehz_loop.on_track_position)
player.on_event('playing',  onehz_loop.on_bm_playing)

print("Entering main loop")
while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        body_manager.prepare_shutdown()
        onehz_loop.prepare_shutdown()
        player.prepare_shutdown()
        body_manager.join()
        onehz_loop.join()
        bus.shutdown()
        exit(0)
