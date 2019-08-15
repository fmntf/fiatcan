import threading
import time
from can import Message
from FiatProtocol import *


class CanOneHertzLoop(threading.Thread):

    should_run = True
    track_position = 0
    bm_ch_playing = None
    bm_ch_playing_locked = None
    bm_ch_phone_locked = None
    bm_ch_muted = None
    bm_channel = None
    bt_is_playing = False
    instpanel_menu_opened = False
    phone_calling = False

    def __init__(self, bus):
        super().__init__()
        self.bus = bus

        self.bm_ch_playing = Message(arbitration_id=CANID_BM_AUDIO_CHANNEL, data=bytearray(MASK_AUDIOCH_MEDIAPLAYER.bytes))
        self.bm_ch_playing_locked = Message(arbitration_id=CANID_BM_AUDIO_CHANNEL, data=bytearray((MASK_AUDIOCH_MEDIAPLAYER | MASK_AUDIOCH_LOCKED).bytes))
        self.bm_ch_phone_locked = Message(arbitration_id=CANID_BM_AUDIO_CHANNEL, data=bytearray((MASK_AUDIOCH_PHONE | MASK_AUDIOCH_LOCKED).bytes))
        self.bm_ch_muted = Message(arbitration_id=CANID_BM_AUDIO_CHANNEL, data=bytearray(MASK_AUDIOCH_MUTED.bytes))
        self.bm_channel = self.bm_ch_muted

    def run(self):
        watchdog1 = Message(arbitration_id=CANID_BM_WATCHDOG, data=bytearray(MESSAGE_BM_WATCHDOG1.bytes))
        watchdog2 = Message(arbitration_id=CANID_BM_WATCHDOG, data=bytearray(MESSAGE_BM_WATCHDOG2.bytes))

        start_time = time.time()
        while self.should_run:
            self.bus.send(self.bm_channel)
            time.sleep(0.2)

            seconds = "0x{:02d}{:02d}487800000000".format(self.track_position // 60,self.track_position % 60)
            self.bus.send(Message(arbitration_id=CANID_BM_TRACK_TIME, data=bytearray(ba(hex=seconds).bytes)))
            time.sleep(0.05)

            self.bus.send(watchdog1)
            time.sleep(0.02)
            self.bus.send(watchdog2)

            if self.bt_is_playing:
                self.track_position += 1

            time.sleep(1.0 - ((time.time() - start_time) % 1.0))

    def on_bt_playing(self, is_playing):
        self.bt_is_playing = is_playing
        self.select_audio_channel()

    def on_bt_position(self, seconds):
        print("Received track position: {}".format(seconds))
        self.track_position = seconds

    def shutdown(self):
        self.should_run = False

    def on_menu_opened(self, is_open):
        self.instpanel_menu_opened = is_open
        self.select_audio_channel()

    def on_phone(self, number):
        if number is None:
            self.phone_calling = False
        else:
            self.phone_calling = True

        self.select_audio_channel()

    def select_audio_channel(self):
        if self.phone_calling:
            self.bm_channel = self.bm_ch_phone_locked
        else:
            if self.instpanel_menu_opened:
                self.bm_channel = self.bm_ch_playing_locked
            else:
                self.bm_channel = self.bm_ch_playing
