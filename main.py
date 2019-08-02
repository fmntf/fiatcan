import can
import threading
import time
import os
from can import Message
from FiatProtocol import *


can_interface = 'vcan0' if os.uname()[4] == 'x86_64' else 'can0'
bus = can.ThreadSafeBus(interface="socketcan", channel=can_interface, bitrate=50000)
app_running = True
body_operational = False


def read_thread_fn(bus):
    br = can.BufferedReader()
    notifier = can.Notifier(bus, [br])
    global body_operational
    while app_running:
        message = br.get_message(1)
        if message is not None:
            arbid = "{0:08x}".format(message.arbitration_id).upper()
            payload = ba(message.data)
            #print("From {}: {}".format(arbid, payload))

            if message.arbitration_id == CANID_BODY_BUTTONS:  # buttons
                if payload & MASK_BUTTON_VOLUME_UP == MASK_BUTTON_VOLUME_UP:
                    print("Volume + key")
                if payload & MASK_BUTTON_VOLUME_DN == MASK_BUTTON_VOLUME_DN:
                    print("Volume - key")
                if payload & MASK_BUTTON_WINDOWS == MASK_BUTTON_WINDOWS:
                    print("Windows key")
                if payload & MASK_BUTTON_MUTE == MASK_BUTTON_MUTE:
                    print("Mute key")
                if payload & MASK_BUTTON_UP == MASK_BUTTON_UP:
                    print("Up key")
                if payload & MASK_BUTTON_DOWN == MASK_BUTTON_DOWN:
                    print("Down key")
                if payload & MASK_BUTTON_MENU == MASK_BUTTON_MENU:
                    print("Menu key")
                if payload & MASK_BUTTON_SOURCE == MASK_BUTTON_SOURCE:
                    print("Source key")

            if message.arbitration_id == CANID_BODY_STATUS:
                sys_status = payload[0:16]
                print("Body computer asked for status, answering {}...".format(sys_status))
                bus.send(Message(arbitration_id=CANID_BM_STATUS, data=bytearray(sys_status.bytes)))
                if sys_status & MESSAGE_STATUS_WORKING == MESSAGE_STATUS_WORKING:
                    body_operational = True
                else:
                    body_operational = False

            if message.arbitration_id == CANID_4003_PROXI:
                print("Answering PROXI request...")
                bus.send(Message(arbitration_id=CANID_BM_PROXI, data=bytearray(payload.bytes)))

    notifier.stop()


def send1hz_thread_fn(bus):
    watchdog1 = Message(arbitration_id=CANID_BM_WATCHDOG, data=bytearray(MESSAGE_BM_WATCHDOG1.bytes))
    watchdog2 = Message(arbitration_id=CANID_BM_WATCHDOG, data=bytearray(MESSAGE_BM_WATCHDOG2.bytes))
    bm_playing = Message(arbitration_id=CANID_BM_AUDIO_CHANNEL, data=bytearray(MASK_AUDIOCH_MEDIAPLAYER.bytes))
    song_time = Message(arbitration_id=CANID_BM_TRACK_TIME, data=bytearray(MESSAGE_BM_ZERO_SECONDS.bytes))

    start_time = time.time()
    while app_running:
        if body_operational:
            bus.send(bm_playing)
            time.sleep(0.3)

            bus.send(song_time)
            time.sleep(0.3)

            bus.send(watchdog1)
            time.sleep(0.02)
            bus.send(watchdog2)

        time.sleep(1.0 - ((time.time() - start_time) % 1.0))


readThread = threading.Thread(target=read_thread_fn, args=(bus,))
readThread.start()

sendThread = threading.Thread(target=send1hz_thread_fn, args=(bus,))
sendThread.start()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        app_running = False
        readThread.join()
        sendThread.join()
        bus.shutdown()
        exit(0)
